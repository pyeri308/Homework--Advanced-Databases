"""Chạy ở terminal thứ hai để xem sơ đồ ghế cập nhật trực tiếp:  python subscriber.py"""
from common import r

ps = r.pubsub(ignore_subscribe_messages=True)
ps.subscribe("seats:c1")
print("Đang nghe kênh seats:c1 ... (Ctrl+C để thoát)")
for msg in ps.listen():
    print("nhận:", msg["data"])
