# Quick RAG Dependencies Installation

## Option 1: Python Script (Recommended)
```bash
python install_rag_dependencies.py
```

## Option 2: Bash Script
```bash
chmod +x install_rag_uv.sh
./install_rag_uv.sh
```

## Option 3: Manual uv Commands
```bash
# Install uv if not already installed
pip install uv

# Install RAG dependencies
uv pip install chromadb>=0.4.0 openai>=1.0.0 numpy>=1.24.0 sentence-transformers>=2.2.0 python-dotenv>=1.0.0
```

## Option 4: One-liner
```bash
pip install uv && uv pip install chromadb>=0.4.0 openai>=1.0.0 numpy>=1.24.0 sentence-transformers>=2.2.0 python-dotenv>=1.0.0
```

## After Installation
1. The system will automatically read your Azure OpenAI API key from the existing `.env` file
2. No need to set environment variables manually - the `.env` file is already configured

2. Test the RAG system:
   ```bash
   python test_rag_system.py
   ```

## Why uv?
- 🚀 **10-100x faster** than pip
- 🔒 **More reliable** dependency resolution
- 📦 **Better caching** and parallel downloads
- 🛡️ **More secure** package installation
