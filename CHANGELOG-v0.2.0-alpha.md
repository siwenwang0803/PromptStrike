# Changelog - v0.2.0-alpha

## Sprint S-2 / Pilot-0 Completion (2025-07-10)

### 🎯 Major Features Added in This Release

- **Guardrail Side-car α**: Kubernetes deployment with published Helm charts for real-time monitoring and one-command install.
- **Enhanced Chaos Testing**: Resilience scoring framework, 30+ tests with mutation types (data corruption, protocol violation, etc.).
- **Community Feedback System**: Multi-source collection (GitHub, telemetry, surveys), automated analysis, insights generation, and roadmap creation.
- **PCI DSS Compliance Integration**: Framework with merchant level assessment (Level 1-4, service provider), detailed reports.
- **Pydantic v2 Migration**: Backward-compatible upgrade for better validation and type safety.
- **Other Improvements**: DOD (Definition of Done) verification for enterprise readiness, lightweight mode enhancements.

### 🔧 Updates to Core Components

- **CLI Enhancements**: Added community subcommands (collect, analyze, priorities, roadmap, update, stats) for feedback management.
- **Deployment**: Helm repo now live for production K8s setups; multi-stage Docker builds optimized further.
- **Testing**: Chaos engineering expanded with resilience scorer and new mutation types.

### 🚀 Installation & Usage Updates

- New Helm Install:
  ```bash
  helm repo add promptstrike https://siwenwang0803.github.io/PromptStrike
  helm install guardrail promptstrike/promptstrike-sidecar --namespace ps --set openai.apiKey=$OPENAI_API_KEY
Community Tools:
bash

Collapse

Wrap

Run

Copy
promptstrike community collect --days 30
promptstrike community roadmap --quarters 4
📊 Sprint S-2 Metrics
Helm Charts: One-command deployment verified in design partner envs.
Chaos Tests: 30+ scenarios, 81% resilience score achieved.
Community System: Automated feedback lifecycle, multi-source integration.
Compliance: Added PCI DSS, total 4 frameworks (NIST, EU, SOC2, PCI).
Target Achieved: Enterprise-ready with DOD compliance; ready for pilots.
🎯 Next: Sprint S-3
Upcoming (aiming for v0.3.0-beta):

Pilot templates and Stripe checkout for paid onboarding ($15k revenue target).
Usage analytics, multi-tenant support.
Continuous scan enhancements.
For prior changes, see CHANGELOG-v0.1.0-alpha.md.

Upgrade Guide
From v0.1.0-alpha: No breaking changes—pip install --upgrade promptstrike or pull new Docker/Helm.
New Config Options: Add chaos_testing and community sections to promptstrike.yaml (see docs).
Future Warnings: v0.3.0 may introduce payment-related fields. File issues for migration help.
Build: Sprint S-2 / Pilot-0

Reference: cid-roadmap-v2

Target: Live in 1 design-partner env, enterprise readiness

Date: July 10, 2025

Status: ✅ Production Ready

text

Collapse

Wrap

Copy
#### 2. 更新主 CHANGELOG-α.md
从“IN PROGRESS”改为“COMPLETED”，并更新 unreleased 为 S-3。

（由于原文件很长，我只输出变更部分；替换相应 section。）

在 "## [Unreleased]" 下：
🚧 Sprint S-3 (Aug 05-18) - PLANNED
 Exit Criteria: ≥3 paid pilots signed
 Deliverable: Pilot template, Stripe checkout, $15k revenue
 Owner: o3 + Perplexity
 Status: Requirements gathering
text

Collapse

Wrap

Copy
在 "## Sprint Delivery Tracking" 下，将 S-2 更新为：
✅ Sprint S-2 (Jul 22-Aug 04) - COMPLETED

 Exit Criteria: Live in 1 design-partner staging env

 Deliverable: Guardrail Side-car α (k8s, Python SDK)

 Owner: GPT-4.5

 Status: Deployed and verified
text

Collapse

Wrap

Copy
#### 3. 更新 README.md（concise 版）
突出 S-2 完成，status 改为 S-3 准备。

（基于你喜欢的 concise 版，只输出变更；替换相应部分。）

在顶部 status：
🚀 Status: ✅ Sprint S-3 Preparation (July 2025) - S-2/Pilot-0 Complete, Enterprise Ready

text

Collapse

Wrap

Copy
在 "Core Features" 下，添加 S-2 亮点：
New in v0.2.0: Guardrail side-car for K8s, enhanced chaos testing (resilience scoring), community feedback system.
text

Collapse

Wrap

Copy
在 "Roadmap & Status" 下：
S-1 (Shipped): CLI, OWASP coverage, reports.
S-2/Pilot-0 (Complete): K8s sidecar, chaos enhancements, PCI DSS. Target: Enterprise deployment.
Upcoming: S-3 (pilots/Stripe, $15k revenue), S-4 (SaaS dashboard).