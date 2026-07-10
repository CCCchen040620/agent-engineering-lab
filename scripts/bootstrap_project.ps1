param(
    [switch]$SkipEmbeddings,
    [switch]$SkipSummaries,
    [switch]$SkipTests
)

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

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

Invoke-ProjectStep "Step 1/4: Migrating SQLite schema..." {
    python -m week10.migrate_sqlite_schema
}

if ($SkipEmbeddings) {
    Write-Host ""
    Write-Host "Step 2/4: Skipping chunk embedding backfill."
}
else {
    Invoke-ProjectStep "Step 2/4: Backfilling chunk embeddings..." {
        python -m week08.backfill_chunk_embeddings
    }
}

if ($SkipSummaries) {
    Write-Host ""
    Write-Host "Step 3/4: Skipping conversation summary backfill."
}
else {
    Invoke-ProjectStep "Step 3/4: Backfilling conversation summaries..." {
        python -m week10.backfill_conversation_summaries
    }
}

if ($SkipTests) {
    Write-Host ""
    Write-Host "Step 4/4: Skipping tests."
}
else {
    Invoke-ProjectStep "Step 4/4: Running tests..." {
        pytest
    }
}

Write-Host ""
Write-Host "Project bootstrap completed successfully."
