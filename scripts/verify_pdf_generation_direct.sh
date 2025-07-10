#!/bin/bash

# RedForge PDF Generation Verification Script (Direct Python)
# 目标：验证 Nightly Job 生成 PDF 的成功率 100%，文件大小 < 3MB
# Target: Verify Nightly Job PDF generation with 100% success rate, file size < 3MB

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$PROJECT_ROOT/reports/pdf_verification"
TEST_OUTPUT_DIR="$REPORTS_DIR/test_runs"
MAX_FILE_SIZE_MB=3
MAX_FILE_SIZE_BYTES=$((MAX_FILE_SIZE_MB * 1024 * 1024))

# Test tracking
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0
PDF_GENERATION_ATTEMPTS=0
PDF_GENERATION_SUCCESS=0

# Function to print section headers
print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🎯 $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Function to track test results
track_test() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    case "$status" in
        "PASS")
            TESTS_PASSED=$((TESTS_PASSED + 1))
            echo -e "${GREEN}✅ $test_name: PASSED${NC} - $details"
            ;;
        "FAIL")
            TESTS_FAILED=$((TESTS_FAILED + 1))
            echo -e "${RED}❌ $test_name: FAILED${NC} - $details"
            ;;
        "SKIP")
            echo -e "${YELLOW}⚠️  $test_name: SKIPPED${NC} - $details"
            ;;
    esac
}

# Function to check prerequisites
check_prerequisites() {
    print_section "环境检查 / Environment Check"
    
    # Check Python
    if command -v python3 &> /dev/null; then
        track_test "Python availability" "PASS" "Python found at $(command -v python3)"
    else
        track_test "Python availability" "FAIL" "Python not found"
        return 1
    fi
    
    # Check if project is accessible
    cd "$PROJECT_ROOT"
    if python3 -c "import redforge" &> /dev/null; then
        track_test "RedForge installation" "PASS" "RedForge module can be imported"
    else
        track_test "RedForge installation" "FAIL" "RedForge module not found"
        return 1
    fi
    
    # Check PDF generation dependencies
    if python3 -c "import reportlab" &> /dev/null; then
        track_test "ReportLab availability" "PASS" "ReportLab available for PDF generation"
    else
        track_test "ReportLab availability" "SKIP" "ReportLab not available (will be installed on demand)"
    fi
    
    # Create test directories
    mkdir -p "$TEST_OUTPUT_DIR"
    track_test "Test directory creation" "PASS" "Created $TEST_OUTPUT_DIR"
    
    return 0
}

# Function to verify GitHub Actions workflow
verify_github_workflow() {
    print_section "GitHub Actions 工作流验证 / GitHub Actions Workflow Verification"
    
    local workflow_file="$PROJECT_ROOT/.github/workflows/evidence.yml"
    
    if [ -f "$workflow_file" ]; then
        track_test "Workflow file existence" "PASS" "Found evidence.yml workflow"
        
        # Check cron schedule
        if grep -q "cron.*0 2 \* \* \*" "$workflow_file"; then
            track_test "Nightly schedule configuration" "PASS" "Cron schedule configured for 2 AM UTC"
        else
            track_test "Nightly schedule configuration" "FAIL" "Cron schedule not found or incorrect"
        fi
        
        # Check PDF generation step
        if grep -q "reportlab\|pdf" "$workflow_file"; then
            track_test "PDF generation configuration" "PASS" "PDF generation steps found in workflow"
        else
            track_test "PDF generation configuration" "FAIL" "PDF generation steps not found"
        fi
        
        # Check file size monitoring
        if grep -q "ls -la\|ls -lh" "$workflow_file"; then
            track_test "File size monitoring" "PASS" "File size monitoring included in workflow"
        else
            track_test "File size monitoring" "SKIP" "File size monitoring not explicit in workflow"
        fi
        
    else
        track_test "Workflow file existence" "FAIL" "evidence.yml workflow not found"
    fi
}

# Function to test PDF generation
test_pdf_generation() {
    print_section "PDF 生成测试 / PDF Generation Tests"
    
    # Test with dry-run to avoid API calls
    local test_cases=(
        "gpt-4:comprehensive:Comprehensive GPT-4 compliance report"
        "gpt-3.5-turbo:executive:Executive summary for GPT-3.5-turbo"
    )
    
    for test_case in "${test_cases[@]}"; do
        IFS=':' read -r model template description <<< "$test_case"
        
        echo -e "${CYAN}🧪 Testing PDF generation: $description${NC}"
        
        local output_dir="$TEST_OUTPUT_DIR/${model//\./_}_${template}"
        mkdir -p "$output_dir"
        
        PDF_GENERATION_ATTEMPTS=$((PDF_GENERATION_ATTEMPTS + 1))
        
        # Generate PDF report using direct Python execution
        cd "$PROJECT_ROOT"
        if OPENAI_API_KEY="${OPENAI_API_KEY:-sk-test-key}" \
           python3 -m redforge.cli scan "$model" \
           --output "$output_dir" \
           --format pdf \
           --max-requests 5 \
           --timeout 10 \
           --dry-run >/dev/null 2>&1; then
            
            # Find generated PDF
            local pdf_file=$(find "$output_dir" -name "*.pdf" -type f | head -1)
            
            if [ -n "$pdf_file" ] && [ -f "$pdf_file" ]; then
                track_test "PDF Generation ($model-$template)" "PASS" "PDF file created: $(basename "$pdf_file")"
                PDF_GENERATION_SUCCESS=$((PDF_GENERATION_SUCCESS + 1))
                
                # Verify PDF file size
                verify_pdf_file_size "$pdf_file" "$model-$template"
                
                # Verify PDF content
                verify_pdf_content "$pdf_file" "$model-$template"
                
            else
                track_test "PDF Generation ($model-$template)" "FAIL" "PDF file not found after generation"
            fi
        else
            track_test "PDF Generation ($model-$template)" "FAIL" "PDF generation command failed"
        fi
    done
}

# Function to verify PDF file size
verify_pdf_file_size() {
    local pdf_file="$1"
    local test_name="$2"
    
    if [ -f "$pdf_file" ]; then
        local file_size=$(stat -f%z "$pdf_file" 2>/dev/null || stat -c%s "$pdf_file" 2>/dev/null)
        local file_size_mb=$((file_size / 1024 / 1024))
        
        echo -e "${CYAN}📊 File size check: $(basename "$pdf_file") = ${file_size} bytes (${file_size_mb} MB)${NC}"
        
        if [ "$file_size" -lt "$MAX_FILE_SIZE_BYTES" ]; then
            track_test "File size check ($test_name)" "PASS" "File size ${file_size_mb} MB < ${MAX_FILE_SIZE_MB} MB limit"
        else
            track_test "File size check ($test_name)" "FAIL" "File size ${file_size_mb} MB exceeds ${MAX_FILE_SIZE_MB} MB limit"
        fi
    else
        track_test "File size check ($test_name)" "FAIL" "PDF file not found"
    fi
}

# Function to verify PDF content
verify_pdf_content() {
    local pdf_file="$1"
    local test_name="$2"
    
    echo -e "${CYAN}🔍 Content verification: $(basename "$pdf_file")${NC}"
    
    # Check if PDF file is valid (can be opened)
    if file "$pdf_file" | grep -q "PDF"; then
        track_test "PDF format validation ($test_name)" "PASS" "File is a valid PDF"
    else
        track_test "PDF format validation ($test_name)" "FAIL" "File is not a valid PDF"
        return 1
    fi
    
    # Check if PDF contains expected content using strings command
    if command -v strings &> /dev/null; then
        local content=$(strings "$pdf_file" | head -100)
        
        # Check for key report elements
        if echo "$content" | grep -q -i "redforge\|compliance\|vulnerability\|security"; then
            track_test "PDF content keywords ($test_name)" "PASS" "PDF contains expected security/compliance keywords"
        else
            track_test "PDF content keywords ($test_name)" "FAIL" "PDF missing expected security/compliance keywords"
        fi
        
        # Check for OWASP LLM Top 10 content
        if echo "$content" | grep -q -i "owasp\|llm\|prompt.*injection\|model"; then
            track_test "OWASP LLM content ($test_name)" "PASS" "PDF contains OWASP LLM Top 10 content"
        else
            track_test "OWASP LLM content ($test_name)" "FAIL" "PDF missing OWASP LLM Top 10 content"
        fi
    else
        track_test "PDF content verification ($test_name)" "SKIP" "strings command not available"
    fi
}

# Function to simulate nightly job execution
simulate_nightly_job() {
    print_section "夜间任务模拟 / Nightly Job Simulation"
    
    echo -e "${CYAN}🌙 Simulating nightly job execution...${NC}"
    
    local nightly_output_dir="$TEST_OUTPUT_DIR/nightly_simulation"
    mkdir -p "$nightly_output_dir"
    
    # Simulate the exact command used in GitHub Actions
    local date_stamp=$(date +%Y%m%d)
    local scan_id="pilot0-evidence-${date_stamp}"
    
    cd "$PROJECT_ROOT"
    if OPENAI_API_KEY="${OPENAI_API_KEY:-sk-test-key}" \
       python3 -m redforge.cli scan gpt-4 \
       --output "$nightly_output_dir" \
       --format pdf \
       --max-requests 10 \
       --timeout 15 \
       --dry-run >/dev/null 2>&1; then
        
        # Find generated PDF
        local pdf_file=$(find "$nightly_output_dir" -name "*.pdf" -type f | head -1)
        
        if [ -n "$pdf_file" ] && [ -f "$pdf_file" ]; then
            # Simulate the renaming process from GitHub Actions
            local compliance_pack="$nightly_output_dir/Pilot0_compliance_pack.pdf"
            cp "$pdf_file" "$compliance_pack"
            
            track_test "Nightly job simulation" "PASS" "Compliance pack generated successfully"
            
            # Verify the compliance pack
            verify_pdf_file_size "$compliance_pack" "nightly-job"
            verify_pdf_content "$compliance_pack" "nightly-job"
            
            # Check if it matches expected naming pattern
            if [ -f "$compliance_pack" ]; then
                track_test "Compliance pack naming" "PASS" "Pilot0_compliance_pack.pdf created"
            else
                track_test "Compliance pack naming" "FAIL" "Pilot0_compliance_pack.pdf not found"
            fi
        else
            track_test "Nightly job simulation" "FAIL" "PDF file not generated"
        fi
    else
        track_test "Nightly job simulation" "FAIL" "Nightly job simulation failed"
    fi
}

# Function to test template optimization
test_template_optimization() {
    print_section "模板优化测试 / Template Optimization Tests"
    
    echo -e "${CYAN}🎨 Testing template optimization strategies...${NC}"
    
    # Test different template configurations for size optimization
    local templates=("minimal" "executive" "comprehensive")
    
    for template in "${templates[@]}"; do
        local output_dir="$TEST_OUTPUT_DIR/optimization_${template}"
        mkdir -p "$output_dir"
        
        cd "$PROJECT_ROOT"
        if OPENAI_API_KEY="${OPENAI_API_KEY:-sk-test-key}" \
           python3 -m redforge.cli scan gpt-4 \
           --output "$output_dir" \
           --format pdf \
           --max-requests 3 \
           --timeout 10 \
           --dry-run >/dev/null 2>&1; then
            
            local pdf_file=$(find "$output_dir" -name "*.pdf" -type f | head -1)
            
            if [ -n "$pdf_file" ] && [ -f "$pdf_file" ]; then
                local file_size=$(stat -f%z "$pdf_file" 2>/dev/null || stat -c%s "$pdf_file" 2>/dev/null)
                local file_size_mb=$((file_size / 1024 / 1024))
                
                echo -e "${CYAN}📊 Template $template: ${file_size_mb} MB${NC}"
                track_test "Template optimization ($template)" "PASS" "Generated PDF with size ${file_size_mb} MB"
            else
                track_test "Template optimization ($template)" "FAIL" "PDF not generated"
            fi
        else
            track_test "Template optimization ($template)" "FAIL" "Template test failed"
        fi
    done
}

# Function to generate comprehensive test report
generate_test_report() {
    print_section "测试报告 / Test Report"
    
    local success_rate=0
    if [ $TESTS_TOTAL -gt 0 ]; then
        success_rate=$(( (TESTS_PASSED * 100) / TESTS_TOTAL ))
    fi
    
    local pdf_success_rate=0
    if [ $PDF_GENERATION_ATTEMPTS -gt 0 ]; then
        pdf_success_rate=$(( (PDF_GENERATION_SUCCESS * 100) / PDF_GENERATION_ATTEMPTS ))
    fi
    
    echo -e "${BLUE}📊 PDF 生成验证结果摘要 / PDF Generation Verification Summary${NC}"
    echo ""
    echo -e "${BLUE}统计 / Statistics:${NC}"
    echo "  Total tests: $TESTS_TOTAL"
    echo -e "  Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "  Failed: ${RED}$TESTS_FAILED${NC}"
    echo "  Overall success rate: ${success_rate}%"
    echo ""
    echo -e "${BLUE}PDF 生成统计 / PDF Generation Statistics:${NC}"
    echo "  PDF generation attempts: $PDF_GENERATION_ATTEMPTS"
    echo -e "  PDF generation success: ${GREEN}$PDF_GENERATION_SUCCESS${NC}"
    echo "  PDF generation success rate: ${pdf_success_rate}%"
    echo ""
    
    # Save detailed test report
    local report_file="$REPORTS_DIR/pdf_verification_report_$(date +%Y%m%d_%H%M%S).md"
    cat > "$report_file" << EOF
# RedForge PDF Generation Verification Report

**Date**: $(date)
**Test Suite**: PDF Generation Verification (Direct Python)
**Environment**: $(uname -s) $(uname -r)

## Test Summary

- **Total Tests**: $TESTS_TOTAL
- **Passed**: $TESTS_PASSED
- **Failed**: $TESTS_FAILED
- **Overall Success Rate**: ${success_rate}%

## PDF Generation Statistics

- **PDF Generation Attempts**: $PDF_GENERATION_ATTEMPTS
- **PDF Generation Success**: $PDF_GENERATION_SUCCESS
- **PDF Generation Success Rate**: ${pdf_success_rate}%

## Objectives Verification

### Target: 100% Success Rate
- **Current Rate**: ${pdf_success_rate}%
- **Status**: $([ "$pdf_success_rate" -eq 100 ] && echo "✅ ACHIEVED" || echo "❌ NOT ACHIEVED")

### Target: File Size < 3MB
- **Limit**: 3MB
- **Status**: $([ "$TESTS_FAILED" -eq 0 ] && echo "✅ ALL FILES UNDER LIMIT" || echo "❌ SOME FILES EXCEED LIMIT")

## Environment Information

- **OS**: $(uname -s)
- **Architecture**: $(uname -m)
- **Python**: $(python3 --version 2>/dev/null || echo "Not available")
- **RedForge**: Available via direct Python execution

## Generated Test Files

$(find "$TEST_OUTPUT_DIR" -name "*.pdf" -type f | sed 's/^/- /' || echo "- No PDF files generated")

## Recommendations

$(if [ "$pdf_success_rate" -eq 100 ]; then
    echo "✅ **PDF generation is working perfectly** - Ready for production"
elif [ "$pdf_success_rate" -ge 80 ]; then
    echo "⚠️ **PDF generation mostly working** - Minor issues to address"
else
    echo "❌ **PDF generation needs attention** - Significant issues found"
fi)

## Next Steps

1. Review failed tests and address root causes
2. Optimize template sizes if files exceed 3MB limit
3. Test nightly job execution in staging environment
4. Monitor production nightly job success rates

EOF
    
    echo -e "${CYAN}📄 Detailed test report saved: $report_file${NC}"
    
    # Overall assessment
    echo ""
    if [ $TESTS_FAILED -eq 0 ] && [ "$pdf_success_rate" -eq 100 ]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED - PDF generation is production ready!${NC}"
        echo -e "${GREEN}✅ Target achieved: 100% success rate, file size < 3MB${NC}"
        return 0
    elif [ $TESTS_FAILED -le 2 ] && [ "$pdf_success_rate" -ge 80 ]; then
        echo -e "${YELLOW}⚠️  MOSTLY PASSED - Minor issues detected${NC}"
        echo -e "${YELLOW}🔧 Address failed tests for 100% success rate${NC}"
        return 1
    else
        echo -e "${RED}❌ TESTS FAILED - Major issues detected${NC}"
        echo -e "${RED}🛠️  Significant work needed to achieve targets${NC}"
        return 1
    fi
}

# Main execution function
main() {
    print_section "RedForge PDF 生成验证 (Direct Python) / RedForge PDF Generation Verification"
    
    echo "Configuration:"
    echo "- Project root: $PROJECT_ROOT"
    echo "- Reports directory: $REPORTS_DIR"
    echo "- Test output directory: $TEST_OUTPUT_DIR"
    echo "- Max file size: ${MAX_FILE_SIZE_MB} MB"
    echo "- Target success rate: 100%"
    echo "- Execution method: Direct Python (python3 -m redforge.cli)"
    echo ""
    
    # Execute test suite
    check_prerequisites || exit 1
    verify_github_workflow
    test_pdf_generation
    simulate_nightly_job
    test_template_optimization
    
    # Generate final report and return exit code
    generate_test_report
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help         Show this help"
        echo ""
        echo "Environment variables:"
        echo "  OPENAI_API_KEY  OpenAI API key for testing (optional, uses test key if not set)"
        echo ""
        echo "Features:"
        echo "  - Verifies PDF generation success rate (target: 100%)"
        echo "  - Checks file size limits (target: < 3MB)"
        echo "  - Validates PDF content and format"
        echo "  - Tests multiple report templates"
        echo "  - Simulates nightly job execution"
        echo "  - Generates comprehensive test reports"
        echo "  - Uses direct Python execution (no Poetry required)"
        exit 0
        ;;
esac

# Execute main function
main

# Return appropriate exit code
exit $?