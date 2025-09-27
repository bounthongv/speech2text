@echo off
echo 🚀 Starting Speech Recognition App - Local Development Mode

:: Set environment variables for local development
set FLASK_ENV=development
set SECRET_KEY=bd3b42ac16e50f86fb21e3c6f10da985c6070897bc37a800c86245c1b958752d
set BMC_USERNAME=laospeech
set DEBUG=True

echo ✅ Environment configured for development
echo 📍 Flask Environment: %FLASK_ENV%
echo 🔧 Using development configuration

:: Run the application using start.py (which handles defaults gracefully)
echo 🏃 Starting application...
python start.py

pause