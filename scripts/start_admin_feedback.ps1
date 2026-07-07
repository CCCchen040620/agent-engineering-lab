$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

Write-Host "Starting Streamlit feedback admin page..."

python -m streamlit run frontend/admin_feedback.py
