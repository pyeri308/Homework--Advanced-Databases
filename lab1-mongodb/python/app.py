"""MongoDB từ Python (pymongo + pandas).

Chạy sau khi đã: docker compose up -d  và chạy 01_insert.js (để có dữ liệu).
"""
import pandas as pd
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=3000)
client.admin.command("ping")  # báo lỗi ngay nếu MongoDB chưa chạy
orders = client.shop.orders

# Create — xoá trước để chạy lại không bị lỗi trùng _id
orders.delete_one({"_id": 1004})
orders.insert_one({"_id": 1004, "customer": {"name": "Hung", "city": "Hue"},
                   "status": "paid", "items": []})

# Read — filter và projection là dict, giống hệt trong shell
print("=== Đơn hàng paid ===")
for doc in orders.find({"status": "paid"}, {"customer.name": 1, "status": 1}):
    print(doc)

# Aggregation — đưa thẳng kết quả vào pandas
pipeline = [
    {"$unwind": "$items"},
    {"$group": {"_id": "$items.sku", "units": {"$sum": "$items.qty"}}},
]
df = pd.DataFrame(orders.aggregate(pipeline))
print("\n=== Số lượng bán theo sku ===")
print(df)
