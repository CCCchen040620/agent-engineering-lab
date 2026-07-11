$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

$Failed = $false

function Check-RequiredCommand($Name, $Hint) {
    if (Get-Command $Name -ErrorAction SilentlyContinue) {
        Write-Host "[OK] command: $Name"
    }
    else {
        Write-Host "[MISSING] command: $Name"
        Write-Host "          $Hint"
        $script:Failed = $true
    }
}

function Check-OptionalCommand($Name, $Hint) {
    if (Get-Command $Name -ErrorAction SilentlyContinue) {
        Write-Host "[OK] optional command: $Name"
    }
    else {
        Write-Host "[WARN] optional command not found: $Name"
        Write-Host "       $Hint"
    }
}

function Check-RequiredFile($Path, $Hint) {
    if (Test-Path $Path) {
        Write-Host "[OK] file: $Path"
    }
    else {
        Write-Host "[MISSING] file: $Path"
        Write-Host "          $Hint"
        $script:Failed = $true
    }
}

Write-Host "Checking local development environment..."

Check-RequiredCommand "python" "Install Python and make sure python is available in PATH."
Check-RequiredCommand "git" "Install Git and make sure git is available in PATH."
Check-RequiredCommand "pytest" "Install project dev dependencies, then run this check again."

Check-OptionalCommand "ollama" "Ollama is required for local LLM and embedding features."
Check-OptionalCommand "docker" "Docker is optional for local development, but required for Docker Compose startup."

Check-RequiredFile ".env.example" "The example environment file documents required config values."
Check-RequiredFile "pyproject.toml" "The Python project config declares dependencies and pytest settings."
Check-RequiredFile "Dockerfile" "The Docker image build depends on this file."
Check-RequiredFile "docker-compose.yml" "Docker Compose startup depends on this file."
Check-RequiredFile "scripts\migrate_sqlite.ps1" "SQLite migration script is required before local startup."
Check-RequiredFile "scripts\check_project.ps1" "Project check script is required for regression checks."
Check-RequiredFile "scripts\start_backend.ps1" "Backend startup script is required for local development."
Check-RequiredFile "scripts\start_frontend.ps1" "Frontend startup script is required for local development."

Write-Host ""
Write-Host "Python version:"
python --version

$PythonMajorMinor = python -c "import sys; print(str(sys.version_info.major) + '.' + str(sys.version_info.minor))"

if ($PythonMajorMinor -ne "3.13") {
    Write-Host "[WARN] Project target Python version is 3.13, but current python is $PythonMajorMinor."
    Write-Host "       Tests may still pass locally, but CI and final delivery should use Python 3.13."
}

Write-Host ""
Write-Host "Git version:"
git --version

if ($Failed) {
    Write-Host ""
    Write-Host "Environment check failed. Fix the missing required items above."
    exit 1
}

Write-Host ""
Write-Host "Environment check completed successfully."
