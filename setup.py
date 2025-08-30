#!/usr/bin/env python3
"""
DICOM Analyzer Setup Script
Automated setup and configuration for the DICOM analysis system
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def print_header():
    print("=" * 60)
    print("🏥 DICOM Analyzer - Automated Setup")
    print("=" * 60)
    print()


def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")

    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False

    print(
        f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def create_virtual_environment():
    """Create virtual environment"""
    print("\n📦 Setting up virtual environment...")

    venv_path = Path("venv")
    if venv_path.exists():
        print("⚠️  Virtual environment already exists")
        response = input("   Do you want to recreate it? (y/N): ").lower()
        if response == 'y':
            shutil.rmtree(venv_path)
        else:
            print("✅ Using existing virtual environment")
            return True

    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False


def install_dependencies():
    """Install required dependencies"""
    print("\n📚 Installing dependencies...")

    # Determine pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = Path("venv/Scripts/pip")
    else:  # Unix/Linux/macOS
        pip_path = Path("venv/bin/pip")

    if not pip_path.exists():
        print("❌ Virtual environment pip not found")
        return False

    try:
        # Upgrade pip first
        subprocess.run([str(pip_path), "install",
                       "--upgrade", "pip"], check=True)

        # Install requirements
        subprocess.run([str(pip_path), "install", "-r",
                       "requirements.txt"], check=True)

        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def setup_environment_file():
    """Setup environment configuration file"""
    print("\n⚙️  Setting up environment configuration...")

    env_file = Path(".env")
    example_file = Path("config.env.example")

    if env_file.exists():
        print("⚠️  .env file already exists")
        response = input("   Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            print("✅ Using existing .env file")
            return True

    if not example_file.exists():
        print("❌ config.env.example not found")
        return False

    try:
        shutil.copy(example_file, env_file)
        print("✅ .env file created from template")
        print()
        print("🔑 IMPORTANT: Please edit the .env file and add your API keys:")
        print("   - OPENAI_API_KEY: Your OpenAI API key")
        print("   - GEMINI_API_KEY: Your Google Gemini API key")
        print("   - SUPABASE_URL: Your Supabase project URL")
        print("   - SUPABASE_KEY: Your Supabase anon key")
        print()
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")

    directories = ["uploads", "temp", "logs"]

    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print(f"✅ Created {directory}/ directory")
        else:
            print(f"✅ {directory}/ directory already exists")

    return True


def test_installation():
    """Test the installation"""
    print("\n🧪 Testing installation...")

    # Determine python path based on OS
    if os.name == 'nt':  # Windows
        python_path = Path("venv/Scripts/python")
    else:  # Unix/Linux/macOS
        python_path = Path("venv/bin/python")

    if not python_path.exists():
        print("❌ Virtual environment python not found")
        return False

    try:
        # Test basic imports
        test_script = '''
import sys
try:
    import pydicom
    import numpy
    import PIL
    import flask
    import openai
    import supabase
    print("✅ All required packages imported successfully")
    sys.exit(0)
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
'''

        result = subprocess.run([str(python_path), "-c", test_script],
                                capture_output=True, text=True)

        if result.returncode == 0:
            print(result.stdout.strip())
            return True
        else:
            print(result.stderr.strip())
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Installation test failed: {e}")
        return False


def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Setup completed successfully!")
    print()
    print("📋 Next Steps:")
    print("1. Edit the .env file and add your API keys")
    print("2. Activate the virtual environment:")

    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source venv/bin/activate")

    print("3. Run the application:")
    print("   python run.py")
    print("   or")
    print("   python app.py")
    print()
    print("🌐 The application will be available at: http://localhost:65432")
    print()
    print("📖 For detailed instructions, see INSTALLATION_GUIDE.md")
    print()


def main():
    """Main setup function"""
    print_header()

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        sys.exit(1)

    # Setup environment file
    if not setup_environment_file():
        sys.exit(1)

    # Create directories
    if not create_directories():
        sys.exit(1)

    # Test installation
    if not test_installation():
        print("⚠️  Installation test failed, but setup may still work")
        print("   Try running the application manually")

    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
