#!/bin/bash

# Day 128: Multi-Language Logging Libraries - Verification Script
set -e

echo "🔍 Verifying Multi-Language Logging Libraries..."

# Check directory structure
echo "📁 Checking project structure..."
expected_dirs=("python-lib" "java-lib" "nodejs-lib" "dotnet-lib" "dashboard" "tests" "examples" "docker")
for dir in "${expected_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "   ✅ $dir/"
    else
        echo "   ❌ Missing: $dir/"
        exit 1
    fi
done

# Check Python library files
echo "🐍 Checking Python library..."
python_files=("python-lib/__init__.py" "python-lib/logger.py" "python-lib/config.py" "python-lib/models.py")
for file in "${python_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
        exit 1
    fi
done

# Check Java library files
echo "☕ Checking Java library..."
java_files=("java-lib/pom.xml" "java-lib/src/main/java/com/distributedlogs/DistributedLogger.java")
for file in "${java_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
        exit 1
    fi
done

# Check Node.js library files
echo "🟨 Checking Node.js library..."
nodejs_files=("nodejs-lib/package.json" "nodejs-lib/index.js")
for file in "${nodejs_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
        exit 1
    fi
done

# Check .NET library files
echo "🔷 Checking .NET library..."
dotnet_files=("dotnet-lib/DistributedLogging.csproj" "dotnet-lib/DistributedLogger.cs")
for file in "${dotnet_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
        exit 1
    fi
done

# Check dashboard files
echo "🌐 Checking dashboard..."
dashboard_files=("dashboard/app.py" "dashboard/templates/dashboard.html")
for file in "${dashboard_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
        exit 1
    fi
done

# Check build scripts
echo "🔨 Checking build scripts..."
build_scripts=("build.sh" "test.sh" "demo.sh" "start.sh" "stop.sh")
for script in "${build_scripts[@]}"; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        echo "   ✅ $script (executable)"
    else
        echo "   ❌ Missing or not executable: $script"
        exit 1
    fi
done

# Check Docker files
echo "🐳 Checking Docker configuration..."
docker_files=("docker-compose.yml" "docker/Dockerfile.dashboard" ".dockerignore")
for file in "${docker_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
        exit 1
    fi
done

# Check examples
echo "📚 Checking examples..."
example_files=("examples/python_demo.py" "examples/nodejs_demo.js" "examples/JavaDemo.java" "examples/Program.cs")
for file in "${example_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
        exit 1
    fi
done

# Check tests
echo "🧪 Checking tests..."
test_files=("tests/test_integration.py" "tests/test_performance.py")
for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
        exit 1
    fi
done

echo ""
echo "🎉 All files verified successfully!"
echo ""
echo "📋 Next Steps:"
echo "   1. Run './build.sh' to build all libraries"
echo "   2. Run './test.sh' to run tests"  
echo "   3. Run './demo.sh' to see the system in action"
echo "   4. Open http://localhost:5000 to view the dashboard"
echo ""
echo "✅ Multi-Language Logging Libraries are ready for use!"
