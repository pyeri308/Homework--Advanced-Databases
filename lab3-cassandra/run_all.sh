#!/usr/bin/env bash
# Lab 3 – Cassandra SensorRing: chạy TỰ ĐỘNG toàn bộ (lý thuyết, bài tập, bước 0 → 4) và lưu kết quả vào results/.
# Chạy bằng bash: macOS / Linux / Git Bash trên Windows / GitHub Actions.  Mất khoảng 10–15 phút.
# Cần ~3 GB RAM trống cho 3 node (Docker Desktop: Settings -> Resources -> Memory >= 4 GB).
set -euo pipefail
cd "$(dirname "$0")"
export MSYS_NO_PATHCONV=1 PYTHONUTF8=1
PY=$(command -v python || command -v python3)
mkdir -p results

cql()      { docker compose exec -T "$1" cqlsh -e "$2"; }
nodetool() { local n=$1; shift; docker compose exec -T "$n" nodetool "$@"; }
log()      { echo; echo "\$ $*"; }

wait_healthy() {   # đợi đến khi các node hiện (healthy)
  for svc in "$@"; do
    echo "... đợi $svc healthy"
    until [ "$(docker inspect -f '{{.State.Health.Status}}' "$(docker compose ps -a -q "$svc")" 2>/dev/null)" = healthy ]; do sleep 3; done
  done
}
wait_status() {    # wait_status <node hỏi> <số UN> <số DN>
  echo "... đợi nodetool status: $2 UN, $3 DN"
  until s=$(nodetool "$1" status 2>/dev/null) && [ "$(grep -c '^UN' <<<"$s")" = "$2" ] && [ "$(grep -c '^DN' <<<"$s")" = "$3" ]; do sleep 3; done
}

# ------------------------------------------------------------------ Bước 0
step0() {
  echo "=== BƯỚC 0: khởi động cụm 3 node (khoảng 3 phút) ==="
  docker compose up -d --wait --wait-timeout 900
  wait_status cass1 3 0
  log docker compose exec cass1 nodetool status; nodetool cass1 status
  log "docker inspect (IP của từng container)"
  docker inspect -f '{{.Name}} {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker compose ps -q)
  log python python/sensorring.py load; "$PY" python/sensorring.py load
}

# ------------------------------------------------------------------ Lý thuyết + bài tập
theory() {
  echo "=== PHẦN LÝ THUYẾT: 01_basics.cql (lỗi InvalidRequest ở cuối là mong đợi) ==="
  docker compose exec -T cass1 cqlsh -f /cql/01_basics.cql 2>&1 || true
  log python python/basics.py; "$PY" python/basics.py
}
exercises() {
  echo "=== BÀI TẬP: 02_exercises.cql (các lỗi InvalidRequest là mong đợi) ==="
  docker compose exec -T cass1 cqlsh -f /cql/02_exercises.cql 2>&1 || true
}

# ------------------------------------------------------------------ Bước 1
step1() {
  echo "=== BƯỚC 1: partition key quyết định node ==="
  log "SELECT DISTINCT sensor_id, token(sensor_id) FROM iot.readings_by_sensor LIMIT 5;"
  cql cass1 "SELECT DISTINCT sensor_id, token(sensor_id) FROM iot.readings_by_sensor LIMIT 5;"
  log nodetool getendpoints iot readings_by_sensor hn-01
  nodetool cass1 getendpoints iot readings_by_sensor hn-01
  log "nodetool status iot   (RF=3: mỗi node Owns 100%)"; nodetool cass1 status iot
  cql cass1 "CREATE KEYSPACE IF NOT EXISTS ring1 WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
             CREATE TABLE IF NOT EXISTS ring1.sensors (sensor_id text PRIMARY KEY);"
  log "getendpoints ring1 (RF=1)"
  for s in hn-01 hn-02 hn-03 hn-04 hn-05 hn-06; do
    echo "$s -> $(nodetool cass1 getendpoints ring1 sensors $s)"
  done
  log "nodetool status ring1   (Owns cộng lại ~100%)"; nodetool cass1 status ring1
  log nodetool ring; nodetool cass1 ring
  log "Kiểm tra quy tắc 'node kế tiếp theo chiều kim đồng hồ'"; "$PY" python/verify_ring.py
}

# ------------------------------------------------------------------ Bước 2
step2() {
  echo "=== BƯỚC 2: truy vấn theo partition vs quét toàn bảng ==="
  log "SELECT * ... WHERE temperature > 31.5   (bị từ chối)"
  cql cass1 "SELECT * FROM iot.readings_by_sensor WHERE temperature > 31.5;" 2>&1 || true
  log "TRACING: theo partition key"
  cql cass1 "CONSISTENCY ONE; TRACING ON;
    SELECT ts, temperature FROM iot.readings_by_sensor WHERE sensor_id = 'hn-01' LIMIT 3;" \
    | grep -E "Executing|live rows|Request complete" || true
  log "TRACING: ALLOW FILTERING"
  cql cass1 "CONSISTENCY ONE; TRACING ON;
    SELECT count(*) FROM iot.readings_by_sensor WHERE temperature > 31.5 ALLOW FILTERING;" \
    | grep -E "range requests|Executing|live rows|Request complete|count|^ +[0-9]+$" || true
}

# ------------------------------------------------------------------ Bước 3
step3() {
  echo "=== BƯỚC 3: consistency level khi mất node ==="
  log "3 node sống: python python/sensorring.py cl"; "$PY" python/sensorring.py cl
  log docker compose stop cass3; docker compose stop cass3
  wait_status cass1 2 1; nodetool cass1 status
  log "2 node sống: python python/sensorring.py cl"; "$PY" python/sensorring.py cl
  log docker compose stop cass2; docker compose stop cass2
  wait_status cass1 1 2; nodetool cass1 status
  log "1 node sống: python python/sensorring.py cl"; "$PY" python/sensorring.py cl
}

# ------------------------------------------------------------------ Bước 4
step4() {
  echo "=== BƯỚC 4: replica cũ (stale) và cách Cassandra sửa ==="
  log docker compose start cass2; docker compose start cass2; wait_healthy cass2
  log "nodetool disablehandoff trên cass1, cass2"
  nodetool cass1 disablehandoff; nodetool cass2 disablehandoff
  nodetool cass1 statushandoff; nodetool cass2 statushandoff

  log "Ghi hn-99 ở QUORUM khi cass3 đang tắt"
  cql cass1 "CONSISTENCY QUORUM;
    INSERT INTO iot.readings_by_sensor (sensor_id, ts, temperature, humidity)
    VALUES ('hn-99', '2026-11-01 09:00:00', 41.0, 30);"

  log docker compose start cass3; docker compose start cass3; wait_healthy cass3
  log docker compose stop cass1 cass2; docker compose stop cass1 cass2
  log "Đọc ở ONE từ cass3 (chỉ cass3 trả lời được) -> mong đợi 0 rows"
  cql cass3 "CONSISTENCY ONE; SELECT * FROM iot.readings_by_sensor WHERE sensor_id = 'hn-99';"

  log docker compose start cass1 cass2; docker compose start cass1 cass2; wait_healthy cass1 cass2
  log "Đọc ở ALL từ cass3 -> mong đợi 1 rows (read repair)"
  for i in $(seq 1 40); do
    if out=$(cql cass3 "CONSISTENCY ALL; SELECT * FROM iot.readings_by_sensor WHERE sensor_id = 'hn-99';" 2>&1) \
       && grep -q "(1 rows)" <<<"$out"; then echo "$out"; break; fi
    echo "(lần $i: chưa đủ replica, thử lại sau 5 giây)"; sleep 5
  done

  log nodetool repair iot; nodetool cass3 repair iot | tail -3
  log "statushandoff (handoff tự bật lại sau khi node khởi động lại)"
  nodetool cass1 statushandoff; nodetool cass2 statushandoff
}

step0     2>&1 | tee results/step0_cluster.txt
theory    2>&1 | tee results/theory.txt
exercises 2>&1 | tee results/exercises.txt
step1     2>&1 | tee results/step1_partition.txt
step2     2>&1 | tee results/step2_tracing.txt
step3     2>&1 | tee results/step3_consistency.txt
step4     2>&1 | tee results/step4_stale_replica.txt

echo
echo "Xong! Kết quả nằm trong lab3-cassandra/results/"
echo "Cụm vẫn đang chạy để bạn thử thêm. Dọn dẹp: docker compose down -v"
