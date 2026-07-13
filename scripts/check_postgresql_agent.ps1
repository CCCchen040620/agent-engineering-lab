param(
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [switch]$SkipEmbeddingBackfill
)

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

function Invoke-PostgresqlAgentStep {
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

if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) {
    $DatabaseUrl = "postgresql://agent_user:agent_password@localhost:5432/agent_db"
}

$env:DATABASE_URL = $DatabaseUrl

Write-Host "Checking PostgreSQL LangGraph Agent flow..."
Write-Host "DATABASE_URL: $DatabaseUrl"
Write-Host "This check assumes Ollama is running and the required models are available."

Invoke-PostgresqlAgentStep "Step 1/5: Checking PostgreSQL Docker service..." {
    & "$PSScriptRoot\check_postgres.ps1"
}

Invoke-PostgresqlAgentStep "Step 2/5: Initializing PostgreSQL schema..." {
    python -m week10.init_postgresql_schema
}

if ($SkipEmbeddingBackfill) {
    Write-Host ""
    Write-Host "Step 3/5: Skipping PostgreSQL chunk embedding backfill."
}
else {
    Invoke-PostgresqlAgentStep "Step 3/5: Backfilling PostgreSQL chunk embeddings..." {
        python -m week10.backfill_postgresql_chunk_embeddings
    }
}

Invoke-PostgresqlAgentStep "Step 4/5: Evaluating PostgreSQL retrieval..." {
    python -m week10.evaluate_postgresql_retrieval
}

Invoke-PostgresqlAgentStep "Step 5/5: Evaluating PostgreSQL LangGraph Agent flow..." {
    python -m week10.evaluate_postgresql_agent
}

Write-Host ""
Write-Host "PostgreSQL Agent check completed successfully."
