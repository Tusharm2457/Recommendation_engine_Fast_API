#!/bin/bash
# Install RAG System Dependencies using uv

echo "📦 Installing RAG System Dependencies with uv"
echo "=================================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "⚠️ uv is not installed. Installing uv first..."
    pip install uv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install uv. Please install it manually:"
        echo "   pip install uv"
        exit 1
    fi
    echo "✅ Successfully installed uv"
else
    echo "✅ uv is already installed"
fi

# Install packages
echo ""
echo "🚀 Installing packages with uv..."

packages=(
    "chromadb>=0.4.0"
    "openai>=1.0.0"
    "numpy>=1.24.0"
    "sentence-transformers>=2.2.0"
    "python-dotenv>=1.0.0"
    "scikit-learn>=1.3.0"
    "tokenizers>=0.21.0"
    "transformers>=4.40.0"
)

success_count=0
total_count=${#packages[@]}

for package in "${packages[@]}"; do
    echo ""
    echo "Installing $package..."
    if uv pip install "$package"; then
        echo "✅ Successfully installed $package"
        ((success_count++))
    else
        echo "❌ Failed to install $package"
    fi
done

echo ""
echo "=================================================="
echo "📊 Installation Summary: $success_count/$total_count packages installed successfully"

if [ $success_count -eq $total_count ]; then
    echo "🎉 All dependencies installed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. The system will automatically read your Azure OpenAI API key from the existing .env file"
    echo "2. Run: python test_rag_system.py"
    echo ""
    echo "💡 Tip: uv is much faster than pip for package management!"
else
    echo "⚠️ Some packages failed to install. Please check the errors above."
    echo ""
    echo "🔧 Troubleshooting:"
    echo "- Make sure you have a stable internet connection"
    echo "- Try running: uv pip install --upgrade pip"
    echo "- If issues persist, try: uv pip install --no-cache-dir <package>"
fi
