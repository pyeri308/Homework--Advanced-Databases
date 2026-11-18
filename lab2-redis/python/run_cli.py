"""Chạy file .redis và in ra giống redis-cli (có cả lệnh lẫn kết quả) để lưu vào results/.

Dùng:  python python/run_cli.py redis/01_strings.redis
"""
import os
import shlex
import sys

import redis

from common import r

# client riêng, dùng giao thức RESP2 giống redis-cli để kết quả in ra y hệt
raw = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", "6379")),
                  protocol=2, decode_responses=True)


def fmt(value, indent=""):
    if value is None:
        return "(nil)"
    if isinstance(value, bool):
        return f"(integer) {int(value)}"
    if isinstance(value, int):
        return f"(integer) {value}"
    if isinstance(value, float):
        return f'"{value:g}"'
    if isinstance(value, (list, tuple)):
        if not value:
            return "(empty array)"
        return "\n".join(f"{indent}{i}) {fmt(v, indent + '   ')}" for i, v in enumerate(value, 1))
    if isinstance(value, dict):
        flat = [x for kv in value.items() for x in kv]
        return fmt(flat, indent)
    if value == "OK":
        return "OK"
    return f'"{value}"'


r.flushdb()
conn = raw.connection_pool.get_connection()   # kết nối thô: nhận phản hồi gốc, không qua xử lý của redis-py
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    print(f"127.0.0.1:6379> {line}")
    try:
        conn.send_command(*shlex.split(line))
        print(fmt(conn.read_response()))
    except Exception as e:  # in lỗi giống redis-cli
        print(f"(error) {e}")
