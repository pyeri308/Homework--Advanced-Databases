"""Lab TicketRush — bán vé concert trên Redis.

Chạy tất cả các bước:     python ticketrush.py
Chạy một bước (vd bước 4): python ticketrush.py 4

Thiết kế key:
    hold:{event}:{seat}   string + TTL   ai đang giữ ghế
    sold:{event}          set            các ghế đã thanh toán
    stock:{event}         string         số vé đứng còn lại
    buyers:{event}        set            người đã mua vé đứng
    rl:sliding:{user}     sorted set     thời điểm các request gần đây
    queue:{event}         sorted set     phòng chờ, score = thời điểm vào
"""
import random
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from common import r, title

# ---------------------------------------------------------------- Bước 0
def race(fn, n=50):
    """Chạy fn(i) từ n luồng cùng lúc, trả về list kết quả."""
    with ThreadPoolExecutor(max_workers=n) as pool:
        return list(pool.map(fn, range(n)))


# ---------------------------------------------------------------- Bước 1
def hold_naive(event, seat, user):
    key = f"hold:{event}:{seat}"
    if r.get(key) is None:
        time.sleep(0.01)                 # nới rộng khe hở để thấy rõ lỗi
        r.set(key, user, ex=300)
        return True
    return False


def hold_nx(event, seat, user, ttl=300):
    return bool(r.set(f"hold:{event}:{seat}", user, nx=True, ex=ttl))


# ---------------------------------------------------------------- Bước 2
HOLD = r.register_script("""
if redis.call('SISMEMBER', KEYS[2], ARGV[2]) == 1 then return 0 end
if redis.call('SET', KEYS[1], ARGV[1], 'NX', 'EX', ARGV[3]) then return 1 end
return 0
""")

CONFIRM = r.register_script("""
if redis.call('GET', KEYS[1]) == ARGV[1] then
  redis.call('SADD', KEYS[2], ARGV[2])
  redis.call('DEL', KEYS[1])
  return 1
end
return 0
""")

RELEASE = r.register_script("""
if redis.call('GET', KEYS[1]) == ARGV[1] then
  return redis.call('DEL', KEYS[1])
end
return 0
""")


def hold(event, seat, user, ttl=300):
    return bool(HOLD(keys=[f"hold:{event}:{seat}", f"sold:{event}"], args=[user, seat, ttl]))


def confirm(event, seat, user):
    return bool(CONFIRM(keys=[f"hold:{event}:{seat}", f"sold:{event}"], args=[user, seat]))


def release(event, seat, user):
    return bool(RELEASE(keys=[f"hold:{event}:{seat}"], args=[user]))


def seat_map(event, seats):
    sold = r.smembers(f"sold:{event}")
    return {
        s: "sold" if s in sold else "held" if r.exists(f"hold:{event}:{s}") else "free"
        for s in seats
    }


# ---------------------------------------------------------------- Bước 3
def buy_general(event, user):
    left = r.decr(f"stock:{event}")
    if left < 0:
        r.incr(f"stock:{event}")         # hoàn lại: đã hết vé
        return False
    r.sadd(f"buyers:{event}", user)
    return True


def buy_general_naive(event, user):
    """Phiên bản SAI (cố ý): kiểm tra rồi mới trừ -> bán lố."""
    if int(r.get(f"stock:{event}")) > 0:
        time.sleep(0.001)
        r.decr(f"stock:{event}")
        r.sadd(f"buyers:{event}", user)
        return True
    return False


# ---------------------------------------------------------------- Bước 4
def allow_fixed(user, limit=5, window=10):
    key = f"rl:fixed:{user}:{int(time.time() // window)}"
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, window, nx=True)    # chỉ đặt TTL lần đầu
    count, _ = pipe.execute()
    return count <= limit


SLIDING = r.register_script("""
local now, window, limit = tonumber(ARGV[1]), tonumber(ARGV[2]), tonumber(ARGV[3])
redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, now - window)
if redis.call('ZCARD', KEYS[1]) < limit then
  redis.call('ZADD', KEYS[1], now, ARGV[4])
  redis.call('PEXPIRE', KEYS[1], window)
  return 1
end
return 0
""")


def allow_sliding(user, limit=5, window_ms=10_000):
    now = int(time.time() * 1000)
    return bool(SLIDING(keys=[f"rl:sliding:{user}"], args=[now, window_ms, limit, uuid.uuid4().hex]))


def try_hold(event, seat, user):
    if not allow_sliding(user):
        return "rate_limited"
    return "ok" if hold(event, seat, user) else "taken"


def wait_until_window_edge(window=10, before=0.2):
    time.sleep(window - time.time() % window - before)


# ---------------------------------------------------------------- Bước 5
def join_queue(event, user):
    r.zadd(f"queue:{event}", {user: time.time()}, nx=True)   # NX: vào lại vẫn giữ chỗ
    return r.zrank(f"queue:{event}", user) + 1


def admit(event, n):
    return [user for user, _ in r.zpopmin(f"queue:{event}", n)]


# ================================================================ DEMO
def step1():
    title("Bước 1: Giữ ghế và race condition")
    for k in range(1, 6):
        r.flushdb()
        wins = race(lambda i: hold_naive("c1", "A1", f"user{i}"))
        print(f"hold_naive lần {k}: winners = {sum(wins)}   (mong đợi 1)")
    for k in range(1, 6):
        r.flushdb()
        wins = race(lambda i: hold_nx("c1", "A1", f"user{i}"))
        print(f"hold_nx    lần {k}: winners = {sum(wins)}")
    print("Người giữ A1:", r.get("hold:c1:A1"), "| TTL:", r.ttl("hold:c1:A1"), "giây")
    time.sleep(2)
    print("Sau 2 giây TTL còn:", r.ttl("hold:c1:A1"), "giây")


def step2():
    title("Bước 2: Hold / confirm / release nguyên tử bằng Lua")
    r.flushdb()
    print('hold("c1","A1","linh")    ->', hold("c1", "A1", "linh"))     # True
    print('hold("c1","A1","nam")     ->', hold("c1", "A1", "nam"))      # False
    print('confirm("c1","A1","nam")  ->', confirm("c1", "A1", "nam"))   # False
    print('confirm("c1","A1","linh") ->', confirm("c1", "A1", "linh"))  # True
    print('hold("c1","A1","nam")     ->', hold("c1", "A1", "nam"))      # False, đã bán
    print("seat_map:", seat_map("c1", ["A1", "A2"]))
    print("SMEMBERS sold:c1 ->", r.smembers("sold:c1"))
    print('\nrelease: hold A2 bởi linh, nam thử release, rồi linh release')
    print('hold("c1","A2","linh")    ->', hold("c1", "A2", "linh"))
    print('release("c1","A2","nam")  ->', release("c1", "A2", "nam"))   # False
    print('release("c1","A2","linh") ->', release("c1", "A2", "linh"))  # True
    print("seat_map:", seat_map("c1", ["A1", "A2"]))


def step3():
    title("Bước 3: Flash sale vé đứng (100 vé, 500 người)")
    r.flushdb()
    r.set("stock:g1", 100)
    ok = race(lambda i: buy_general("g1", f"user{i}"), n=500)
    print("buy_general       -> bán:", sum(ok), "| stock còn:", r.get("stock:g1"),
          "| số buyers:", r.scard("buyers:g1"), "  (mong đợi 100 0 100)")

    r.flushdb()
    r.set("stock:g1", 100)
    ok = race(lambda i: buy_general_naive("g1", f"user{i}"), n=500)
    print("buy_general_naive -> bán:", sum(ok), "| stock còn:", r.get("stock:g1"),
          "| số buyers:", r.scard("buyers:g1"), "  <- bán lố!")


def step4():
    title("Bước 4: Rate limiting")
    r.flushdb()
    print("Fixed window, 8 request liên tiếp:", [allow_fixed("linh") for _ in range(8)])

    print("\nThí nghiệm biên cửa sổ (fixed window)...")
    wait_until_window_edge()
    first = [allow_fixed("bot") for _ in range(5)]
    time.sleep(0.4)
    second = [allow_fixed("bot") for _ in range(5)]
    print("Fixed  :", first + second, f"-> {sum(first + second)} request lọt trong 0.4s")

    print("\nThí nghiệm biên cửa sổ (sliding window)...")
    wait_until_window_edge()
    first = [allow_sliding("bot") for _ in range(5)]
    time.sleep(0.4)
    second = [allow_sliding("bot") for _ in range(5)]
    print("Sliding:", first + second, f"-> {sum(first + second)} request lọt trong 0.4s")

    print("\nGắn vào luồng đặt ghế (một bot bấm 8 lần):")
    r.flushdb()
    print([try_hold("c1", f"B{i}", "bot") for i in range(8)])


def step5():
    title("Bước 5: Phòng chờ ảo")
    r.flushdb()
    for name in ["u1", "u2", "u3"]:
        print(name, "vào hàng, vị trí", join_queue("c1", name))
    print("u1 vào lại, vị trí", join_queue("c1", "u1"), "(vẫn giữ chỗ)")
    print("admit 2 người:", admit("c1", 2))
    print("u3 giờ ở vị trí", join_queue("c1", "u3"))


def step6(runs=10):
    title("Bước 6: Stress test cuối — 100 người tranh 20 ghế")
    seats = [f"S{i}" for i in range(1, 21)]

    def buyer(i):
        user = f"user{i}"
        for seat in seats:
            if hold("c1", seat, user):
                time.sleep(random.random() * 0.05)       # đang thanh toán
                if confirm("c1", seat, user):
                    return seat
        return None

    all_ok = True
    for k in range(1, runs + 1):
        r.flushdb()
        got = [s for s in race(buyer, n=100) if s]
        result = (len(got), len(set(got)), r.scard("sold:c1"))
        all_ok &= result == (20, 20, 20)
        print(f"Lần {k:2}: {result[0]} {result[1]} {result[2]}")
    print("KẾT LUẬN:", "luôn 20 20 20, không bán trùng ghế" if all_ok else "CÓ LỖI!")


STEPS = {1: step1, 2: step2, 3: step3, 4: step4, 5: step5, 6: step6}

if __name__ == "__main__":
    chosen = [int(a) for a in sys.argv[1:]] or list(STEPS)
    for s in chosen:
        STEPS[s]()
