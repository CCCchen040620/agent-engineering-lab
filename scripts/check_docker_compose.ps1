$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

$Failed = $false

function Fail-Check($Message) {
    Write-Host "[FAILED] $Message"
    $script:Failed = $true
}

function Pass-Check($Message) {
    Write-Host "[OK] $Message"
}

function Test-HttpEndpoint($Name, $Url) {
    try {
        $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5

        if ($Response.StatusCode -ge 200 -and $Response.StatusCode -lt 300) {
            Pass-Check "$Name is reachable: $Url"
        }
        else {
            Fail-Check "$Name returned status code $($Response.StatusCode): $Url"
        }
    }
    catch {
        Fail-Check "$Name is not reachable: $Url"
        Write-Host "         $($_.Exception.Message)"
    }
}

function Test-ComposeService($ServiceName) {
    $ContainerId = docker compose ps -q $ServiceName

    if ([string]::IsNullOrWhiteSpace($ContainerId)) {
        Fail-Check "Docker Compose service is not running: $ServiceName"
        return
    }

    $Status = docker inspect -f "{{.State.Status}}" $ContainerId

    if ($Status -eq "running") {
        Pass-Check "Docker Compose service is running: $ServiceName"
    }
    else {
        Fail-Check "Docker Compose service status is $Status: $ServiceName"
    }
}

Write-Host "Checking Docker Compose runtime..."
Write-Host "This script assumes you already ran: docker compose up --build"
Write-Host ""

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Fail-Check "docker command is not available."
}
else {
    Test-ComposeService "backend"
    Test-ComposeService "frontend"
}

Test-HttpEndpoint "FastAPI health check" "http://127.0.0.1:8000/health"
Test-HttpEndpoint "Streamlit health check" "http://127.0.0.1:8501/_stcore/health"

if ($Failed) {
    Write-Host ""
    Write-Host "Docker Compose check failed."
    Write-Host "Suggested next steps:"
    Write-Host "1. Confirm Docker Desktop is running."
    Write-Host "2. Run: docker compose up --build"
    Write-Host "3. Wait until backend and frontend finish startup."
    Write-Host "4. Run this script again."
    exit 1
}

Write-Host ""
Write-Host "Docker Compose check completed successfully."
