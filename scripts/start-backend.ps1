$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\..\backend"
if (!(Test-Path ".venv\Scripts\Activate.ps1")) {
  Write-Error "Virtual environment not found. Follow README.md first."
  exit 1
}
. .\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
