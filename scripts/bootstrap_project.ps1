param(
    [switch]$SkipEnvironmentCheck,
    [switch]$SkipEmbeddings,
    [switch]$SkipSummaries,
    [switch]$SkipTests
)

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot
$PythonExecutable = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExecutable)) {
    $PythonExecutable = "python"
}

function Invoke-ProjectStep {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host $Name

    & $Command

    if ($LASTEXITCODE -ne 0) {
        Write-Host "$Name failed."
        exit $LASTEXITCODE
    }
}

Write-Host "Bootstrapping Enterprise Knowledge Base Agent project..."
Write-Host "Python executable: $PythonExecutable"

if ($SkipEnvironmentCheck) {
    Write-Host ""
    Write-Host "Step 1/5: Skipping environment check."
}
else {
    Invoke-ProjectStep "Step 1/5: Checking local environment..." {
        & "$PSScriptRoot\check_environment.ps1"
    }
}

Invoke-ProjectStep "Step 2/5: Migrating SQLite schema..." {
    & $PythonExecutable -m week10.migrate_sqlite_schema
}

if ($SkipEmbeddings) {
    Write-Host ""
    Write-Host "Step 3/5: Skipping chunk embedding backfill."
}
else {
    Invoke-ProjectStep "Step 3/5: Backfilling chunk embeddings..." {
        & $PythonExecutable -m week08.backfill_chunk_embeddings
    }
}

if ($SkipSummaries) {
    Write-Host ""
    Write-Host "Step 4/5: Skipping conversation summary backfill."
}
else {
    Invoke-ProjectStep "Step 4/5: Backfilling conversation summaries..." {
        & $PythonExecutable -m week10.backfill_conversation_summaries
    }
}

if ($SkipTests) {
    Write-Host ""
    Write-Host "Step 5/5: Skipping tests."
}
else {
    Invoke-ProjectStep "Step 5/5: Running tests..." {
        & $PythonExecutable -m pytest
    }
}

Write-Host ""
Write-Host "Project bootstrap completed successfully."
