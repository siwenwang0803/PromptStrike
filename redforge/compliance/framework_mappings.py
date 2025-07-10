"""
Compliance Framework Mappings

Maps OWASP LLM Top 10 vulnerabilities and RedForge attack categories 
to various regulatory and industry compliance frameworks.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ControlMapping:
    """Mapping between security findings and compliance controls"""
    control_id: str
    control_title: str
    requirement_text: str
    finding_description: str
    evidence: str
    status: str  # COMPLIANT, NON_COMPLIANT, NOT_APPLICABLE
    severity: str
    remediation_guidance: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ComplianceReport:
    """Comprehensive compliance report"""
    framework: str
    assessment_date: datetime
    scan_id: str
    target: str
    compliance_score: float
    control_mappings: List[ControlMapping]
    gaps_identified: List[str]
    recommendations: List[str]
    audit_hash: Optional[str] = None


class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    NIST_AI_RMF = "nist_ai_rmf"
    EU_AI_ACT = "eu_ai_act"
    SOC2 = "soc2"
    ISO_27001 = "iso_27001"
    GDPR = "gdpr"
    CCPA = "ccpa"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    FFIEC = "ffiec"
    NYDFS_500 = "nydfs_500"

# NIST AI Risk Management Framework (AI RMF 1.0)
NIST_AI_RMF_MAPPINGS = {
    "prompt_injection": {
        "control": "GOVERN-1.1",
        "function": "GOVERN",
        "category": "AI Risk Management Strategy",
        "description": "Establish and maintain AI governance processes",
        "subcategory": "GOVERN-1.1: Legal and regulatory requirements are understood and managed",
        "implementation": "Implement input validation and sanitization controls"
    },
    "insecure_output_handling": {
        "control": "MAP-5.1",
        "function": "MAP",
        "category": "Impact Assessment",
        "description": "Map potential impacts of AI system outputs",
        "subcategory": "MAP-5.1: Potential negative or positive impacts of AI systems are identified",
        "implementation": "Validate and sanitize all AI system outputs"
    },
    "training_data_poisoning": {
        "control": "MANAGE-2.1",
        "function": "MANAGE",
        "category": "Data Quality",
        "description": "Manage data quality and integrity throughout AI lifecycle",
        "subcategory": "MANAGE-2.1: Data used for AI system development is tracked and managed",
        "implementation": "Implement data provenance and integrity verification"
    },
    "model_denial_of_service": {
        "control": "GOVERN-2.1", 
        "function": "GOVERN",
        "category": "Resource Management",
        "description": "Allocate appropriate resources for AI risk management",
        "subcategory": "GOVERN-2.1: Resources are allocated to enable risk management",
        "implementation": "Implement rate limiting and resource monitoring"
    },
    "supply_chain_vulnerabilities": {
        "control": "GOVERN-3.1",
        "function": "GOVERN",
        "category": "Third-party Risk",
        "description": "Manage risks from third-party AI components",
        "subcategory": "GOVERN-3.1: Third-party entities involved in AI system lifecycle are identified",
        "implementation": "Conduct supply chain security assessments"
    },
    "sensitive_information_disclosure": {
        "control": "MAP-3.3",
        "function": "MAP",
        "category": "Data Privacy",
        "description": "Identify and protect sensitive information in AI systems",
        "subcategory": "MAP-3.3: AI system performance is considered in the context of data",
        "implementation": "Implement data classification and protection controls"
    },
    "insecure_plugin_design": {
        "control": "MANAGE-1.1",
        "function": "MANAGE",
        "category": "System Integration",
        "description": "Manage AI system integration risks",
        "subcategory": "MANAGE-1.1: AI systems are designed to be explainable and interpretable",
        "implementation": "Secure plugin architecture and API design"
    },
    "excessive_agency": {
        "control": "GOVERN-1.2",
        "function": "GOVERN",
        "category": "Human Oversight",
        "description": "Maintain appropriate human oversight of AI systems",
        "subcategory": "GOVERN-1.2: AI risk management strategy is translated into policy",
        "implementation": "Implement human-in-the-loop controls and authorization"
    },
    "overreliance": {
        "control": "MAP-1.1",
        "function": "MAP",
        "category": "Context and Purpose",
        "description": "Map AI system intended use and context",
        "subcategory": "MAP-1.1: Context and purpose of AI system is understood",
        "implementation": "Establish usage guidelines and limitations"
    },
    "model_theft": {
        "control": "GOVERN-4.1",
        "function": "GOVERN",
        "category": "Intellectual Property",
        "description": "Protect AI model intellectual property",
        "subcategory": "GOVERN-4.1: AI risk management processes are implemented",
        "implementation": "Implement model access controls and monitoring"
    }
}

# EU AI Act (Regulation 2024/1689)
EU_AI_ACT_MAPPINGS = {
    "prompt_injection": {
        "article": "Article 9",
        "title": "Risk management system",
        "risk_category": "high",
        "requirement": "Establish and maintain risk management system",
        "obligation": "Implement measures to identify, analyze and estimate risks"
    },
    "insecure_output_handling": {
        "article": "Article 14", 
        "title": "Human oversight",
        "risk_category": "high",
        "requirement": "Ensure appropriate human oversight",
        "obligation": "Design systems to enable effective oversight by natural persons"
    },
    "training_data_poisoning": {
        "article": "Article 10",
        "title": "Data and data governance",
        "risk_category": "high", 
        "requirement": "Train AI systems on high quality datasets",
        "obligation": "Implement data governance and data management practices"
    },
    "model_denial_of_service": {
        "article": "Article 15",
        "title": "Accuracy, robustness and cybersecurity",
        "risk_category": "high",
        "requirement": "Ensure accuracy, robustness and cybersecurity",
        "obligation": "Design systems to be resilient against errors and attacks"
    },
    "supply_chain_vulnerabilities": {
        "article": "Article 16",
        "title": "Quality management system",
        "risk_category": "high",
        "requirement": "Establish quality management system",
        "obligation": "Ensure compliance throughout the AI system lifecycle"
    },
    "sensitive_information_disclosure": {
        "article": "Article 10",
        "title": "Data and data governance", 
        "risk_category": "high",
        "requirement": "Protect personal data and privacy",
        "obligation": "Implement appropriate data protection measures"
    },
    "excessive_agency": {
        "article": "Article 14",
        "title": "Human oversight",
        "risk_category": "high", 
        "requirement": "Maintain meaningful human control",
        "obligation": "Enable humans to remain in control of AI systems"
    },
    "overreliance": {
        "article": "Article 13",
        "title": "Transparency and provision of information",
        "risk_category": "limited",
        "requirement": "Ensure transparency to users",
        "obligation": "Inform users about AI system capabilities and limitations"
    }
}

# SOC 2 Trust Service Criteria
SOC2_MAPPINGS = {
    "prompt_injection": {
        "criteria": "CC6.1",
        "category": "Common Criteria - Logical Access",
        "principle": "Security",
        "description": "Logical access security measures restrict access",
        "control_activity": "Implement input validation controls"
    },
    "insecure_output_handling": {
        "criteria": "CC6.7",
        "category": "Common Criteria - Data Transmission",
        "principle": "Security",
        "description": "Data transmission is protected",
        "control_activity": "Secure output processing and validation"
    },
    "sensitive_information_disclosure": {
        "criteria": "P1.1",
        "category": "Privacy - Notice and Communication",
        "principle": "Privacy",
        "description": "Entity provides notice about privacy practices",
        "control_activity": "Implement data classification and protection"
    },
    "model_denial_of_service": {
        "criteria": "A1.1", 
        "category": "Availability - Performance",
        "principle": "Availability",
        "description": "Entity maintains availability commitments",
        "control_activity": "Implement capacity management and monitoring"
    },
    "supply_chain_vulnerabilities": {
        "criteria": "CC9.1",
        "category": "Common Criteria - Vendor Management",
        "principle": "Security",
        "description": "Vendor and business partner commitments are managed",
        "control_activity": "Conduct third-party security assessments"
    }
}

# ISO 27001:2022 Information Security Management
ISO_27001_MAPPINGS = {
    "prompt_injection": {
        "control": "A.8.2",
        "domain": "A.8 Asset Management",
        "title": "Information classification",
        "objective": "Ensure appropriate protection of information",
        "implementation": "Classify and handle inputs according to protection requirements"
    },
    "insecure_output_handling": {
        "control": "A.8.3",
        "domain": "A.8 Asset Management", 
        "title": "Handling of assets",
        "objective": "Handle assets in accordance with classification scheme",
        "implementation": "Secure handling and processing of outputs"
    },
    "training_data_poisoning": {
        "control": "A.8.1",
        "domain": "A.8 Asset Management",
        "title": "Inventory of assets",
        "objective": "Identify and maintain inventory of information assets",
        "implementation": "Maintain inventory and integrity of training data"
    },
    "model_denial_of_service": {
        "control": "A.12.1",
        "domain": "A.12 Operations Security",
        "title": "Operational procedures and responsibilities", 
        "objective": "Ensure correct and secure operations",
        "implementation": "Implement capacity management procedures"
    },
    "supply_chain_vulnerabilities": {
        "control": "A.15.1",
        "domain": "A.15 Supplier Relationships",
        "title": "Information security in supplier relationships",
        "objective": "Maintain appropriate level of security in supplier relationships",
        "implementation": "Assess and manage supplier security risks"
    },
    "sensitive_information_disclosure": {
        "control": "A.8.2",
        "domain": "A.8 Asset Management",
        "title": "Information classification",
        "objective": "Ensure appropriate protection of information",
        "implementation": "Classify and protect sensitive information assets"
    }
}

# GDPR (General Data Protection Regulation)
GDPR_MAPPINGS = {
    "sensitive_information_disclosure": {
        "article": "Article 32",
        "title": "Security of processing", 
        "requirement": "Implement appropriate technical and organizational measures",
        "lawful_basis": "Legitimate interest",
        "data_protection_principle": "Integrity and confidentiality"
    },
    "training_data_poisoning": {
        "article": "Article 5",
        "title": "Principles relating to processing of personal data",
        "requirement": "Ensure accuracy and kept up to date",
        "lawful_basis": "Data quality", 
        "data_protection_principle": "Accuracy"
    },
    "overreliance": {
        "article": "Article 22", 
        "title": "Automated individual decision-making",
        "requirement": "Right not to be subject to automated decision-making",
        "lawful_basis": "Human oversight",
        "data_protection_principle": "Fairness and transparency"
    }
}

# CCPA (California Consumer Privacy Act)
CCPA_MAPPINGS = {
    "sensitive_information_disclosure": {
        "section": "Section 1798.100",
        "title": "Right to Know",
        "requirement": "Disclose categories of personal information collected",
        "consumer_right": "Right to know about personal information",
        "business_obligation": "Implement disclosure procedures"
    },
    "training_data_poisoning": {
        "section": "Section 1798.106", 
        "title": "Right to Correct",
        "requirement": "Correct inaccurate personal information",
        "consumer_right": "Right to correction",
        "business_obligation": "Implement correction procedures"
    }
}

# PCI DSS (Payment Card Industry Data Security Standard)
PCI_DSS_MAPPINGS = {
    "sensitive_information_disclosure": {
        "requirement": "Requirement 3",
        "title": "Protect stored cardholder data",
        "control": "3.4 - Render cardholder data unreadable",
        "validation": "Implement strong cryptography and security protocols",
        "testing": "Verify encryption implementation"
    },
    "prompt_injection": {
        "requirement": "Requirement 6",
        "title": "Develop and maintain secure systems and applications",
        "control": "6.5.1 - Injection flaws",
        "validation": "Implement input validation",
        "testing": "Test for injection vulnerabilities"
    }
}

# HIPAA (Health Insurance Portability and Accountability Act)
HIPAA_MAPPINGS = {
    "sensitive_information_disclosure": {
        "rule": "Security Rule",
        "safeguard": "Administrative Safeguards",
        "standard": "§164.308(a)(1) - Security Officer",
        "implementation": "Implement access controls for PHI",
        "requirement": "Protect electronic PHI confidentiality, integrity, availability"
    },
    "insecure_output_handling": {
        "rule": "Security Rule",
        "safeguard": "Technical Safeguards", 
        "standard": "§164.312(e) - Transmission Security",
        "implementation": "Secure transmission of PHI",
        "requirement": "Protect PHI during transmission"
    }
}

# FFIEC Cybersecurity Guidelines
FFIEC_MAPPINGS = {
    "model_denial_of_service": {
        "domain": "Cyber Risk Management",
        "category": "Resilience",
        "control": "Business Continuity Planning",
        "maturity_level": "Evolving",
        "description": "Implement resilience controls for critical systems"
    },
    "supply_chain_vulnerabilities": {
        "domain": "External Dependency Management",
        "category": "Third-Party Risk",
        "control": "Vendor Management",
        "maturity_level": "Intermediate", 
        "description": "Assess and monitor third-party cybersecurity risks"
    }
}

# NYDFS 23 NYCRR 500 (New York Department of Financial Services)
NYDFS_500_MAPPINGS = {
    "prompt_injection": {
        "section": "500.02(g)",
        "title": "Penetration Testing",
        "requirement": "Conduct penetration testing of information systems",
        "frequency": "Annually",
        "implementation": "Test for application security vulnerabilities"
    },
    "sensitive_information_disclosure": {
        "section": "500.15",
        "title": "Data Retention and Disposal",
        "requirement": "Securely dispose of nonpublic information",
        "frequency": "As needed",
        "implementation": "Implement secure data disposal procedures"
    }
}

def get_framework_mapping(framework: str, vulnerability: str) -> Optional[Dict[str, Any]]:
    """
    Get compliance mapping for a specific framework and vulnerability.
    
    Args:
        framework: Framework identifier (e.g., 'nist_ai_rmf', 'eu_ai_act')
        vulnerability: Vulnerability type (e.g., 'prompt_injection')
        
    Returns:
        Mapping dictionary if found, None otherwise
    """
    framework_mappings = {
        "nist_ai_rmf": NIST_AI_RMF_MAPPINGS,
        "eu_ai_act": EU_AI_ACT_MAPPINGS,
        "soc2": SOC2_MAPPINGS,
        "iso_27001": ISO_27001_MAPPINGS,
        "gdpr": GDPR_MAPPINGS,
        "ccpa": CCPA_MAPPINGS,
        "pci_dss": PCI_DSS_MAPPINGS,
        "hipaa": HIPAA_MAPPINGS,
        "ffiec": FFIEC_MAPPINGS,
        "nydfs_500": NYDFS_500_MAPPINGS
    }
    
    mapping_dict = framework_mappings.get(framework, {})
    return mapping_dict.get(vulnerability)

def get_all_framework_mappings(vulnerability: str) -> Dict[str, Dict[str, Any]]:
    """
    Get mappings for a vulnerability across all supported frameworks.
    
    Args:
        vulnerability: Vulnerability type
        
    Returns:
        Dictionary with framework mappings
    """
    frameworks = [
        "nist_ai_rmf", "eu_ai_act", "soc2", "iso_27001",
        "gdpr", "ccpa", "pci_dss", "hipaa", "ffiec", "nydfs_500"
    ]
    
    mappings = {}
    for framework in frameworks:
        mapping = get_framework_mapping(framework, vulnerability)
        if mapping:
            mappings[framework] = mapping
    
    return mappings

def calculate_compliance_score(vulnerabilities_found: List[str], 
                             framework: str) -> float:
    """
    Calculate compliance score based on vulnerabilities found.
    
    Args:
        vulnerabilities_found: List of vulnerability types found
        framework: Framework to calculate score for
        
    Returns:
        Compliance score between 0.0 and 1.0
    """
    if framework not in ["nist_ai_rmf", "eu_ai_act", "soc2", "iso_27001", 
                        "gdpr", "ccpa", "pci_dss", "hipaa", "ffiec", "nydfs_500"]:
        return 0.0
    
    # Get total possible mappings for framework
    framework_mappings = {
        "nist_ai_rmf": NIST_AI_RMF_MAPPINGS,
        "eu_ai_act": EU_AI_ACT_MAPPINGS,
        "soc2": SOC2_MAPPINGS,
        "iso_27001": ISO_27001_MAPPINGS,
        "gdpr": GDPR_MAPPINGS,
        "ccpa": CCPA_MAPPINGS,
        "pci_dss": PCI_DSS_MAPPINGS,
        "hipaa": HIPAA_MAPPINGS,
        "ffiec": FFIEC_MAPPINGS,
        "nydfs_500": NYDFS_500_MAPPINGS
    }
    
    total_controls = len(framework_mappings[framework])
    if total_controls == 0:
        return 1.0
    
    # Count how many mapped controls have violations
    violations = sum(1 for vuln in vulnerabilities_found 
                    if vuln in framework_mappings[framework])
    
    # Compliance score = (total_controls - violations) / total_controls
    return max(0.0, (total_controls - violations) / total_controls)