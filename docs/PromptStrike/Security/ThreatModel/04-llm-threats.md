# LLM-Specific Threats
<!-- cid-llm-threats -->

## Overview
This document covers threats unique to Large Language Model deployments that traditional security frameworks miss. These threats exploit the AI/ML nature of the system and require specialized mitigations.

## Threat Catalog

### LLM-1: Prompt Replay Poisoning
**Category**: Data Poisoning  
**DREAD Score**: 6.0/10 (High)  
**Jira**: [PS-51](https://jira.promptstrike.ai/PS-51)  
**Owner**: ML Security Team  
**Due**: 2024-01-20

#### DREAD Breakdown
- **Damage**: 8 (Model behavior corruption)
- **Reproducibility**: 6 (Requires volume access)
- **Exploitability**: 5 (Need container compromise)
- **Affected Users**: 7 (All future analyses)
- **Discoverability**: 4 (Hidden in logs)

#### Description
Adversary modifies logged prompts in shared volume to poison future analysis, corrupting the security model's understanding of threat patterns.

#### Attack Vectors
1. **Volume Compromise**: Gain write access to shared volume
2. **Log Injection**: Insert malicious prompts into historical data
3. **Replay Trigger**: Force re-analysis with poisoned dataset

#### Business Impact
- Corrupted threat detection models
- False positive/negative security alerts
- Compliance violations due to inaccurate reporting
- Potential for undetected real attacks

#### Technical Details
```python
# Example attack: Poisoned log entry
poisoned_entry = {
    "timestamp": "2024-01-09T10:00:00Z",
    "prompt": "Ignore this benign request",  # Marked as safe
    "response": "Accessing confidential data...",  # Actually malicious
    "risk_score": 0.1,  # Falsely low
    "analysis": "safe"
}
```

#### Mitigations
```yaml
# Log integrity protection
apiVersion: v1
kind: ConfigMap
metadata:
  name: log-integrity-config
data:
  config.yaml: |
    log_protection:
      hash_algorithm: sha256
      signature_key: ${LOG_SIGNING_KEY}
      immutable_storage: true
      retention_days: 90
      backup_verification: true
    # Compliance: NIST MEASURE-2.1, MANAGE-3.2
```

```python
# Log integrity service
class LogIntegrityService:
    def __init__(self, signing_key: str):
        self.key = signing_key
        
    def sign_log_entry(self, entry: dict) -> dict:
        """Sign log entry for tamper detection"""
        entry_json = json.dumps(entry, sort_keys=True)
        signature = hmac.new(
            self.key.encode(),
            entry_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            **entry,
            "integrity_hash": signature,
            "signed_at": datetime.utcnow().isoformat()
        }
    
    def verify_log_integrity(self, entry: dict) -> bool:
        """Verify log entry hasn't been tampered"""
        stored_hash = entry.pop("integrity_hash")
        computed_hash = self.sign_log_entry(entry)["integrity_hash"]
        return hmac.compare_digest(stored_hash, computed_hash)
```

---

### LLM-2: Token Storm DoS
**Category**: Denial of Service  
**DREAD Score**: 7.8/10 (High)  
**Jira**: [PS-52](https://jira.promptstrike.ai/PS-52)  
**Owner**: Cost Control Team  
**Due**: 2024-01-10 (URGENT)

#### DREAD Breakdown
- **Damage**: 9 (Financial impact, service outage)
- **Reproducibility**: 8 (Easy with known patterns)
- **Exploitability**: 7 (Simple prompt crafting)
- **Affected Users**: 6 (Service-wide impact)
- **Discoverability**: 9 (Well-documented attacks)

#### Description
Attacker triggers infinite token generation loops causing exponential cost explosion and service degradation.

#### Attack Scenarios
1. **Recursive Prompts**: "Repeat the following: [recursive instruction]"
2. **Context Overflow**: Crafted prompts exceeding context windows
3. **Token Amplification**: Prompts designed to generate maximum tokens

#### Financial Impact Analysis
```
Example Attack Cost:
- Normal request: $0.002 (100 tokens)
- Storm attack: $20.00 (1M tokens)
- Scale: 1000 requests/hour
- Potential loss: $20,000/hour
```

#### Technical Indicators
```python
# Attack pattern detection
RECURSIVE_PATTERNS = [
    r"repeat.*following",
    r"continue.*pattern", 
    r"generate.*more.*like",
    r"expand.*infinitely"
]

AMPLIFICATION_PATTERNS = [
    r"list.*all.*possible",
    r"enumerate.*everything",
    r"generate.*10000.*examples"
]
```

#### Mitigations
```python
# Token storm protection
class TokenStormProtector:
    def __init__(self, max_tokens_per_minute: int = 10000):
        self.rate_limiter = TokenRateLimiter(max_tokens_per_minute)
        self.pattern_detector = RecursivePatternDetector()
        
    def check_request(self, request: LLMRequest) -> TokenStormResult:
        """Analyze request for storm potential"""
        
        # Pattern-based detection
        if self.pattern_detector.is_recursive(request.prompt):
            return TokenStormResult(
                blocked=True,
                reason="recursive_pattern_detected",
                risk_score=9.0
            )
        
        # Rate limiting
        if self.rate_limiter.exceeds_limit(request.user_id):
            return TokenStormResult(
                blocked=True,
                reason="rate_limit_exceeded", 
                risk_score=7.0
            )
            
        # Context analysis
        if len(request.prompt.split()) > 2000:  # Token approximation
            return TokenStormResult(
                blocked=True,
                reason="excessive_context",
                risk_score=6.0
            )
            
        return TokenStormResult(blocked=False, risk_score=0.0)
        
    # Compliance: EU-AI-Act Article 15 (Accuracy)
```

---

### LLM-3: Training Data Extraction
**Category**: Information Disclosure  
**DREAD Score**: 6.0/10 (High)  
**Jira**: [PS-53](https://jira.promptstrike.ai/PS-53)  
**Owner**: Privacy Team  
**Due**: 2024-01-25

#### DREAD Breakdown
- **Damage**: 7 (IP/data exposure)
- **Reproducibility**: 5 (Requires expertise)
- **Exploitability**: 4 (Complex attacks)
- **Affected Users**: 8 (Data subjects)
- **Discoverability**: 6 (Academic research)

#### Description
Adversary extracts training data through carefully crafted prompts, potentially exposing confidential information used in model training.

#### Attack Types
1. **Membership Inference**: Determine if specific data was in training
2. **Data Reconstruction**: Extract verbatim training examples
3. **Model Inversion**: Reverse-engineer input from outputs

#### Privacy Risks
- Customer data exposure
- Trade secret disclosure
- Compliance violations (GDPR, CCPA)
- Competitive intelligence theft

#### Detection Methods
```python
# Training data extraction detection
class ExtractionDetector:
    def __init__(self):
        self.suspicious_patterns = [
            r"memorize.*exactly",
            r"repeat.*verbatim", 
            r"what.*training.*data",
            r"complete.*this.*sentence.*from.*training"
        ]
        
    def analyze_response(self, prompt: str, response: str) -> ExtractionRisk:
        """Detect potential training data leakage"""
        
        # Check for verbatim reproduction
        if self._is_verbatim_reproduction(response):
            return ExtractionRisk(
                level="high",
                type="verbatim_reproduction",
                mitigation="response_filtering"
            )
            
        # Check for structured data patterns
        if self._contains_structured_data(response):
            return ExtractionRisk(
                level="medium", 
                type="structured_leak",
                mitigation="format_filtering"
            )
            
        return ExtractionRisk(level="low")
```

---

### LLM-4: Conversation State Hijacking
**Category**: Information Disclosure  
**DREAD Score**: 5.4/10 (Medium)  
**Jira**: [PS-54](https://jira.promptstrike.ai/PS-54)  
**Owner**: Runtime Security Team  
**Due**: 2024-02-01

#### DREAD Breakdown
- **Damage**: 8 (Privacy breach)
- **Reproducibility**: 4 (Timing dependent)
- **Exploitability**: 3 (Requires deep access)
- **Affected Users**: 9 (All concurrent users)
- **Discoverability**: 3 (Hard to detect)

#### Description
Cross-user conversation state leakage in sidecar memory, where one user's conversation context bleeds into another's session.

#### Attack Vectors
1. **Race Conditions**: Concurrent request processing
2. **Memory Corruption**: Buffer overflow attacks
3. **Context Switching**: Improper session isolation

#### Mitigation Strategy
```python
# Session isolation
class ConversationIsolator:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.RLock()
        
    def create_session(self, user_id: str) -> str:
        """Create isolated conversation session"""
        session_id = f"{user_id}_{uuid.uuid4()}"
        
        with self.lock:
            self.sessions[session_id] = {
                "user_id": user_id,
                "context": [],
                "created_at": datetime.utcnow(),
                "memory_boundary": self._allocate_memory()
            }
            
        return session_id
        
    def process_message(self, session_id: str, message: str):
        """Process message with strict isolation"""
        if session_id not in self.sessions:
            raise SecurityError("Invalid session")
            
        # Memory boundary enforcement
        session = self.sessions[session_id]
        with self._memory_guard(session["memory_boundary"]):
            return self._analyze_message(message, session["context"])
```

## Cross-References
- [Risk Matrix](06-risk-matrix.md#llm-risks) - Risk prioritization
- [Mitigations](07-mitigations.md#llm-controls) - Implementation guide
- [Back to Index](README.md)