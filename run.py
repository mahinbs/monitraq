#!/usr/bin/env python3
"""
Startup script for DICOM Analyzer
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  .env file not found!")
        print("📝 Creating .env file from template...")
        
        if os.path.exists('config.env.example'):
            import shutil
            shutil.copy('config.env.example', '.env')
            print("✅ .env file created from template")
        else:
            print("❌ config.env.example not found!")
            return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    print("✅ Environment configured correctly")
    return True

def check_dependencies():
    """Check if all dependencies are installed"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        'pydicom',
        'numpy',
        'PIL',
        'cv2',
        'openai',
        'flask',
        'dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            elif package == 'cv2':
                import cv2
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("📦 Installing dependencies...")
        os.system(f"{sys.executable} -m pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed")
    return True

def create_upload_directory():
    """Create upload directory if it doesn't exist"""
    upload_dir = Path('uploads')
    if not upload_dir.exists():
        print("📁 Creating uploads directory...")
        upload_dir.mkdir(exist_ok=True)
        print("✅ Uploads directory created")

def main():
    """Main startup function"""
    print("🏥 DICOM Analyzer Startup")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        return 1
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed")
        return 1
    
    # Create upload directory
    create_upload_directory()
    
    print("\n🚀 Starting Open Source DICOM Analyzer...")
    print("🌐 Application will be available at: http://localhost:[dynamic port]")
    print("⏹️  Press Ctrl+C to stop the server")
    print("=" * 40)
    
    try:
        # Import and run the Flask app
        from app import app
        
        # Run the application
        app.run(
            debug=True,
            host='0.0.0.0',
            port=0,  # Let the OS choose an available port
            use_reloader=False  # Disable reloader to avoid duplicate processes
        )
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down DICOM Analyzer...")
        return 0
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
