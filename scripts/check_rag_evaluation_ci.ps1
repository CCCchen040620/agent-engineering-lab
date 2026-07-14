Write-Host "Running lightweight RAG evaluation for CI..."

$ErrorActionPreference = "Stop"

$python = ".\.venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    $python = "python"
}

& $python -m pytest tests/test_evaluation_cases.py tests/test_run_rag_evaluation.py

Write-Host "Lightweight RAG evaluation completed successfully."