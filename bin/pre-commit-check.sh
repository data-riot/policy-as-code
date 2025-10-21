#!/bin/bash
# Pre-commit checks script
# Run this manually if you want to check before committing

echo "🧪 Running pre-commit checks..."

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Please run this from the project root directory"
    exit 1
fi

# Run the same checks as CI
echo "1. Testing imports..."
python3 -c "from policy_as_code import *; print('✅ All imports work')" || exit 1

echo "2. Running tests..."
python3 -m pytest tests/ -q || exit 1

echo "3. Running pre-commit hooks (includes formatting)..."
python3 -m pre_commit run --all-files || exit 1

echo "🎉 All pre-commit checks passed! Ready to commit."
