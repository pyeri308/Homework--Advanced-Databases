-- 02_exercises.cql — 3 bài tập (Exercises)
-- Chạy: docker compose exec -T cass1 cqlsh -f /cql/02_exercises.cql
USE shop;

-- ===== Bài 1: "10 đơn mới nhất của một khách" và "đơn hàng theo ngày"
-- Mỗi câu hỏi một bảng; cùng dữ liệu được ghi vào cả hai (denormalize).
CREATE TABLE IF NOT EXISTS orders_by_customer (
    customer_id text,
    order_ts    timestamp,
    order_id    text,
    total       decimal,
    status      text,
    PRIMARY KEY ((customer_id), order_ts, order_id)
) WITH CLUSTERING ORDER BY (order_ts DESC, order_id ASC);

CREATE TABLE IF NOT EXISTS orders_by_day (
    order_day   date,
    order_ts    timestamp,
    order_id    text,
    customer_id text,
    total       decimal,
    PRIMARY KEY ((order_day), order_ts, order_id)
) WITH CLUSTERING ORDER BY (order_ts DESC, order_id ASC);

BEGIN BATCH
  INSERT INTO orders_by_customer (customer_id, order_ts, order_id, total, status) VALUES ('linh', '2026-10-20 09:00:00', 'o-1001', 43.0, 'paid');
  INSERT INTO orders_by_day      (order_day, order_ts, order_id, customer_id, total) VALUES ('2026-10-20', '2026-10-20 09:00:00', 'o-1001', 'linh', 43.0);
APPLY BATCH;
BEGIN BATCH
  INSERT INTO orders_by_customer (customer_id, order_ts, order_id, total, status) VALUES ('linh', '2026-10-21 14:30:00', 'o-1004', 12.5, 'shipped');
  INSERT INTO orders_by_day      (order_day, order_ts, order_id, customer_id, total) VALUES ('2026-10-21', '2026-10-21 14:30:00', 'o-1004', 'linh', 12.5);
APPLY BATCH;
BEGIN BATCH
  INSERT INTO orders_by_customer (customer_id, order_ts, order_id, total, status) VALUES ('nam', '2026-10-20 10:15:00', 'o-1002', 22.0, 'paid');
  INSERT INTO orders_by_day      (order_day, order_ts, order_id, customer_id, total) VALUES ('2026-10-20', '2026-10-20 10:15:00', 'o-1002', 'nam', 22.0);
APPLY BATCH;
BEGIN BATCH
  INSERT INTO orders_by_customer (customer_id, order_ts, order_id, total, status) VALUES ('mai', '2026-10-21 08:45:00', 'o-1003', 12.5, 'paid');
  INSERT INTO orders_by_day      (order_day, order_ts, order_id, customer_id, total) VALUES ('2026-10-21', '2026-10-21 08:45:00', 'o-1003', 'mai', 12.5);
APPLY BATCH;

-- 10 đơn mới nhất của linh
SELECT order_ts, order_id, total, status FROM orders_by_customer WHERE customer_id = 'linh' LIMIT 10;
-- Các đơn trong ngày 2026-10-20
SELECT order_ts, order_id, customer_id, total FROM orders_by_day WHERE order_day = '2026-10-20';

-- ===== Bài 2: 3 cảm biến + truy vấn thiếu partition key
CREATE TABLE IF NOT EXISTS ex_readings (
    sensor_id text, ts timestamp, temperature double,
    PRIMARY KEY ((sensor_id), ts)
) WITH CLUSTERING ORDER BY (ts DESC);
INSERT INTO ex_readings (sensor_id, ts, temperature) VALUES ('s1', '2026-10-22 08:00:00', 26.0);
INSERT INTO ex_readings (sensor_id, ts, temperature) VALUES ('s1', '2026-10-22 08:05:00', 26.4);
INSERT INTO ex_readings (sensor_id, ts, temperature) VALUES ('s2', '2026-10-22 08:00:00', 29.1);
INSERT INTO ex_readings (sensor_id, ts, temperature) VALUES ('s3', '2026-10-22 08:00:00', 31.7);
SELECT * FROM ex_readings WHERE sensor_id = 's2';
-- Thiếu partition key -> InvalidRequest (lỗi là kết quả mong đợi)
SELECT * FROM ex_readings WHERE temperature > 28;
-- Có partition key nhưng lọc theo cột thường cũng bị từ chối
SELECT * FROM ex_readings WHERE sensor_id = 's1' AND temperature > 26;

-- ===== Bài 3: chia partition theo tháng (time bucket)
-- Mỗi cảm biến có một partition cho mỗi tháng -> partition không phình mãi theo năm tháng.
CREATE TABLE IF NOT EXISTS readings_by_sensor_month (
    sensor_id   text,
    month       text,          -- dạng 'YYYY-MM'
    ts          timestamp,
    temperature double,
    humidity    double,
    PRIMARY KEY ((sensor_id, month), ts)
) WITH CLUSTERING ORDER BY (ts DESC);
INSERT INTO readings_by_sensor_month (sensor_id, month, ts, temperature, humidity) VALUES ('hn-01', '2026-10', '2026-10-22 08:00:00', 27.5, 71);
INSERT INTO readings_by_sensor_month (sensor_id, month, ts, temperature, humidity) VALUES ('hn-01', '2026-10', '2026-10-31 23:55:00', 26.9, 74);
INSERT INTO readings_by_sensor_month (sensor_id, month, ts, temperature, humidity) VALUES ('hn-01', '2026-11', '2026-11-01 00:00:00', 26.7, 75);
-- Đọc một tháng: phải đưa đủ cả hai cột của partition key
SELECT * FROM readings_by_sensor_month WHERE sensor_id = 'hn-01' AND month = '2026-10';
-- Hai tháng: liệt kê các partition bằng IN
SELECT * FROM readings_by_sensor_month WHERE sensor_id = 'hn-01' AND month IN ('2026-10', '2026-11');
-- Token khác nhau => hai tháng có thể nằm ở hai node khác nhau
SELECT DISTINCT sensor_id, month, token(sensor_id, month) FROM readings_by_sensor_month;
