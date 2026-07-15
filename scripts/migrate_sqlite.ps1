$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot
$PythonExecutable = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExecutable)) {
    $PythonExecutable = "python"
}

Write-Host "Migrating SQLite schema..."
Write-Host "Python executable: $PythonExecutable"

& $PythonExecutable -m week10.migrate_sqlite_schema
