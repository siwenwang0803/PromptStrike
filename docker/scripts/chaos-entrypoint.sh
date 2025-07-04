#!/bin/bash

# Chaos Testing Entrypoint Script
# Handles initialization, monitoring, and cleanup for chaos tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

# Check if running in privileged mode (should not be for safety)
check_security() {
    log "Checking security configuration..."
    
    if [ "$(id -u)" = "0" ]; then
        error "Running as root user - security risk!"
        exit 1
    fi
    
    # Check if we're in a container
    if [ ! -f /.dockerenv ]; then
        warn "Not running in Docker container - chaos tests may affect host system"
    fi
    
    success "Security checks passed"
}

# Initialize chaos testing environment
init_chaos_env() {
    log "Initializing chaos testing environment..."
    
    # Create required directories
    mkdir -p /app/results /app/logs /app/artifacts /app/tmp
    
    # Set up configuration
    if [ ! -f "/app/chaos-config.yaml" ]; then
        log "No config file found, using default configuration"
        cat > /app/chaos-config.yaml << EOF
version: "1.0"
mutation:
  enabled: true
  intensity: 0.3
chaos_replay:
  enabled: true
  duration: 60
span_mutation:
  enabled: true
  malformation_rate: 0.5
gork_generation:
  enabled: true
  corruption_rate: 0.7
reporting:
  enabled: true
  output_path: "/app/results"
EOF
    fi
    
    # Validate configuration
    python -c "
from tests.chaos.config import validate_chaos_config
issues = validate_chaos_config('/app/chaos-config.yaml')
if issues:
    print('Configuration issues found:')
    for issue in issues:
        print(f'  - {issue}')
    exit(1)
else:
    print('Configuration validated successfully')
"
    
    success "Environment initialized"
}

# Monitor resource usage during tests
monitor_resources() {
    local duration=$1
    local log_file="/app/logs/resource_monitor.log"
    
    log "Starting resource monitoring for ${duration}s..."
    
    {
        echo "timestamp,memory_usage_mb,cpu_percent,disk_usage_mb"
        
        for ((i=0; i<duration; i+=5)); do
            timestamp=$(date +'%Y-%m-%d %H:%M:%S')
            
            # Memory usage (in MB)
            memory_kb=$(awk '/MemTotal:/ {total=$2} /MemAvailable:/ {available=$2} END {print total-available}' /proc/meminfo 2>/dev/null || echo "0")
            memory_mb=$((memory_kb / 1024))
            
            # CPU usage (approximation)
            cpu_percent=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 2>/dev/null || echo "0")
            
            # Disk usage of /app (in MB)
            disk_usage_kb=$(du -sk /app 2>/dev/null | cut -f1 || echo "0")
            disk_usage_mb=$((disk_usage_kb / 1024))
            
            echo "${timestamp},${memory_mb},${cpu_percent},${disk_usage_mb}"
            
            sleep 5
        done
    } > "$log_file" &
    
    echo $! > /app/tmp/monitor_pid
}

# Stop resource monitoring
stop_monitoring() {
    if [ -f "/app/tmp/monitor_pid" ]; then
        local pid=$(cat /app/tmp/monitor_pid)
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            log "Resource monitoring stopped"
        fi
        rm -f /app/tmp/monitor_pid
    fi
}

# Cleanup function
cleanup() {
    log "Starting cleanup..."
    
    # Stop monitoring
    stop_monitoring
    
    # Archive logs
    if [ -d "/app/logs" ] && [ "$(ls -A /app/logs)" ]; then
        timestamp=$(date +'%Y%m%d_%H%M%S')
        tar -czf "/app/artifacts/chaos_logs_${timestamp}.tar.gz" -C /app logs/
        log "Logs archived to artifacts/"
    fi
    
    # Generate summary report
    python -c "
import json
import os
from datetime import datetime

summary = {
    'execution_timestamp': datetime.now().isoformat(),
    'environment': os.getenv('CHAOS_ENVIRONMENT', 'docker'),
    'config_file': '/app/chaos-config.yaml',
    'results_path': '/app/results',
    'artifacts_path': '/app/artifacts'
}

with open('/app/artifacts/execution_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)
"
    
    success "Cleanup completed"
}

# Trap signals for graceful shutdown
trap cleanup EXIT INT TERM

# Validate arguments
validate_args() {
    if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        cat << EOF
Chaos Testing Docker Container

Usage:
  docker run promptstrike-chaos [COMMAND] [OPTIONS]

Commands:
  pytest [args]              Run pytest with chaos tests
  report                     Generate resilience report only
  validate                   Validate configuration only
  monitor [duration]         Run resource monitoring only
  shell                      Start interactive shell

Environment Variables:
  CHAOS_ENVIRONMENT         Testing environment (docker, ci, staging)
  CHAOS_INTENSITY           Chaos intensity (0.0-1.0, default: 0.3)
  CHAOS_DURATION            Test duration in seconds (default: 120)
  CHAOS_MEMORY_LIMIT        Memory limit (default: 2Gi)
  CHAOS_CPU_LIMIT           CPU limit (default: 1000m)
  CHAOS_CONFIG_PATH         Path to config file (default: /app/chaos-config.yaml)

Examples:
  # Run all chaos tests
  docker run promptstrike-chaos

  # Run specific test category
  docker run promptstrike-chaos pytest tests/chaos/ -k "mutation"

  # Generate report only
  docker run promptstrike-chaos report

  # Run with custom configuration
  docker run -e CHAOS_INTENSITY=0.5 promptstrike-chaos

  # Run with mounted config
  docker run -v \$(pwd)/my-config.yaml:/app/chaos-config.yaml promptstrike-chaos
EOF
        exit 0
    fi
}

# Main execution logic
main() {
    local command=${1:-"pytest"}
    shift || true
    
    log "Starting chaos testing container..."
    log "Command: $command"
    log "Arguments: $*"
    
    # Validate arguments
    validate_args "$command"
    
    # Security checks
    check_security
    
    # Initialize environment
    init_chaos_env
    
    case "$command" in
        "pytest")
            log "Running chaos tests with pytest..."
            
            # Start resource monitoring
            test_duration=${CHAOS_DURATION:-120}
            monitor_resources $((test_duration + 60))  # Extra time for setup/teardown
            
            # Run tests
            python -m pytest "$@" || {
                error "Tests failed with exit code $?"
                exit 1
            }
            
            success "Chaos tests completed successfully"
            ;;
            
        "report")
            log "Generating resilience report..."
            
            python -m tests.chaos.resilience_scorer \
                --results-path /app/results \
                --output-path /app/artifacts/resilience_report.json \
                --format json
            
            success "Report generated"
            ;;
            
        "validate")
            log "Validating configuration..."
            
            python -c "
from tests.chaos.config import validate_chaos_config
issues = validate_chaos_config('${CHAOS_CONFIG_PATH:-/app/chaos-config.yaml}')
if issues:
    print('❌ Configuration validation failed:')
    for issue in issues:
        print(f'  - {issue}')
    exit(1)
else:
    print('✅ Configuration is valid')
"
            ;;
            
        "monitor")
            duration=${1:-60}
            log "Running resource monitoring for ${duration}s..."
            monitor_resources "$duration"
            wait
            ;;
            
        "shell")
            log "Starting interactive shell..."
            exec /bin/bash
            ;;
            
        *)
            log "Executing custom command: $command $*"
            exec "$command" "$@"
            ;;
    esac
}

# Run main function with all arguments
main "$@"