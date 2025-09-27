# Local Development Runner for Speech Recognition App
Write-Host "Starting Speech Recognition App - Local Development Mode" -ForegroundColor Green

# Set environment variables for local development
$env:FLASK_ENV = "development"
$env:SECRET_KEY = "bd3b42ac16e50f86fb21e3c6f10da985c6070897bc37a800c86245c1b958752d"
$env:BMC_USERNAME = "laospeech"  # Dedicated BMC account for Lao Speech Recognition
$env:DEBUG = "True"

Write-Host "Environment configured for development" -ForegroundColor Green
Write-Host "Flask Environment: $env:FLASK_ENV" -ForegroundColor Cyan
Write-Host "Using development configuration" -ForegroundColor Cyan

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Warning: Virtual environment not detected" -ForegroundColor Yellow
    Write-Host "Please activate your virtual environment first:" -ForegroundColor Yellow
    Write-Host ".\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host ""
}

# Run the application using start.py
Write-Host "Starting application..." -ForegroundColor Green
Write-Host "Once started, open http://localhost:5000 in your browser" -ForegroundColor Cyan
Write-Host ""

python start.py