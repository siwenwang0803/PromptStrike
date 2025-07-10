#!/bin/bash
# RedForge CLI Matrix Test Script
# Tests CLI stability with concurrent attacks and multiple output formats
# Reference: Production readiness testing for Sprint S-2

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
MODELS="gpt-4"
FORMATS="json,pdf,html"
CONCURRENCY=50
OUTPUT_DIR="./test_outputs"
LOG_DIR="./logs"
VERBOSE=false
DRY_RUN=false
VALIDATE_OUTPUT=true
PERFORMANCE_MONITOR=true

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

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --models)
            MODELS="$2"
            shift 2
            ;;
        --formats)
            FORMATS="$2"
            shift 2
            ;;
        --concurrency)
            CONCURRENCY="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-validation)
            VALIDATE_OUTPUT=false
            shift
            ;;
        --no-monitor)
            PERFORMANCE_MONITOR=false
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --models MODELS           Comma-separated list of models (default: gpt-4)"
            echo "  --formats FORMATS         Comma-separated list of formats (default: json,pdf,html)"
            echo "  --concurrency N           Number of concurrent attacks (default: 50)"
            echo "  --output-dir DIR          Output directory (default: ./test_outputs)"
            echo "  --verbose                 Enable verbose output"
            echo "  --dry-run                 Show what would be tested without running"
            echo "  --skip-validation         Skip output validation"
            echo "  --no-monitor              Disable performance monitoring"
            echo "  --help                    Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Convert comma-separated lists to arrays
IFS=',' read -ra MODEL_ARRAY <<< "$MODELS"
IFS=',' read -ra FORMAT_ARRAY <<< "$FORMATS"

# Create necessary directories
mkdir -p "$OUTPUT_DIR" "$LOG_DIR" "$OUTPUT_DIR/reports"

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if redforge is available
    if ! command -v redforge &> /dev/null && ! poetry run redforge --help &> /dev/null 2>&1; then
        print_error "RedForge CLI not found. Please install it first."
        exit 1
    fi
    
    # Check for required environment variables
    if [[ -z "${OPENAI_API_KEY:-}" ]] && [[ ! " ${MODEL_ARRAY[@]} " =~ " local-llama " ]]; then
        print_warning "OPENAI_API_KEY not set. Required for OpenAI models."
    fi
    
    # Check if jq is available for JSON validation
    if command -v jq &> /dev/null; then
        HAS_JQ=true
    else
        HAS_JQ=false
        print_warning "jq not found. JSON validation will be skipped."
    fi
    
    # Check for performance monitoring tools
    if [[ "$PERFORMANCE_MONITOR" == true ]]; then
        if command -v iostat &> /dev/null; then
            HAS_IOSTAT=true
        else
            HAS_IOSTAT=false
            print_warning "iostat not found. Disk I/O monitoring will be skipped."
        fi
    fi
    
    print_success "Prerequisites check completed"
}

# Function to monitor system performance
monitor_performance() {
    local pid=$1
    local model=$2
    local format=$3
    local perf_log="$LOG_DIR/performance_${model}_${format}_$(date +%s).log"
    
    if [[ "$PERFORMANCE_MONITOR" == false ]]; then
        return
    fi
    
    print_status "Starting performance monitoring (PID: $pid)..."
    
    {
        echo "Timestamp,CPU%,Memory(MB),LoadAvg"
        while kill -0 $pid 2>/dev/null; do
            if [[ "$(uname)" == "Darwin" ]]; then
                # macOS
                cpu=$(ps -p $pid -o %cpu= 2>/dev/null || echo "0")
                mem=$(ps -p $pid -o rss= 2>/dev/null || echo "0")
                mem=$((mem / 1024))  # Convert KB to MB
                load=$(uptime | awk -F'load averages:' '{print $2}' | awk '{print $1}')
            else
                # Linux
                cpu=$(ps -p $pid -o %cpu= 2>/dev/null || echo "0")
                mem=$(ps -p $pid -o rss= 2>/dev/null || echo "0")
                mem=$((mem / 1024))  # Convert KB to MB
                load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}')
            fi
            echo "$(date +%s),$cpu,$mem,$load"
            sleep 2
        done
    } > "$perf_log" &
    
    echo $! > "$LOG_DIR/monitor_${pid}.pid"
}

# Function to stop performance monitoring
stop_monitoring() {
    local pid=$1
    local monitor_pid_file="$LOG_DIR/monitor_${pid}.pid"
    
    if [[ -f "$monitor_pid_file" ]]; then
        local monitor_pid=$(cat "$monitor_pid_file")
        if kill -0 $monitor_pid 2>/dev/null; then
            kill $monitor_pid 2>/dev/null || true
        fi
        rm -f "$monitor_pid_file"
    fi
}

# Function to validate JSON output
validate_json() {
    local json_file=$1
    
    if [[ "$HAS_JQ" != true ]]; then
        return 0
    fi
    
    if jq empty "$json_file" 2>/dev/null; then
        # Check for required fields
        local scan_id=$(jq -r '.scan_id // empty' "$json_file")
        local target=$(jq -r '.target // empty' "$json_file")
        local results=$(jq -r '.results // empty' "$json_file")
        
        if [[ -n "$scan_id" && -n "$target" && -n "$results" ]]; then
            print_success "JSON validation passed: $(basename "$json_file")"
            return 0
        else
            print_error "JSON missing required fields: $(basename "$json_file")"
            return 1
        fi
    else
        print_error "Invalid JSON format: $(basename "$json_file")"
        return 1
    fi
}

# Function to validate PDF output
validate_pdf() {
    local pdf_file=$1
    
    if [[ -f "$pdf_file" ]]; then
        local size=$(stat -f%z "$pdf_file" 2>/dev/null || stat -c%s "$pdf_file" 2>/dev/null)
        if [[ $size -gt 1000 ]]; then
            print_success "PDF validation passed: $(basename "$pdf_file") (${size} bytes)"
            return 0
        else
            print_error "PDF file too small: $(basename "$pdf_file") (${size} bytes)"
            return 1
        fi
    else
        print_error "PDF file not found: $(basename "$pdf_file")"
        return 1
    fi
}

# Function to validate HTML output
validate_html() {
    local html_file=$1
    
    if [[ -f "$html_file" ]]; then
        if grep -q "<html" "$html_file" && grep -q "RedForge" "$html_file"; then
            print_success "HTML validation passed: $(basename "$html_file")"
            return 0
        else
            print_error "HTML missing required content: $(basename "$html_file")"
            return 1
        fi
    else
        print_error "HTML file not found: $(basename "$html_file")"
        return 1
    fi
}

# Function to run a single test
run_single_test() {
    local model=$1
    local format=$2
    local test_id=$3
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local output_base="${OUTPUT_DIR}/reports/${model}_${format}_${test_id}_${timestamp}"
    local log_file="${LOG_DIR}/test_${model}_${format}_${test_id}.log"
    
    print_status "Testing model: $model, format: $format, test: $test_id"
    
    if [[ "$DRY_RUN" == true ]]; then
        echo "poetry run redforge scan $model --format $format --output ${output_base} --max-requests 5"
        return 0
    fi
    
    # Run the actual command
    local cmd="poetry run redforge scan $model --format $format --output ${output_base} --max-requests 5"
    
    if [[ "$VERBOSE" == true ]]; then
        cmd="$cmd --verbose"
    fi
    
    # Execute and capture output
    if $cmd > "$log_file" 2>&1; then
        print_success "Test completed: $model/$format/$test_id"
        
        # Validate output if enabled
        if [[ "$VALIDATE_OUTPUT" == true ]]; then
            case $format in
                json)
                    validate_json "${output_base}/redforge_scan_*.json" || true
                    ;;
                pdf)
                    validate_pdf "${output_base}/redforge_scan_*.pdf" || true
                    ;;
                html)
                    validate_html "${output_base}/redforge_scan_*.html" || true
                    ;;
            esac
        fi
        
        return 0
    else
        print_error "Test failed: $model/$format/$test_id (see $log_file)"
        if [[ "$VERBOSE" == true ]]; then
            tail -20 "$log_file"
        fi
        return 1
    fi
}

# Function to run concurrent tests
run_concurrent_tests() {
    local model=$1
    local format=$2
    local concurrency=$3
    
    print_status "Starting $concurrency concurrent tests for $model with $format output..."
    
    local pids=()
    local start_time=$(date +%s)
    
    # Start concurrent processes
    for ((i=1; i<=concurrency; i++)); do
        run_single_test "$model" "$format" "$i" &
        pids+=($!)
        
        # Small delay to avoid overwhelming the system
        if (( i % 10 == 0 )); then
            sleep 0.5
        fi
    done
    
    # Monitor the main process group
    if [[ "$PERFORMANCE_MONITOR" == true && ${#pids[@]} -gt 0 ]]; then
        monitor_performance $$ "$model" "$format"
    fi
    
    # Wait for all processes to complete
    local failed=0
    for pid in "${pids[@]}"; do
        if ! wait $pid; then
            ((failed++))
        fi
    done
    
    # Stop monitoring
    if [[ "$PERFORMANCE_MONITOR" == true ]]; then
        stop_monitoring $$
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_status "Completed $concurrency tests in ${duration}s ($failed failed)"
    
    return $failed
}

# Function to test error handling
test_error_handling() {
    print_status "Testing error handling..."
    
    local error_tests=(
        "invalid-model|Invalid model name"
        "gpt-4 --api-key ''|API key required"
        "gpt-4 --timeout 0|Invalid timeout"
        "gpt-4 --max-requests -1|Invalid max requests"
        "gpt-4 --format invalid|Invalid format"
    )
    
    for test in "${error_tests[@]}"; do
        IFS='|' read -r cmd expected_error <<< "$test"
        
        print_status "Testing: poetry run redforge scan $cmd"
        
        if [[ "$DRY_RUN" == true ]]; then
            echo "Would test: $cmd"
            continue
        fi
        
        if poetry run redforge scan $cmd 2>&1 | grep -q "$expected_error"; then
            print_success "Error handling correct: $expected_error"
        else
            print_error "Error handling failed for: $cmd"
        fi
    done
}

# Function to generate summary report
generate_summary() {
    local summary_file="${OUTPUT_DIR}/test_summary_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "RedForge CLI Matrix Test Summary"
        echo "==================================="
        echo "Date: $(date)"
        echo "Models tested: ${MODEL_ARRAY[*]}"
        echo "Formats tested: ${FORMAT_ARRAY[*]}"
        echo "Concurrency: $CONCURRENCY"
        echo ""
        echo "Test Results:"
        echo "-------------"
        
        # Count output files
        for model in "${MODEL_ARRAY[@]}"; do
            for format in "${FORMAT_ARRAY[@]}"; do
                local count=$(find "$OUTPUT_DIR/reports" -name "${model}_${format}_*.${format}" 2>/dev/null | wc -l)
                echo "$model/$format: $count files generated"
            done
        done
        
        echo ""
        echo "Log files:"
        echo "----------"
        ls -la "$LOG_DIR"/*.log 2>/dev/null || echo "No log files found"
        
        if [[ "$PERFORMANCE_MONITOR" == true ]]; then
            echo ""
            echo "Performance Metrics:"
            echo "-------------------"
            
            for perf_log in "$LOG_DIR"/performance_*.log; do
                if [[ -f "$perf_log" ]]; then
                    echo "$(basename "$perf_log"):"
                    # Calculate average CPU and memory
                    awk -F',' 'NR>1 {cpu+=$2; mem+=$3; count++} END {
                        if (count > 0) {
                            printf "  Avg CPU: %.2f%%\n  Avg Memory: %.2f MB\n", cpu/count, mem/count
                        }
                    }' "$perf_log"
                fi
            done
        fi
        
    } > "$summary_file"
    
    print_success "Summary report generated: $summary_file"
    
    # Display summary
    cat "$summary_file"
}

# Main execution
main() {
    print_status "RedForge CLI Matrix Test Starting..."
    print_status "Models: ${MODEL_ARRAY[*]}"
    print_status "Formats: ${FORMAT_ARRAY[*]}"
    print_status "Concurrency: $CONCURRENCY"
    print_status "Output directory: $OUTPUT_DIR"
    
    # Check prerequisites
    check_prerequisites
    
    # Run error handling tests first
    if [[ "$DRY_RUN" == false ]]; then
        test_error_handling
    fi
    
    # Run matrix tests
    local total_failed=0
    
    for model in "${MODEL_ARRAY[@]}"; do
        for format in "${FORMAT_ARRAY[@]}"; do
            if run_concurrent_tests "$model" "$format" "$CONCURRENCY"; then
                print_success "Completed: $model with $format"
            else
                print_error "Failed: $model with $format"
                ((total_failed++))
            fi
            
            # Add delay between test sets
            sleep 2
        done
    done
    
    # Generate summary report
    generate_summary
    
    # Final status
    if [[ $total_failed -eq 0 ]]; then
        print_success "All tests completed successfully!"
        exit 0
    else
        print_error "$total_failed test sets failed"
        exit 1
    fi
}

# Run main function
main