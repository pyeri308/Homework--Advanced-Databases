"""Bài tập (Exercises) của bài Redis."""
import json
import time

from common import r, title

r.flushdb()

# ---------------------------------------------------------------- Bài 1
title("Bài 1: Leaderboard bằng sorted set — top 3")
r.zadd("leaderboard", {"linh": 1200, "nam": 950, "mai": 1430, "hung": 1100, "lan": 1310})
for rank, (player, score) in enumerate(r.zrevrange("leaderboard", 0, 2, withscores=True), 1):
    print(f"#{rank}  {player:<6} {int(score)}")
print("Hạng của nam:", r.zrevrank("leaderboard", "nam") + 1)

# ---------------------------------------------------------------- Bài 2
title("Bài 2: Hồ sơ người dùng (hash) + tìm theo thành phố (set mỗi city)")
users = {
    1: {"name": "Linh", "city": "Hanoi", "age": 21},
    2: {"name": "Nam", "city": "Da Nang", "age": 22},
    3: {"name": "Mai", "city": "Hanoi", "age": 20},
    4: {"name": "Hung", "city": "Hue", "age": 23},
    5: {"name": "Lan", "city": "Hanoi", "age": 19},
}


def city_key(city):
    return "city:" + city.lower().replace(" ", "_")


for uid, profile in users.items():
    r.hset(f"user:{uid}", mapping=profile)
    r.sadd(city_key(profile["city"]), uid)       # "index" tự xây: city -> tập id


def users_in(city):
    ids = sorted(r.smembers(city_key(city)), key=int)
    pipe = r.pipeline()
    for uid in ids:
        pipe.hgetall(f"user:{uid}")
    return list(zip(ids, pipe.execute()))


for city in ["Hanoi", "Da Nang"]:
    print(f"Người dùng ở {city}:")
    for uid, profile in users_in(city):
        print(f"  user:{uid} -> {profile}")

# ---------------------------------------------------------------- Bài 3
title("Bài 3: Đo tốc độ cache-aside với 100 request lặp lại")
SLOW = 0.1   # giây/lần truy vấn giả lập (bài học dùng 1s; giảm để chạy nhanh hơn)
N = 100


def slow_query(product_id):
    time.sleep(SLOW)
    return {"id": product_id, "title": "Python Basics", "price": 12.5}


def get_product(product_id):
    key = f"product:{product_id}"
    cached = r.get(key)
    if cached is not None:
        return json.loads(cached)
    product = slow_query(product_id)
    r.set(key, json.dumps(product), ex=300)
    return product


start = time.perf_counter()
for _ in range(N):
    slow_query(7)
no_cache = time.perf_counter() - start

r.delete("product:7")
start = time.perf_counter()
for _ in range(N):
    get_product(7)
with_cache = time.perf_counter() - start

print(f"Không cache : {no_cache:.3f}s cho {N} request")
print(f"Có cache    : {with_cache:.3f}s cho {N} request (1 miss + {N - 1} hit)")
print(f"Tăng tốc    : ~{no_cache / with_cache:.0f} lần")
