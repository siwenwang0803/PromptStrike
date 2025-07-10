#!/bin/bash

# 基于 Prometheus 的资源监控脚本
OUTPUT_FILE="prometheus_resource_monitoring.csv"
MONITOR_DURATION=300  # 5分钟
PROMETHEUS_URL="http://localhost:9090"

echo "timestamp,cpu_millicores,memory_bytes,memory_mi,disk_read_bps,disk_write_bps,network_rx_bps,network_tx_bps,pod_restarts,alert_status" > $OUTPUT_FILE

echo "开始 Prometheus 资源监控 (${MONITOR_DURATION}秒)..."

for i in $(seq 1 $MONITOR_DURATION); do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # CPU 使用率 (millicores)
    cpu_query='rate(container_cpu_usage_seconds_total{namespace="psguard-test",container="psguard"}[1m]) * 1000'
    cpu_millicores=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=${cpu_query}" | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null)
    
    # 内存使用 (bytes 和 Mi)
    mem_query='container_memory_working_set_bytes{namespace="psguard-test",container="psguard"}'
    memory_bytes=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=${mem_query}" | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null)
    memory_mi=$(echo "scale=2; $memory_bytes / 1024 / 1024" | bc 2>/dev/null || echo "0")
    
    # 磁盘 I/O (bytes/sec)
    disk_read_query='rate(container_fs_reads_bytes_total{namespace="psguard-test",container="psguard"}[1m])'
    disk_write_query='rate(container_fs_writes_bytes_total{namespace="psguard-test",container="psguard"}[1m])'
    disk_read_bps=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=${disk_read_query}" | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null)
    disk_write_bps=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=${disk_write_query}" | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null)
    
    # 网络流量 (bytes/sec)
    net_rx_query='rate(container_network_receive_bytes_total{namespace="psguard-test"}[1m])'
    net_tx_query='rate(container_network_transmit_bytes_total{namespace="psguard-test"}[1m])'
    network_rx_bps=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=${net_rx_query}" | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null)
    network_tx_bps=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=${net_tx_query}" | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null)
    
    # Pod 重启次数
    restart_query='kube_pod_container_status_restarts_total{namespace="psguard-test",container="psguard"}'
    pod_restarts=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=${restart_query}" | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null)
    
    # 检查告警状态
    alerts=$(curl -s "${PROMETHEUS_URL}/api/v1/alerts" | jq -r '.data.alerts[] | select(.labels.component=="psguard-sidecar") | .state' 2>/dev/null | tr '\n' ',' | sed 's/,$//')
    alert_status=${alerts:-"none"}
    
    # 记录数据
    echo "$timestamp,$cpu_millicores,$memory_bytes,$memory_mi,$disk_read_bps,$disk_write_bps,$network_rx_bps,$network_tx_bps,$pod_restarts,$alert_status" >> $OUTPUT_FILE
    
    # 实时告警检查
    if (( $(echo "$cpu_millicores > 200" | bc -l 2>/dev/null || echo 0) )); then
        echo -e "\033[0;31m⚠️ CPU 超限: ${cpu_millicores}m > 200m\033[0m"
    fi
    
    if (( $(echo "$memory_mi > 180" | bc -l 2>/dev/null || echo 0) )); then
        echo -e "\033[0;31m⚠️ 内存超限: ${memory_mi}Mi > 180Mi\033[0m"
    fi
    
    # 每30秒报告进度
    if [ $((i % 30)) -eq 0 ]; then
        echo "监控中... $i/$MONITOR_DURATION 秒 - CPU: ${cpu_millicores}m, 内存: ${memory_mi}Mi"
    fi
    
    sleep 1
done

echo "Prometheus 监控完成！数据保存在 $OUTPUT_FILE"
