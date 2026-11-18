# Chạy toàn bộ lab Redis và lưu kết quả vào results/  (Windows PowerShell)
Set-Location $PSScriptRoot
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

New-Item -ItemType Directory -Force results | Out-Null
docker compose up -d

Write-Host "Đợi Redis sẵn sàng..."
do {
  Start-Sleep -Seconds 1
  $pong = docker compose exec -T redis redis-cli ping 2>$null
} until ($pong -match "PONG")

function Save($name, [string[]]$cmdArgs) {
  Write-Host ">>> $name" -ForegroundColor Cyan
  $out = python @cmdArgs
  if ($LASTEXITCODE -ne 0) { Write-Host "LỖI khi chạy $name" -ForegroundColor Red; exit 1 }
  $out | Write-Host
  $out | Out-File -Encoding utf8 "results/$name.txt"
}

Save 01_strings    @("python/run_cli.py", "redis/01_strings.redis")
Save 02_structures @("python/run_cli.py", "redis/02_structures.redis")
Save cache_demo    @("python/cache_demo.py")
Save ticketrush    @("python/ticketrush.py")
Save exercises     @("python/exercises.py")
Save extensions    @("python/extensions.py")

Write-Host "Xong! Kết quả nằm trong lab2-redis/results/" -ForegroundColor Green
