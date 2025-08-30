# DICOM Analyzer - Complete Installation Guide

## Prerequisites

- **Python 3.8 or higher** (recommended: Python 3.10+)
- **Git** (for cloning repository)
- **OpenAI API Key** (with GPT-4 Vision access)
- **Google Gemini API Key** (optional, for enhanced AI analysis)
- **Supabase Account** (for database storage)

## Step-by-Step Installation

### 1. Clone and Setup Project

```bash
# Clone the repository
git clone <your-repository-url>
cd DICOM

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# If you encounter any issues, install packages individually:
pip install openai==1.3.7
pip install pydicom==2.4.3
pip install pillow==10.1.0
pip install numpy==1.24.3
pip install flask==3.0.0
pip install flask-cors==4.0.0
pip install python-dotenv==1.0.0
pip install requests==2.31.0
pip install matplotlib==3.7.2
pip install opencv-python==4.8.1.78
pip install scikit-image==0.21.0
pip install pandas==2.0.3
pip install torch==2.0.1
pip install torchvision==0.15.2
pip install transformers==4.35.0
pip install sentence-transformers==2.2.2
pip install google-generativeai==0.3.2
pip install reportlab==4.0.4
pip install supabase==2.3.4
```

### 3. Setup Environment Variables

```bash
# Copy the example environment file
cp config.env.example .env
```

Edit the `.env` file with your API keys:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your_secret_key_here

# DICOM Analysis Configuration
MAX_FILE_SIZE=50MB
SUPPORTED_MODALITIES=CT,MR,XR,US,CR,DR,NM,PT
```

### 4. Setup Supabase Database

1. **Create Supabase Account**: Go to [supabase.com](https://supabase.com) and create an account
2. **Create New Project**: Create a new project and note down the URL and anon key
3. **Database will be auto-created** when you first run the application

### 5. Run the Application

```bash
# Method 1: Using the startup script (recommended)
python run.py

# Method 2: Direct Flask run
python app.py

# Method 3: Using Flask command
flask run --host=0.0.0.0 --port=65432
```

The application will be available at: `http://localhost:65432`

### 6. Verify Installation

1. **Check Health Endpoint**: Visit `http://localhost:65432/api/health`
2. **Upload Test DICOM**: Try uploading a DICOM file through the web interface
3. **Check Console**: Look for successful initialization messages

## Troubleshooting

### Common Issues:

1. **OpenAI API Key Issues**:
   ```bash
   python debug_openai.py
   ```

2. **Missing Dependencies**:
   ```bash
   python test_installation.py
   ```

3. **DICOM File Issues**:
   - Ensure files have `.dcm` or `.dicom` extensions
   - Check file size (max 50MB)
   - Verify DICOM format validity

4. **Port Already in Use**:
   - Change port in `app.py` or `run.py`
   - Or kill existing process: `netstat -ano | findstr :65432`

### Performance Optimization:

1. **GPU Support** (for faster local analysis):
   ```bash
   # Install CUDA-enabled PyTorch if you have NVIDIA GPU
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

2. **Memory Management**:
   - For large DICOM files, consider increasing system RAM
   - Monitor memory usage during batch processing

## API Keys Setup

### OpenAI API Key:
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create account and add payment method
3. Generate API key with GPT-4 Vision access
4. Add to `.env` file

### Google Gemini API Key:
1. Go to [makersuite.google.com](https://makersuite.google.com)
2. Create API key
3. Add to `.env` file

### Supabase Setup:
1. Create project at [supabase.com](https://supabase.com)
2. Get project URL and anon key from Settings > API
3. Add to `.env` file

## Next Steps

After successful installation:
1. Upload your first DICOM file
2. Test AI analysis functionality
3. Generate PDF reports
4. Check Supabase database for stored results
5. Explore batch processing with multiple files

## Support

If you encounter issues:
1. Check the console logs
2. Verify all API keys are correct
3. Ensure all dependencies are installed
4. Check firewall/antivirus settings
5. Try running individual test scripts
