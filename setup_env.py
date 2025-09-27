#!/usr/bin/env python3
"""
Environment setup script for Speech Recognition App
Generates secure keys and creates .env file
"""
import secrets
import os

def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_urlsafe(32)

def create_env_file():
    """Create .env file with secure defaults"""
    
    print("🔧 Setting up environment for Speech Recognition App")
    print("=" * 50)
    
    # Generate secure secret key
    secret_key = generate_secret_key()
    print(f"✅ Generated secure SECRET_KEY")
    
    # Get BMC username
    bmc_username = input("Enter your Buy Me a Coffee username (or press Enter for 'yourusername'): ").strip()
    if not bmc_username:
        bmc_username = "yourusername"
    
    # Create .env content
    env_content = f"""# Speech Recognition App Environment Configuration
# Generated automatically - DO NOT COMMIT TO VERSION CONTROL

# Flask Configuration
SECRET_KEY={secret_key}
FLASK_ENV=development

# Buy Me a Coffee Integration
BMC_USERNAME={bmc_username}

# Usage Limits (minutes per month)
FREE_TIER_MINUTES=30
EMAIL_TIER_MINUTES=120

# Server Configuration
HOST=localhost
PORT=5000

# For production deployment, set:
# FLASK_ENV=production
# And use your platform's environment variable system
"""
    
    # Write .env file
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created .env file")
    print(f"✅ BMC Username: {bmc_username}")
    print(f"✅ BMC URL: https://buymeacoffee.com/{bmc_username}")
    
    # Create .gitignore if it doesn't exist
    gitignore_content = """# Environment variables
.env
.env.local
.env.production

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
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
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
"""
    
    if not os.path.exists('.gitignore'):
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)
        print("✅ Created .gitignore file")
    
    print("\n🚀 Setup complete!")
    print("\nNext steps:")
    print("1. Run: python start.py")
    print("2. Open: http://localhost:5000")
    print("3. Test the application")
    print("4. When ready, deploy to production")
    print(f"5. Update BMC username in production: {bmc_username}")

def main():
    """Main setup function"""
    if os.path.exists('.env'):
        overwrite = input(".env file already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Setup cancelled.")
            return
    
    create_env_file()

if __name__ == '__main__':
    main()
