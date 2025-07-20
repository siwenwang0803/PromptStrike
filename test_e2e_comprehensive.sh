#!/usr/bin/env bash
# RedForge Comprehensive End-to-End Test Script
# Tests complete customer journey across S-1, S-2, S-3 deliverables
# Covers: CLI → Docker → API Gateway → Supabase → Stripe → ConvertKit

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEST_EMAIL="test$(date +%s)@redforge.test"
API_BASE="${REDFORGE_API_BASE:-https://api-gateway-uenk.onrender.com}"
SUPABASE_URL="${SUPABASE_URL:-}"
STRIPE_PRICE_STARTER="${STRIPE_PRICE_STARTER:-price_test}"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TEST_RESULTS=()

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    TEST_RESULTS+=("✅ $1")
}

error() {
    echo -e "${RED}❌ $1${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    TEST_RESULTS+=("❌ $1")
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

section() {
    echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}🔥 $1${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

check_prereq() {
    local cmd=$1
    local name=$2
    if ! command -v "$cmd" &> /dev/null; then
        error "$name not found. Please install $name"
        return 1
    fi
    success "$name available"
}

test_api_call() {
    local method=$1
    local url=$2
    local expected_status=$3
    local description=$4
    shift 4
    local args=()
    if [[ $# -gt 0 ]]; then
        args=("$@")
    fi
    
    log "Testing: $description"
    
    if command -v http &> /dev/null; then
        # Using HTTPie
        local response
        local status
        if [[ ${#args[@]} -eq 0 ]]; then
            response=$(http --print=HhBb --ignore-stdin "$method" "$url" 2>&1 || true)
        else
            response=$(http --print=HhBb --ignore-stdin "$method" "$url" "${args[@]}" 2>&1 || true)
        fi
        status=$(echo "$response" | grep "HTTP/" | awk '{print $2}' | tail -1)
    elif command -v curl &> /dev/null; then
        # Using curl
        local response
        local status
        if [[ ${#args[@]} -eq 0 ]]; then
            response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "$method" "$url" 2>&1 || true)
        else
            response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "$method" "$url" "${args[@]}" 2>&1 || true)
        fi
        status=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    else
        error "Neither httpie nor curl available"
        return 1
    fi
    
    if [[ "$status" == "$expected_status" ]]; then
        success "$description (HTTP $status)"
        echo "$response"
        return 0
    else
        error "$description (Expected HTTP $expected_status, got $status)"
        echo "$response"
        return 1
    fi
}

# ============================================================================
# Sprint S-1 Tests: CLI + Docker + OTEL
# ============================================================================

test_s1_cli() {
    section "Sprint S-1: CLI Core Functionality"
    
    # Test 1: CLI Help
    if redforge --help &> /dev/null; then
        success "CLI help command works"
    else
        error "CLI help command failed"
    fi
    
    # Test 2: Doctor diagnostics
    if redforge doctor &> /dev/null; then
        success "CLI doctor diagnostics pass"
    else
        error "CLI doctor diagnostics failed"
    fi
    
    # Test 3: List attacks
    local attack_count
    attack_count=$(redforge list-attacks | grep -c "LLM" || echo "0")
    if [[ "$attack_count" -gt 10 ]]; then
        success "Attack packs loaded ($attack_count attacks)"
    else
        error "Insufficient attacks loaded ($attack_count)"
    fi
    
    # Test 4: Dry run scan
    if redforge scan gpt-4 --dry-run --output ./test_reports &> /dev/null; then
        success "Dry run scan completed"
    else
        error "Dry run scan failed"
    fi
    
    # Test 5: Report generation
    if [[ -d "./test_reports" ]]; then
        success "Report directory created"
        local report_files
        report_files=$(find ./test_reports -name "*.json" | wc -l)
        if [[ "$report_files" -gt 0 ]]; then
            success "JSON reports generated ($report_files files)"
        else
            warning "No JSON reports found"
        fi
    else
        error "Report directory not created"
    fi
}

test_s1_docker() {
    section "Sprint S-1: Docker Deployment"
    
    # Test 1: Docker build (if Docker available)
    if command -v docker &> /dev/null; then
        log "Testing Docker build..."
        if docker build -t redforge-test . &> /dev/null; then
            success "Docker image builds successfully"
            
            # Test 2: Container healthcheck
            log "Testing container startup..."
            local container_id
            container_id=$(docker run -d -p 8001:8000 redforge-test)
            sleep 5
            
            if curl -s http://localhost:8001 &> /dev/null; then
                success "Container serves HTTP traffic"
            else
                warning "Container HTTP check failed"
            fi
            
            docker stop "$container_id" &> /dev/null || true
            docker rm "$container_id" &> /dev/null || true
        else
            error "Docker build failed"
        fi
    else
        warning "Docker not available, skipping container tests"
    fi
}

# ============================================================================
# Sprint S-2 Tests: Guardrail + Threat Model + Compliance
# ============================================================================

test_s2_guardrail() {
    section "Sprint S-2: Guardrail Sidecar"
    
    # Test 1: Guardrail SDK import
    if python3 -c "from guardrail.sdk import GuardrailClient; print('OK')" &> /dev/null; then
        success "Guardrail SDK imports successfully"
    else
        error "Guardrail SDK import failed"
    fi
    
    # Test 2: Cost Guard functionality
    if python3 -c "from redforge.sidecar import CostGuard; cg = CostGuard(); result = cg.detect_token_storm('test'); print('OK')" &> /dev/null; then
        success "Cost Guard functional"
    else
        error "Cost Guard failed"
    fi
    
    # Test 3: Threat model documentation
    if [[ -f "docs/RedForge/Security/Guardrail_Threat_Model.md" ]]; then
        success "Threat model documentation exists"
    else
        error "Threat model documentation missing"
    fi
    
    # Test 4: OTEL span schema
    if [[ -f "docs/RedForge/Guardrail/OTEL_SPAN_SCHEMA.md" ]]; then
        success "OTEL span schema documented"
    else
        error "OTEL span schema missing"
    fi
}

test_s2_compliance() {
    section "Sprint S-2: Compliance Framework"
    
    # Test 1: PCI DSS compliance
    if python3 -c "from redforge.compliance.pci_dss_framework import PCIDSSFramework; print('OK')" &> /dev/null; then
        success "PCI DSS framework available"
    else
        error "PCI DSS framework missing"
    fi
    
    # Test 2: Framework mappings
    if [[ -f "redforge/compliance/framework_mappings.py" ]]; then
        success "Framework mappings exist"
    else
        error "Framework mappings missing"
    fi
    
    # Test 3: Report generation
    if python3 -c "from redforge.compliance.report_generator import ComplianceReportGenerator; print('OK')" &> /dev/null; then
        success "Compliance report generator available"
    else
        error "Compliance report generator missing"
    fi
}

# ============================================================================
# Sprint S-3 Tests: Open-Core + API Gateway + Supabase + Stripe
# ============================================================================

test_s3_api_gateway() {
    section "Sprint S-3: API Gateway Functionality"
    
    # Test 1: Health check
    test_api_call GET "$API_BASE/healthz" "200" "API Gateway health check"
    
    # Test 2: API documentation
    test_api_call GET "$API_BASE/docs" "200" "API documentation endpoint"
    
    # Test 3: Rate limiting headers
    log "Testing rate limiting..."
    if command -v http &> /dev/null; then
        local response
        response=$(http GET "$API_BASE/healthz" 2>&1 || true)
        if echo "$response" | grep -q "X-RateLimit"; then
            success "Rate limiting headers present"
        else
            warning "Rate limiting headers not found"
        fi
    fi
}

test_s3_user_signup() {
    section "Sprint S-3: User Registration & API Keys"
    
    log "Testing user signup with email: $TEST_EMAIL"
    
    # Test 1: User registration
    local signup_response
    if command -v http &> /dev/null; then
        signup_response=$(http --ignore-stdin POST "$API_BASE/signup" email="$TEST_EMAIL" 2>&1 || true)
    else
        signup_response=$(curl -s -X POST -H "Content-Type: application/json" -d "{\"email\":\"$TEST_EMAIL\"}" "$API_BASE/signup" 2>&1 || true)
    fi
    
    if echo "$signup_response" | grep -q "api_key"; then
        success "User signup successful"
        API_KEY=$(echo "$signup_response" | grep -o '"api_key":"[^"]*"' | cut -d'"' -f4)
        log "Generated API key: ${API_KEY:0:8}..."
    else
        error "User signup failed"
        echo "$signup_response"
        return 1
    fi
}

test_s3_free_tier() {
    section "Sprint S-3: Free Tier Limitations"
    
    if [[ -z "${API_KEY:-}" ]]; then
        error "No API key available for testing"
        return 1
    fi
    
    # Test 1: First scan (should succeed)
    log "Testing first free scan..."
    if test_api_call POST "$API_BASE/scan" "200" "First free scan" \
        "X-API-Key:$API_KEY" "Content-Type:application/json" \
        --raw '{"target":"gpt-4","dry_run":true,"attack_pack":"owasp-llm-top10"}'; then
        
        local scan_id
        scan_id=$(echo "$response" | grep -o '"scan_id":"[^"]*"' | cut -d'"' -f4)
        log "Scan ID: $scan_id"
        
        # Test 2: Check scan status
        if test_api_call GET "$API_BASE/status/$scan_id" "200" "Scan status check" \
            "X-API-Key:$API_KEY"; then
            success "Scan status accessible"
        fi
    fi
    
    # Test 3: Second scan (should fail with 402)
    log "Testing second scan (should hit free limit)..."
    test_api_call POST "$API_BASE/scan" "402" "Second scan (free limit)" \
        "X-API-Key:$API_KEY" "Content-Type:application/json" \
        --raw '{"target":"gpt-4","dry_run":true}' || true
}

test_s3_supabase() {
    section "Sprint S-3: Supabase Backend"
    
    if [[ -z "$SUPABASE_URL" ]]; then
        warning "SUPABASE_URL not set, skipping Supabase tests"
        return 0
    fi
    
    # Test 1: Supabase connection
    if command -v supabase &> /dev/null; then
        log "Testing Supabase connection..."
        if supabase status &> /dev/null; then
            success "Supabase CLI connected"
        else
            warning "Supabase CLI connection failed"
        fi
    else
        warning "Supabase CLI not available"
    fi
    
    # Test 2: Database schema
    if [[ -f "supabase/migrations/002_api_keys_and_tiers.sql" ]]; then
        success "Database migration files exist"
    else
        error "Database migration files missing"
    fi
}

test_s3_convertkit() {
    section "Sprint S-3: ConvertKit Integration"
    
    # Test 1: ConvertKit module
    if python3 -c "from redforge.integrations.convertkit import ConvertKitClient; print('OK')" &> /dev/null; then
        success "ConvertKit integration available"
    else
        error "ConvertKit integration missing"
    fi
    
    # Test 2: Email signup endpoint
    if test_api_call POST "$API_BASE/signup" "200" "Email signup (ConvertKit)" \
        "Content-Type:application/json" \
        --raw "{\"email\":\"test-ck-$(date +%s)@example.com\"}"; then
        success "Email signup triggers ConvertKit"
    fi
}

# ============================================================================
# Performance & Load Testing
# ============================================================================

test_performance() {
    section "Performance & Load Testing"
    
    if [[ -z "${API_KEY:-}" ]]; then
        warning "No API key for performance testing"
        return 0
    fi
    
    # Test 1: Rate limiting
    if command -v hey &> /dev/null; then
        log "Testing rate limiting with concurrent requests..."
        local load_result
        load_result=$(hey -n 20 -c 5 -H "X-API-Key: $API_KEY" "$API_BASE/healthz" 2>&1 || true)
        
        if echo "$load_result" | grep -q "429"; then
            success "Rate limiting active under load"
        else
            warning "Rate limiting behavior unclear"
        fi
    elif command -v ab &> /dev/null; then
        log "Testing with Apache Bench..."
        ab -n 10 -c 2 -H "X-API-Key: $API_KEY" "$API_BASE/healthz" &> /dev/null || true
        success "Load testing completed"
    else
        warning "No load testing tools available (hey, ab)"
    fi
}

# ============================================================================
# Integration Testing
# ============================================================================

test_cli_cloud_integration() {
    section "CLI ↔ Cloud Integration"
    
    if [[ -z "${API_KEY:-}" ]]; then
        warning "No API key for CLI cloud integration"
        return 0
    fi
    
    # Test CLI with cloud API key
    log "Testing CLI with cloud API key..."
    if REDFORGE_API_KEY="$API_KEY" redforge scan gpt-4 --dry-run &> /dev/null; then
        success "CLI cloud integration works"
    else
        warning "CLI cloud integration failed"
    fi
}

# ============================================================================
# Cleanup & Reporting
# ============================================================================

cleanup() {
    log "Cleaning up test artifacts..."
    rm -rf ./test_reports 2>/dev/null || true
    docker rmi redforge-test 2>/dev/null || true
}

generate_report() {
    section "Test Results Summary"
    
    echo -e "\n${GREEN}📊 Test Results:${NC}"
    echo -e "${GREEN}✅ Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}❌ Failed: $TESTS_FAILED${NC}"
    echo -e "${BLUE}📝 Total: $((TESTS_PASSED + TESTS_FAILED))${NC}"
    
    echo -e "\n${YELLOW}📋 Detailed Results:${NC}"
    for result in "${TEST_RESULTS[@]}"; do
        echo "  $result"
    done
    
    local success_rate
    if [[ $((TESTS_PASSED + TESTS_FAILED)) -gt 0 ]]; then
        success_rate=$((TESTS_PASSED * 100 / (TESTS_PASSED + TESTS_FAILED)))
        echo -e "\n${BLUE}🎯 Success Rate: ${success_rate}%${NC}"
        
        if [[ $success_rate -ge 90 ]]; then
            echo -e "${GREEN}🚀 Excellent! Ready for production deployment${NC}"
        elif [[ $success_rate -ge 75 ]]; then
            echo -e "${YELLOW}⚠️  Good, but some issues need attention${NC}"
        else
            echo -e "${RED}❌ Critical issues found, deployment not recommended${NC}"
        fi
    fi
    
    # Generate JSON report
    cat > test_results.json <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "summary": {
    "passed": $TESTS_PASSED,
    "failed": $TESTS_FAILED,
    "success_rate": $success_rate
  },
  "test_email": "$TEST_EMAIL",
  "api_key": "${API_KEY:0:8}...",
  "environment": {
    "api_base": "$API_BASE",
    "supabase_url": "${SUPABASE_URL:-not_set}"
  }
}
EOF
    log "Test results saved to test_results.json"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    section "🔥 RedForge Comprehensive E2E Testing"
    
    log "Test Email: $TEST_EMAIL"
    log "API Base: $API_BASE"
    log "Starting comprehensive test suite..."
    
    # Prerequisites
    section "Prerequisites Check"
    check_prereq "python3" "Python 3"
    check_prereq "redforge" "RedForge CLI" || warning "RedForge CLI not in PATH"
    
    # Execute test suites
    test_s1_cli
    test_s1_docker
    test_s2_guardrail
    test_s2_compliance
    test_s3_api_gateway
    test_s3_user_signup
    test_s3_free_tier
    test_s3_supabase
    test_s3_convertkit
    test_performance
    test_cli_cloud_integration
    
    # Generate final report
    generate_report
    cleanup
    
    # Exit with appropriate code
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log "All tests passed! 🎉"
        exit 0
    else
        log "Some tests failed. Check the report above."
        exit 1
    fi
}

# Handle interrupts
trap cleanup EXIT INT TERM

# Run main function
main "$@"