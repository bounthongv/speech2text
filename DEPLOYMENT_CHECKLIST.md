# 🚀 Cloud Deployment Checklist

## 📁 Files to Upload to GitHub

### ✅ REQUIRED Files (Must Upload):
- `web_app.py` - Main Flask application
- `start.py` - Production startup script  
- `config.py` - Configuration management
- `transcribe_final.py` - Core transcription logic
- `mic_calibration.py` - Microphone calibration
- `phrase_dictionary.py` - Text processing
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version for Heroku
- `railway.json` - Railway configuration
- `templates/` folder - All HTML templates
- `static/` folder - All CSS/JS files
- `ffmpeg/` folder - FFmpeg binaries (entire folder)
- `models/` folder - AI models if any
- `optimum-treat-453903-v3-9f1bae929e46.json` - Google Cloud credentials

### ⚠️ DO NOT Upload:
- `.env` file - Contains secrets
- `venv/` folder - Virtual environment
- `__pycache__/` folders - Python cache
- `usage_data.json` - User data
- `users.json` - User data
- `uploads/` folder - Uploaded files
- `results/` folder - Generated results

### 📋 Step-by-Step Upload Process:

1. **Create .gitignore file** (if not exists):
```
# Environment variables
.env
.env.local
.env.production

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd

# Virtual environment
venv/
.venv/

# Application data
usage_data.json
users.json
uploads/
results/
temp/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

2. **Initialize Git Repository**:
```bash
git init
git add .gitignore
git add .
git commit -m "Initial deployment - Speech Recognition App"
```

3. **Create GitHub Repository**:
- Go to github.com
- Click "New Repository"
- Name: `speech-recognition-app` (or your preferred name)
- Make it PUBLIC (easier for Railway)
- Don't initialize with README (you already have files)

4. **Push to GitHub**:
```bash
git remote add origin https://github.com/YOUR_USERNAME/speech-recognition-app.git
git branch -M main
git push -u origin main
```

## ☕ BMC Setup Process:

### Step 1: Create Buy Me a Coffee Account
1. Go to https://buymeacoffee.com
2. Sign up with email
3. Choose username (examples for Lao Speech Recognition):
   - `lao-speech`
   - `laospeechapp`
   - `lao-transcribe` 
   - `bounthong-lao`
   - `laospeechrecognition`

### Step 2: Set Up Profile
1. Add profile description:
   ```
   "Support my free speech-to-text application! 
   Your support helps keep the service running and adds unlimited usage."
   ```
2. Set supporter goals
3. Add thank you message
4. Note your username for deployment

## 🚂 Railway Deployment:

### Step 1: Railway Setup
1. Go to https://railway.app
2. Sign up with GitHub account
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository

### Step 2: Environment Variables
Set these in Railway dashboard:

**REQUIRED:**
```
SECRET_KEY=your-super-secret-production-key-here
FLASK_ENV=production
BMC_USERNAME=your-actual-bmc-username
```

**OPTIONAL (with defaults):**
```
FREE_TIER_MINUTES=60
EMAIL_TIER_MINUTES=240
```

### Step 3: Generate Production Secret Key
Run this in Python to generate secure key:
```python
import secrets
print(secrets.token_urlsafe(32))
```

## 🧪 Testing Checklist:

After deployment, test these features:

### Anonymous User (1 hour limit):
- [ ] Can access the app
- [ ] Can upload audio file
- [ ] Can record from microphone
- [ ] Usage tracking shows correctly
- [ ] Limit enforcement works

### Email User (4 hour limit):
- [ ] Email registration works
- [ ] Limit increases to 4 hours
- [ ] Usage tracking updates

### BMC Integration:
- [ ] Coffee button links to your BMC page
- [ ] Can complete donation on BMC
- [ ] Supporter status can be verified

### Core Features:
- [ ] Speech recognition works
- [ ] File upload works
- [ ] Real-time transcription works
- [ ] Mobile responsive
- [ ] Error handling works

## 🔗 Final URLs:

After successful deployment:
- **Your App**: https://your-app-name.railway.app
- **Your BMC**: https://buymeacoffee.com/your-username
- **GitHub Repo**: https://github.com/yourusername/speech-recognition-app

## 💰 Expected Costs:

**Railway Pricing:**
- Month 1-2: $0 (Free tier)
- Month 3+: $5-15/month (usage-based)

**Break-even**: 2-3 BMC supporters ($6-9/month)

## 🚨 Common Issues & Solutions:

### Build Fails:
- Check Railway logs
- Verify all required files uploaded
- Check requirements.txt

### App Won't Start:
- Verify environment variables set
- Check SECRET_KEY is set
- Verify FLASK_ENV=production

### BMC Not Working:
- Verify BMC_USERNAME is correct
- Check BMC profile is public
- Test BMC link manually

### Google Cloud Errors:
- Verify credentials file uploaded
- Check file permissions
- Ensure API is enabled

---

**Ready to deploy? Follow this checklist step by step! 🎯**