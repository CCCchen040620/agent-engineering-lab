$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

Write-Host "Migrating SQLite schema..."

python -m week10.migrate_sqlite_schema