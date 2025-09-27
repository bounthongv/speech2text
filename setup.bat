@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing/Updating dependencies...
pip install -r requirements.txt

echo.
echo Setup complete! Your environment is ready.
echo You can now run any of the transcription scripts:
echo.
echo 1. transcribe_improved.py - Basic enhanced version
echo 2. transcribe_enhanced.py - Advanced features
echo 3. transcribe_meeting.py - Real-time meeting transcription
echo.
echo Example: python transcribe_improved.py
pause
