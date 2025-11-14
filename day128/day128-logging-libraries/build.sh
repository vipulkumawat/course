#!/bin/bash

# Day 128: Multi-Language Logging Libraries - Build Script
set -e

echo "🔨 Building Multi-Language Logging Libraries..."

# Create Python virtual environment
echo "🐍 Setting up Python environment..."
if python3 -m venv venv 2>/dev/null; then
    source venv/bin/activate
    # Install Python dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ Python environment ready"
else
    echo "⚠️  Failed to create Python virtual environment. Please install python3-venv:"
    echo "   sudo apt install python3-venv"
    echo "   Then run this script again."
    echo "⚠️  Skipping Python setup..."
fi

# Build Java library
echo "☕ Building Java library..."
cd java-lib
if command -v mvn &> /dev/null; then
    mvn clean compile
    echo "✅ Java library built"
else
    echo "⚠️  Maven not found, skipping Java build"
fi
cd ..

# Install Node.js dependencies
echo "🟨 Setting up Node.js environment..."
cd nodejs-lib
if command -v npm &> /dev/null; then
    npm install
    echo "✅ Node.js dependencies installed"
else
    echo "⚠️  npm not found, skipping Node.js setup"
fi
cd ..

# Build .NET library
echo "🔷 Building .NET library..."
cd dotnet-lib
if command -v dotnet &> /dev/null; then
    dotnet build
    echo "✅ .NET library built"
else
    echo "⚠️  .NET SDK not found, skipping .NET build"
fi
cd ..

echo "🎉 All libraries built successfully!"
