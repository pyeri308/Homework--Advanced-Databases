#!/usr/bin/env bash
# Lab 4 – Neo4j: chạy toàn bộ và lưu kết quả vào results/  (macOS / Linux / Git Bash / GitHub Actions)
set -euo pipefail
cd "$(dirname "$0")"
export MSYS_NO_PATHCONV=1 PYTHONUTF8=1
PY=$(command -v python || command -v python3)
mkdir -p results

echo "Khởi động Neo4j..."
docker compose up -d --wait --wait-timeout 300

cyp() {
  echo ">>> cypher/$1.cypher"
  docker compose exec -T neo4j cypher-shell -u neo4j -p learnneo4j --format plain --fail-at-end \
    -f "/cypher/$1.cypher" 2>&1 | tee "results/$1.txt" || echo "!!! có lỗi trong $1.cypher, xem results/$1.txt"
}

cyp 01_shop_read
cyp 02_shop_write
cyp 03_exercises
echo ">>> python/shop.py";            "$PY" python/shop.py           2>&1 | tee results/shop_python.txt
echo ">>> python/campus.py check";    "$PY" python/campus.py check   2>&1 | tee results/campus_check.txt
echo ">>> python/campus.py extra";    "$PY" python/campus.py extra   2>&1 | tee results/campus_extra.txt
echo ">>> python/plan.py";            "$PY" python/plan.py           2>&1 | tee results/step8_plan.txt
echo ">>> python/campus.py setup";    "$PY" python/campus.py setup   # để lại dữ liệu sạch cho Neo4j Browser

echo
echo "Xong! Kết quả nằm trong lab4-neo4j/results/"
echo "Mở http://localhost:7474 (neo4j / learnneo4j) để xem đồ thị và chụp màn hình."
