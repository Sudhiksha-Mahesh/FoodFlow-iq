# Start FoodFlow IQ for local development on Windows.
# Opens backend (port 8000) and frontend (port 5173) in separate windows.

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

$Python = Join-Path $Backend ".venv313\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = Join-Path $Backend ".venv\Scripts\python.exe"
}

if (-not (Test-Path $Python)) {
    Write-Host "No Python virtual environment found. Run from backend/:"
    Write-Host "  python -m venv .venv313"
    Write-Host "  .\.venv313\Scripts\pip install -r requirements.txt"
    exit 1
}

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$Backend'; & '$Python' -m uvicorn app.main:app --reload --port 8000"
)

if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
    Push-Location $Frontend
    npm install
    Pop-Location
}

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$Frontend'; npm run dev"
)

Write-Host "FoodFlow IQ starting..."
Write-Host "  Frontend: http://localhost:5173"
Write-Host "  Backend:  http://localhost:8000/api/health"
