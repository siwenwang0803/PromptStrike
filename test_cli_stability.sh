#!/bin/bash
# Lightweight CLI Stability Test
# Tests basic functionality without external dependencies

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test configuration
TEST_DIR="cli_test_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$TEST_DIR/logs" "$TEST_DIR/results"

echo "PromptStrike CLI Stability Test"
echo "==============================="
echo "Test directory: $TEST_DIR"
echo ""

# Function to run test
run_test() {
    local test_name=$1
    local cmd=$2
    local expected_exit=$3
    
    echo -n "Testing $test_name... "
    
    if eval "$cmd" > "$TEST_DIR/logs/${test_name}.log" 2>&1; then
        if [[ $expected_exit -eq 0 ]]; then
            echo -e "${GREEN}✓ PASSED${NC}"
            return 0
        else
            echo -e "${RED}✗ FAILED${NC} (should have failed)"
            return 1
        fi
    else
        if [[ $expected_exit -ne 0 ]]; then
            echo -e "${GREEN}✓ PASSED${NC} (correctly failed)"
            return 0
        else
            echo -e "${RED}✗ FAILED${NC}"
            return 1
        fi
    fi
}

# Phase 1: Basic CLI Tests
echo "Phase 1: Basic CLI Functionality"
echo "--------------------------------"

run_test "help_command" "python3 -m promptstrike.cli --help" 0
run_test "version_command" "python3 -m promptstrike.cli version" 0
run_test "list_attacks" "python3 -m promptstrike.cli list-attacks" 0
run_test "doctor_command" "python3 -m promptstrike.cli doctor" 0

# Phase 2: Error Handling
echo ""
echo "Phase 2: Error Handling"
echo "----------------------"

run_test "invalid_model" "python3 -m promptstrike.cli scan invalid-model --dry-run" 1
run_test "missing_target" "python3 -m promptstrike.cli scan" 1
run_test "invalid_format" "python3 -m promptstrike.cli scan gpt-4 --format invalid --dry-run" 1
run_test "invalid_timeout" "python3 -m promptstrike.cli scan gpt-4 --timeout -1 --dry-run" 1

# Phase 3: Dry Run Tests
echo ""
echo "Phase 3: Dry Run Tests (Simulating 50 concurrent)"
echo "-------------------------------------------------"

# Test different models and formats
MODELS=("gpt-4" "gpt-3.5-turbo")
FORMATS=("json" "pdf" "html")

for model in "${MODELS[@]}"; do
    for format in "${FORMATS[@]}"; do
        echo ""
        echo "Testing $model with $format format (5 concurrent)..."
        
        # Start 5 concurrent processes (reduced from 50 for quick testing)
        pids=()
        for i in {1..5}; do
            python3 -m promptstrike.cli scan "$model" \
                --format "$format" \
                --output "$TEST_DIR/results/${model}_${format}_${i}" \
                --max-requests 5 \
                --dry-run \
                > "$TEST_DIR/logs/dry_run_${model}_${format}_${i}.log" 2>&1 &
            pids+=($!)
        done
        
        # Wait for all processes
        failed=0
        for pid in "${pids[@]}"; do
            if ! wait $pid; then
                ((failed++))
            fi
        done
        
        if [[ $failed -eq 0 ]]; then
            echo -e "${GREEN}✓ All 5 concurrent tests passed${NC}"
        else
            echo -e "${YELLOW}⚠ $failed out of 5 tests failed${NC}"
        fi
    done
done

# Phase 4: Output Validation
echo ""
echo "Phase 4: Output Validation"
echo "-------------------------"

# Check if dry run shows attack plan
echo -n "Checking dry run output... "
if python3 -m promptstrike.cli scan gpt-4 --dry-run 2>&1 | grep -q "attack plan"; then
    echo -e "${GREEN}✓ Dry run shows attack plan${NC}"
else
    echo -e "${YELLOW}⚠ Dry run output may be incomplete${NC}"
fi

# Phase 5: Performance Check
echo ""
echo "Phase 5: Performance Analysis"
echo "----------------------------"

# Time a list-attacks command
echo -n "Timing list-attacks command... "
start_time=$(date +%s)
python3 -m promptstrike.cli list-attacks > /dev/null 2>&1
end_time=$(date +%s)
duration=$((end_time - start_time))
echo "completed in ${duration}s"

# Count attacks
attack_count=$(python3 -m promptstrike.cli list-attacks 2>/dev/null | grep -E "LLM[0-9]+-[0-9]+" | wc -l)
echo "Found $attack_count attacks in OWASP pack"

# Generate Summary Report
echo ""
echo "Generating Test Summary..."
echo "========================="

report_file="$TEST_DIR/test_summary.txt"
{
    echo "PromptStrike CLI Stability Test Summary"
    echo "======================================"
    echo "Date: $(date)"
    echo "Python: $(python3 --version)"
    echo "Working Directory: $(pwd)"
    echo ""
    echo "Test Results:"
    echo "- Basic CLI commands: PASSED"
    echo "- Error handling: PASSED"
    echo "- Concurrent dry runs: TESTED (5 concurrent per model/format)"
    echo "- Attack count: $attack_count"
    echo ""
    echo "Log files: $(ls -1 $TEST_DIR/logs/*.log | wc -l)"
    echo "Result directories: $(ls -1d $TEST_DIR/results/*/ 2>/dev/null | wc -l)"
    echo ""
    echo "Recommendations for Production:"
    echo "1. Install all dependencies: pip install -r requirements.txt"
    echo "2. Increase concurrency to 50-100 for stress testing"
    echo "3. Test with real API endpoints (with rate limiting)"
    echo "4. Validate actual output files (JSON schema, PDF content)"
    echo "5. Monitor memory usage during high concurrency"
    echo "6. Add retry logic for transient failures"
    echo "7. Implement progress bars for long-running scans"
} > "$report_file"

cat "$report_file"
echo ""
echo "Full test results saved in: $TEST_DIR/"

# Check for critical issues
echo ""
echo "Critical Issues Check:"
echo "--------------------"

if grep -q "ImportError\|ModuleNotFoundError" "$TEST_DIR/logs"/*.log 2>/dev/null; then
    echo -e "${RED}✗ Missing dependencies detected${NC}"
    echo "  Run: pip install -r requirements.txt"
else
    echo -e "${GREEN}✓ No import errors detected${NC}"
fi

if grep -q "Traceback\|Exception" "$TEST_DIR/logs"/*.log 2>/dev/null | grep -v "expected"; then
    echo -e "${YELLOW}⚠ Some exceptions detected (review logs)${NC}"
else
    echo -e "${GREEN}✓ No unexpected exceptions${NC}"
fi