$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

Write-Host "Starting Streamlit document admin page..."

python -m streamlit run frontend/admin_documents.py
