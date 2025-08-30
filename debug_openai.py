#!/usr/bin/env python3
"""
Debug script to test OpenAI client initialization
"""

import os
from dotenv import load_dotenv

def test_openai_initialization():
    """Test different OpenAI initialization methods"""
    print("🔍 Debugging OpenAI Client Initialization")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key or api_key == 'your_openai_api_key_here':
        print("❌ No API key found")
        return
    
    print(f"✅ API key found: {api_key[:20]}...")
    
    # Test 1: Basic OpenAI import
    print("\n1️⃣ Testing basic import...")
    try:
        from openai import OpenAI
        print("✅ OpenAI import successful")
    except Exception as e:
        print(f"❌ OpenAI import failed: {e}")
        return
    
    # Test 2: Basic initialization
    print("\n2️⃣ Testing basic initialization...")
    try:
        client = OpenAI(api_key=api_key)
        print("✅ Basic initialization successful")
    except Exception as e:
        print(f"❌ Basic initialization failed: {e}")
    
    # Test 3: With base_url
    print("\n3️⃣ Testing with base_url...")
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.openai.com/v1"
        )
        print("✅ Base URL initialization successful")
    except Exception as e:
        print(f"❌ Base URL initialization failed: {e}")
    
    # Test 4: Legacy client
    print("\n4️⃣ Testing legacy client...")
    try:
        import openai
        openai.api_key = api_key
        print("✅ Legacy client initialization successful")
    except Exception as e:
        print(f"❌ Legacy client failed: {e}")
    
    # Test 5: Test API call
    print("\n5️⃣ Testing API call...")
    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        print(f"✅ API call successful - {len(models.data)} models")
    except Exception as e:
        print(f"❌ API call failed: {e}")

if __name__ == "__main__":
    test_openai_initialization()

