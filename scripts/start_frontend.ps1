$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

Write-Host "Starting Streamlit user app..."
Write-Host "Make sure FastAPI backend is running before using chat, upload, or feedback features."

python -m streamlit run frontend/streamlit_app.py
