# Lab 1 – Document Store (MongoDB)

## Cấu trúc
```
lab1-mongodb/
├── compose.yaml               # chạy MongoDB bằng Docker
├── mongosh/                   # script chạy bằng mongosh (bên trong container)
│   ├── 01_insert.js           # Create (đồng thời reset dữ liệu)
│   ├── 02_queries.js          # Read
│   ├── 03_update_delete.js    # Update / Delete
│   ├── 04_aggregation.js      # Aggregation pipeline
│   ├── 05_indexes.js          # Index + explain()
│   ├── ex1_shapes.js          # Bài tập 1
│   ├── ex2_revenue_by_city.js # Bài tập 2
│   └── ex3_index_benchmark.js # Bài tập 3
├── python/
│   ├── requirements.txt
│   └── app.py                 # pymongo + pandas
├── run_all.sh / run_all.ps1   # chạy tất cả và lưu kết quả vào results/
└── results/                   # output của từng script (được tạo khi chạy run_all)
```

## Cần cài
Docker Desktop (đang chạy), VS Code, Python 3.10+. Không cần cài mongosh vì đã có sẵn trong container.

## Bước 1 – Khởi động MongoDB
```
cd lab1-mongodb
docker compose up -d
docker compose ps          # thấy mongo "running" là được
```

## Bước 2 – Chạy từng script
```
docker compose exec mongo mongosh --quiet -f /scripts/01_insert.js
docker compose exec mongo mongosh --quiet -f /scripts/02_queries.js
docker compose exec mongo mongosh --quiet -f /scripts/03_update_delete.js
docker compose exec mongo mongosh --quiet -f /scripts/04_aggregation.js
docker compose exec mongo mongosh --quiet -f /scripts/05_indexes.js
```
Bài tập:
```
docker compose exec mongo mongosh --quiet -f /scripts/ex1_shapes.js
docker compose exec mongo mongosh --quiet -f /scripts/01_insert.js   # reset trước bài 2
docker compose exec mongo mongosh --quiet -f /scripts/ex2_revenue_by_city.js
docker compose exec mongo mongosh --quiet -f /scripts/ex3_index_benchmark.js
```
Muốn gõ lệnh tay: `docker compose exec mongo mongosh` rồi `use shop`, thoát bằng `exit`.

## Bước 3 – Chạy phần Python
```
cd python
python -m venv .venv
.venv\Scripts\activate            # Windows (PowerShell)
source .venv/bin/activate         # macOS / Linux
pip install -r requirements.txt
python app.py
```

## Chạy tất cả một lần và lưu kết quả
Kích hoạt venv và cài requirements trước (Bước 3), rồi ở thư mục gốc:
```
.\run_all.ps1        # Windows PowerShell
bash run_all.sh       # macOS / Linux / Git Bash
```
Kết quả của từng script được lưu thành file trong `results/` (ví dụ `results/05_indexes.txt`).

## Dọn dẹp
```
docker compose down       # dừng container, giữ dữ liệu
docker compose down -v    # dừng và xoá luôn dữ liệu
```
