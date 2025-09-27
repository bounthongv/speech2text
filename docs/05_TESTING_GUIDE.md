# 🧪 Speech Recognition App - Testing Guide

## Quick Feature Test

After fixing the issues, here's how to verify everything works:

### 1. Run Feature Verification Script

```powershell
# In your activated virtual environment
(venv) PS D:\speechRecognition> python test_features.py
```

This will test:
- ✅ All required Python packages
- ✅ FFmpeg configuration  
- ✅ Google Cloud authentication
- ✅ Audio processing capabilities
- ✅ Web application configuration
- ✅ Module imports

### 2. Start the Application

Choose one of these methods:

**Method A: PowerShell Script (Recommended)**
```powershell
(venv) PS D:\speechRecognition> .\run_local.ps1
```

**Method B: Batch Script**
```cmd
(venv) D:\speechRecognition> run_local.bat
```

**Method C: Direct Python**
```powershell
(venv) PS D:\speechRecognition> python start.py
```

### 3. Test Core Features

Once the app is running (http://localhost:5000):

#### A. Upload File Transcription
1. Navigate to http://localhost:5000
2. Upload a small audio file (.wav, .mp3, .m4a)
3. Check if transcription completes successfully

#### B. Microphone Test (if microphone available)
1. Click "Start Recording" button
2. Speak for a few seconds
3. Click "Stop Recording"
4. Verify transcription appears

#### C. Usage Tracking
1. Check if usage minutes are tracked correctly
2. Test anonymous vs email user tiers

### 4. Check for Common Issues

**If FFmpeg warning appears:**
- Verify ffmpeg.exe exists in: `d:\speechRecognition\ffmpeg\bin\`
- The app should still work with the warning

**If Google Cloud errors:**
- Verify `optimum-treat-453903-v3-9f1bae929e46.json` exists
- Check GOOGLE_APPLICATION_CREDENTIALS environment variable

**If module import errors:**
- Run: `pip install -r requirements.txt`
- Check for missing dependencies

### 5. Production Readiness Check

Before Railway deployment:

```powershell
# Test production configuration
$env:FLASK_ENV = "production"
$env:SECRET_KEY = "your-production-secret-key"
python start.py
```

### 6. Expected Output

Successful startup should show:
```
✅ FFmpeg configured successfully at d:\speechRecognition\ffmpeg\bin\ffmpeg.exe
🚀 Starting Speech Recognition App on 0.0.0.0:5000
📊 Environment: development
☕ Buy Me a Coffee: https://buymeacoffee.com/yourusername
```

## Troubleshooting

### Common Solutions

1. **Virtual Environment Issues**
   ```powershell
   # Recreate virtual environment
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Port Already in Use**
   ```powershell
   # Kill processes using port 5000
   netstat -ano | findstr :5000
   taskkill /PID <process_id> /F
   ```

3. **Module Not Found Errors**
   ```powershell
   # Ensure you're in the right directory and venv is active
   cd d:\speechRecognition
   .\venv\Scripts\Activate.ps1
   pip list  # Verify packages are installed
   ```

4. **Google Cloud Authentication**
   ```powershell
   # Set credentials manually
   $env:GOOGLE_APPLICATION_CREDENTIALS = "d:\speechRecognition\optimum-treat-453903-v3-9f1bae929e46.json"
   ```

## Next Steps for Railway Deployment

1. ✅ Verify local functionality
2. 🚀 Push code to GitHub repository  
3. 🔐 Set Railway environment variables:
   - `SECRET_KEY=your-production-secret`
   - `FLASK_ENV=production`
   - `BMC_USERNAME=your-buymeacoffee-username`
4. 🌐 Deploy to Railway
5. 🧪 Test production deployment

Need help? Check the logs and error messages - they now provide better debugging information!