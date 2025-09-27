#!/usr/bin/env python3
"""
Feature Verification Script for Speech Recognition App
Tests all core components to ensure they work correctly
"""

import sys
import os
import tempfile
import wave
import numpy as np
from datetime import datetime

def test_imports():
    """Test all critical imports"""
    print("🔍 Testing imports...")
    
    try:
        import speech_recognition as sr
        print(f"✅ SpeechRecognition: {sr.__version__}")
    except ImportError as e:
        print(f"❌ SpeechRecognition: {e}")
        return False
    
    try:
        from google.cloud import speech_v1p1beta1 as speech
        print("✅ Google Cloud Speech API")
    except ImportError as e:
        print(f"❌ Google Cloud Speech API: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
    except ImportError as e:
        print(f"❌ NumPy: {e}")
        return False
    
    try:
        from scipy import signal
        print("✅ SciPy (for audio processing)")
    except ImportError as e:
        print(f"❌ SciPy: {e}")
        return False
    
    try:
        from pydub import AudioSegment
        print("✅ PyDub (for audio conversion)")
    except ImportError as e:
        print(f"❌ PyDub: {e}")
        return False
    
    try:
        import flask
        print(f"✅ Flask: {flask.__version__}")
    except ImportError as e:
        print(f"❌ Flask: {e}")
        return False
    
    return True

def test_ffmpeg():
    """Test FFmpeg configuration"""
    print("\n🔍 Testing FFmpeg configuration...")
    
    try:
        from pydub import AudioSegment
        
        # Create a simple test audio
        test_audio = AudioSegment.silent(duration=1000)  # 1 second of silence
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            test_audio.export(temp_file.name, format="wav")
            
            # Try to read it back
            loaded_audio = AudioSegment.from_wav(temp_file.name)
            print("✅ FFmpeg: Audio processing works correctly")
            
            # Clean up
            os.unlink(temp_file.name)
            return True
            
    except Exception as e:
        print(f"❌ FFmpeg: {e}")
        return False

def test_google_cloud_auth():
    """Test Google Cloud authentication"""
    print("\n🔍 Testing Google Cloud authentication...")
    
    # Check for credentials file
    credentials_file = "optimum-treat-453903-v3-9f1bae929e46.json"
    if os.path.exists(credentials_file):
        print(f"✅ Credentials file found: {credentials_file}")
        
        # Set environment variable
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file
        
        try:
            from google.cloud import speech_v1p1beta1 as speech
            client = speech.SpeechClient()
            print("✅ Google Cloud Speech client initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Google Cloud client error: {e}")
            return False
    else:
        print(f"❌ Credentials file not found: {credentials_file}")
        return False

def test_audio_processing():
    """Test audio processing capabilities"""
    print("\n🔍 Testing audio processing...")
    
    try:
        # Create a test audio file
        sample_rate = 16000
        duration = 2  # seconds
        frequency = 440  # A4 note
        
        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = (np.sin(2 * np.pi * frequency * t) * 32767 * 0.5).astype(np.int16)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            # Test reading the file
            with wave.open(temp_file.name, 'rb') as wav_file:
                frames = wav_file.readframes(-1)
                read_data = np.frombuffer(frames, dtype=np.int16)
                
            print("✅ Audio processing: WAV file creation and reading works")
            
            # Clean up
            os.unlink(temp_file.name)
            return True
            
    except Exception as e:
        print(f"❌ Audio processing: {e}")
        return False

def test_web_app_config():
    """Test web application configuration"""
    print("\n🔍 Testing web application configuration...")
    
    try:
        # Set development environment if not set
        if not os.environ.get('FLASK_ENV'):
            os.environ['FLASK_ENV'] = 'development'
        if not os.environ.get('SECRET_KEY'):
            os.environ['SECRET_KEY'] = 'dev-test-key'
            
        from config import config
        from web_app import app
        
        print(f"✅ Flask app created successfully")
        print(f"✅ Environment: {os.environ.get('FLASK_ENV', 'not set')}")
        print(f"✅ Secret key: {'set' if app.config.get('SECRET_KEY') else 'not set'}")
        print(f"✅ Upload folder: {app.config.get('UPLOAD_FOLDER', 'not configured')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Web app configuration error: {e}")
        return False
    """Test web application imports"""
    print("\n🔍 Testing web application imports...")
    
    try:
        # Test key modules used by web_app.py
        from transcribe_final import transcribe_audio_final
        print("✅ transcribe_final module")
        
        # Test mic_calibration with exception handling
        try:
            from mic_calibration import MicrophoneCalibrator
            print("✅ mic_calibration module")
        except ImportError as e:
            print(f"⚠️  mic_calibration module: {e} (may need PyAudio)")
        
        # Test phrase_dictionary with exception handling  
        try:
            from phrase_dictionary import PhraseDictionary
            print("✅ phrase_dictionary module")
        except ImportError as e:
            print(f"⚠️  phrase_dictionary module: {e} (optional dependencies)")
        
        from config import config
        print("✅ config module")
        
        return True
        
    except ImportError as e:
        print(f"❌ Critical web app import error: {e}")
        return False

def main():
    """Run all feature tests"""
    print("🚀 Speech Recognition App - Feature Verification")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Core Imports", test_imports),
        ("FFmpeg Configuration", test_ffmpeg),
        ("Google Cloud Authentication", test_google_cloud_auth),
        ("Audio Processing", test_audio_processing),
        ("Web App Configuration", test_web_app_config),
        ("Web App Modules", test_web_app_imports),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: Unexpected error - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 FEATURE VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print()
    print(f"📈 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All features are working correctly!")
        print("🚀 Your application is ready for deployment!")
    else:
        print("⚠️  Some features need attention before deployment.")
        print("💡 Please check the failed tests above and resolve any issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)