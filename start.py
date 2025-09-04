#!/usr/bin/env python3
"""
Production startup script for Speech Recognition App
"""
import os
import sys
from web_app import app, socketio

def main():
    """Main entry point for the application"""
    
    # Set default environment variables if not set
    if not os.environ.get('SECRET_KEY'):
        print("INFO: SECRET_KEY not set. Using default for development.")
        os.environ['SECRET_KEY'] = 'dev-secret-key-please-change-in-production'
    
    if not os.environ.get('FLASK_ENV'):
        # Default to development for local usage, production for deployment
        default_env = 'development' if 'PORT' not in os.environ else 'production'
        os.environ['FLASK_ENV'] = default_env
        print(f"INFO: FLASK_ENV not set. Defaulting to '{default_env}'")
    
    if not os.environ.get('BMC_USERNAME'):
        print("INFO: BMC_USERNAME not set. Using default.")
        os.environ['BMC_USERNAME'] = 'yourusername'
    
    # Get port from environment (Railway, Heroku, etc.)
    port = int(os.environ.get('PORT', 5050))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 Starting Speech Recognition App on {host}:{port}")
    print(f"📊 Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"☕ Buy Me a Coffee: https://buymeacoffee.com/{os.environ.get('BMC_USERNAME', 'yourusername')}")
    
    # Start the application
    socketio.run(
        app,
        host=host,
        port=port,
        debug=False,
        allow_unsafe_werkzeug=True
    )

if __name__ == '__main__':
    main()
