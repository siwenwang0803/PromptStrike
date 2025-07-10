#!/bin/bash

# 完整监控堆栈设置 - Prometheus + Grafana + 告警规则

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_msg() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_msg $BLUE "🔧 设置完整监控堆栈"
print_msg $BLUE "目标: Prometheus (≤15s scrape) + Grafana + 告警规则"

# 1. 创建监控命名空间
print_msg $BLUE "1. 创建监控命名空间..."
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# 2. 安装 metrics-server（如果尚未安装）
print_msg $BLUE "2. 确保 metrics-server 正确配置..."
if ! kubectl get deployment metrics-server -n kube-system &>/dev/null; then
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
fi

# 为 Kind 集群配置 metrics-server
kubectl patch deployment metrics-server -n kube-system --patch '
spec:
  template:
    spec:
      containers:
      - name: metrics-server
        args:
        - --cert-dir=/tmp
        - --secure-port=4443
        - --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
        - --kubelet-use-node-status-port
        - --metric-resolution=15s
        - --kubelet-insecure-tls
' || true

# 3. 创建 Prometheus 配置（15s scrape interval）
print_msg $BLUE "3. 创建 Prometheus 配置..."
cat > prometheus-config.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 10s  # 更频繁的全局抓取
      evaluation_interval: 10s
      external_labels:
        cluster: 'psguard-test'
        environment: 'testing'

    rule_files:
      - "/etc/prometheus/rules/*.yml"

    scrape_configs:
    # PSGuard Sidecar 监控（高频）
    - job_name: 'psguard-sidecar'
      scrape_interval: 10s  # 10秒抓取间隔
      scrape_timeout: 5s
      metrics_path: '/metrics'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - psguard-test
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: kubernetes_pod_name

    # Kubernetes 节点监控
    - job_name: 'kubernetes-nodes'
      scrape_interval: 15s
      kubernetes_sd_configs:
      - role: node
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - target_label: __address__
        replacement: kubernetes.default.svc:443
      - source_labels: [__meta_kubernetes_node_name]
        regex: (.+)
        target_label: __metrics_path__
        replacement: /api/v1/nodes/${1}/proxy/metrics

    # cAdvisor 容器监控（资源使用）
    - job_name: 'kubernetes-cadvisor'
      scrape_interval: 10s  # 容器资源监控高频抓取
      kubernetes_sd_configs:
      - role: node
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        insecure_skip_verify: true
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - target_label: __address__
        replacement: kubernetes.default.svc:443
      - source_labels: [__meta_kubernetes_node_name]
        regex: (.+)
        target_label: __metrics_path__
        replacement: /api/v1/nodes/${1}/proxy/metrics/cadvisor

    # Kubelet 监控
    - job_name: 'kubernetes-kubelet'
      scrape_interval: 15s
      kubernetes_sd_configs:
      - role: node
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        insecure_skip_verify: true
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - target_label: __address__
        replacement: kubernetes.default.svc:443
      - source_labels: [__meta_kubernetes_node_name]
        regex: (.+)
        target_label: __metrics_path__
        replacement: /api/v1/nodes/${1}/proxy/metrics

    alerting:
      alertmanagers:
      - static_configs:
        - targets:
          - alertmanager:9093
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-rules
  namespace: monitoring
data:
  psguard-alerts.yml: |
    groups:
    - name: psguard-sidecar
      rules:
      # CPU 使用率告警
      - alert: PSGuardHighCPU
        expr: |
          (
            rate(container_cpu_usage_seconds_total{namespace="psguard-test",container="psguard"}[1m]) * 1000
          ) > 200
        for: 1m
        labels:
          severity: critical
          component: psguard-sidecar
        annotations:
          summary: "PSGuard Sidecar CPU usage exceeds limit"
          description: "PSGuard sidecar CPU usage is {{ $value }}m, exceeding the 200m limit for more than 1 minute."

      # 内存使用率告警
      - alert: PSGuardHighMemory
        expr: |
          (
            container_memory_working_set_bytes{namespace="psguard-test",container="psguard"} / 1024 / 1024
          ) > 180
        for: 1m
        labels:
          severity: critical
          component: psguard-sidecar
        annotations:
          summary: "PSGuard Sidecar memory usage exceeds limit"
          description: "PSGuard sidecar memory usage is {{ $value }}Mi, exceeding the 180Mi limit for more than 1 minute."

      # Pod 重启告警
      - alert: PSGuardPodRestarting
        expr: |
          increase(kube_pod_container_status_restarts_total{namespace="psguard-test",container="psguard"}[5m]) > 0
        for: 0m
        labels:
          severity: warning
          component: psguard-sidecar
        annotations:
          summary: "PSGuard Sidecar pod is restarting"
          description: "PSGuard sidecar pod has restarted {{ $value }} times in the last 5 minutes."

      # 请求错误率告警
      - alert: PSGuardHighErrorRate
        expr: |
          (
            rate(http_requests_total{job="psguard-sidecar",status=~"5.."}[5m]) /
            rate(http_requests_total{job="psguard-sidecar"}[5m])
          ) * 100 > 5
        for: 2m
        labels:
          severity: warning
          component: psguard-sidecar
        annotations:
          summary: "PSGuard Sidecar high error rate"
          description: "PSGuard sidecar error rate is {{ $value }}% over the last 5 minutes."

      # 磁盘 I/O 告警
      - alert: PSGuardHighDiskIO
        expr: |
          (
            rate(container_fs_reads_bytes_total{namespace="psguard-test",container="psguard"}[1m]) +
            rate(container_fs_writes_bytes_total{namespace="psguard-test",container="psguard"}[1m])
          ) / 1024 / 1024 > 100  # 100MB/s
        for: 2m
        labels:
          severity: warning
          component: psguard-sidecar
        annotations:
          summary: "PSGuard Sidecar high disk I/O"
          description: "PSGuard sidecar disk I/O is {{ $value }}MB/s, which may indicate performance issues."

      # 网络带宽告警
      - alert: PSGuardHighNetworkTraffic
        expr: |
          (
            rate(container_network_receive_bytes_total{namespace="psguard-test"}[1m]) +
            rate(container_network_transmit_bytes_total{namespace="psguard-test"}[1m])
          ) / 1024 / 1024 > 50  # 50MB/s
        for: 2m
        labels:
          severity: warning
          component: psguard-sidecar
        annotations:
          summary: "PSGuard Sidecar high network traffic"
          description: "PSGuard sidecar network traffic is {{ $value }}MB/s, which may indicate high load."
EOF

# 4. 部署 Prometheus
print_msg $BLUE "4. 部署 Prometheus..."
cat > prometheus-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
  labels:
    app: prometheus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      serviceAccountName: prometheus
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        args:
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus/'
        - '--web.console.libraries=/etc/prometheus/console_libraries'
        - '--web.console.templates=/etc/prometheus/consoles'
        - '--storage.tsdb.retention.time=2h'  # 短期存储用于测试
        - '--web.enable-lifecycle'
        - '--web.enable-admin-api'
        ports:
        - containerPort: 9090
          name: http
        volumeMounts:
        - name: prometheus-config
          mountPath: /etc/prometheus/prometheus.yml
          subPath: prometheus.yml
        - name: prometheus-rules
          mountPath: /etc/prometheus/rules/psguard-alerts.yml
          subPath: psguard-alerts.yml
        - name: prometheus-storage
          mountPath: /prometheus/
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
          requests:
            cpu: 200m
            memory: 256Mi
      volumes:
      - name: prometheus-config
        configMap:
          name: prometheus-config
      - name: prometheus-rules
        configMap:
          name: prometheus-rules
      - name: prometheus-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: monitoring
  labels:
    app: prometheus
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090
    name: http
  type: ClusterIP
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
- apiGroups: [""]
  resources:
  - nodes
  - nodes/proxy
  - services
  - endpoints
  - pods
  verbs: ["get", "list", "watch"]
- apiGroups: ["extensions"]
  resources:
  - ingresses
  verbs: ["get", "list", "watch"]
- nonResourceURLs: ["/metrics"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
- kind: ServiceAccount
  name: prometheus
  namespace: monitoring
EOF

# 5. 部署 Grafana
print_msg $BLUE "5. 部署 Grafana..."
cat > grafana-deployment.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-config
  namespace: monitoring
data:
  grafana.ini: |
    [analytics]
    check_for_updates = true
    [grafana_net]
    url = https://grafana.net
    [log]
    mode = console
    [paths]
    data = /var/lib/grafana/data
    logs = /var/log/grafana
    plugins = /var/lib/grafana/plugins
    provisioning = /etc/grafana/provisioning
    [server]
    http_port = 3000
    [security]
    admin_user = admin
    admin_password = admin123
  datasources.yaml: |
    apiVersion: 1
    datasources:
    - name: Prometheus
      type: prometheus
      url: http://prometheus:9090
      access: proxy
      isDefault: true
  dashboards.yaml: |
    apiVersion: 1
    providers:
    - name: 'default'
      orgId: 1
      folder: ''
      type: file
      disableDeletion: false
      updateIntervalSeconds: 10
      allowUiUpdates: true
      options:
        path: /var/lib/grafana/dashboards
  psguard-dashboard.json: |
    {
      "dashboard": {
        "id": null,
        "title": "PSGuard Sidecar Monitoring",
        "tags": ["psguard", "sidecar", "monitoring"],
        "style": "dark",
        "timezone": "browser",
        "panels": [
          {
            "id": 1,
            "title": "CPU Usage (millicores)",
            "type": "stat",
            "targets": [
              {
                "expr": "rate(container_cpu_usage_seconds_total{namespace=\"psguard-test\",container=\"psguard\"}[1m]) * 1000",
                "legendFormat": "CPU Usage"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "thresholds": {
                  "steps": [
                    {"color": "green", "value": null},
                    {"color": "yellow", "value": 150},
                    {"color": "red", "value": 200}
                  ]
                },
                "unit": "short",
                "max": 250,
                "min": 0
              }
            },
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
          },
          {
            "id": 2,
            "title": "Memory Usage (Mi)",
            "type": "stat",
            "targets": [
              {
                "expr": "container_memory_working_set_bytes{namespace=\"psguard-test\",container=\"psguard\"} / 1024 / 1024",
                "legendFormat": "Memory Usage"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "thresholds": {
                  "steps": [
                    {"color": "green", "value": null},
                    {"color": "yellow", "value": 140},
                    {"color": "red", "value": 180}
                  ]
                },
                "unit": "short",
                "max": 200,
                "min": 0
              }
            },
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
          }
        ],
        "time": {"from": "now-5m", "to": "now"},
        "refresh": "5s"
      }
    }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
          name: http
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: admin123
        volumeMounts:
        - name: grafana-config
          mountPath: /etc/grafana/grafana.ini
          subPath: grafana.ini
        - name: grafana-datasources
          mountPath: /etc/grafana/provisioning/datasources/datasources.yaml
          subPath: datasources.yaml
        - name: grafana-dashboards-config
          mountPath: /etc/grafana/provisioning/dashboards/dashboards.yaml
          subPath: dashboards.yaml
        - name: grafana-dashboard
          mountPath: /var/lib/grafana/dashboards/psguard-dashboard.json
          subPath: psguard-dashboard.json
        resources:
          limits:
            cpu: 200m
            memory: 256Mi
          requests:
            cpu: 100m
            memory: 128Mi
      volumes:
      - name: grafana-config
        configMap:
          name: grafana-config
      - name: grafana-datasources
        configMap:
          name: grafana-config
      - name: grafana-dashboards-config
        configMap:
          name: grafana-config
      - name: grafana-dashboard
        configMap:
          name: grafana-config
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: monitoring
spec:
  selector:
    app: grafana
  ports:
  - port: 3000
    targetPort: 3000
    name: http
  type: ClusterIP
EOF

# 应用配置
kubectl apply -f prometheus-config.yaml
kubectl apply -f prometheus-deployment.yaml
kubectl apply -f grafana-deployment.yaml

# 6. 等待服务启动
print_msg $BLUE "6. 等待监控服务启动..."
kubectl wait --for=condition=Ready pod -l app=prometheus -n monitoring --timeout=300s
kubectl wait --for=condition=Ready pod -l app=grafana -n monitoring --timeout=300s

# 7. 验证服务状态
print_msg $BLUE "7. 验证服务状态..."
kubectl get pods -n monitoring
kubectl get svc -n monitoring

# 8. 设置端口转发用于访问
print_msg $BLUE "8. 设置端口转发..."
kubectl port-forward svc/prometheus 9090:9090 -n monitoring &
PROM_PID=$!
kubectl port-forward svc/grafana 3000:3000 -n monitoring &
GRAFANA_PID=$!

sleep 5

# 9. 验证访问
print_msg $BLUE "9. 验证监控服务访问..."
if curl -s http://localhost:9090/api/v1/status/config > /dev/null; then
    print_msg $GREEN "✅ Prometheus 可访问 (http://localhost:9090)"
else
    print_msg $RED "❌ Prometheus 不可访问"
fi

if curl -s http://localhost:3000/api/health > /dev/null; then
    print_msg $GREEN "✅ Grafana 可访问 (http://localhost:3000)"
    print_msg $YELLOW "   用户名: admin, 密码: admin123"
else
    print_msg $RED "❌ Grafana 不可访问"
fi

# 10. 清理
print_msg $BLUE "10. 清理临时文件..."
rm -f prometheus-config.yaml prometheus-deployment.yaml grafana-deployment.yaml

print_msg $GREEN "🎉 完整监控堆栈部署完成！"
print_msg $BLUE "监控配置："
print_msg $BLUE "  Prometheus: http://localhost:9090 (scrape interval: 10s)"
print_msg $BLUE "  Grafana: http://localhost:3000 (admin/admin123)"
print_msg $BLUE "  告警规则: CPU > 200m, Memory > 180Mi (持续1分钟)"

print_msg $BLUE "包含的告警规则："
print_msg $BLUE "  - PSGuardHighCPU: CPU > 200m 持续 1 分钟"
print_msg $BLUE "  - PSGuardHighMemory: Memory > 180Mi 持续 1 分钟"
print_msg $BLUE "  - PSGuardPodRestarting: Pod 重启检测"
print_msg $BLUE "  - PSGuardHighErrorRate: 错误率 > 5%"
print_msg $BLUE "  - PSGuardHighDiskIO: 磁盘 I/O > 100MB/s"
print_msg $BLUE "  - PSGuardHighNetworkTraffic: 网络流量 > 50MB/s"

print_msg $BLUE "下一步："
print_msg $BLUE "1. 访问 Grafana 查看实时监控"
print_msg $BLUE "2. 运行完整的 500 RPS 测试"
print_msg $BLUE "3. 观察告警触发情况"

# 保持端口转发运行
print_msg $YELLOW "端口转发将保持运行，按 Ctrl+C 停止"
wait