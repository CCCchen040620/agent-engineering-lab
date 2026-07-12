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

Write-Host "Checking PostgreSQL Docker Compose service..."
Write-Host "This script assumes you already ran: docker compose up postgres"
Write-Host ""

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Fail-Check "docker command is not available."
}
else {
    $ContainerId = docker compose ps -q postgres

    if ([string]::IsNullOrWhiteSpace($ContainerId)) {
        Fail-Check "Docker Compose service is not running: postgres"
    }
    else {
        $Status = docker inspect -f "{{.State.Status}}" $ContainerId

        if ($Status -eq "running") {
            Pass-Check "Docker Compose service is running: postgres"
        }
        else {
            Fail-Check "Docker Compose service status is ${Status}: postgres is not running."
        }

        $Health = docker inspect -f "{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}" $ContainerId

        if ($Health -eq "healthy") {
            Pass-Check "PostgreSQL service is healthy."
        }
        else {
            Fail-Check "PostgreSQL service health is $Health."
        }
    }
}

if ($Failed) {
    Write-Host ""
    Write-Host "PostgreSQL check failed."
    Write-Host "Suggested next steps:"
    Write-Host "1. Confirm Docker Desktop is running."
    Write-Host "2. Run: docker compose up postgres"
    Write-Host "3. Wait until postgres becomes healthy."
    Write-Host "4. Run this script again."
    exit 1
}

Write-Host ""
Write-Host "PostgreSQL check completed successfully."