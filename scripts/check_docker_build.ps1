$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

Write-Host "Checking Docker Compose image build..."
Write-Host "This script runs: docker compose build"
Write-Host ""

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[FAILED] docker command is not available."
    Write-Host "Suggested next step: install and start Docker Desktop."
    exit 1
}

docker compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[FAILED] Docker Compose build failed."
    Write-Host "Suggested next steps:"
    Write-Host "1. Confirm Docker Desktop is running."
    Write-Host "2. Confirm network access is available for pulling base images and installing dependencies."
    Write-Host "3. Check Dockerfile and pyproject.toml dependency configuration."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Docker Compose image build completed successfully."
