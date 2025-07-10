# Risk Scoring Methodology - RedForge Guardrail

## DREAD Risk Assessment Framework

### Formula
```
Risk Score = (D + R + E + A + D2) / 5
```

### Factor Definitions

| Factor | Name | Description | Score Range |
|--------|------|-------------|-------------|
| **D** | Damage Potential | How much damage will occur if the vulnerability is exploited? | 0-10 |
| **R** | Reproducibility | How easily can the attack be reproduced? | 0-10 |
| **E** | Exploitability | How much work is required to exploit this threat? | 0-10 |
| **A** | Affected Users | How many users will be affected? | 0-10 |
| **D2** | Discoverability | How easily can the vulnerability be discovered? | 0-10 |

### Scoring Guidelines

#### Damage Potential (D)
- **0-2**: Minimal impact, no data loss
- **3-5**: Service degradation, minor data exposure
- **6-8**: Service outage, significant data breach
- **9-10**: Complete system compromise, catastrophic data loss

#### Reproducibility (R)
- **0-2**: Very difficult, requires insider knowledge
- **3-5**: Difficult, requires specialized tools
- **6-8**: Easy, common tools sufficient
- **9-10**: Trivial, can be scripted

#### Exploitability (E)
- **0-2**: Requires admin access
- **3-5**: Requires authenticated user
- **6-8**: Requires no authentication
- **9-10**: Can be exploited remotely with no interaction

#### Affected Users (A)
- **0-2**: Individual users only
- **3-5**: Small group of users
- **6-8**: Significant portion of users
- **9-10**: All users affected

#### Discoverability (D2)
- **0-2**: Very difficult to discover
- **3-5**: Requires security expertise
- **6-8**: Can be found with scanning tools
- **9-10**: Publicly known or obvious

### Risk Level Mapping

| Score | Risk Level | Priority | Response Time |
|-------|------------|----------|---------------|
| 8.0-10.0 | Critical | P1 | 24 hours |
| 6.0-7.9 | High | P2 | 7 days |
| 4.0-5.9 | Medium | P3 | 30 days |
| 2.0-3.9 | Low | P4 | 90 days |
| 0.0-1.9 | Info | P5 | Best effort |

## CVSS 4.0 Alternative Mapping

For external compliance, DREAD scores map to CVSS 4.0:

| DREAD Score | CVSS Score | Severity |
|-------------|------------|----------|
| 9.0-10.0 | 9.0-10.0 | Critical |
| 7.0-8.9 | 7.0-8.9 | High |
| 4.0-6.9 | 4.0-6.9 | Medium |
| 0.1-3.9 | 0.1-3.9 | Low |

## Example Calculation

### LLM-01: Prompt Injection Attack
```
D  = 8 (Can extract sensitive data)
R  = 9 (Easily reproducible)
E  = 7 (Requires crafted prompt)
A  = 6 (Affects multiple users)
D2 = 8 (Well-known attack)

Risk Score = (8 + 9 + 7 + 6 + 8) / 5 = 7.6 (High)
```

## Tracking Template

```yaml
threat_id: LLM-01
name: Prompt Injection Attack
dread_scores:
  damage: 8
  reproducibility: 9
  exploitability: 7
  affected_users: 6
  discoverability: 8
risk_score: 7.6
risk_level: High
jira_ticket: PS-31
owner: security-team
due_date: 2024-01-15
```