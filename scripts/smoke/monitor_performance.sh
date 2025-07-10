#!/bin/bash
# Performance monitoring script for PromptStrike CLI tests
# Monitors CPU, memory, disk I/O, and network usage during test execution

set -euo pipefail

# Default values
INTERVAL=2
OUTPUT_FILE="performance_metrics.csv"
PROCESS_NAME="promptstrike"
MONITOR_PID=""
MONITOR_DOCKER=false

# Function to show usage
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -i INTERVAL     Sampling interval in seconds (default: 2)"
    echo "  -o FILE         Output CSV file (default: performance_metrics.csv)"
    echo "  -p PROCESS      Process name to monitor (default: promptstrike)"
    echo "  -P PID          Specific PID to monitor"
    echo "  -d              Monitor Docker containers"
    echo "  -h              Show this help"
    exit 0
}

# Parse command line arguments
while getopts "i:o:p:P:dh" opt; do
    case $opt in
        i) INTERVAL="$OPTARG";;
        o) OUTPUT_FILE="$OPTARG";;
        p) PROCESS_NAME="$OPTARG";;
        P) MONITOR_PID="$OPTARG";;
        d) MONITOR_DOCKER=true;;
        h) usage;;
        *) usage;;
    esac
done

# Detect OS
OS=$(uname -s)

# Function to get system metrics on macOS
get_macos_metrics() {
    local timestamp=$(date +%s)
    
    # CPU usage (system-wide)
    local cpu=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    
    # Memory usage
    local mem_info=$(vm_stat | perl -ne '/page size of (\d+)/ and $size=$1; /Pages\s+([^:]+)[^\d]+(\d+)/ and printf("%-16s % 16.2f Mi\n", "$1:", $2 * $size / 1048576);')
    local mem_used=$(echo "$mem_info" | grep "active:" | awk '{print $2}')
    local mem_wired=$(echo "$mem_info" | grep "wired down:" | awk '{print $3}')
    local mem_compressed=$(echo "$mem_info" | grep "compressed:" | awk '{print $2}')
    local total_mem=$((${mem_used%.*} + ${mem_wired%.*} + ${mem_compressed%.*}))
    
    # Load average
    local load=$(uptime | awk -F'load averages:' '{print $2}' | awk '{print $1}')
    
    # Disk I/O (requires iostat)
    local disk_read="0"
    local disk_write="0"
    if command -v iostat &> /dev/null; then
        local io_stats=$(iostat -d -c 1 -n 1 | tail -1)
        disk_read=$(echo "$io_stats" | awk '{print $3}')
        disk_write=$(echo "$io_stats" | awk '{print $4}')
    fi
    
    # Network (bytes)
    local net_in=$(netstat -ib | grep -E '^en[0-9]' | awk '{sum+=$7} END {print sum}')
    local net_out=$(netstat -ib | grep -E '^en[0-9]' | awk '{sum+=$10} END {print sum}')
    
    echo "$timestamp,$cpu,$total_mem,$load,$disk_read,$disk_write,$net_in,$net_out"
}

# Function to get system metrics on Linux
get_linux_metrics() {
    local timestamp=$(date +%s)
    
    # CPU usage
    local cpu=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    
    # Memory usage (MB)
    local mem_info=$(free -m | grep "^Mem:")
    local mem_used=$(echo "$mem_info" | awk '{print $3}')
    
    # Load average
    local load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}')
    
    # Disk I/O
    local disk_read="0"
    local disk_write="0"
    if command -v iostat &> /dev/null; then
        local io_stats=$(iostat -d 1 2 | tail -n +4 | head -1)
        disk_read=$(echo "$io_stats" | awk '{print $3}')
        disk_write=$(echo "$io_stats" | awk '{print $4}')
    fi
    
    # Network (bytes)
    local net_stats=$(cat /proc/net/dev | grep -E 'eth0|ens|enp' | head -1)
    local net_in=$(echo "$net_stats" | awk '{print $2}')
    local net_out=$(echo "$net_stats" | awk '{print $10}')
    
    echo "$timestamp,$cpu,$mem_used,$load,$disk_read,$disk_write,$net_in,$net_out"
}

# Function to get process-specific metrics
get_process_metrics() {
    local pid=$1
    
    if [[ "$OS" == "Darwin" ]]; then
        # macOS
        if ps -p $pid > /dev/null 2>&1; then
            local cpu=$(ps -p $pid -o %cpu= 2>/dev/null || echo "0")
            local mem=$(ps -p $pid -o rss= 2>/dev/null || echo "0")
            local mem_mb=$((mem / 1024))
            echo "$cpu,$mem_mb"
        else
            echo "0,0"
        fi
    else
        # Linux
        if [[ -f /proc/$pid/stat ]]; then
            local stat=$(cat /proc/$pid/stat 2>/dev/null)
            local cpu=$(ps -p $pid -o %cpu= 2>/dev/null || echo "0")
            local mem=$(ps -p $pid -o rss= 2>/dev/null || echo "0")
            local mem_mb=$((mem / 1024))
            echo "$cpu,$mem_mb"
        else
            echo "0,0"
        fi
    fi
}

# Function to get Docker container metrics
get_docker_metrics() {
    if command -v docker &> /dev/null && docker ps &> /dev/null; then
        local containers=$(docker ps --filter "name=promptstrike" --format "{{.Names}}")
        local total_cpu=0
        local total_mem=0
        
        for container in $containers; do
            local stats=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" "$container" 2>/dev/null || echo "0%,0MiB")
            local cpu=$(echo "$stats" | cut -d',' -f1 | sed 's/%//')
            local mem=$(echo "$stats" | cut -d',' -f2 | awk '{print $1}' | sed 's/MiB//')
            
            total_cpu=$(echo "$total_cpu + $cpu" | bc)
            total_mem=$(echo "$total_mem + $mem" | bc)
        done
        
        echo "$total_cpu,$total_mem"
    else
        echo "0,0"
    fi
}

# Initialize output file with headers
echo "Timestamp,CPU%,Memory_MB,Load_Avg,Disk_Read_KB/s,Disk_Write_KB/s,Net_In_Bytes,Net_Out_Bytes,Process_CPU%,Process_Mem_MB,Docker_CPU%,Docker_Mem_MB" > "$OUTPUT_FILE"

echo "Starting performance monitoring..."
echo "Interval: ${INTERVAL}s"
echo "Output: $OUTPUT_FILE"
echo "Press Ctrl+C to stop"

# Store initial network values for rate calculation
if [[ "$OS" == "Darwin" ]]; then
    prev_net_in=$(netstat -ib | grep -E '^en[0-9]' | awk '{sum+=$7} END {print sum}')
    prev_net_out=$(netstat -ib | grep -E '^en[0-9]' | awk '{sum+=$10} END {print sum}')
else
    net_stats=$(cat /proc/net/dev | grep -E 'eth0|ens|enp' | head -1)
    prev_net_in=$(echo "$net_stats" | awk '{print $2}')
    prev_net_out=$(echo "$net_stats" | awk '{print $10}')
fi

# Main monitoring loop
while true; do
    # Get system metrics
    if [[ "$OS" == "Darwin" ]]; then
        sys_metrics=$(get_macos_metrics)
    else
        sys_metrics=$(get_linux_metrics)
    fi
    
    # Get process metrics if specified
    proc_metrics="0,0"
    if [[ -n "$MONITOR_PID" ]]; then
        proc_metrics=$(get_process_metrics "$MONITOR_PID")
    elif [[ -n "$PROCESS_NAME" ]]; then
        # Find PIDs by process name
        if [[ "$OS" == "Darwin" ]]; then
            pids=$(pgrep -f "$PROCESS_NAME" 2>/dev/null || true)
        else
            pids=$(pgrep -f "$PROCESS_NAME" 2>/dev/null || true)
        fi
        
        if [[ -n "$pids" ]]; then
            total_cpu=0
            total_mem=0
            
            for pid in $pids; do
                metrics=$(get_process_metrics "$pid")
                cpu=$(echo "$metrics" | cut -d',' -f1)
                mem=$(echo "$metrics" | cut -d',' -f2)
                total_cpu=$(echo "$total_cpu + $cpu" | bc)
                total_mem=$(echo "$total_mem + $mem" | bc)
            done
            
            proc_metrics="$total_cpu,$total_mem"
        fi
    fi
    
    # Get Docker metrics if enabled
    docker_metrics="0,0"
    if [[ "$MONITOR_DOCKER" == true ]]; then
        docker_metrics=$(get_docker_metrics)
    fi
    
    # Write to CSV
    echo "${sys_metrics},${proc_metrics},${docker_metrics}" >> "$OUTPUT_FILE"
    
    # Sleep for interval
    sleep "$INTERVAL"
done