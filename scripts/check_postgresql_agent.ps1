param(
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [switch]$SkipEmbeddingBackfill
)

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot
$PythonExecutable = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExecutable)) {
    $PythonExecutable = "python"
}

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
Write-Host "Python executable: $PythonExecutable"
Write-Host "This check assumes Ollama is running and the required models are available."

Invoke-PostgresqlAgentStep "Step 1/8: Checking PostgreSQL Docker service..." {
    & "$PSScriptRoot\check_postgres.ps1"
}

Invoke-PostgresqlAgentStep "Step 2/8: Initializing PostgreSQL schema..." {
    & $PythonExecutable -m week10.init_postgresql_schema
}

if ($SkipEmbeddingBackfill) {
    Write-Host ""
    Write-Host "Step 3/8: Skipping PostgreSQL chunk embedding backfill."
}
else {
    Invoke-PostgresqlAgentStep "Step 3/8: Backfilling PostgreSQL chunk embeddings..." {
        & $PythonExecutable -m week10.backfill_postgresql_chunk_embeddings
    }
}

Invoke-PostgresqlAgentStep "Step 4/8: Evaluating PostgreSQL retrieval..." {
    & $PythonExecutable -m week10.evaluate_postgresql_retrieval
}

Invoke-PostgresqlAgentStep "Step 5/8: Evaluating PostgreSQL LangGraph Agent flow..." {
    & $PythonExecutable -m week10.evaluate_postgresql_agent
}

Invoke-PostgresqlAgentStep "Step 6/8: Evaluating PostgreSQL Agent end-to-end indexing flow..." {
    & $PythonExecutable -m week10.evaluate_postgresql_agent_end_to_end
}

Invoke-PostgresqlAgentStep "Step 7/8: Evaluating PostgreSQL conversation chat flow..." {
    & $PythonExecutable -m week10.evaluate_postgresql_conversation_chat
}

Invoke-PostgresqlAgentStep "Step 8/8: Evaluating ingested document Agent answer flow..." {
    & $PythonExecutable -m week11.evaluate_document_ingestion_agent_flow `
        --title "SQLite 迁移验收文档" `
        --question "SQLite 迁移测试片段一是什么？" `
        --top-k 3 `
        --min-score 0.6
}

Write-Host ""
Write-Host "PostgreSQL Agent check completed successfully."
