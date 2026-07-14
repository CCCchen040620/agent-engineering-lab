param(
    [string]$DatabaseUrl = $env:DATABASE_URL
)

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot
$PythonExecutable = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExecutable)) {
    $PythonExecutable = "python"
}

if (-not [string]::IsNullOrWhiteSpace($DatabaseUrl)) {
    $env:DATABASE_URL = $DatabaseUrl
}

Write-Host "Running unified RAG evaluation..."
Write-Host "Python executable: $PythonExecutable"

if (-not [string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
    Write-Host "DATABASE_URL: $env:DATABASE_URL"
}
else {
    Write-Host "DATABASE_URL is not set. SQLite cases can still run; PostgreSQL cases may be skipped."
}

& $PythonExecutable -m week11.run_rag_evaluation

if ($LASTEXITCODE -ne 0) {
    Write-Host "RAG evaluation failed."
    exit $LASTEXITCODE
}

Write-Host "RAG evaluation completed successfully."
