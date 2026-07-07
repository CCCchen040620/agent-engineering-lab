$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

Write-Host "Starting FastAPI backend..."
Write-Host "API docs: http://127.0.0.1:8000/docs"
Write-Host "Health check: http://127.0.0.1:8000/health"

python -m uvicorn backend.main:app --reload
