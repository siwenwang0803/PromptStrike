# 📊 Render 监控配置指南

## 🚨 Health Check 告警设置

### 1. 在 Render Dashboard 中设置告警

1. **进入服务**: 打开 `redforge-api-gateway` 服务
2. **Settings → Alerts**
3. **Add Alert**:
   - **Alert Type**: `Health Check Failed`
   - **Conditions**: `2 consecutive failures`
   - **Notification**: 添加邮箱和 Slack (如果有)

### 2. 配置示例

```
Alert Name: API Gateway Health Check
Type: Health Check Failed
Threshold: 2 consecutive failures
Recipients: your-email@example.com
```

## 🔍 日志搜索 (Request ID)

### 现在每个请求都有唯一 ID:

```bash
# 用户看到 500 错误时的响应头
X-Request-ID: a1b2c3d4

# 在 Render Logs 中搜索
[a1b2c3d4] POST /scan - 192.168.1.100
[a1b2c3d4] API key verification error: Name or service not known
[a1b2c3d4] Response: 503
```

### 日志格式:
- **请求**: `[req_id] METHOD path - client_ip`
- **响应**: `[req_id] Response: status_code`
- **错误**: `[req_id] Error description`

## 📈 免费 Uptime Robot 监控

### 1. 注册 Uptime Robot

1. 访问: https://uptimerobot.com/
2. 注册免费账户 (最多 50 个监控)

### 2. 添加监控

```
Monitor Type: HTTP(s)
URL: https://api-gateway-uenk.onrender.com/healthz
Friendly Name: RedForge API Gateway
Monitoring Interval: 5 minutes (免费版)
```

### 3. 告警设置

```
Alert Contacts: 
- Email: your-email@example.com
- Slack/Discord: (可选)

Alert When:
- Monitor goes DOWN
- Monitor goes UP (恢复)
```

## 📱 推荐告警渠道

### 1. 邮件告警 (必须)
- 立即通知服务异常
- 包含完整错误信息

### 2. Slack 告警 (推荐)
- 团队实时通知
- 便于协作处理

### 3. 手机 APP (可选)
- Uptime Robot 有手机 APP
- 支持推送通知

## 🎯 监控指标

### Health Check 响应示例:
```json
{
  "service": "RedForge API Gateway",
  "version": "0.2.0",
  "status": "ok",
  "timestamp": "2025-01-18T18:30:00Z",
  "database": "connected",
  "request_id": "a1b2c3d4",
  "supabase_url": "https://memfjxlbjjjtdsgipdlz.supabase.co..."
}
```

### 监控要点:
- ✅ `status: "ok"` - 服务正常
- ✅ `database: "connected"` - 数据库连接正常
- ⚠️ `status: "degraded"` - 数据库连接问题
- ❌ 任何 5xx 错误 - 服务异常

## 🔧 故障排查流程

### 1. 收到告警时:
1. 检查 Render 服务状态
2. 查看 Render Logs
3. 搜索具体的 Request ID

### 2. 常见问题:
- **503 错误**: 数据库连接问题，通常自动恢复
- **500 错误**: 服务内部错误，需要查看日志
- **Health Check 失败**: 服务可能重启中

### 3. 快速测试:
```bash
# 测试健康检查
curl -I https://api-gateway-uenk.onrender.com/healthz

# 检查响应头中的 Request ID
curl -v https://api-gateway-uenk.onrender.com/healthz
```

## 🎉 配置完成后的好处

1. **实时监控**: 5分钟内发现问题
2. **快速定位**: Request ID 帮助快速找到错误
3. **自动告警**: 无需手动检查服务状态
4. **历史数据**: Uptime Robot 提供可用性统计

---

**配置时间**: 约 10 分钟  
**成本**: 免费  
**收益**: 大幅提升服务可靠性监控  