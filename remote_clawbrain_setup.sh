#!/bin/bash
# ClawBrain Remote Setup Script
# Runs on EC2 to set up the ClawBrain environment

set -e

echo "🧠 ClawBrain Remote Setup"
echo "=========================="
echo ""

CLAWBRAIN_DIR="/home/ubuntu/ClawBrain"

# Check if we're in the right directory
if [ ! -f "clawbrain" ]; then
    echo "❌ Error: clawbrain executable not found"
    echo "This script must be run from the ClawBrain directory"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "API keys may not be available"
fi

# Create Python virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo "✅ Virtual environment created"
    else
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
else
    echo "ℹ️  Virtual environment already exists"
fi

# Install Python dependencies in venv
echo ""
echo "📦 Installing Python dependencies in virtual environment..."
if [ -f "requirements.txt" ]; then
    venv/bin/pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✅ Python dependencies installed"
    else
        echo "❌ Failed to install Python dependencies"
        exit 1
    fi
else
    echo "⚠️  requirements.txt not found, skipping Python setup"
fi

# Install Node.js dependencies for WhatsApp bot
echo ""
echo "📦 Installing Node.js dependencies..."
if [ -d "messaging_service" ]; then
    cd messaging_service
    
    # Check if package.json exists
    if [ -f "package.json" ]; then
        npm install
        if [ $? -eq 0 ]; then
            echo "✅ Node.js dependencies installed"
        else
            echo "❌ Failed to install Node.js dependencies"
            exit 1
        fi
    else
        echo "⚠️  package.json not found in messaging_service/"
    fi
    
    cd ..
else
    echo "⚠️  messaging_service directory not found"
fi

# Verify installation
echo ""
echo "🔍 Verifying installation..."

# Test Python imports (use venv if available)
if [ -d "venv" ]; then
    PYTHON_CMD="venv/bin/python3"
else
    PYTHON_CMD="python3"
fi

$PYTHON_CMD -c "import llm_brain" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ llm_brain module available"
else
    echo "⚠️  llm_brain module may have issues"
fi

$PYTHON_CMD -c "import scheduler" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ scheduler module available"
else
    echo "⚠️  scheduler module may have issues"
fi

# Test clawbrain CLI
if [ -x "clawbrain" ]; then
    echo "✅ clawbrain is executable"
else
    echo "❌ clawbrain is not executable"
    chmod +x clawbrain
    echo "✅ Fixed clawbrain permissions"
fi

# Load environment variables and test
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    
    if [ -n "$GEMINI_API_KEY" ]; then
        echo "✅ GEMINI_API_KEY loaded"
    else
        echo "⚠️  GEMINI_API_KEY not found in .env"
    fi
    
    if [ -n "$ANTHROPIC_API_KEY" ]; then
        echo "✅ ANTHROPIC_API_KEY loaded"
    else
        echo "⚠️  ANTHROPIC_API_KEY not found in .env"
    fi
fi

echo ""
echo "=========================="
echo "✅ Setup Complete!"
echo "=========================="
echo ""
echo "IMPORTANT: Activate the virtual environment first:"
echo "  source venv/bin/activate"
echo ""
echo "Then test the installation:"
echo "  ./clawbrain version"
echo "  ./clawbrain status"
echo ""
echo "Set up WhatsApp bot:"
echo "  cd messaging_service"
echo "  node index.js  # Scan QR code"
echo "  pm2 start index.js --name clawbrain-whatsapp"
echo ""
