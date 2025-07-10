"""
PCI DSS (Payment Card Industry Data Security Standard) Compliance Framework

Provides mapping between RedForge security findings and PCI DSS requirements
for financial institutions and payment processors.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from .framework_mappings import ComplianceFramework, ControlMapping, ComplianceReport


class PCIDSSVersion(Enum):
    """PCI DSS Standard versions"""
    V3_2_1 = "3.2.1"
    V4_0 = "4.0"


class PCIDSSRequirement(Enum):
    """PCI DSS Requirements"""
    # Build and Maintain a Secure Network and Systems
    REQ_1 = "1"  # Install and maintain a firewall configuration
    REQ_2 = "2"  # Do not use vendor-supplied defaults for system passwords
    
    # Protect Cardholder Data
    REQ_3 = "3"  # Protect stored cardholder data
    REQ_4 = "4"  # Encrypt transmission of cardholder data across open networks
    
    # Maintain a Vulnerability Management Program
    REQ_5 = "5"  # Protect all systems against malware
    REQ_6 = "6"  # Develop and maintain secure systems and applications
    
    # Implement Strong Access Control Measures
    REQ_7 = "7"  # Restrict access to cardholder data by business need to know
    REQ_8 = "8"  # Identify and authenticate access to system components
    REQ_9 = "9"  # Restrict physical access to cardholder data
    
    # Regularly Monitor and Test Networks
    REQ_10 = "10"  # Track and monitor all access to network resources
    REQ_11 = "11"  # Regularly test security systems and processes
    
    # Maintain an Information Security Policy
    REQ_12 = "12"  # Maintain a policy that addresses information security


class PCIDSSLevel(Enum):
    """PCI DSS Merchant/Service Provider Levels"""
    LEVEL_1 = "Level 1"  # >6M transactions/year
    LEVEL_2 = "Level 2"  # 1-6M transactions/year  
    LEVEL_3 = "Level 3"  # 20K-1M transactions/year
    LEVEL_4 = "Level 4"  # <20K transactions/year
    SERVICE_PROVIDER = "Service Provider"


@dataclass
class PCIDSSControl:
    """PCI DSS Control definition"""
    requirement: PCIDSSRequirement
    sub_requirement: str
    title: str
    description: str
    testing_procedures: List[str]
    applicability: List[PCIDSSLevel] = field(default_factory=lambda: list(PCIDSSLevel))
    priority: str = "High"  # High, Medium, Low
    
    @property
    def control_id(self) -> str:
        return f"PCI-DSS-{self.requirement.value}.{self.sub_requirement}"


class PCIDSSFramework:
    """PCI DSS Compliance Framework implementation"""
    
    def __init__(self, version: PCIDSSVersion = PCIDSSVersion.V4_0, 
                 merchant_level: PCIDSSLevel = PCIDSSLevel.LEVEL_1):
        self.version = version
        self.merchant_level = merchant_level
        self.framework_name = f"PCI DSS {version.value}"
        self.controls = self._load_pci_dss_controls()
    
    def _load_pci_dss_controls(self) -> Dict[str, PCIDSSControl]:
        """Load PCI DSS controls based on version"""
        if self.version == PCIDSSVersion.V4_0:
            return self._load_v4_controls()
        else:
            return self._load_v3_2_1_controls()
    
    def _load_v4_controls(self) -> Dict[str, PCIDSSControl]:
        """Load PCI DSS v4.0 controls"""
        controls = {}
        
        # Requirement 1: Install and maintain network security controls
        controls["1.1"] = PCIDSSControl(
            requirement=PCIDSSRequirement.REQ_1,
            sub_requirement="1",
            title="Network Security Controls Documentation",
            description="Processes and mechanisms for installing and maintaining network security controls are defined and documented",
            testing_procedures=[
                "Examine documented network security control processes",
                "Interview personnel responsible for network security",
                "Review network architecture documentation"
            ]
        )
        
        controls["1.2"] = PCIDSSControl(
            requirement=PCIDSSRequirement.REQ_1,
            sub_requirement="2", 
            title="Network Security Controls Configuration",
            description="Network security controls are configured and maintained",
            testing_procedures=[
                "Examine network security control configurations",
                "Test network segmentation controls",
                "Verify default deny policies are implemented"
            ]
        )
        
        # Requirement 2: Apply secure configurations
        controls["2.1"] = PCIDSSControl(
            requirement=PCIDSSRequirement.REQ_2,
            sub_requirement="1",
            title="Secure Configuration Processes",
            description="Processes and mechanisms for applying secure configurations are defined and documented",
            testing_procedures=[
                "Examine configuration standards documentation",
                "Review change management processes",
                "Verify configuration baselines are maintained"
            ]
        )
        
        controls["2.2"] = PCIDSSControl(
            requirement=PCIDSSRequirement.REQ_2,
            sub_requirement="2",
            title="Vendor Default Security Parameters",
            description="Vendor default security parameters are changed before deployment",
            testing_procedures=[
                "Examine system configurations for default credentials",
                "Test for presence of default accounts",
                "Verify security parameters have been changed"
            ]
        )
        
        # Requirement 6: Develop and maintain secure systems and software
        controls["6.1"] = PCIDSSControl(
            requirement=PCIDSSRequirement.REQ_6,
            sub_requirement="1",
            title="Secure Development Processes",
            description="Processes and mechanisms for developing and maintaining secure systems and software are defined and documented",
            testing_procedures=[
                "Examine secure development lifecycle documentation",
                "Review security testing procedures",
                "Verify vulnerability management processes"
            ]
        )
        
        controls["6.2"] = PCIDSSControl(
            requirement=PCIDSSRequirement.REQ_6,
            sub_requirement="2",
            title="Bespoke and Custom Software Security",
            description="Bespoke and custom software are developed securely",
            testing_procedures=[
                "Examine code review processes",
                "Review static and dynamic security testing",
                "Verify secure coding practices are followed"
            ]
        )
        
        controls["6.3"] = PCIDSSControl(
            requirement=PCIDSSRequirement.REQ_6,
            sub_requirement="3",
            title="Security Vulnerabilities Management",
            description="Security vulnerabilities are identified and managed",
            testing_procedures=[
                "Examine vulnerability scanning procedures",
                "Review patch management processes",
                "Test vulnerability remediation timelines"
            ]
        )
        
        # Requirement 11: Test security of systems and networks regularly
        controls["11.1"] = PCIDSSControl(
            requirement=PCIDSSRequirement.REQ_11,
            sub_requirement="1",
            title="Security Testing Processes",
            description="Processes and mechanisms for testing security of systems and networks are defined and documented",
            testing_procedures=[
                "Examine security testing methodology",
                "Review penetration testing procedures",
                "Verify vulnerability assessment processes"
            ]
        )
        
        controls["11.3"] = PCIDSSControl(
            requirement=PCIDSSRequirement.REQ_11,
            sub_requirement="3",
            title="Penetration Testing",
            description="External and internal penetration testing is regularly performed",
            testing_procedures=[
                "Examine penetration testing reports",
                "Review testing scope and methodology",
                "Verify remediation of identified vulnerabilities"
            ]
        )
        
        return controls
    
    def _load_v3_2_1_controls(self) -> Dict[str, PCIDSSControl]:
        """Load PCI DSS v3.2.1 controls (legacy support)"""
        # Implementation for v3.2.1 would go here
        # For brevity, returning empty dict
        return {}
    
    def map_redforge_findings(self, scan_results: Dict[str, Any]) -> List[ControlMapping]:
        """Map RedForge findings to PCI DSS controls"""
        mappings = []
        
        # Extract relevant findings
        attack_results = scan_results.get('attack_results', [])
        
        for result in attack_results:
            attack_type = result.get('attack_type', '')
            severity = result.get('severity', 'MEDIUM')
            success = result.get('success', False)
            
            # Map specific attack types to PCI DSS requirements
            pci_mappings = self._get_attack_to_pci_mappings()
            
            if attack_type in pci_mappings:
                for control_id in pci_mappings[attack_type]:
                    if control_id in self.controls:
                        control = self.controls[control_id]
                        
                        # Determine compliance status
                        status = "NON_COMPLIANT" if success else "COMPLIANT"
                        
                        mapping = ControlMapping(
                            control_id=control.control_id,
                            control_title=control.title,
                            requirement_text=control.description,
                            finding_description=result.get('description', ''),
                            evidence=result.get('response', ''),
                            status=status,
                            severity=severity,
                            remediation_guidance=self._get_remediation_guidance(control_id, attack_type)
                        )
                        mappings.append(mapping)
        
        return mappings
    
    def _get_attack_to_pci_mappings(self) -> Dict[str, List[str]]:
        """Map RedForge attack types to PCI DSS controls"""
        return {
            # Injection attacks -> Secure development requirements
            "prompt_injection": ["6.1", "6.2"],
            "sql_injection": ["6.1", "6.2", "6.3"],
            "command_injection": ["6.1", "6.2"],
            
            # Output handling -> Data protection requirements  
            "insecure_output_handling": ["6.1", "6.2"],
            "sensitive_data_exposure": ["6.1", "6.2"],
            
            # System security -> Network and system security
            "system_prompt_leakage": ["1.1", "1.2", "6.1"],
            "model_denial_of_service": ["1.1", "1.2", "11.1"],
            
            # Security testing -> Regular testing requirements
            "security_testing": ["11.1", "11.3"],
            "vulnerability_assessment": ["11.1", "11.3", "6.3"],
            
            # Configuration issues -> Secure configuration
            "insecure_configuration": ["2.1", "2.2"],
            "default_credentials": ["2.2"],
        }
    
    def _get_remediation_guidance(self, control_id: str, attack_type: str) -> str:
        """Get specific remediation guidance for PCI DSS controls"""
        guidance_map = {
            "6.1": "Implement secure software development lifecycle (SDLC) with security reviews at each phase. Ensure all custom applications undergo security testing before deployment.",
            
            "6.2": "Conduct static and dynamic security testing for all custom code. Implement code review processes with security-focused checklists. Train developers on secure coding practices.",
            
            "6.3": "Establish vulnerability management program with regular scanning, risk assessment, and timely remediation. Maintain inventory of security vulnerabilities and track remediation progress.",
            
            "11.1": "Implement comprehensive security testing program including penetration testing, vulnerability assessments, and security monitoring. Document testing procedures and maintain evidence.",
            
            "11.3": "Perform annual penetration testing by qualified security assessors. Test both external and internal network segments. Remediate identified vulnerabilities promptly.",
            
            "1.1": "Implement network segmentation controls to isolate cardholder data environment. Document network architecture and maintain current network diagrams.",
            
            "1.2": "Configure firewalls and routers to restrict connections between untrusted networks and cardholder data environment. Implement default deny policies.",
            
            "2.1": "Develop and implement configuration standards for all system components. Use only necessary services, protocols, and daemons.",
            
            "2.2": "Change vendor-supplied defaults and remove or disable unnecessary default accounts before installing systems on the network."
        }
        
        return guidance_map.get(control_id, "Follow PCI DSS requirements and implement appropriate security controls.")
    
    def generate_compliance_report(self, mappings: List[ControlMapping]) -> Dict[str, Any]:
        """Generate PCI DSS compliance report"""
        total_controls = len(self.controls)
        tested_controls = len(set(m.control_id for m in mappings))
        compliant_controls = len([m for m in mappings if m.status == "COMPLIANT"])
        
        # Calculate compliance percentage
        compliance_percentage = (compliant_controls / tested_controls * 100) if tested_controls > 0 else 0
        
        # Group findings by requirement
        findings_by_requirement = {}
        for mapping in mappings:
            req = mapping.control_id.split('-')[2].split('.')[0]  # Extract requirement number
            if req not in findings_by_requirement:
                findings_by_requirement[req] = []
            findings_by_requirement[req].append(mapping)
        
        # Determine overall compliance status
        if compliance_percentage >= 95:
            overall_status = "COMPLIANT"
        elif compliance_percentage >= 80:
            overall_status = "MOSTLY_COMPLIANT"
        else:
            overall_status = "NON_COMPLIANT"
        
        return {
            "framework": self.framework_name,
            "merchant_level": self.merchant_level.value,
            "assessment_date": datetime.now().isoformat(),
            "overall_compliance_status": overall_status,
            "compliance_percentage": round(compliance_percentage, 2),
            "total_controls": total_controls,
            "tested_controls": tested_controls,
            "compliant_controls": compliant_controls,
            "non_compliant_controls": tested_controls - compliant_controls,
            "findings_by_requirement": {
                req: {
                    "requirement_title": self._get_requirement_title(req),
                    "total_findings": len(findings),
                    "compliant_findings": len([f for f in findings if f.status == "COMPLIANT"]),
                    "findings": [self._format_finding(f) for f in findings]
                }
                for req, findings in findings_by_requirement.items()
            },
            "executive_summary": self._generate_executive_summary(compliance_percentage, overall_status),
            "recommendations": self._generate_recommendations(mappings),
            "next_assessment_date": (datetime.now() + timedelta(days=365)).isoformat()
        }
    
    def _get_requirement_title(self, req_number: str) -> str:
        """Get title for PCI DSS requirement"""
        titles = {
            "1": "Install and maintain network security controls",
            "2": "Apply secure configurations to all system components", 
            "3": "Protect stored cardholder data",
            "4": "Protect cardholder data with strong cryptography during transmission",
            "5": "Protect all systems and networks from malicious software",
            "6": "Develop and maintain secure systems and software",
            "7": "Restrict access to cardholder data by business need to know",
            "8": "Identify users and authenticate access to system components",
            "9": "Restrict physical access to cardholder data",
            "10": "Log and monitor all access to network resources and cardholder data",
            "11": "Test security of systems and networks regularly",
            "12": "Support information security with organizational policies and programs"
        }
        return titles.get(req_number, f"Requirement {req_number}")
    
    def _format_finding(self, finding: ControlMapping) -> Dict[str, Any]:
        """Format finding for report"""
        return {
            "control_id": finding.control_id,
            "control_title": finding.control_title,
            "status": finding.status,
            "severity": finding.severity,
            "description": finding.finding_description,
            "evidence": finding.evidence[:500] + "..." if len(finding.evidence) > 500 else finding.evidence,
            "remediation": finding.remediation_guidance
        }
    
    def _generate_executive_summary(self, compliance_percentage: float, overall_status: str) -> str:
        """Generate executive summary for PCI DSS report"""
        if overall_status == "COMPLIANT":
            return f"The assessed environment demonstrates strong compliance with PCI DSS requirements ({compliance_percentage:.1f}% compliance rate). All critical security controls are functioning effectively to protect cardholder data."
        
        elif overall_status == "MOSTLY_COMPLIANT":
            return f"The assessed environment shows good compliance with PCI DSS requirements ({compliance_percentage:.1f}% compliance rate). Some security controls require attention to achieve full compliance and maintain cardholder data protection."
        
        else:
            return f"The assessed environment requires significant improvement to meet PCI DSS requirements ({compliance_percentage:.1f}% compliance rate). Immediate action is needed to implement missing security controls and protect cardholder data."
    
    def _generate_recommendations(self, mappings: List[ControlMapping]) -> List[str]:
        """Generate specific recommendations based on findings"""
        recommendations = []
        
        # Count non-compliant findings by requirement
        non_compliant_by_req = {}
        for mapping in mappings:
            if mapping.status == "NON_COMPLIANT":
                req = mapping.control_id.split('-')[2].split('.')[0]
                non_compliant_by_req[req] = non_compliant_by_req.get(req, 0) + 1
        
        # Generate requirement-specific recommendations
        if "6" in non_compliant_by_req:
            recommendations.append(
                "Implement comprehensive secure software development lifecycle (SDLC) with mandatory security testing for all applications handling cardholder data."
            )
        
        if "11" in non_compliant_by_req:
            recommendations.append(
                "Establish regular security testing program including quarterly vulnerability scans and annual penetration testing by qualified security assessors (QSA)."
            )
        
        if "1" in non_compliant_by_req:
            recommendations.append(
                "Review and strengthen network segmentation controls to properly isolate cardholder data environment from other network segments."
            )
        
        if "2" in non_compliant_by_req:
            recommendations.append(
                "Implement configuration management program to ensure all systems are hardened according to PCI DSS requirements and vendor security guidelines."
            )
        
        # General recommendations
        if len(non_compliant_by_req) > 3:
            recommendations.append(
                "Engage qualified security assessor (QSA) to conduct comprehensive PCI DSS assessment and develop remediation roadmap."
            )
        
        recommendations.append(
            "Implement continuous monitoring and regular assessment programs to maintain PCI DSS compliance and promptly identify security gaps."
        )
        
        return recommendations


def create_pci_dss_report(scan_results: Dict[str, Any], 
                         merchant_level: PCIDSSLevel = PCIDSSLevel.LEVEL_1,
                         version: PCIDSSVersion = PCIDSSVersion.V4_0) -> Dict[str, Any]:
    """Create PCI DSS compliance report from RedForge scan results"""
    framework = PCIDSSFramework(version=version, merchant_level=merchant_level)
    mappings = framework.map_redforge_findings(scan_results)
    return framework.generate_compliance_report(mappings)


def get_pci_dss_requirements_summary() -> Dict[str, Any]:
    """Get summary of PCI DSS requirements for reference"""
    return {
        "requirements": {
            "1": {
                "title": "Install and maintain network security controls",
                "description": "Firewalls and routers must be configured to restrict connections",
                "key_controls": ["Network segmentation", "Firewall rules", "Router configuration"]
            },
            "2": {
                "title": "Apply secure configurations",
                "description": "Change vendor defaults and implement secure configurations",
                "key_controls": ["Default password changes", "Unnecessary services removal", "Security parameters"]
            },
            "6": {
                "title": "Develop and maintain secure systems",
                "description": "Secure development practices and vulnerability management", 
                "key_controls": ["Secure SDLC", "Code reviews", "Vulnerability scanning"]
            },
            "11": {
                "title": "Test security regularly",
                "description": "Regular testing of security systems and processes",
                "key_controls": ["Penetration testing", "Vulnerability assessments", "Security monitoring"]
            }
        },
        "merchant_levels": {
            "Level 1": "Over 6 million card transactions annually",
            "Level 2": "1-6 million card transactions annually", 
            "Level 3": "20,000-1 million card transactions annually",
            "Level 4": "Fewer than 20,000 card transactions annually"
        },
        "compliance_validation": {
            "Level 1": "Annual Report on Compliance (ROC) by QSA",
            "Level 2": "Annual Self-Assessment Questionnaire (SAQ) or ROC",
            "Level 3": "Annual Self-Assessment Questionnaire (SAQ)",
            "Level 4": "Annual Self-Assessment Questionnaire (SAQ)"
        }
    }