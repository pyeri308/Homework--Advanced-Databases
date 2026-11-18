# Lab 4 – Graph Database (Neo4j): CampusGraph

Đồ thị trường đại học (sinh viên, môn học, môn tiên quyết, bạn bè) và 7 hàm Python, mỗi hàm là một truy vấn Cypher
gọi qua driver: lịch sử học, chuỗi tiên quyết, môn được đăng ký, gợi ý bạn, đường kết nối, môn "nút thắt",
và ghi điểm an toàn trong một transaction.

## Cấu trúc
```
lab4-neo4j/
├── compose.yaml               # Neo4j 5 (có healthcheck), mount ./import và ./cypher
├── import/people.csv          # dữ liệu cho LOAD CSV
├── cypher/
│   ├── 01_shop_read.cypher    # dữ liệu cửa hàng + MATCH, OPTIONAL MATCH, WITH, path, shortest path, gợi ý
│   ├── 02_shop_write.cypher   # CREATE/SET/REMOVE, MERGE, UNWIND, LOAD CSV, constraint, index, full-text
│   └── 03_exercises.cypher    # bài tập 1–4 (bạn của bạn, gợi ý cho Mai, metro, lịch sử làm việc)
├── python/
│   ├── requirements.txt
│   ├── campus.py              # LAB CHÍNH: 7 task + check + phần Going further
│   ├── plan.py                # Bước 8 (PROFILE có/không constraint, mô phỏng 100.000 SV) + bài tập 5
│   └── shop.py                # phần "Neo4j from Python" của bài
├── run_all.sh / run_all.ps1   # chạy tất cả, lưu output vào results/
├── results/                   # kết quả chạy
└── screenshots/               # ảnh chụp cần nộp
```

## Cách chạy
```
cd lab4-neo4j
docker compose up -d --wait          # đợi Neo4j healthy

python -m venv .venv
.venv\Scripts\activate               # Windows
source .venv/bin/activate            # macOS / Linux
pip install -r python/requirements.txt

python python/campus.py setup        # nạp dữ liệu (XOÁ toàn bộ database trước)
python python/campus.py check        # 8 dòng PASS
python python/campus.py extra        # phần Going further
python python/plan.py                # Bước 8: query plan

.\run_all.ps1                        # hoặc chạy tất cả một lần (Windows)
bash run_all.sh                      # (macOS / Linux / Git Bash)
```
Neo4j Browser: http://localhost:7474, đăng nhập `neo4j` / `learnneo4j`.

## Cần nộp (theo đề)
1. `python/campus.py` đã làm đủ 7 task.
2. Ảnh chụp màn hình `python python/campus.py check` với 8 dòng PASS, lưu vào `screenshots/campus_check.png`.

Nên chụp thêm `screenshots/graph.png` trong Neo4j Browser với truy vấn
`MATCH (c:Course)-[r:REQUIRES]->(p:Course) RETURN c, r, p`.

## Ghi chú cài đặt
- Các hàm không hard-code đáp án: mọi giá trị truyền bằng tham số `$sid`, `$code`, `$k`, nên chạy được với bất kỳ sinh viên hay môn nào.
- Độ dài đường đi biến thiên giới hạn `*1..20` (hằng số `MAX_DEPTH`), theo lời khuyên "luôn đặt cận trên" của bài.
- Task 7 chạy cả 3 truy vấn (kiểm tra tồn tại → tìm môn tiên quyết còn thiếu → `MERGE`) trên cùng một `tx`.
  Nếu `raise ValueError`, transaction bị rollback nên không ghi gì.
