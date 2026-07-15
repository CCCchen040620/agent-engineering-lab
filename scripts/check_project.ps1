$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot
$PythonExecutable = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExecutable)) {
    $PythonExecutable = "python"
}

Write-Host "Checking project..."
Write-Host "Python executable: $PythonExecutable"

Write-Host "Step 1/2: Migrating SQLite schema..."
& $PythonExecutable -m week10.migrate_sqlite_schema

if ($LASTEXITCODE -ne 0) {
    Write-Host "SQLite schema migration failed."
    exit $LASTEXITCODE
}

Write-Host "Step 2/2: Running tests..."
& $PythonExecutable -m pytest

if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed."
    exit $LASTEXITCODE
}

Write-Host "Project check completed successfully."
