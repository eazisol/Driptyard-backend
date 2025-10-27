# Stop all Python processes
Write-Host "🛑 Stopping all Python processes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Clear Python cache
Write-Host "🧹 Clearing Python cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Filter __pycache__ -Recurse -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "✅ Cleanup complete!" -ForegroundColor Green
Write-Host ""

# Run startup check
& .\venv\Scripts\python.exe startup_check.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Startup check failed! Please fix database configuration." -ForegroundColor Red
    exit 1
}

# Start server
Write-Host "Starting FastAPI server..." -ForegroundColor Cyan
& .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

