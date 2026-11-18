-- 01_basics.cql — phần lý thuyết: keyspace, bảng thiết kế theo truy vấn, insert, select
-- Chạy: docker compose exec -T cass1 cqlsh -f /cql/01_basics.cql

DROP KEYSPACE IF EXISTS shop;
CREATE KEYSPACE shop
  WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
USE shop;

CREATE TABLE readings_by_sensor (
    sensor_id   text,
    ts          timestamp,
    temperature double,
    humidity    double,
    PRIMARY KEY ((sensor_id), ts)
) WITH CLUSTERING ORDER BY (ts DESC);

INSERT INTO readings_by_sensor (sensor_id, ts, temperature, humidity)
VALUES ('hn-01', '2026-10-22 08:00:00', 27.5, 71);
INSERT INTO readings_by_sensor (sensor_id, ts, temperature, humidity)
VALUES ('hn-01', '2026-10-22 08:05:00', 27.8, 70);
INSERT INTO readings_by_sensor (sensor_id, ts, temperature, humidity)
VALUES ('hn-02', '2026-10-22 08:00:00', 25.1, 80);

-- Nhanh: có partition key
SELECT * FROM readings_by_sensor WHERE sensor_id = 'hn-01' LIMIT 10;

SELECT * FROM readings_by_sensor
WHERE sensor_id = 'hn-01' AND ts >= '2026-10-22 08:02:00';

-- Bị từ chối: không có partition key (lỗi InvalidRequest là kết quả mong đợi)
SELECT * FROM readings_by_sensor WHERE temperature > 27;
