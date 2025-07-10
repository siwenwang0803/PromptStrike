#!/bin/bash
# RedForge Environment Setup Script
# Ensures proper installation of all dependencies

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "RedForge Environment Setup"
echo "=============================="
echo ""

# Check Python version
print_status "Checking Python version..."
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.11"

if [[ $(echo "$PYTHON_VERSION >= $REQUIRED_VERSION" | bc) -eq 1 ]]; then
    print_success "Python $PYTHON_VERSION found (>= $REQUIRED_VERSION required)"
else
    print_error "Python $PYTHON_VERSION found, but >= $REQUIRED_VERSION required"
    exit 1
fi

# Create virtual environment
VENV_DIR=".venv"
if [[ ! -d "$VENV_DIR" ]]; then
    print_status "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
print_success "Virtual environment activated"

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
print_success "pip upgraded"

# Check if Poetry is preferred
if command -v poetry &> /dev/null; then
    print_status "Poetry detected. Would you like to use Poetry instead? (y/n)"
    read -r USE_POETRY
    
    if [[ "$USE_POETRY" == "y" || "$USE_POETRY" == "Y" ]]; then
        print_status "Installing with Poetry..."
        poetry install
        print_success "Dependencies installed with Poetry"
        
        # Create a script to run with Poetry
        cat > run_with_poetry.sh << 'EOF'
#!/bin/bash
poetry run python -m redforge.cli "$@"
EOF
        chmod +x run_with_poetry.sh
        print_success "Created run_with_poetry.sh helper script"
    else
        print_status "Installing from requirements.txt..."
        pip install -r requirements.txt
        print_success "Dependencies installed from requirements.txt"
    fi
else
    print_status "Installing from requirements.txt..."
    pip install -r requirements.txt
    print_success "Dependencies installed from requirements.txt"
fi

# Install in development mode
print_status "Installing RedForge in development mode..."
pip install -e . > /dev/null 2>&1 || {
    print_warning "Could not install in editable mode, setting PYTHONPATH instead"
    export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
}

# Verify installation
print_status "Verifying installation..."
echo ""

# Test imports
print_status "Testing imports..."
python -c "
import sys
try:
    import click
    print('  ✓ click')
    import pydantic
    print('  ✓ pydantic (v' + pydantic.__version__ + ')')
    import httpx
    print('  ✓ httpx')
    import rich
    print('  ✓ rich')
    import typer
    print('  ✓ typer')
    import openai
    print('  ✓ openai')
    import jinja2
    print('  ✓ jinja2')
    import yaml
    print('  ✓ yaml')
    import tenacity
    print('  ✓ tenacity')
    import reportlab
    print('  ✓ reportlab')
    
    # Test RedForge imports
    sys.path.insert(0, '.')
    import redforge
    print('  ✓ redforge package')
    from redforge.cli import app
    print('  ✓ CLI module')
    from redforge.core.scanner import LLMScanner
    print('  ✓ Scanner module')
    from redforge.core.attacks import AttackPackLoader
    print('  ✓ Attack module')
    
    print('')
    print('All imports successful!')
    
except ImportError as e:
    print(f'  ✗ Import error: {e}')
    sys.exit(1)
"

if [[ $? -eq 0 ]]; then
    print_success "All imports verified"
else
    print_error "Import verification failed"
    exit 1
fi

# Test CLI
print_status "Testing CLI..."
echo ""

# Test help command
if python -m redforge.cli --help > /dev/null 2>&1; then
    print_success "CLI help command works"
else
    print_error "CLI help command failed"
fi

# Test version command
if python -m redforge.cli version > /dev/null 2>&1; then
    print_success "CLI version command works"
else
    print_error "CLI version command failed"
fi

# Test list-attacks command
if python -m redforge.cli list-attacks > /dev/null 2>&1; then
    ATTACK_COUNT=$(python -m redforge.cli list-attacks 2>/dev/null | grep -E "LLM[0-9]+-[0-9]+" | wc -l)
    print_success "CLI list-attacks works (found $ATTACK_COUNT attacks)"
else
    print_error "CLI list-attacks command failed"
fi

# Create run script
cat > run_redforge.sh << 'EOF'
#!/bin/bash
# Helper script to run RedForge with proper environment

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

if [[ -d ".venv" ]]; then
    source .venv/bin/activate
fi

python -m redforge.cli "$@"
EOF

chmod +x run_redforge.sh

# Summary
echo ""
echo "Setup Summary"
echo "============="
print_success "Environment setup complete!"
echo ""
echo "To use RedForge:"
echo "1. Activate the virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Run CLI commands:"
echo "   python -m redforge.cli --help"
echo "   python -m redforge.cli scan gpt-4 --dry-run"
echo ""
echo "Or use the helper script:"
echo "   ./run_redforge.sh --help"
echo ""

# Check for API keys
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    print_warning "OPENAI_API_KEY not set. You'll need to set it for actual scans:"
    echo "   export OPENAI_API_KEY='your-api-key'"
fi

echo ""
echo "Next steps:"
echo "1. Set your API keys (if not already done)"
echo "2. Run the test suite: bash scripts/smoke/run_cli_matrix.sh --dry-run"
echo "3. Check the doctor command: ./run_redforge.sh doctor"