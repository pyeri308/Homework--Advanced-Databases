"""Phần mở rộng (Extensions) của lab TicketRush."""
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from common import r, title
from ticketrush import allow_sliding, confirm, hold

# ---------------------------------------------------------------- 1. Gia hạn giữ ghế
EXTEND = r.register_script("""
if redis.call('GET', KEYS[1]) ~= ARGV[1] then return 0 end
if redis.call('EXISTS', KEYS[2]) == 1 then return 0 end
local newttl = redis.call('TTL', KEYS[1]) + tonumber(ARGV[2])
redis.call('EXPIRE', KEYS[1], newttl)
redis.call('SET', KEYS[2], '1', 'EX', newttl)
return newttl
""")


def extend_hold(event, seat, user, extra=120):
    """Chỉ chủ ghế được gia hạn, và chỉ một lần. Trả về TTL mới (0 nếu bị từ chối)."""
    return EXTEND(keys=[f"hold:{event}:{seat}", f"extended:{event}:{seat}"], args=[user, extra])


# ---------------------------------------------------------------- 2. Đếm ngược
def countdown(event, seat):
    ttl = r.ttl(f"hold:{event}:{seat}")
    return "không có ai giữ" if ttl < 0 else f"còn {ttl // 60}:{ttl % 60:02d}"


# ---------------------------------------------------------------- 3. Giới hạn theo IP
def try_hold_ip(event, seat, user, ip):
    if not allow_sliding(f"user:{user}", limit=5):
        return "rate_limited_user"
    if not allow_sliding(f"ip:{ip}", limit=20):
        return "rate_limited_ip"
    return "ok" if hold(event, seat, user) else "taken"


# ---------------------------------------------------------------- 4. Pub/sub
def confirm_and_publish(event, seat, user):
    ok = confirm(event, seat, user)
    if ok:
        r.publish(f"seats:{event}", json.dumps({"type": "seat_sold", "seat": seat, "user": user}))
    return ok


if __name__ == "__main__":
    r.flushdb()

    title("Mở rộng 1 + 2: Gia hạn giữ ghế và đếm ngược")
    hold("c1", "A1", "linh", ttl=300)
    print("Đếm ngược:", countdown("c1", "A1"))
    print("nam gia hạn  ->", extend_hold("c1", "A1", "nam"), "(không phải chủ)")
    print("linh gia hạn ->", extend_hold("c1", "A1", "linh"), "giây")
    print("linh gia hạn lần 2 ->", extend_hold("c1", "A1", "linh"), "(chỉ được 1 lần)")
    print("Đếm ngược:", countdown("c1", "A1"))

    title("Mở rộng 3: Giới hạn theo IP (20 request / 10s / IP)")
    r.flushdb()
    results = [try_hold_ip("c1", f"S{i}", f"user{i}", "10.0.0.1") for i in range(30)]
    print("30 user khác nhau, cùng 1 IP:",
          {k: results.count(k) for k in sorted(set(results))})

    title("Mở rộng 4: Pub/sub — cập nhật sơ đồ ghế trực tiếp")
    r.flushdb()
    received = []
    ps = r.pubsub(ignore_subscribe_messages=True)
    ps.subscribe("seats:c1")

    def listen():
        for msg in ps.listen():
            received.append(msg["data"])
            print("  [subscriber] nhận:", msg["data"])
            if len(received) == 3:
                break

    t = threading.Thread(target=listen); t.start()
    time.sleep(0.2)
    for seat, user in [("A1", "linh"), ("A2", "nam"), ("A3", "mai")]:
        hold("c1", seat, user)
        confirm_and_publish("c1", seat, user)
    t.join(timeout=3); ps.close()
    print("Đã nhận", len(received), "thông báo")

    title("Mở rộng 5: Throughput — không Lua vs SET NX vs Lua (2000 lượt, 50 luồng)")
    N = 2000

    def naive(i):  # GET rồi SET, không nguyên tử
        k = f"hold:bench:S{i}"
        if r.get(k) is None:
            r.set(k, "u", ex=300)

    def nx(i):
        r.set(f"hold:bench:S{i}", "u", nx=True, ex=300)

    def lua(i):
        hold("bench", f"S{i}", "u")

    for name, fn in [("GET + SET (sai)", naive), ("SET NX EX", nx), ("Lua HOLD", lua)]:
        r.flushdb()
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=50) as pool:
            list(pool.map(fn, range(N)))
        dt = time.perf_counter() - start
        print(f"{name:<16}: {N / dt:8.0f} ops/s")
