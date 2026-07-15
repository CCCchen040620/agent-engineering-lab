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

function Wait-TaskCenterTaskFinished {
    param(
        [int]$TaskId,
        [string]$Label
    )

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $Deadline) {
        try {
            $CurrentTask = Invoke-RestMethod `
                -Method Get `
                -Uri "$BackendBaseUrl/api/v1/tasks/$TaskId" `
                -TimeoutSec 10
        }
        catch {
            Fail-TaskCenterCheck "Failed to read $Label status."
        }

        Write-Host "Task $TaskId status: $($CurrentTask.status)"

        if ($CurrentTask.status -in @("succeeded", "failed", "canceled")) {
            return $CurrentTask
        }

        Start-Sleep -Seconds $PollIntervalSeconds
    }

    Fail-TaskCenterCheck "$Label did not finish within $TimeoutSeconds seconds."
}

function Read-TaskCenterEvents {
    param([int]$TaskId)

    try {
        return @(
            Invoke-RestMethod `
                -Method Get `
                -Uri "$BackendBaseUrl/api/v1/tasks/$TaskId/events" `
                -TimeoutSec 10
        )
    }
    catch {
        Fail-TaskCenterCheck "Failed to read task $TaskId events."
    }
}

function Assert-TaskCenterEventsInclude {
    param(
        [int]$TaskId,
        [string[]]$RequiredEventTypes
    )

    $Events = @(Read-TaskCenterEvents -TaskId $TaskId)
    $EventTypes = @($Events | ForEach-Object { $_.event_type })

    foreach ($EventType in $RequiredEventTypes) {
        if (-not ($EventTypes -contains $EventType)) {
            Fail-TaskCenterCheck "Task $TaskId events do not include $EventType."
        }
    }

    Write-Host "[OK] Task $TaskId events include: $($RequiredEventTypes -join ', ')"

    return $Events
}

Write-Host "Checking task center flow..."
Write-Host "DATABASE_URL: $DatabaseUrl"
Write-Host "Backend API: $BackendBaseUrl"
Write-Host "Python executable: $PythonExecutable"
Write-Host "This check assumes FastAPI is already running with the PostgreSQL DATABASE_URL."
Write-Host "It also assumes Ollama and the embedding model are available."

Invoke-TaskCenterStep "Step 1/7: Checking PostgreSQL Docker service..." {
    & "$PSScriptRoot\check_postgres.ps1"
}

Invoke-TaskCenterStep "Step 2/7: Initializing PostgreSQL schema..." {
    & $PythonExecutable -m week10.init_postgresql_schema
}

Write-Host ""
Write-Host "Step 3/7: Checking backend health..."

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
Write-Host "Step 4/7: Creating asynchronous PostgreSQL document ingestion task..."

$Timestamp = Get-Date -Format "yyyyMMddHHmmss"
$TaskTitle = "Task Center Check $Timestamp"
$TaskPayload = @{
    title = $TaskTitle
    file_type = "md"
    content = "Task center asynchronous document ingestion acceptance snippet."
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
Write-Host "Step 5/7: Polling successful task status..."

$FinalTask = Wait-TaskCenterTaskFinished -TaskId $Task.id -Label "document ingestion task"

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
Write-Host "Step 6/7: Checking successful task events..."

$SuccessEvents = Assert-TaskCenterEventsInclude `
    -TaskId $FinalTask.id `
    -RequiredEventTypes @("task_created", "task_started", "task_succeeded")

Write-Host "Successful task event count: $($SuccessEvents.Count)"

Write-Host ""
Write-Host "Step 7/7: Checking controlled failure and retry event flow..."

try {
    $DuplicateTask = Invoke-RestMethod `
        -Method Post `
        -Uri "$BackendBaseUrl/api/v1/tasks/postgresql-document-ingestion/run-async" `
        -ContentType "application/json; charset=utf-8" `
        -Body $TaskPayload `
        -TimeoutSec 30
}
catch {
    Fail-TaskCenterCheck "Failed to create controlled duplicate document task."
}

if ($null -eq $DuplicateTask.id) {
    Fail-TaskCenterCheck "Controlled duplicate task response does not include task id."
}

Write-Host "[OK] Controlled duplicate task submitted. Task ID: $($DuplicateTask.id)"

$FailedTask = Wait-TaskCenterTaskFinished -TaskId $DuplicateTask.id -Label "controlled duplicate task"

if ($FailedTask.status -ne "failed") {
    Fail-TaskCenterCheck "Controlled duplicate task should fail, but status is $($FailedTask.status)."
}

if ($FailedTask.error -notlike "duplicate_document:*") {
    Fail-TaskCenterCheck "Controlled duplicate task did not fail with duplicate_document."
}

Show-TaskFailureDiagnostic $FailedTask.error

$FailedTaskEvents = Assert-TaskCenterEventsInclude `
    -TaskId $FailedTask.id `
    -RequiredEventTypes @("task_created", "task_started", "task_failed")

Write-Host "Failed task event count: $($FailedTaskEvents.Count)"

try {
    $RetryTask = Invoke-RestMethod `
        -Method Post `
        -Uri "$BackendBaseUrl/api/v1/tasks/$($FailedTask.id)/retry-async" `
        -TimeoutSec 30
}
catch {
    Fail-TaskCenterCheck "Failed to create retry task from controlled failed task."
}

if ($null -eq $RetryTask.id) {
    Fail-TaskCenterCheck "Retry task response does not include task id."
}

if ([int]$RetryTask.retry_of_task_id -ne [int]$FailedTask.id) {
    Fail-TaskCenterCheck "Retry task does not point back to the failed task."
}

$FailedTaskEventsAfterRetry = Assert-TaskCenterEventsInclude `
    -TaskId $FailedTask.id `
    -RequiredEventTypes @("task_retry_created")

$RetryEvents = @(
    $FailedTaskEventsAfterRetry |
        Where-Object { $_.event_type -eq "task_retry_created" }
)

$LatestRetryEvent = $RetryEvents[-1]

if ($null -eq $LatestRetryEvent.metadata.retry_task_id) {
    Fail-TaskCenterCheck "Retry event does not include retry_task_id."
}

if ([int]$LatestRetryEvent.metadata.retry_task_id -ne [int]$RetryTask.id) {
    Fail-TaskCenterCheck "Retry event retry_task_id does not match the created retry task."
}

Write-Host "[OK] Failed task retry event points to retry task ID: $($RetryTask.id)"

$FinalRetryTask = Wait-TaskCenterTaskFinished -TaskId $RetryTask.id -Label "retry task"

if ([int]$FinalRetryTask.retry_of_task_id -ne [int]$FailedTask.id) {
    Fail-TaskCenterCheck "Finished retry task lost retry_of_task_id."
}

$RetryRequiredEventTypes = @("task_created", "task_started")

if ($FinalRetryTask.status -eq "succeeded") {
    $RetryRequiredEventTypes += "task_succeeded"
}
elseif ($FinalRetryTask.status -eq "failed") {
    $RetryRequiredEventTypes += "task_failed"
}
else {
    Fail-TaskCenterCheck "Retry task ended with unsupported status: $($FinalRetryTask.status)."
}

$RetryTaskEvents = Assert-TaskCenterEventsInclude `
    -TaskId $FinalRetryTask.id `
    -RequiredEventTypes $RetryRequiredEventTypes

Write-Host "Retry task final status: $($FinalRetryTask.status)"
Write-Host "Retry task event count: $($RetryTaskEvents.Count)"

Write-Host ""
Write-Host "Task center check completed successfully."
Write-Host "Task ID: $($FinalTask.id)"
Write-Host "Document ID: $($FinalTask.result.document_id)"
Write-Host "Chunks: $($FinalTask.result.chunk_count)"
Write-Host "Embeddings: $($FinalTask.result.embedding_count)"
Write-Host "Controlled failed task ID: $($FailedTask.id)"
Write-Host "Retry task ID: $($FinalRetryTask.id)"
