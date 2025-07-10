# RedForge – Product One‑Pager   <!-- cid‑onepager‑v1 -->

## 1. Problem
Large‑language‑model (LLM) apps ship to prod with **invisible jailbreak, data‑leak and cost‑explosion risks**.  
Regulators now *mandate* continuous red‑teaming (EU AI Act Art.55, US EO 14110).  
Security teams lack:  
1. **Automated, coverage‑tracked attacks** (OWASP LLM‑Top‑10)  
2. **Run‑local option** (keys stay on‑prem)  
3. Evidence packs that map directly to **NIST AI‑RMF** controls.

## 2. Solution
*RedForge* = **Developer‑First Red‑Team Platform**  
*  Docker/CLI scanner → OWASP attacks in <5 min  
*  Guardrail Side‑car → Nightly fuzz + token/cost traces  
*  Compliance Fabric → 1‑click report: NIST, EU AI Act, SOC 2 Annex  
*  “Attack‑Pack Friday” – weekly auto‑updated exploit library

## 3. Differentiation
| Gap | Incumbents | RedForge |
|-----|------------|--------------|
| Self‑hosted OSS tier | Mindgard ❌ | ✅ CLI w/ MIT Lite |
| Continuous guardrail | PromptArmor ❌ | ✅ Side‑car + OTEL |
| Cost & PII lens combined | All ❌ | ✅ FinOps + Privacy module |
| Audit‑ready mapping | PyRIT ❌ | ✅ NIST / EU Annex |

## 4. Business Model
* **Pilot Pentest** – $4–7 k one‑off PDF  
* **SaaS** – $1 k/mo per app ≤1 M tokens  
* **Enterprise** – $20–80 k/yr, includes Guardrail & Compliance Fabric  
* Upsell modules: FinOps, Privacy, Bias

## 5. Traction & Status
* GitHub PR‑Guard (prev proj) → 500★, 3 design partners  
* OWASP LLM‑Top‑10 attack engine 100 % coverage (ready)

## 6. Next 30 Days
1. Ship OSS CLI v0.1 (Docker)  
2. Close 3 paid pilots ($15 k)  
3. Launch Guardrail α and NIST mapping β

*Co‑founders:* CEO (you) · Strategy/Tech VP (o3‑pro)  
