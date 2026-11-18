# Lab 2 – Key-Value Store (Redis): TicketRush

Xây phần lõi backend bán vé concert trên Redis và chứng minh bằng 50–500 luồng chạy song song rằng hệ thống
không bao giờ bán trùng ghế, không bán lố vé, và chặn được bot.

## Cấu trúc
```
lab2-redis/
├── compose.yaml              # Redis 8 bằng Docker
├── redis/                    # lệnh redis-cli của phần lý thuyết
│   ├── 01_strings.redis      # string, counter, expiry
│   └── 02_structures.redis   # hash, list, set, sorted set
├── python/
│   ├── requirements.txt
│   ├── common.py             # kết nối Redis dùng chung
│   ├── run_cli.py            # chạy file .redis và in kết quả giống redis-cli
│   ├── cache_demo.py         # cache-aside + rate limiter đơn giản
│   ├── ticketrush.py         # LAB chính: bước 0 → 6
│   ├── exercises.py          # 3 bài tập
│   ├── extensions.py         # 5 phần mở rộng
│   └── subscriber.py         # nghe pub/sub ở terminal thứ hai
├── run_all.sh / run_all.ps1  # chạy tất cả, lưu output vào results/
└── results/                  # kết quả đã chạy
```

## Thiết kế key
| Key | Kiểu | Ý nghĩa |
|---|---|---|
| `hold:{event}:{seat}` | string + TTL | ai đang giữ ghế |
| `sold:{event}` | set | ghế đã thanh toán |
| `stock:{event}` | string (counter) | vé đứng còn lại |
| `buyers:{event}` | set | người đã mua vé đứng |
| `rl:sliding:{user}` | sorted set | thời điểm các request gần đây |
| `queue:{event}` | sorted set | phòng chờ, score = thời điểm vào |

## Cách chạy
```
cd lab2-redis
docker compose up -d

python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # macOS / Linux
pip install -r python/requirements.txt

.\run_all.ps1                     # Windows: chạy tất cả + lưu results/
bash run_all.sh                   # macOS / Linux / Git Bash
```
Chạy riêng từng phần:
```
python python/ticketrush.py       # tất cả các bước
python python/ticketrush.py 4     # chỉ bước 4
python python/exercises.py
python python/extensions.py
docker compose exec -T redis redis-cli < redis/02_structures.redis   # chạy bằng redis-cli thật
docker compose exec redis redis-cli                                  # gõ lệnh tay
```
Xem pub/sub trực tiếp: mở terminal 1 chạy `python python/subscriber.py`, terminal 2 chạy `python python/extensions.py`.

> **Lưu ý:** các script gọi `flushdb()` để reset dữ liệu. Chỉ chạy trên Redis của container này.

## Kết quả chính
| Thí nghiệm | Kết quả |
|---|---|
| 50 luồng giữ ghế A1: `GET` rồi `SET` | 50 người cùng "thắng" (lỗi race condition) |
| 50 luồng giữ ghế A1: `SET NX EX` | luôn đúng 1 người thắng |
| 500 người mua 100 vé đứng bằng `DECR` | bán 100, stock 0, 100 buyers |
| 500 người mua bằng kiểm tra rồi trừ (cố ý sai) | bán 112 vé, stock −12 (bán lố) |
| Biên cửa sổ: fixed window | 10/10 request lọt trong 0.4s (gấp đôi giới hạn) |
| Biên cửa sổ: sliding window | chỉ 5/10 request lọt |
| Stress test 100 người / 20 ghế, chạy 10 lần | lần nào cũng `20 20 20` |
| Cache-aside 100 request | 10.0s → 0.1s (nhanh ~96 lần) |

Chi tiết xem thư mục `results/`.

Môi trường khi tạo `results/`: Redis 8.10, redis-py 8.1, Python 3.12.
