"""Redis từ Python: cache-aside và rate limiter đơn giản (phần lý thuyết của bài)."""
import json
import time

from common import r, title

r.flushdb()


def slow_query(product_id: int) -> dict:
    time.sleep(1)                                   # giả lập truy vấn database chậm
    return {"id": product_id, "title": "Python Basics", "price": 12.5}


def get_product(product_id: int) -> dict:
    key = f"product:{product_id}"
    cached = r.get(key)
    if cached is not None:
        return json.loads(cached)                   # hit: nhanh
    product = slow_query(product_id)                # miss: chậm
    r.set(key, json.dumps(product), ex=300)         # giữ 5 phút
    return product


title("Cache-aside")
start = time.perf_counter(); get_product(7); print(f"first : {time.perf_counter() - start:.3f}s  (cache miss)")
start = time.perf_counter(); get_product(7); print(f"second: {time.perf_counter() - start:.3f}s  (cache hit)")
print("TTL product:7 =", r.ttl("product:7"), "giây")


def allow(user: str, limit: int = 5) -> bool:
    key = f"rate:{user}:{int(time.time() // 60)}"   # mỗi phút một bộ đếm
    count = r.incr(key)
    if count == 1:
        r.expire(key, 60)
    return count <= limit


title("Rate limiter đơn giản: 5 request / phút")
print([allow("linh") for _ in range(7)])
