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

Invoke-PostgresqlAgentStep "Step 1/7: Checking PostgreSQL Docker service..." {
    & "$PSScriptRoot\check_postgres.ps1"
}

Invoke-PostgresqlAgentStep "Step 2/7: Initializing PostgreSQL schema..." {
    python -m week10.init_postgresql_schema
}

if ($SkipEmbeddingBackfill) {
    Write-Host ""
    Write-Host "Step 3/7: Skipping PostgreSQL chunk embedding backfill."
}
else {
    Invoke-PostgresqlAgentStep "Step 3/7: Backfilling PostgreSQL chunk embeddings..." {
        python -m week10.backfill_postgresql_chunk_embeddings
    }
}

Invoke-PostgresqlAgentStep "Step 4/7: Evaluating PostgreSQL retrieval..." {
    python -m week10.evaluate_postgresql_retrieval
}

Invoke-PostgresqlAgentStep "Step 5/7: Evaluating PostgreSQL LangGraph Agent flow..." {
    python -m week10.evaluate_postgresql_agent
}

Invoke-PostgresqlAgentStep "Step 6/7: Evaluating PostgreSQL Agent end-to-end indexing flow..." {
    python -m week10.evaluate_postgresql_agent_end_to_end
}

Invoke-PostgresqlAgentStep "Step 7/7: Evaluating PostgreSQL conversation chat flow..." {
    python -m week10.evaluate_postgresql_conversation_chat
}

Write-Host ""
Write-Host "PostgreSQL Agent check completed successfully."
