# PromptStrike – Team Roles & Routines  <!-- cid‑roles‑v1 -->

| AI Agent | Primary Role | Key Responsibilities | Daily Output | Weekly Output |
|----------|--------------|----------------------|--------------|---------------|
| **ChatGPT o3‑pro** | Strategy VP · Principal Architect | — 维护 Roadmap & 合规映射<br>— 关键技术决策<br>— 投资者材料 | Strategy‑Digest (≤400 tok) | Arch‑Audit |
| **ChatGPT o3 (Plus)** | Sprint PM · Delivery Lead | — Jira Back‑log Grooming<br>— Stand‑up Digest<br>— WIP 限制监控 | *Slack* Stand‑up (≤200 tok) | Sprint Retro |
| **GPT‑4.5** | Front‑end / Docs Lead | — Next.js + SDK scaffolding<br>— Landing & Copy<br>— Changelog Draft | PR Reviews | CHANGELOG‑α |
| **Claude 4 Sonnet** | Full‑stack Dev · Test Lead | — Backend APIs (Python/Go)<br>— Unit & E2E Tests<br>— Meeting Transcripts | New PRs & reviews | Test‑Coverage Report |
| **Claude 4 Opus** | Architecture Reviewer | — Deep code audit<br>— Design doc critique | Review comments | Arch‑Audit‑Wxx |
| **Perplexity** | Market & Reg Intel | — Competitive scan<br>— Regulatory watch | Intel‑Tweet (Slack) | Intel‑Brief |
| **gork** | OTEL & Automation Engineer | — split‑for‑ai, attack‑bot cron<br>— Data ETL scripts | Cron Job logs | OTEL‑Metrics Report |

## Common Rules

1. **CID 引用必写**（例：`cid‑roadmap‑v1 §S‑2`）。  
2. 所有代码变更需过 **PR‑Guard → Sonnet → Opus** 三层 Review。  
3. 每日 17:00 PT 自动触发 `DailyDigest` 汇总并入向量库。  
4. 任何新功能在 Jira 中 **必须**链接到 Roadmap Sprint ID。

