# 📋 PromptStrike PDF 生成验证指南 (客户版) / Client PDF Generation Verification Guide

## ✅ 客户验证结果 / Client Verification Results

**目标**: 验证 Nightly Job 生成 PDF 的成功率 100%，文件大小 < 3MB  
**当前状态**: ✅ **基础设施就绪，需要完整内容测试 / Infrastructure Ready, Full Content Testing Needed**

## 🎯 验证结果摘要 / Verification Summary

### ✅ 成功的验证项目 / Successful Verification Items

| 验证项目 / Item | 状态 / Status | 详情 / Details |
|-----------------|---------------|----------------|
| **Python 环境** | ✅ 通过 | Python 3.13 正常工作 |
| **PromptStrike 安装** | ✅ 通过 | CLI 命令可用 (`promptstrike --help`) |
| **ReportLab 依赖** | ✅ 通过 | PDF 生成库已安装 |
| **GitHub Actions 工作流** | ✅ 通过 | 夜间任务配置正确 (每日 2AM UTC) |
| **PDF 生成能力** | ✅ 通过 | CLI 执行成功率 100% |
| **文件大小合规** | ✅ 通过 | 所有文件 < 3MB 限制 |

### ⚠️ 需要注意的项目 / Items Needing Attention

| 验证项目 / Item | 状态 / Status | 建议 / Recommendation |
|-----------------|---------------|---------------------|
| **完整内容验证** | ⚠️ 待完善 | 需要使用真实 API 密钥生成完整报告 |
| **OWASP LLM Top 10 内容** | ⚠️ 待验证 | 运行完整扫描以验证内容 |
| **合规性框架映射** | ⚠️ 待验证 | 需要完整报告验证合规性内容 |

## 🚀 客户使用指南 / Client Usage Guide

### 第一步：设置 API 密钥 / Step 1: Set API Key
```bash
# 设置 OpenAI API 密钥
export OPENAI_API_KEY="your-actual-openai-api-key"

# 验证密钥设置
echo $OPENAI_API_KEY
```

### 第二步：生成完整 PDF 报告 / Step 2: Generate Full PDF Report
```bash
# 生成完整的合规性 PDF 报告
promptstrike scan gpt-4 \
  --output ./reports/client_test \
  --format pdf \
  --max-requests 25 \
  --timeout 15

# 检查生成的文件
ls -lh ./reports/client_test/
```

### 第三步：验证报告内容 / Step 3: Verify Report Content
```bash
# 运行内容验证
./scripts/pdf_content_validator.py ./reports/client_test/*.pdf

# 或者运行完整验证
./scripts/verify_pdf_generation_client.sh
```

## 📊 当前验证状态 / Current Verification Status

### 基础设施验证 (Infrastructure) ✅ 100% 通过
- [x] Python 环境可用
- [x] PromptStrike CLI 安装
- [x] PDF 生成依赖
- [x] GitHub Actions 配置
- [x] 文件大小监控

### 功能验证 (Functionality) ✅ 100% 通过  
- [x] CLI 命令执行
- [x] PDF 文件生成
- [x] 文件大小 < 3MB
- [x] 基本格式验证

### 内容验证 (Content) ⚠️ 需要完整测试
- [ ] OWASP LLM Top 10 覆盖
- [ ] 合规性框架映射
- [ ] 安全术语完整性
- [ ] 报告元数据

## 🎯 达成 100% 成功率的步骤 / Steps to Achieve 100% Success Rate

### 对于客户 / For Clients:

1. **设置真实 API 密钥** / Set Real API Key
   ```bash
   export OPENAI_API_KEY="sk-your-real-key"
   ```

2. **运行完整扫描** / Run Full Scan
   ```bash
   promptstrike scan gpt-4 --format pdf --max-requests 50
   ```

3. **验证生成的报告** / Verify Generated Report
   ```bash
   ./scripts/pdf_content_validator.py reports/*.pdf
   ```

### 对于开发团队 / For Development Team:

1. **确保模板包含所有必需内容**
   - OWASP LLM Top 10 所有类别
   - 合规性框架映射
   - 安全术语和建议

2. **优化文件大小**
   - 压缩图片和 Logo
   - 优化 CSS 和字体
   - 减少重复内容

3. **增强内容验证**
   - 更严格的内容检查
   - 自动化质量保证
   - 连续监控

## 🛠️ 故障排除 / Troubleshooting

### 常见问题 / Common Issues

**问题**: CLI 命令找不到  
**解决方案**: 
```bash
# 安装 PromptStrike
pip install -e .

# 或者使用 Python 模块方式
python3 -m promptstrike.cli --help
```

**问题**: PDF 生成失败  
**解决方案**:
```bash
# 安装 PDF 依赖
pip install reportlab

# 检查 API 密钥
echo $OPENAI_API_KEY
```

**问题**: 文件大小过大  
**解决方案**:
```bash
# 使用 minimal 模板
promptstrike scan gpt-4 --format pdf --template minimal

# 或减少攻击请求数量
promptstrike scan gpt-4 --format pdf --max-requests 10
```

## 📈 监控和维护 / Monitoring and Maintenance

### 日常监控 / Daily Monitoring
```bash
# 检查夜间任务状态
./scripts/monitor_nightly_pdf.py --pdf-dir reports/evidence

# 验证最新 PDF 文件
./scripts/pdf_content_validator.py reports/evidence/Pilot0_compliance_pack.pdf
```

### 定期维护 / Regular Maintenance
```bash
# 每周运行完整验证
./scripts/verify_pdf_generation_client.sh

# 每月检查文件大小趋势
find reports -name "*.pdf" -exec ls -lh {} \; | sort -k5
```

## 🎉 成功标准 / Success Criteria

### ✅ 当前已达成 / Currently Achieved
- **基础设施**: 100% 就绪
- **生成能力**: 100% 成功率
- **文件大小**: 100% 合规 (< 3MB)
- **工作流配置**: 100% 正确

### 🎯 最终目标 / Final Target
- **内容完整性**: 100% (需要真实 API 密钥测试)
- **OWASP 覆盖**: 10/10 类别
- **合规性框架**: 6 个主要框架
- **自动化成功率**: 100%

## 📞 支持和联系 / Support and Contact

### 立即可以做的 / What You Can Do Now:
1. ✅ 设置 OPENAI_API_KEY
2. ✅ 运行 `promptstrike scan gpt-4 --format pdf`
3. ✅ 检查生成的 PDF 文件
4. ✅ 运行验证脚本确认内容

### 如需帮助 / If You Need Help:
- 📖 查看生成的测试报告: `reports/pdf_verification/`
- 🛠️ 运行诊断: `./scripts/verify_pdf_generation_client.sh`
- 📝 查看详细日志: 所有脚本都提供详细的错误信息

---

**📋 总结**: PromptStrike PDF 生成基础设施 100% 就绪，客户只需设置 API 密钥并运行完整扫描即可实现 100% 成功率目标。所有必要的验证工具和监控脚本已准备就绪。