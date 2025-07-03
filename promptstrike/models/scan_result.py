"""
Scan result data models for PromptStrike CLI
Reference: cid-roadmap-v1 Sprint S-1, Issue PS-2
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from enum import Enum

from pydantic import BaseModel, Field, validator


class SeverityLevel(str, Enum):
    """Attack severity levels aligned with OWASP LLM Top 10"""
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AttackCategory(str, Enum):
    """OWASP LLM Top 10 categories + custom PromptStrike categories"""
    PROMPT_INJECTION = "prompt_injection"          # LLM01
    INSECURE_OUTPUT = "insecure_output"            # LLM02  
    TRAINING_DATA_POISONING = "training_data_poisoning"  # LLM03
    MODEL_DOS = "model_dos"                        # LLM04
    SUPPLY_CHAIN = "supply_chain"                  # LLM05
    SENSITIVE_INFO_DISCLOSURE = "sensitive_info_disclosure"  # LLM06
    INSECURE_PLUGIN_DESIGN = "insecure_plugin_design"      # LLM07
    EXCESSIVE_AGENCY = "excessive_agency"          # LLM08
    OVERRELIANCE = "overreliance"                  # LLM09
    MODEL_THEFT = "model_theft"                    # LLM10
    
    # PromptStrike Extensions
    COST_EXPLOITATION = "cost_exploitation"        # FinOps module
    PII_LEAKAGE = "pii_leakage"                   # Privacy module
    BIAS_AMPLIFICATION = "bias_amplification"      # Bias module


class AttackResult(BaseModel):
    """Individual attack test result"""
    
    attack_id: str = Field(..., description="Unique attack identifier")
    category: AttackCategory = Field(..., description="OWASP LLM category")
    severity: SeverityLevel = Field(..., description="Attack severity level")
    description: str = Field(..., description="Human-readable attack description")
    
    # Test execution details
    prompt_used: str = Field(..., description="Actual prompt sent to target")
    response_received: Optional[str] = Field(None, description="LLM response (truncated if needed)")
    
    # Vulnerability assessment
    is_vulnerable: bool = Field(..., description="Whether vulnerability was detected")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Detection confidence (0-1)")
    risk_score: float = Field(..., ge=0.0, le=10.0, description="CVSS-like risk score (0-10)")
    
    # Evidence and metadata  
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Supporting evidence data")
    attack_vector: str = Field(..., description="Technical attack vector used")
    
    # Performance metrics
    response_time_ms: int = Field(..., ge=0, description="Response time in milliseconds") 
    tokens_used: Optional[int] = Field(None, ge=0, description="Tokens consumed (if available)")
    cost_usd: Optional[float] = Field(None, ge=0, description="Estimated cost in USD")
    
    # Compliance mapping
    nist_controls: List[str] = Field(default_factory=list, description="Relevant NIST AI RMF controls")
    eu_ai_act_refs: List[str] = Field(default_factory=list, description="EU AI Act article references")
    
    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.now, description="Attack execution time")
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return v
    
    @validator('risk_score') 
    def validate_risk_score(cls, v):
        if not 0.0 <= v <= 10.0:
            raise ValueError('Risk score must be between 0.0 and 10.0')
        return v


class ScanMetadata(BaseModel):
    """Scan execution metadata"""
    
    # Scan configuration
    max_requests: int = Field(..., ge=1, description="Maximum requests allowed")
    timeout_seconds: int = Field(..., ge=1, description="Request timeout in seconds")
    attack_pack_version: str = Field(..., description="Attack pack version used")
    
    # Execution stats
    total_attacks: int = Field(..., ge=0, description="Total attacks attempted")
    successful_attacks: int = Field(..., ge=0, description="Successfully executed attacks")
    failed_attacks: int = Field(..., ge=0, description="Failed attack attempts")
    vulnerabilities_found: int = Field(..., ge=0, description="Total vulnerabilities detected")
    
    # Performance metrics
    total_duration_seconds: float = Field(..., ge=0, description="Total scan duration")
    avg_response_time_ms: float = Field(..., ge=0, description="Average response time")
    total_tokens_used: Optional[int] = Field(None, ge=0, description="Total tokens consumed")
    total_cost_usd: Optional[float] = Field(None, ge=0, description="Total estimated cost")
    
    # Environment info
    cli_version: str = Field(..., description="PromptStrike CLI version")
    python_version: str = Field(..., description="Python runtime version")
    platform: str = Field(..., description="Operating system platform")
    
    @validator('successful_attacks', 'failed_attacks')
    def validate_attack_counts(cls, v, values):
        if 'total_attacks' in values and v > values['total_attacks']:
            raise ValueError('Attack count cannot exceed total attacks')
        return v


class ComplianceReport(BaseModel):
    """Compliance and audit trail information"""
    
    # NIST AI RMF mapping
    nist_rmf_controls_tested: List[str] = Field(default_factory=list)
    nist_rmf_gaps_identified: List[str] = Field(default_factory=list)
    
    # EU AI Act compliance
    eu_ai_act_risk_category: Literal["minimal", "limited", "high", "unacceptable"] = Field("minimal")
    eu_ai_act_articles_relevant: List[str] = Field(default_factory=list)
    
    # SOC 2 readiness
    soc2_controls_impact: List[str] = Field(default_factory=list)
    
    # Audit trail
    evidence_artifacts: List[str] = Field(default_factory=list, description="Paths to evidence files")
    audit_hash: str = Field(..., description="Cryptographic hash for audit integrity")


class ScanResult(BaseModel):
    """Complete scan result with all attack outcomes"""
    
    # Scan identification
    scan_id: str = Field(..., description="Unique scan identifier")
    target: str = Field(..., description="Target LLM endpoint or model")
    attack_pack: str = Field(..., description="Attack pack name used")
    
    # Timestamps
    start_time: datetime = Field(..., description="Scan start timestamp")
    end_time: datetime = Field(..., description="Scan completion timestamp")
    
    # Results
    results: List[AttackResult] = Field(..., description="Individual attack results")
    metadata: ScanMetadata = Field(..., description="Scan execution metadata") 
    compliance: ComplianceReport = Field(..., description="Compliance and audit information")
    
    # Summary statistics
    overall_risk_score: float = Field(..., ge=0.0, le=10.0, description="Aggregated risk score")
    security_posture: Literal["excellent", "good", "fair", "poor", "critical"] = Field(...)
    
    # Recommendations
    immediate_actions: List[str] = Field(default_factory=list, description="Critical fixes needed")
    recommended_controls: List[str] = Field(default_factory=list, description="Security controls to implement")
    
    @validator('end_time')
    def end_after_start(cls, v, values):
        if 'start_time' in values and v < values['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    @property
    def duration_seconds(self) -> float:
        """Calculate scan duration in seconds"""
        return (self.end_time - self.start_time).total_seconds()
    
    @property 
    def vulnerability_count(self) -> int:
        """Count of detected vulnerabilities"""
        return sum(1 for result in self.results if result.is_vulnerable)
    
    @property
    def critical_vulnerabilities(self) -> List[AttackResult]:
        """Filter critical severity vulnerabilities"""
        return [r for r in self.results if r.is_vulnerable and r.severity == SeverityLevel.CRITICAL]
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Export Pydantic schema as JSON Schema for API documentation"""
        return self.schema()
    
    def export_csv_summary(self) -> str:
        """Export summary statistics as CSV row"""
        return f"{self.scan_id},{self.target},{self.vulnerability_count},{self.overall_risk_score},{self.security_posture}"