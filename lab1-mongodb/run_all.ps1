# Chạy toàn bộ bài và lưu kết quả vào thư mục results/  (Windows PowerShell)
Set-Location $PSScriptRoot
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8   # giữ đúng tiếng Việt
$env:PYTHONUTF8 = "1"

New-Item -ItemType Directory -Force results | Out-Null
docker compose up -d

Write-Host "Đợi MongoDB sẵn sàng..."
do {
  Start-Sleep -Seconds 1
  docker compose exec -T mongo mongosh --quiet --eval "db.adminCommand('ping').ok" *> $null
} until ($LASTEXITCODE -eq 0)

function Run($name, [switch]$Silent) {
  $out = docker compose exec -T mongo mongosh --quiet -f "/scripts/$name.js"
  if ($LASTEXITCODE -ne 0) { Write-Host "LỖI khi chạy $name" -ForegroundColor Red; exit 1 }
  if (-not $Silent) {
    Write-Host ">>> $name" -ForegroundColor Cyan
    $out | Write-Host
    $out | Out-File -Encoding utf8 "results/$name.txt"
  }
}

Run 01_insert
Run 02_queries
Run 03_update_delete
Run 04_aggregation
Run 05_indexes

Run ex1_shapes
Run 01_insert -Silent        # reset dữ liệu trước bài 2
Run ex2_revenue_by_city
Run ex3_index_benchmark

Run 01_insert -Silent        # reset trước Python
Write-Host ">>> python/app.py" -ForegroundColor Cyan
$out = python python/app.py
$out | Write-Host
$out | Out-File -Encoding utf8 "results/python_app.txt"

Write-Host "Xong! Kết quả nằm trong thư mục results/" -ForegroundColor Green
