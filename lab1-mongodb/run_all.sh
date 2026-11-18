#!/usr/bin/env bash
# Chạy toàn bộ bài và lưu kết quả vào thư mục results/  (macOS / Linux / Git Bash / GitHub Actions)
set -euo pipefail
cd "$(dirname "$0")"
export MSYS_NO_PATHCONV=1     # tránh Git Bash trên Windows đổi sai đường dẫn /scripts/...
export PYTHONUTF8=1

mkdir -p results
docker compose up -d

echo "Đợi MongoDB sẵn sàng..."
until docker compose exec -T mongo mongosh --quiet --eval "db.adminCommand('ping').ok" >/dev/null 2>&1; do
  sleep 1
done

run() {
  echo ">>> $1"
  docker compose exec -T mongo mongosh --quiet -f "/scripts/$1.js" | tee "results/$1.txt"
}

run 01_insert
run 02_queries
run 03_update_delete
run 04_aggregation
run 05_indexes

run ex1_shapes
docker compose exec -T mongo mongosh --quiet -f /scripts/01_insert.js > /dev/null   # reset trước bài 2
run ex2_revenue_by_city
run ex3_index_benchmark

docker compose exec -T mongo mongosh --quiet -f /scripts/01_insert.js > /dev/null   # reset trước Python
echo ">>> python/app.py"
python python/app.py | tee results/python_app.txt

echo "Xong! Kết quả nằm trong thư mục results/"
