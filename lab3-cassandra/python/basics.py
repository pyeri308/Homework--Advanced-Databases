"""Cassandra từ Python (phần lý thuyết của bài). Chạy sau 01_basics.cql (cần keyspace shop)."""
from datetime import datetime

from cassandra.cluster import Cluster

cluster = Cluster(["127.0.0.1"])
session = cluster.connect("shop")

insert = session.prepare(
    "INSERT INTO readings_by_sensor (sensor_id, ts, temperature, humidity) "
    "VALUES (?, ?, ?, ?)"
)
session.execute(insert, ("hn-01", datetime(2026, 10, 22, 8, 10), 28.0, 69.0))

rows = session.execute(
    "SELECT ts, temperature FROM readings_by_sensor WHERE sensor_id = %s LIMIT 5",
    ("hn-01",),
)
print("5 bản ghi mới nhất của hn-01:")
for row in rows:
    print(row.ts, row.temperature)

cluster.shutdown()
