#!/usr/bin/env bash
# Chạy toàn bộ lab Redis và lưu kết quả vào results/  (macOS / Linux / Git Bash / GitHub Actions)
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONUTF8=1

mkdir -p results
docker compose up -d

echo "Đợi Redis sẵn sàng..."
until docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; do sleep 1; done

run_py() { echo ">>> $1"; python "python/$1.py" "${@:2}" | tee "results/$1.txt"; }

echo ">>> 01_strings";    python python/run_cli.py redis/01_strings.redis    | tee results/01_strings.txt
echo ">>> 02_structures"; python python/run_cli.py redis/02_structures.redis | tee results/02_structures.txt
run_py cache_demo
run_py ticketrush
run_py exercises
run_py extensions

echo "Xong! Kết quả nằm trong lab2-redis/results/"
