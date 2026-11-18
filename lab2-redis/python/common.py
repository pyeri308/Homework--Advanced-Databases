"""Kết nối Redis dùng chung cho mọi script."""
import os

import redis

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
)
r.ping()  # báo lỗi ngay nếu Redis chưa chạy


def title(text):
    print(f"\n{'=' * 60}\n{text}\n{'=' * 60}")
