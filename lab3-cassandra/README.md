# Lab 3 – Wide-Column (Cassandra): SensorRing

Kiểm chứng các tuyên bố của bài học trên một cụm Cassandra 3 node thật:
- partition key quyết định node nào lưu dữ liệu;
- truy vấn không có partition key phải quét toàn cụm;
- consistency có thể điều chỉnh, kể cả trường hợp đọc phải dữ liệu cũ (stale).

## Cấu trúc
```
lab3-cassandra/
├── compose.yaml              # cụm 3 node cass1, cass2, cass3 (khởi động lần lượt nhờ healthcheck)
├── cql/
│   ├── 01_basics.cql         # phần lý thuyết: keyspace shop, readings_by_sensor, truy vấn bị từ chối
│   └── 02_exercises.cql      # 3 bài tập: 2 bảng đơn hàng, truy vấn thiếu partition key, bucket theo tháng
├── python/
│   ├── requirements.txt
│   ├── basics.py             # phần "Cassandra from Python" (prepared statement)
│   ├── sensorring.py         # script của lab: load / cl
│   └── verify_ring.py        # Bước 1: tự kiểm tra quy tắc "node kế tiếp theo chiều kim đồng hồ"
├── run_all.sh                # chạy TỰ ĐỘNG cả 5 bước (kể cả tắt/bật node), lưu vào results/
└── results/                  # kết quả chạy
```

## Yêu cầu máy
3 node cần khoảng **3 GB RAM trống**. Docker Desktop: Settings → Resources → Memory **≥ 4 GB**.
Nếu node bị kill với exit code 137 thì là thiếu RAM.

## Chạy tự động (khuyên dùng)
```
cd lab3-cassandra
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r python/requirements.txt
bash run_all.sh                   # 10–15 phút
```
Trên Windows, chạy `run_all.sh` bằng **Git Bash** (cài kèm Git for Windows), vì lab có nhiều lệnh
bash (vòng lặp, grep). Script tự làm đúng trình tự của bài:

| Bước | Script làm gì | File kết quả |
|---|---|---|
| 0 | `up --wait` 3 node, đợi 3 dòng `UN`, nạp 3000 bản ghi | `step0_cluster.txt` |
| Lý thuyết | `01_basics.cql` + `basics.py` | `theory.txt` |
| Bài tập | `02_exercises.cql` | `exercises.txt` |
| 1 | token, getendpoints, keyspace ring1 (RF=1), nodetool ring, kiểm tra quy tắc vòng | `step1_partition.txt` |
| 2 | TRACING: truy vấn theo partition vs ALLOW FILTERING | `step2_tracing.txt` |
| 3 | `cl` với 3 → 2 → 1 node sống (đợi đến khi thấy `DN`) | `step3_consistency.txt` |
| 4 | tắt handoff, ghi QUORUM, đọc ONE từ cass3 (0 rows), đọc ALL (1 rows), repair | `step4_stale_replica.txt` |

Sau khi chạy xong, cụm vẫn bật để bạn thử thêm. Dọn dẹp: `docker compose down -v`.

## Chạy tay từng bước
Làm theo đúng hướng dẫn trong bài học. Mọi lệnh đều chạy trong thư mục `lab3-cassandra`, ví dụ:
```
docker compose up -d
docker compose exec cass1 nodetool status
python python/sensorring.py load
docker compose exec cass1 cqlsh
docker compose exec -T cass1 cqlsh -f /cql/01_basics.cql
python python/verify_ring.py hn-01 hn-07
docker compose stop cass3
python python/sensorring.py cl
```
Trong PowerShell, thay `grep -E "a|b"` bằng `Select-String "a|b"`.

## Ghi chú
- Lỗi `InvalidRequest` trong `theory.txt` và `exercises.txt` là **cố ý**: đó là các truy vấn thiếu partition key mà bài yêu cầu thử.
- IP và token của cụm bạn sẽ khác ví dụ trong bài, nhưng quy tắc vòng luôn đúng (`verify_ring.py` in `OK` cho từng sensor).
- Nhiệt độ được sinh ngẫu nhiên nên số dòng ALLOW FILTERING trả về mỗi lần chạy hơi khác.
