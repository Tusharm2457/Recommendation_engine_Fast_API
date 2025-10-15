#!/usr/bin/env python3
"""
Install RAG System Dependencies using uv
"""

import subprocess
import sys
import shutil

def check_uv_installed():
    """Check if uv is installed"""
    return shutil.which("uv") is not None

def install_uv():
    """Install uv if not already installed"""
    try:
        print("📦 Installing uv...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uv"])
        print("✅ Successfully installed uv")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install uv: {e}")
        return False

def install_package(package):
    """Install a package using uv"""
    try:
        subprocess.check_call(["uv", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    """Install all required packages using uv"""
    print("📦 Installing RAG System Dependencies with uv")
    print("="*50)
    
    # Check if uv is installed
    if not check_uv_installed():
        print("⚠️ uv is not installed. Installing uv first...")
        if not install_uv():
            print("❌ Failed to install uv. Please install it manually:")
            print("   pip install uv")
            return
    else:
        print("✅ uv is already installed")
    
    packages = [
        "chromadb>=0.4.0",
        "openai>=1.0.0", 
        "numpy>=1.24.0",
        "sentence-transformers>=2.2.0",
        "python-dotenv>=1.0.0",
        "scikit-learn>=1.3.0",
        "tokenizers>=0.21.0",
        "transformers>=4.40.0"
    ]
    
    print(f"\n🚀 Installing {len(packages)} packages with uv...")
    success_count = 0
    
    for package in packages:
        print(f"\nInstalling {package}...")
        if install_package(package):
            success_count += 1
    
    print(f"\n{'='*50}")
    print(f"📊 Installation Summary: {success_count}/{len(packages)} packages installed successfully")
    
    if success_count == len(packages):
        print("🎉 All dependencies installed successfully!")
        print("\nNext steps:")
        print("1. The system will automatically read your Azure OpenAI API key from the existing .env file")
        print("2. Run: python test_rag_system.py")
        print("\n💡 Tip: uv is much faster than pip for package management!")
    else:
        print("⚠️ Some packages failed to install. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("- Make sure you have a stable internet connection")
        print("- Try running: uv pip install --upgrade pip")
        print("- If issues persist, try: uv pip install --no-cache-dir <package>")

if __name__ == "__main__":
    main()
