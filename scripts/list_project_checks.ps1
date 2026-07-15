$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

Write-Host "Enterprise Knowledge Agent check command guide"
Write-Host ""

Write-Host "1. Local quick checks"
Write-Host "   Scope: no running PostgreSQL service or Ollama model is required."
Write-Host "   Commands:"
Write-Host "   - .\scripts\check_environment.ps1"
Write-Host "   - .\scripts\check_project.ps1"
Write-Host "   - .\scripts\check_rag_evaluation_ci.ps1"
Write-Host ""

Write-Host "2. PostgreSQL checks"
Write-Host "   Scope: requires Docker PostgreSQL / pgvector, but does not represent final delivery validation."
Write-Host "   Commands:"
Write-Host "   - docker compose up -d postgres"
Write-Host "   - .\scripts\check_postgres.ps1"
Write-Host "   - .\.venv\Scripts\python.exe -m week10.init_postgresql_schema"
Write-Host ""

Write-Host "3. Pre-delivery full checks"
Write-Host "   Scope: requires PostgreSQL, Ollama, embeddings, and local generation models."
Write-Host "   Commands:"
Write-Host "   - .\scripts\check_task_center.ps1"
Write-Host "   - .\scripts\check_postgresql_agent.ps1 -SkipConversationChat -SkipIngestedDocumentCheck"
Write-Host "   - .\scripts\check_postgresql_agent.ps1 -RunBatchDocumentIngestionCheck"
Write-Host "   - .\scripts\check_rag_evaluation.ps1"
