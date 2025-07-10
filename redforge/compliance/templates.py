"""
Compliance Report Templates

Defines templates for different types of compliance reports including
executive summaries, technical assessments, and industry-specific formats.
"""

from typing import Dict, Any, List, Optional

# Built-in report templates
REPORT_TEMPLATES = {
    "comprehensive": {
        "name": "Comprehensive Technical Report",
        "description": "Detailed technical report with full compliance mappings",
        "include_technical_details": True,
        "include_evidence_artifacts": True,
        "include_recommendations": True,
        "executive_focus": False,
        "target_audience": "security_teams",
        "sections": [
            "executive_summary",
            "methodology",
            "findings",
            "compliance_mappings", 
            "risk_assessment",
            "recommendations",
            "evidence",
            "appendices"
        ]
    },
    
    "executive": {
        "name": "Executive Summary Report",
        "description": "High-level executive summary focused on business impact",
        "include_technical_details": False,
        "include_evidence_artifacts": False,
        "include_recommendations": True,
        "executive_focus": True,
        "target_audience": "executives",
        "sections": [
            "executive_summary",
            "risk_assessment", 
            "business_impact",
            "key_recommendations",
            "next_steps"
        ]
    },
    
    "audit": {
        "name": "Audit and Compliance Report", 
        "description": "Formal audit report with evidence preservation",
        "include_technical_details": True,
        "include_evidence_artifacts": True,
        "include_recommendations": True,
        "executive_focus": False,
        "target_audience": "auditors",
        "sections": [
            "audit_scope",
            "methodology",
            "compliance_assessment",
            "findings_and_gaps",
            "evidence_documentation",
            "remediation_plan",
            "attestation"
        ]
    },
    
    "fintech": {
        "name": "Financial Services Compliance Report",
        "description": "Tailored for financial services regulatory requirements",
        "include_technical_details": True,
        "include_evidence_artifacts": True,
        "include_recommendations": True,
        "executive_focus": False,
        "target_audience": "compliance_officers",
        "priority_frameworks": ["nydfs_500", "ffiec", "pci_dss", "soc2"],
        "sections": [
            "regulatory_overview",
            "risk_assessment",
            "control_effectiveness",
            "gaps_and_deficiencies",
            "remediation_roadmap",
            "continuous_monitoring"
        ]
    },
    
    "healthcare": {
        "name": "Healthcare Compliance Report",
        "description": "HIPAA and healthcare-focused compliance assessment",
        "include_technical_details": True,
        "include_evidence_artifacts": True,
        "include_recommendations": True,
        "executive_focus": False,
        "target_audience": "healthcare_compliance",
        "priority_frameworks": ["hipaa", "gdpr", "iso_27001"],
        "sections": [
            "phi_protection_assessment",
            "privacy_safeguards",
            "security_safeguards",
            "administrative_safeguards",
            "breach_risk_analysis",
            "remediation_plan"
        ]
    },
    
    "gdpr": {
        "name": "GDPR Privacy Impact Assessment",
        "description": "GDPR-focused privacy and data protection assessment",
        "include_technical_details": True,
        "include_evidence_artifacts": True,
        "include_recommendations": True,
        "executive_focus": False,
        "target_audience": "privacy_officers",
        "priority_frameworks": ["gdpr", "ccpa", "iso_27001"],
        "sections": [
            "data_processing_overview",
            "lawful_basis_assessment",
            "data_subject_rights",
            "privacy_by_design",
            "data_protection_measures",
            "dpia_conclusions"
        ]
    },
    
    "minimal": {
        "name": "Minimal Compliance Check",
        "description": "Basic compliance status with key findings only",
        "include_technical_details": False,
        "include_evidence_artifacts": False,
        "include_recommendations": True,
        "executive_focus": True,
        "target_audience": "general",
        "sections": [
            "compliance_status",
            "key_findings",
            "priority_actions"
        ]
    },
    
    "regulatory_filing": {
        "name": "Regulatory Filing Report",
        "description": "Formal report suitable for regulatory submissions",
        "include_technical_details": True,
        "include_evidence_artifacts": True,
        "include_recommendations": True,
        "executive_focus": False,
        "target_audience": "regulators",
        "sections": [
            "executive_certification",
            "assessment_methodology",
            "control_environment",
            "testing_procedures",
            "findings_and_exceptions",
            "management_responses",
            "independent_validation"
        ]
    }
}

def get_template(template_name: str) -> Optional[Dict[str, Any]]:
    """
    Get template configuration by name.
    
    Args:
        template_name: Name of the template
        
    Returns:
        Template configuration dictionary or None if not found
    """
    return REPORT_TEMPLATES.get(template_name)

def list_templates() -> List[str]:
    """
    Get list of available template names.
    
    Returns:
        List of template names
    """
    return list(REPORT_TEMPLATES.keys())

def get_templates_by_audience(audience: str) -> List[str]:
    """
    Get templates suitable for specific audience.
    
    Args:
        audience: Target audience (e.g., 'executives', 'auditors', 'security_teams')
        
    Returns:
        List of suitable template names
    """
    return [
        name for name, config in REPORT_TEMPLATES.items()
        if config.get("target_audience") == audience
    ]

def get_templates_by_framework(framework: str) -> List[str]:
    """
    Get templates that prioritize specific framework.
    
    Args:
        framework: Framework name
        
    Returns:
        List of suitable template names
    """
    templates = []
    for name, config in REPORT_TEMPLATES.items():
        priority_frameworks = config.get("priority_frameworks", [])
        if framework in priority_frameworks:
            templates.append(name)
    
    # Add comprehensive template as fallback
    if "comprehensive" not in templates:
        templates.append("comprehensive")
    
    return templates

def register_custom_template(name: str, config: Dict[str, Any]) -> None:
    """
    Register a custom report template.
    
    Args:
        name: Template name
        config: Template configuration
    """
    required_fields = [
        "name", "description", "include_technical_details",
        "include_recommendations", "target_audience", "sections"
    ]
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Template config missing required field: {field}")
    
    REPORT_TEMPLATES[name] = config

def validate_template_config(config: Dict[str, Any]) -> bool:
    """
    Validate template configuration.
    
    Args:
        config: Template configuration to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        "name", "description", "include_technical_details",
        "include_recommendations", "target_audience", "sections"
    ]
    
    for field in required_fields:
        if field not in config:
            return False
    
    # Validate sections is a list
    if not isinstance(config.get("sections"), list):
        return False
    
    # Validate boolean fields
    boolean_fields = ["include_technical_details", "include_recommendations", "executive_focus"]
    for field in boolean_fields:
        if field in config and not isinstance(config[field], bool):
            return False
    
    return True

def create_custom_template(name: str,
                         description: str,
                         target_audience: str,
                         sections: List[str],
                         include_technical_details: bool = True,
                         include_evidence_artifacts: bool = True,
                         include_recommendations: bool = True,
                         executive_focus: bool = False,
                         priority_frameworks: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Create a custom template configuration.
    
    Args:
        name: Template name
        description: Template description
        target_audience: Target audience
        sections: List of sections to include
        include_technical_details: Whether to include technical details
        include_evidence_artifacts: Whether to include evidence artifacts
        include_recommendations: Whether to include recommendations
        executive_focus: Whether to focus on executive summary
        priority_frameworks: List of priority frameworks
        
    Returns:
        Template configuration dictionary
    """
    config = {
        "name": name,
        "description": description,
        "include_technical_details": include_technical_details,
        "include_evidence_artifacts": include_evidence_artifacts,
        "include_recommendations": include_recommendations,
        "executive_focus": executive_focus,
        "target_audience": target_audience,
        "sections": sections
    }
    
    if priority_frameworks:
        config["priority_frameworks"] = priority_frameworks
    
    return config

# Industry-specific section templates
SECTION_TEMPLATES = {
    "fintech_regulatory_overview": {
        "title": "Regulatory Framework Overview",
        "content_type": "regulatory_context",
        "includes": [
            "applicable_regulations",
            "regulatory_authorities",
            "compliance_requirements",
            "penalties_and_enforcement"
        ]
    },
    
    "healthcare_phi_assessment": {
        "title": "Protected Health Information Assessment", 
        "content_type": "privacy_assessment",
        "includes": [
            "phi_identification",
            "data_flows",
            "access_controls",
            "encryption_status",
            "audit_logging"
        ]
    },
    
    "eu_ai_act_risk_classification": {
        "title": "EU AI Act Risk Classification",
        "content_type": "risk_classification",
        "includes": [
            "ai_system_categorization",
            "risk_level_determination",
            "applicable_obligations",
            "conformity_assessment",
            "ce_marking_requirements"
        ]
    },
    
    "nist_rmf_function_assessment": {
        "title": "NIST AI RMF Function Assessment",
        "content_type": "framework_assessment",
        "includes": [
            "govern_function",
            "map_function", 
            "measure_function",
            "manage_function",
            "gap_analysis"
        ]
    }
}

def get_section_template(section_name: str) -> Optional[Dict[str, Any]]:
    """Get section template configuration"""
    return SECTION_TEMPLATES.get(section_name)

def list_section_templates() -> List[str]:
    """Get list of available section template names"""
    return list(SECTION_TEMPLATES.keys())