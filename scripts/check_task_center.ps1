param(
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [string]$BackendBaseUrl = $env:BACKEND_API_BASE_URL,
    [int]$TimeoutSeconds = 120,
    [int]$PollIntervalSeconds = 2
)

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot
$PythonExecutable = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExecutable)) {
    $PythonExecutable = "python"
}

if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) {
    $DatabaseUrl = "postgresql://agent_user:agent_password@localhost:5432/agent_db"
}

if ([string]::IsNullOrWhiteSpace($BackendBaseUrl)) {
    $BackendBaseUrl = "http://127.0.0.1:8000"
}

$env:DATABASE_URL = $DatabaseUrl

function Invoke-TaskCenterStep {
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

function Fail-TaskCenterCheck {
    param([string]$Message)

    Write-Host "[FAILED] $Message"
    exit 1
}

function Show-TaskFailureDiagnostic {
    param([string]$ErrorText)

    if ([string]::IsNullOrWhiteSpace($ErrorText)) {
        Write-Host "Failure reason: unknown_error"
        Write-Host "Suggested next step: check backend logs."
        return
    }

    $Parts = $ErrorText.Split(":", 2)
    $ErrorCode = $Parts[0].Trim()
    $ErrorMessage = ""

    if ($Parts.Length -gt 1) {
        $ErrorMessage = $Parts[1].Trim()
    }

    Write-Host "Failure reason: $ErrorCode"
    Write-Host "Error message: $ErrorMessage"

    if ($ErrorCode -eq "invalid_payload") {
        Write-Host "Suggested next step: check task payload fields."
    }
    elseif ($ErrorCode -eq "duplicate_document") {
        Write-Host "Suggested next step: use a unique document title or clean evaluation documents."
    }
    elseif ($ErrorCode -eq "postgresql_connection_error") {
        Write-Host "Suggested next step: check PostgreSQL service and DATABASE_URL."
    }
    elseif ($ErrorCode -eq "embedding_generation_error") {
        Write-Host "Suggested next step: check Ollama and the embedding model."
    }
    else {
        Write-Host "Suggested next step: check backend logs."
    }
}

Write-Host "Checking task center flow..."
Write-Host "DATABASE_URL: $DatabaseUrl"
Write-Host "Backend API: $BackendBaseUrl"
Write-Host "Python executable: $PythonExecutable"
Write-Host "This check assumes FastAPI is already running with the PostgreSQL DATABASE_URL."
Write-Host "It also assumes Ollama and the embedding model are available."

Invoke-TaskCenterStep "Step 1/5: Checking PostgreSQL Docker service..." {
    & "$PSScriptRoot\check_postgres.ps1"
}

Invoke-TaskCenterStep "Step 2/5: Initializing PostgreSQL schema..." {
    & $PythonExecutable -m week10.init_postgresql_schema
}

Write-Host ""
Write-Host "Step 3/5: Checking backend health..."

try {
    $Health = Invoke-RestMethod -Method Get -Uri "$BackendBaseUrl/health" -TimeoutSec 10
}
catch {
    Fail-TaskCenterCheck "Backend health check failed. Start FastAPI and retry."
}

if ($Health.status -ne "ok") {
    Fail-TaskCenterCheck "Backend health status is not ok."
}

Write-Host "[OK] Backend health check passed."

Write-Host ""
Write-Host "Step 4/5: Creating asynchronous PostgreSQL document ingestion task..."

$Timestamp = Get-Date -Format "yyyyMMddHHmmss"
$TaskTitle = "Task Center Check $Timestamp"
$TaskPayload = @{
    title = $TaskTitle
    file_type = "md"
    content = "任务中心异步入库验收片段。"
    source = "evaluation"
} | ConvertTo-Json -Depth 5

try {
    $Task = Invoke-RestMethod `
        -Method Post `
        -Uri "$BackendBaseUrl/api/v1/tasks/postgresql-document-ingestion/run-async" `
        -ContentType "application/json; charset=utf-8" `
        -Body $TaskPayload `
        -TimeoutSec 30
}
catch {
    Fail-TaskCenterCheck "Failed to create asynchronous document ingestion task."
}

if ($null -eq $Task.id) {
    Fail-TaskCenterCheck "Task response does not include task id."
}

Write-Host "[OK] Task submitted. Task ID: $($Task.id)"
Write-Host "Initial status: $($Task.status)"

Write-Host ""
Write-Host "Step 5/5: Polling task status..."

$Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$FinalTask = $null

while ((Get-Date) -lt $Deadline) {
    try {
        $CurrentTask = Invoke-RestMethod `
            -Method Get `
            -Uri "$BackendBaseUrl/api/v1/tasks/$($Task.id)" `
            -TimeoutSec 10
    }
    catch {
        Fail-TaskCenterCheck "Failed to read task status."
    }

    Write-Host "Task $($Task.id) status: $($CurrentTask.status)"

    if ($CurrentTask.status -eq "succeeded" -or $CurrentTask.status -eq "failed") {
        $FinalTask = $CurrentTask
        break
    }

    Start-Sleep -Seconds $PollIntervalSeconds
}

if ($null -eq $FinalTask) {
    Fail-TaskCenterCheck "Task did not finish within $TimeoutSeconds seconds."
}

if ($FinalTask.status -eq "failed") {
    Write-Host ""
    Write-Host "Task failed."
    Show-TaskFailureDiagnostic $FinalTask.error
    exit 1
}

if ($null -eq $FinalTask.result.document_id) {
    Fail-TaskCenterCheck "Succeeded task result does not include document_id."
}

if ($FinalTask.result.chunk_count -le 0) {
    Fail-TaskCenterCheck "Succeeded task result does not include indexed chunks."
}

if ($FinalTask.result.embedding_count -le 0) {
    Fail-TaskCenterCheck "Succeeded task result does not include embeddings."
}

Write-Host ""
Write-Host "Task center check completed successfully."
Write-Host "Task ID: $($FinalTask.id)"
Write-Host "Document ID: $($FinalTask.result.document_id)"
Write-Host "Chunks: $($FinalTask.result.chunk_count)"
Write-Host "Embeddings: $($FinalTask.result.embedding_count)"
