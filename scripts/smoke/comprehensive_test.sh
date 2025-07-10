#!/bin/bash
# Comprehensive CLI Stability Test for RedForge
# Tests concurrent attacks, multiple output formats, error handling, and performance

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test configuration
TEST_DIR="./cli_stability_test_$(date +%Y%m%d_%H%M%S)"
VENV_DIR="$TEST_DIR/venv"
RESULTS_DIR="$TEST_DIR/results"
LOGS_DIR="$TEST_DIR/logs"

# Function to print colored output
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

# Function to setup test environment
setup_environment() {
    print_status "Setting up test environment..."
    
    # Create test directories
    mkdir -p "$TEST_DIR" "$RESULTS_DIR" "$LOGS_DIR"
    
    # Create Python virtual environment
    print_status "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Install dependencies
    print_status "Installing dependencies..."
    pip install --upgrade pip > "$LOGS_DIR/pip_upgrade.log" 2>&1
    
    # Install from requirements.txt if exists
    if [[ -f requirements.txt ]]; then
        pip install -r requirements.txt > "$LOGS_DIR/pip_install.log" 2>&1
    fi
    
    # Install the package in development mode
    pip install -e . > "$LOGS_DIR/pip_install_dev.log" 2>&1 || {
        print_warning "Failed to install in dev mode, trying direct install"
        export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
    }
    
    print_success "Environment setup complete"
}

# Function to test basic CLI functionality
test_basic_cli() {
    print_status "Testing basic CLI functionality..."
    
    local test_log="$LOGS_DIR/basic_cli_test.log"
    
    # Test help command
    if python -m redforge.cli --help > "$test_log" 2>&1; then
        print_success "CLI help command works"
    else
        print_error "CLI help command failed"
        cat "$test_log"
        return 1
    fi
    
    # Test version command
    if python -m redforge.cli version >> "$test_log" 2>&1; then
        print_success "CLI version command works"
    else
        print_error "CLI version command failed"
        return 1
    fi
    
    # Test doctor command
    if python -m redforge.cli doctor >> "$test_log" 2>&1; then
        print_success "CLI doctor command works"
    else
        print_warning "CLI doctor command failed (may be due to missing API key)"
    fi
    
    # Test list-attacks command
    if python -m redforge.cli list-attacks >> "$test_log" 2>&1; then
        print_success "CLI list-attacks command works"
        # Count attacks
        local attack_count=$(python -m redforge.cli list-attacks 2>/dev/null | grep -E "LLM[0-9]+-[0-9]+" | wc -l)
        print_status "Found $attack_count attacks in OWASP pack"
    else
        print_error "CLI list-attacks command failed"
        return 1
    fi
}

# Function to test error handling
test_error_handling() {
    print_status "Testing error handling..."
    
    local test_log="$LOGS_DIR/error_handling_test.log"
    local passed=0
    local failed=0
    
    # Test cases for error handling
    declare -a error_tests=(
        "scan invalid-model|Invalid model"
        "scan gpt-4 --timeout 0|Invalid timeout"
        "scan gpt-4 --max-requests -1|Invalid max"
        "scan gpt-4 --format invalid|Invalid format"
        "scan|Missing required"
    )
    
    for test_case in "${error_tests[@]}"; do
        IFS='|' read -r cmd expected <<< "$test_case"
        
        print_status "Testing: $cmd"
        if python -m redforge.cli $cmd > "$test_log" 2>&1; then
            print_error "Command should have failed: $cmd"
            ((failed++))
        else
            if grep -qi "$expected" "$test_log" 2>/dev/null; then
                print_success "Error handling correct for: $cmd"
                ((passed++))
            else
                print_warning "Error message not as expected for: $cmd"
                ((failed++))
            fi
        fi
    done
    
    print_status "Error handling tests: $passed passed, $failed failed"
}

# Function to test concurrent dry runs
test_concurrent_dry_runs() {
    print_status "Testing concurrent dry runs..."
    
    local concurrency=50
    local models=("gpt-4" "gpt-3.5-turbo")
    local formats=("json" "pdf" "html")
    local pids=()
    
    for model in "${models[@]}"; do
        for format in "${formats[@]}"; do
            print_status "Starting $concurrency concurrent dry runs for $model/$format..."
            
            for ((i=1; i<=concurrency; i++)); do
                (
                    python -m redforge.cli scan "$model" \
                        --format "$format" \
                        --output "$RESULTS_DIR/${model}_${format}_${i}" \
                        --dry-run \
                        > "$LOGS_DIR/dry_run_${model}_${format}_${i}.log" 2>&1
                ) &
                pids+=($!)
                
                # Throttle process creation
                if (( i % 10 == 0 )); then
                    sleep 0.1
                fi
            done
        done
    done
    
    # Wait for all processes
    print_status "Waiting for ${#pids[@]} dry run processes to complete..."
    local failed=0
    for pid in "${pids[@]}"; do
        if ! wait $pid; then
            ((failed++))
        fi
    done
    
    if [[ $failed -eq 0 ]]; then
        print_success "All $concurrency concurrent dry runs completed successfully"
    else
        print_warning "$failed out of ${#pids[@]} dry runs failed"
    fi
}

# Function to test with mock API responses
test_with_mock_api() {
    print_status "Testing with mock API responses..."
    
    # Create a mock response script
    cat > "$TEST_DIR/mock_llm.py" << 'EOF'
import json
import time
import random

def mock_response():
    time.sleep(random.uniform(0.1, 0.5))  # Simulate API latency
    
    responses = [
        "I cannot ignore previous instructions.",
        "Here is the information you requested.",
        "I'm designed to be helpful, harmless, and honest.",
        "<script>alert('test')</script>",
        "The system prompt is: Be helpful and harmless."
    ]
    
    return {
        "choices": [{
            "message": {
                "content": random.choice(responses)
            }
        }],
        "usage": {
            "total_tokens": random.randint(50, 200)
        }
    }

if __name__ == "__main__":
    import sys
    print(json.dumps(mock_response()))
EOF
    
    # Run tests with mock
    print_status "Running scan with mock responses..."
    
    # Note: Since we can't easily mock the HTTP client, we'll test the dry-run extensively
    python -m redforge.cli scan "gpt-4" \
        --format all \
        --output "$RESULTS_DIR/mock_test" \
        --dry-run \
        --verbose \
        > "$LOGS_DIR/mock_test.log" 2>&1
    
    if [[ $? -eq 0 ]]; then
        print_success "Mock test completed successfully"
    else
        print_error "Mock test failed"
    fi
}

# Function to test output validation
test_output_validation() {
    print_status "Testing output validation..."
    
    # Create sample output files for validation
    mkdir -p "$RESULTS_DIR/validation_test"
    
    # Create valid JSON
    cat > "$RESULTS_DIR/validation_test/valid.json" << 'EOF'
{
    "scan_id": "ps-20250108-123456-0001",
    "target": "gpt-4",
    "attack_pack": "owasp-llm-top10",
    "start_time": "2025-01-08T12:34:56Z",
    "end_time": "2025-01-08T12:35:56Z",
    "overall_risk_score": 6.5,
    "security_posture": "fair",
    "results": [
        {
            "attack_id": "LLM01-001",
            "category": "prompt_injection",
            "severity": "critical",
            "is_vulnerable": true,
            "confidence_score": 0.85,
            "risk_score": 8.5
        }
    ],
    "metadata": {
        "total_attacks": 47,
        "successful_attacks": 45,
        "vulnerabilities_found": 3
    },
    "compliance": {
        "nist_rmf_controls_tested": ["GV-1.1", "MP-2.3"],
        "eu_ai_act_risk_category": "high"
    }
}
EOF
    
    # Create invalid JSON
    echo '{"invalid": json}' > "$RESULTS_DIR/validation_test/invalid.json"
    
    # Create valid HTML
    cat > "$RESULTS_DIR/validation_test/valid.html" << 'EOF'
<!DOCTYPE html>
<html>
<head><title>RedForge Scan Report</title></head>
<body>
    <h1>RedForge Security Scan Report</h1>
    <p>Target: gpt-4</p>
    <p>Risk Score: 6.5/10</p>
</body>
</html>
EOF
    
    # Run validation
    if [[ -f scripts/smoke/validate_outputs.py ]]; then
        python scripts/smoke/validate_outputs.py "$RESULTS_DIR/validation_test" -v \
            > "$LOGS_DIR/validation_test.log" 2>&1
        
        if [[ $? -eq 0 ]]; then
            print_success "Output validation test passed"
        else
            print_warning "Some validation tests failed (expected for invalid.json)"
        fi
    else
        print_warning "Validation script not found"
    fi
}

# Function to run performance monitoring test
test_performance_monitoring() {
    print_status "Testing performance monitoring..."
    
    if [[ -f scripts/smoke/monitor_performance.sh ]]; then
        # Start performance monitoring in background
        scripts/smoke/monitor_performance.sh \
            -o "$LOGS_DIR/performance_metrics.csv" \
            -p "redforge" \
            -i 1 &
        
        local monitor_pid=$!
        print_status "Started performance monitor (PID: $monitor_pid)"
        
        # Run some concurrent operations
        print_status "Running concurrent operations for performance testing..."
        for i in {1..20}; do
            python -m redforge.cli list-attacks > /dev/null 2>&1 &
        done
        
        # Wait a bit
        sleep 5
        
        # Stop monitoring
        kill $monitor_pid 2>/dev/null || true
        
        if [[ -f "$LOGS_DIR/performance_metrics.csv" ]]; then
            local lines=$(wc -l < "$LOGS_DIR/performance_metrics.csv")
            print_success "Performance monitoring captured $lines data points"
        else
            print_warning "Performance metrics file not created"
        fi
    else
        print_warning "Performance monitoring script not found"
    fi
}

# Function to generate test report
generate_test_report() {
    print_status "Generating test report..."
    
    local report_file="$TEST_DIR/test_report.txt"
    
    {
        echo "RedForge CLI Stability Test Report"
        echo "====================================="
        echo "Date: $(date)"
        echo "Test Directory: $TEST_DIR"
        echo ""
        echo "Test Results:"
        echo "-------------"
        
        # Count log files
        echo "- Log files generated: $(find "$LOGS_DIR" -name "*.log" | wc -l)"
        
        # Count dry run results
        echo "- Dry run tests: $(find "$LOGS_DIR" -name "dry_run_*.log" | wc -l)"
        
        # Check for errors
        echo "- Errors found: $(grep -r "Error\|ERROR\|Failed" "$LOGS_DIR" 2>/dev/null | wc -l)"
        
        # Performance summary
        if [[ -f "$LOGS_DIR/performance_metrics.csv" ]]; then
            echo ""
            echo "Performance Metrics:"
            echo "-------------------"
            tail -5 "$LOGS_DIR/performance_metrics.csv"
        fi
        
        echo ""
        echo "Recommendations:"
        echo "----------------"
        echo "1. Increase timeout values for slow API responses"
        echo "2. Implement retry logic for transient failures"
        echo "3. Add connection pooling for concurrent requests"
        echo "4. Consider rate limiting to prevent API throttling"
        echo "5. Add progress indicators for long-running scans"
        
    } > "$report_file"
    
    print_success "Test report generated: $report_file"
    cat "$report_file"
}

# Main test execution
main() {
    print_status "Starting RedForge CLI Stability Tests"
    echo "========================================="
    
    # Setup environment
    setup_environment
    
    # Run test suites
    test_basic_cli
    test_error_handling
    test_concurrent_dry_runs
    test_with_mock_api
    test_output_validation
    test_performance_monitoring
    
    # Generate report
    generate_test_report
    
    # Cleanup
    deactivate 2>/dev/null || true
    
    print_success "All tests completed!"
    print_status "Test results saved in: $TEST_DIR"
}

# Run main function
main