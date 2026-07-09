$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

Write-Host "Checking project..."

Write-Host "Step 1/2: Migrating SQLite schema..."
python -m week10.migrate_sqlite_schema

if ($LASTEXITCODE -ne 0) {
    Write-Host "SQLite schema migration failed."
    exit $LASTEXITCODE
}

Write-Host "Step 2/2: Running tests..."
pytest

if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed."
    exit $LASTEXITCODE
}

Write-Host "Project check completed successfully."