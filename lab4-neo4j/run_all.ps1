# Lab 4 – Neo4j: chạy toàn bộ và lưu kết quả vào results/  (Windows PowerShell)
Set-Location $PSScriptRoot
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
New-Item -ItemType Directory -Force results | Out-Null

Write-Host "Khởi động Neo4j..."
docker compose up -d --wait --wait-timeout 300

function Save($name, [scriptblock]$cmd) {
  Write-Host ">>> $name" -ForegroundColor Cyan
  $out = & $cmd 2>&1 | ForEach-Object { "$_" }
  $out | Write-Host
  $out | Out-File -Encoding utf8 "results/$name.txt"
}

foreach ($f in "01_shop_read", "02_shop_write", "03_exercises") {
  Save $f { docker compose exec -T neo4j cypher-shell -u neo4j -p learnneo4j --format plain --fail-at-end -f "/cypher/$f.cypher" }
}
Save shop_python   { python python/shop.py }
Save campus_check  { python python/campus.py check }
Save campus_extra  { python python/campus.py extra }
Save step8_plan    { python python/plan.py }
python python/campus.py setup | Out-Null   # để lại dữ liệu sạch cho Neo4j Browser

Write-Host "Xong! Kết quả nằm trong lab4-neo4j/results/" -ForegroundColor Green
Write-Host "Mở http://localhost:7474 (neo4j / learnneo4j) để xem đồ thị và chụp màn hình."
