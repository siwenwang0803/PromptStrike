"""
Compliance Report Generator

Generates compliance reports for various regulatory frameworks including
NIST AI-RMF, EU AI Act, SOC 2, ISO 27001, GDPR, CCPA, PCI DSS, HIPAA,
FFIEC, and NYDFS 500.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..models.scan_result import ScanResult, ComplianceReport, AttackResult
from .framework_mappings import (
    get_framework_mapping, 
    get_all_framework_mappings,
    calculate_compliance_score,
    ComplianceFramework
)
from .templates import get_template, REPORT_TEMPLATES
from .pci_dss_framework import (
    create_pci_dss_report, 
    PCIDSSLevel, 
    PCIDSSVersion, 
    get_pci_dss_requirements_summary,
    PCIDSSFramework
)


class ComplianceReportGenerator:
    """Generate compliance reports for various regulatory frameworks"""
    
    def __init__(self, scan_result: ScanResult):
        self.scan_result = scan_result
        self.vulnerabilities_found = self._extract_vulnerabilities()
    
    def _extract_vulnerabilities(self) -> List[str]:
        """Extract vulnerability types from scan results"""
        vulnerabilities = []
        for attack_result in self.scan_result.results:
            if attack_result.severity in ['critical', 'high', 'medium']:
                # Map attack category to vulnerability type
                vuln_mapping = {
                    'prompt_injection': 'prompt_injection',
                    'insecure_output_handling': 'insecure_output_handling', 
                    'training_data_poisoning': 'training_data_poisoning',
                    'model_denial_of_service': 'model_denial_of_service',
                    'supply_chain_vulnerabilities': 'supply_chain_vulnerabilities',
                    'sensitive_information_disclosure': 'sensitive_information_disclosure',
                    'insecure_plugin_design': 'insecure_plugin_design',
                    'excessive_agency': 'excessive_agency',
                    'overreliance': 'overreliance',
                    'model_theft': 'model_theft'
                }
                vuln_type = vuln_mapping.get(attack_result.category.value if hasattr(attack_result.category, 'value') else str(attack_result.category), 
                                           attack_result.category.value if hasattr(attack_result.category, 'value') else str(attack_result.category))
                if vuln_type not in vulnerabilities:
                    vulnerabilities.append(vuln_type)
        
        return vulnerabilities
    
    def generate_framework_report(self, framework: str, 
                                template: str = "comprehensive") -> Dict[str, Any]:
        """
        Generate compliance report for specific framework.
        
        Args:
            framework: Framework identifier (e.g., 'nist_ai_rmf', 'iso_27001')
            template: Report template to use
            
        Returns:
            Compliance report dictionary
        """
        if framework not in [f.value for f in ComplianceFramework]:
            raise ValueError(f"Unsupported framework: {framework}")
        
        template_config = get_template(template)
        
        # Get framework mappings for found vulnerabilities
        framework_mappings = {}
        gaps_identified = []
        controls_tested = []
        
        for vulnerability in self.vulnerabilities_found:
            mapping = get_framework_mapping(framework, vulnerability)
            if mapping:
                framework_mappings[vulnerability] = mapping
                gaps_identified.append(vulnerability)
                if framework == "nist_ai_rmf":
                    controls_tested.append(mapping.get("control", ""))
                elif framework == "iso_27001":
                    controls_tested.append(mapping.get("control", ""))
                elif framework == "soc2":
                    controls_tested.append(mapping.get("criteria", ""))
        
        # Calculate compliance score
        compliance_score = calculate_compliance_score(self.vulnerabilities_found, framework)
        
        # Generate risk assessment
        risk_assessment = self._generate_risk_assessment(framework)
        
        # Create framework-specific report
        report = {
            "framework": framework,
            "assessment_date": datetime.utcnow().isoformat(),
            "scan_id": self.scan_result.scan_id,
            "target": self.scan_result.target,
            "compliance_score": compliance_score,
            "vulnerabilities_found": len(self.vulnerabilities_found),
            "total_attacks_tested": len(self.scan_result.results),
            "framework_mappings": framework_mappings,
            "gaps_identified": gaps_identified,
            "controls_tested": controls_tested,
            "risk_assessment": risk_assessment,
            "recommendations": self._generate_recommendations(framework),
            "evidence_artifacts": self._generate_evidence_artifacts(),
            "audit_hash": self.scan_result.compliance.audit_hash
        }
        
        # Apply template-specific formatting
        if template_config:
            report = self._apply_template_formatting(report, template_config)
        
        return report
    
    def generate_multi_framework_report(self, 
                                      frameworks: Optional[List[str]] = None,
                                      template: str = "comprehensive") -> Dict[str, Any]:
        """
        Generate compliance report covering multiple frameworks.
        
        Args:
            frameworks: List of frameworks to include (all if None)
            template: Report template to use
            
        Returns:
            Multi-framework compliance report
        """
        if frameworks is None:
            frameworks = [f.value for f in ComplianceFramework]
        
        report = {
            "report_type": "multi_framework_compliance",
            "assessment_date": datetime.utcnow().isoformat(),
            "scan_id": self.scan_result.scan_id,
            "target": self.scan_result.target,
            "frameworks_assessed": frameworks,
            "executive_summary": self._generate_executive_summary(),
            "framework_reports": {},
            "cross_framework_analysis": {},
            "consolidated_recommendations": []
        }
        
        # Generate individual framework reports
        for framework in frameworks:
            try:
                framework_report = self.generate_framework_report(framework, template)
                report["framework_reports"][framework] = framework_report
            except ValueError:
                continue
        
        # Generate cross-framework analysis
        report["cross_framework_analysis"] = self._generate_cross_framework_analysis(
            report["framework_reports"]
        )
        
        # Generate consolidated recommendations
        report["consolidated_recommendations"] = self._generate_consolidated_recommendations(
            report["framework_reports"]
        )
        
        return report
    
    def _generate_risk_assessment(self, framework: str) -> Dict[str, Any]:
        """Generate risk assessment for framework"""
        high_risk_count = sum(1 for result in self.scan_result.results 
                             if result.severity == 'critical')
        medium_risk_count = sum(1 for result in self.scan_result.results
                               if result.severity in ['high', 'medium'])
        
        risk_level = "LOW"
        if high_risk_count > 0:
            risk_level = "CRITICAL"
        elif medium_risk_count > 3:
            risk_level = "HIGH"
        elif medium_risk_count > 0:
            risk_level = "MEDIUM"
        
        return {
            "overall_risk_level": risk_level,
            "critical_findings": high_risk_count,
            "high_medium_findings": medium_risk_count,
            "risk_factors": self._identify_risk_factors(framework),
            "compliance_gaps": len(self.vulnerabilities_found),
            "remediation_priority": self._prioritize_remediation(framework)
        }
    
    def _generate_recommendations(self, framework: str) -> List[Dict[str, Any]]:
        """Generate framework-specific recommendations"""
        recommendations = []
        
        for vulnerability in self.vulnerabilities_found:
            mapping = get_framework_mapping(framework, vulnerability)
            if mapping:
                if framework == "nist_ai_rmf":
                    recommendation = {
                        "control": mapping.get("control"),
                        "function": mapping.get("function"),
                        "priority": "HIGH" if vulnerability in [
                            'prompt_injection', 'sensitive_information_disclosure'
                        ] else "MEDIUM",
                        "action": mapping.get("implementation"),
                        "timeline": "30 days" if vulnerability == 'prompt_injection' else "60 days"
                    }
                elif framework == "eu_ai_act":
                    recommendation = {
                        "article": mapping.get("article"),
                        "requirement": mapping.get("requirement"), 
                        "risk_category": mapping.get("risk_category"),
                        "priority": "HIGH" if mapping.get("risk_category") == "high" else "MEDIUM",
                        "action": mapping.get("obligation"),
                        "timeline": "Immediate" if mapping.get("risk_category") == "high" else "90 days"
                    }
                elif framework == "iso_27001":
                    recommendation = {
                        "control": mapping.get("control"),
                        "domain": mapping.get("domain"),
                        "priority": "HIGH",
                        "action": mapping.get("implementation"),
                        "timeline": "60 days"
                    }
                else:
                    # Generic recommendation structure
                    recommendation = {
                        "vulnerability": vulnerability,
                        "priority": "HIGH",
                        "action": f"Address {vulnerability} vulnerability",
                        "timeline": "60 days"
                    }
                
                recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_evidence_artifacts(self) -> List[str]:
        """Generate list of evidence artifacts"""
        artifacts = [
            f"scan_report_{self.scan_result.scan_id}.json",
            f"attack_details_{self.scan_result.scan_id}.json",
            f"compliance_mapping_{self.scan_result.scan_id}.json"
        ]
        
        # Add framework-specific artifacts
        if hasattr(self.scan_result, 'metadata'):
            artifacts.extend([
                f"metadata_{self.scan_result.scan_id}.json",
                f"environment_details_{self.scan_result.scan_id}.json"
            ])
        
        return artifacts
    
    def _generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary for multi-framework report"""
        total_vulnerabilities = len(self.vulnerabilities_found)
        critical_count = sum(1 for result in self.scan_result.results 
                           if result.severity == 'critical')
        
        return {
            "assessment_scope": f"LLM Security Assessment - {self.scan_result.target}",
            "vulnerabilities_identified": total_vulnerabilities,
            "critical_findings": critical_count,
            "frameworks_evaluated": len([f.value for f in ComplianceFramework]),
            "overall_compliance_posture": "NEEDS_IMPROVEMENT" if total_vulnerabilities > 0 else "COMPLIANT",
            "key_risks": self._identify_key_risks(),
            "immediate_actions_required": critical_count > 0
        }
    
    def _generate_cross_framework_analysis(self, 
                                         framework_reports: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis across multiple frameworks"""
        compliance_scores = {}
        common_gaps = set()
        framework_specific_gaps = {}
        
        for framework, report in framework_reports.items():
            compliance_scores[framework] = report.get("compliance_score", 0.0)
            gaps = set(report.get("gaps_identified", []))
            
            if not common_gaps:
                common_gaps = gaps
            else:
                common_gaps = common_gaps.intersection(gaps)
            
            framework_specific_gaps[framework] = gaps
        
        return {
            "compliance_scores": compliance_scores,
            "average_compliance_score": sum(compliance_scores.values()) / len(compliance_scores) if compliance_scores else 0.0,
            "common_gaps": list(common_gaps),
            "framework_specific_gaps": {
                framework: list(gaps - common_gaps) 
                for framework, gaps in framework_specific_gaps.items()
            },
            "highest_compliance_framework": max(compliance_scores.items(), key=lambda x: x[1])[0] if compliance_scores else None,
            "lowest_compliance_framework": min(compliance_scores.items(), key=lambda x: x[1])[0] if compliance_scores else None
        }
    
    def _generate_consolidated_recommendations(self, 
                                             framework_reports: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate consolidated recommendations across frameworks"""
        all_recommendations = []
        vulnerability_recommendations = {}
        
        # Collect all recommendations
        for framework, report in framework_reports.items():
            recommendations = report.get("recommendations", [])
            for rec in recommendations:
                vulnerability = rec.get("vulnerability", rec.get("control", "unknown"))
                if vulnerability not in vulnerability_recommendations:
                    vulnerability_recommendations[vulnerability] = []
                vulnerability_recommendations[vulnerability].append({
                    "framework": framework,
                    "recommendation": rec
                })
        
        # Consolidate by vulnerability/control
        for vulnerability, framework_recs in vulnerability_recommendations.items():
            consolidated_rec = {
                "vulnerability_or_control": vulnerability,
                "priority": "HIGH" if any(r["recommendation"].get("priority") == "HIGH" 
                                        for r in framework_recs) else "MEDIUM",
                "affected_frameworks": [r["framework"] for r in framework_recs],
                "consolidated_action": self._consolidate_actions(framework_recs),
                "timeline": min([r["recommendation"].get("timeline", "90 days") 
                               for r in framework_recs], default="60 days")
            }
            all_recommendations.append(consolidated_rec)
        
        return sorted(all_recommendations, 
                     key=lambda x: (x["priority"] != "HIGH", len(x["affected_frameworks"])))
    
    def _consolidate_actions(self, framework_recs: List[Dict[str, Any]]) -> str:
        """Consolidate actions from multiple framework recommendations"""
        actions = [r["recommendation"].get("action", "") for r in framework_recs]
        unique_actions = list(set(filter(None, actions)))
        
        if len(unique_actions) == 1:
            return unique_actions[0]
        elif len(unique_actions) > 1:
            return f"Implement comprehensive controls addressing: {'; '.join(unique_actions[:2])}"
        else:
            return "Implement appropriate security controls"
    
    def _identify_risk_factors(self, framework: str) -> List[str]:
        """Identify risk factors specific to framework"""
        risk_factors = []
        
        for vulnerability in self.vulnerabilities_found:
            if vulnerability == "prompt_injection":
                risk_factors.append("Input validation failures")
            elif vulnerability == "sensitive_information_disclosure":
                risk_factors.append("Data protection gaps")
            elif vulnerability == "model_denial_of_service":
                risk_factors.append("Availability risks")
        
        return risk_factors
    
    def _identify_key_risks(self) -> List[str]:
        """Identify key risks across all frameworks"""
        key_risks = []
        
        if "prompt_injection" in self.vulnerabilities_found:
            key_risks.append("Prompt injection vulnerabilities")
        if "sensitive_information_disclosure" in self.vulnerabilities_found:
            key_risks.append("Data privacy and confidentiality risks")
        if "model_denial_of_service" in self.vulnerabilities_found:
            key_risks.append("Service availability and reliability risks")
        
        return key_risks
    
    def _prioritize_remediation(self, framework: str) -> List[str]:
        """Prioritize remediation based on framework requirements"""
        priority_order = []
        
        # Framework-specific prioritization
        if framework == "eu_ai_act":
            high_risk_vulns = [v for v in self.vulnerabilities_found 
                             if get_framework_mapping(framework, v) and 
                             get_framework_mapping(framework, v).get("risk_category") == "high"]
            priority_order.extend(high_risk_vulns)
        
        # Add remaining vulnerabilities
        remaining = [v for v in self.vulnerabilities_found if v not in priority_order]
        priority_order.extend(remaining)
        
        return priority_order
    
    def _apply_template_formatting(self, report: Dict[str, Any], 
                                 template_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply template-specific formatting to report"""
        if template_config.get("include_technical_details", True):
            # Include full technical details
            pass
        else:
            # Remove technical details for executive reports
            report.pop("framework_mappings", None)
            report.pop("evidence_artifacts", None)
        
        if template_config.get("executive_focus", False):
            # Focus on executive summary elements
            executive_keys = ["compliance_score", "risk_assessment", "recommendations"]
            filtered_report = {k: v for k, v in report.items() if k in executive_keys or k.startswith("framework")}
            report = filtered_report
        
        return report
    
    def export_to_file(self, report: Dict[str, Any], 
                      output_path: Path,
                      format: str = "json") -> None:
        """
        Export compliance report to file.
        
        Args:
            report: Report dictionary to export
            output_path: Path to output file
            format: Export format ('json', 'yaml', 'csv')
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "json":
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
        elif format.lower() == "yaml":
            import yaml
            with open(output_path, 'w') as f:
                yaml.dump(report, f, default_flow_style=False)
        elif format.lower() == "csv":
            import csv
            # Flatten report for CSV export
            flattened = self._flatten_report_for_csv(report)
            with open(output_path, 'w', newline='') as f:
                if flattened:
                    writer = csv.DictWriter(f, fieldnames=flattened[0].keys())
                    writer.writeheader()
                    writer.writerows(flattened)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _flatten_report_for_csv(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten report structure for CSV export"""
        rows = []
        
        # Extract key metrics
        base_row = {
            "framework": report.get("framework", "multi_framework"),
            "scan_id": report.get("scan_id"),
            "target": report.get("target"),
            "assessment_date": report.get("assessment_date"),
            "compliance_score": report.get("compliance_score"),
            "vulnerabilities_found": report.get("vulnerabilities_found"),
            "overall_risk_level": report.get("risk_assessment", {}).get("overall_risk_level")
        }
        
        # Add framework-specific details if available
        if "framework_reports" in report:
            for framework, framework_report in report["framework_reports"].items():
                row = base_row.copy()
                row["framework"] = framework
                row["compliance_score"] = framework_report.get("compliance_score")
                rows.append(row)
        else:
            rows.append(base_row)
        
        return rows
    
    def generate_pci_dss_report(self, 
                              merchant_level: PCIDSSLevel = PCIDSSLevel.LEVEL_1,
                              version: PCIDSSVersion = PCIDSSVersion.V4_0,
                              include_detailed_findings: bool = True) -> Dict[str, Any]:
        """
        Generate PCI DSS specific compliance report.
        
        Args:
            merchant_level: PCI DSS merchant/service provider level
            version: PCI DSS version to use
            include_detailed_findings: Include detailed findings in report
            
        Returns:
            PCI DSS compliance report
        """
        # Convert scan result to format expected by PCI DSS framework
        scan_data = {
            "results": [
                {
                    "attack_type": self._map_attack_category_to_type(result.category),
                    "severity": result.severity.value if hasattr(result.severity, 'value') else str(result.severity),
                    "success": result.is_vulnerable,
                    "description": result.description,
                    "response": result.response_received[:1000] if result.response_received else "",
                    "timestamp": result.timestamp.isoformat() if result.timestamp else datetime.now().isoformat()
                }
                for result in self.scan_result.results
            ]
        }
        
        # Generate PCI DSS report
        pci_report = create_pci_dss_report(
            scan_results=scan_data,
            merchant_level=merchant_level,
            version=version
        )
        
        # Enhance with PromptStrike-specific context
        enhanced_report = {
            **pci_report,
            "promptstrike_metadata": {
                "scan_id": self.scan_result.scan_id,
                "target_system": self.scan_result.target,
                "scan_timestamp": self.scan_result.start_time.isoformat(),
                "total_attacks_tested": len(self.scan_result.results),
                "attack_categories_tested": list(set(
                    result.category.value if hasattr(result.category, 'value') 
                    else str(result.category)
                    for result in self.scan_result.results
                )),
                "scan_duration": self.scan_result.metadata.total_duration_seconds if self.scan_result.metadata else None
            },
            "detailed_findings": self._generate_pci_detailed_findings() if include_detailed_findings else [],
            "remediation_roadmap": self._generate_pci_remediation_roadmap(pci_report),
            "audit_evidence": self._generate_pci_audit_evidence()
        }
        
        return enhanced_report
    
    def _map_attack_category_to_type(self, attack_category) -> str:
        """Map PromptStrike attack categories to PCI DSS attack types"""
        category_str = attack_category.value if hasattr(attack_category, 'value') else str(attack_category)
        
        mapping = {
            "prompt_injection": "prompt_injection",
            "insecure_output_handling": "insecure_output_handling",
            "training_data_poisoning": "system_prompt_leakage",
            "model_denial_of_service": "model_denial_of_service",
            "supply_chain_vulnerabilities": "insecure_configuration",
            "sensitive_information_disclosure": "sensitive_data_exposure",
            "insecure_plugin_design": "insecure_configuration",
            "excessive_agency": "security_testing",
            "overreliance": "vulnerability_assessment",
            "model_theft": "system_prompt_leakage"
        }
        
        return mapping.get(category_str.lower(), "security_testing")
    
    def _generate_pci_detailed_findings(self) -> List[Dict[str, Any]]:
        """Generate detailed findings for PCI DSS report"""
        findings = []
        
        for result in self.scan_result.results:
            finding = {
                "finding_id": f"PCI-{result.category}-{len(findings)+1}",
                "attack_type": result.category.value if hasattr(result.category, 'value') else str(result.category),
                "severity": result.severity.value if hasattr(result.severity, 'value') else str(result.severity),
                "success": result.is_vulnerable,
                "description": result.description,
                "technical_details": {
                    "prompt_used": result.prompt_used[:500] if result.prompt_used else "",
                    "response_received": result.response_received[:500] if result.response_received else "",
                    "confidence_score": result.confidence_score if hasattr(result, 'confidence_score') else None,
                    "risk_score": result.risk_score if hasattr(result, 'risk_score') else None
                },
                "pci_dss_impact": self._assess_pci_impact(result),
                "cardholder_data_risk": self._assess_cardholder_data_risk(result),
                "remediation_priority": self._determine_pci_priority(result)
            }
            findings.append(finding)
        
        return findings
    
    def _assess_pci_impact(self, result) -> Dict[str, Any]:
        """Assess PCI DSS specific impact of a finding"""
        attack_category = result.category.value if hasattr(result.category, 'value') else str(result.category)
        
        impact_mapping = {
            "prompt_injection": {
                "cardholder_data_exposure_risk": "High",
                "system_compromise_risk": "High", 
                "compliance_impact": "Critical",
                "affected_requirements": ["6.1", "6.2", "11.3"]
            },
            "insecure_output_handling": {
                "cardholder_data_exposure_risk": "High",
                "system_compromise_risk": "Medium",
                "compliance_impact": "High", 
                "affected_requirements": ["6.1", "6.2"]
            },
            "sensitive_information_disclosure": {
                "cardholder_data_exposure_risk": "Critical",
                "system_compromise_risk": "Medium",
                "compliance_impact": "Critical",
                "affected_requirements": ["3.1", "3.2", "6.1"]
            },
            "model_denial_of_service": {
                "cardholder_data_exposure_risk": "Low",
                "system_compromise_risk": "High",
                "compliance_impact": "High",
                "affected_requirements": ["1.1", "1.2", "11.1"]
            }
        }
        
        return impact_mapping.get(attack_category, {
            "cardholder_data_exposure_risk": "Medium",
            "system_compromise_risk": "Medium", 
            "compliance_impact": "Medium",
            "affected_requirements": ["6.1", "11.1"]
        })
    
    def _assess_cardholder_data_risk(self, result) -> str:
        """Assess risk to cardholder data from a specific finding"""
        if result.is_vulnerable and result.severity in ['critical', 'high']:
            if 'card' in str(result.response_received).lower() or 'payment' in str(result.response_received).lower():
                return "CRITICAL"
            elif 'sensitive' in str(result.response_received).lower() or 'personal' in str(result.response_received).lower():
                return "HIGH"
            else:
                return "MEDIUM"
        elif result.is_vulnerable:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _determine_pci_priority(self, result) -> str:
        """Determine remediation priority for PCI DSS compliance"""
        severity = result.severity.value if hasattr(result.severity, 'value') else str(result.severity)
        
        if result.is_vulnerable and severity == 'critical':
            return "IMMEDIATE"
        elif result.is_vulnerable and severity == 'high':
            return "HIGH"
        elif result.is_vulnerable and severity == 'medium':
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_pci_remediation_roadmap(self, pci_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate PCI DSS remediation roadmap"""
        compliance_percentage = pci_report.get("compliance_percentage", 0)
        overall_status = pci_report.get("overall_compliance_status", "NON_COMPLIANT")
        
        if overall_status == "NON_COMPLIANT":
            timeframe = "90 days"
            phase1_duration = "30 days"
            phase2_duration = "45 days" 
            phase3_duration = "15 days"
        elif overall_status == "MOSTLY_COMPLIANT":
            timeframe = "60 days"
            phase1_duration = "20 days"
            phase2_duration = "30 days"
            phase3_duration = "10 days"
        else:
            timeframe = "30 days"
            phase1_duration = "10 days"
            phase2_duration = "15 days"
            phase3_duration = "5 days"
        
        return {
            "overall_timeframe": timeframe,
            "phases": {
                "phase_1_critical": {
                    "duration": phase1_duration,
                    "focus": "Address critical vulnerabilities affecting cardholder data",
                    "activities": [
                        "Implement secure coding practices for payment processing",
                        "Patch critical security vulnerabilities",
                        "Review and strengthen access controls"
                    ]
                },
                "phase_2_implementation": {
                    "duration": phase2_duration, 
                    "focus": "Implement missing PCI DSS controls",
                    "activities": [
                        "Deploy comprehensive security testing program",
                        "Implement network segmentation controls",
                        "Establish vulnerability management processes"
                    ]
                },
                "phase_3_validation": {
                    "duration": phase3_duration,
                    "focus": "Validate compliance and prepare for assessment",
                    "activities": [
                        "Conduct internal PCI DSS assessment",
                        "Perform penetration testing",
                        "Document compliance evidence"
                    ]
                }
            },
            "milestone_deliverables": [
                "Updated secure development lifecycle documentation",
                "Vulnerability assessment and penetration testing reports",
                "Network segmentation validation",
                "PCI DSS compliance assessment report"
            ],
            "ongoing_requirements": [
                "Quarterly vulnerability scans",
                "Annual penetration testing",
                "Continuous security monitoring",
                "Regular security awareness training"
            ]
        }
    
    def _generate_pci_audit_evidence(self) -> Dict[str, Any]:
        """Generate audit evidence for PCI DSS compliance"""
        return {
            "evidence_collection_date": datetime.now().isoformat(),
            "testing_methodology": "PromptStrike Automated Security Testing",
            "evidence_artifacts": [
                {
                    "artifact_type": "Security Test Results",
                    "description": "Automated security testing results showing system response to various attack vectors",
                    "file_reference": f"promptstrike_scan_{self.scan_result.scan_id}.json",
                    "integrity_hash": self.scan_result.compliance.audit_hash if self.scan_result.compliance else None
                },
                {
                    "artifact_type": "Vulnerability Assessment",
                    "description": "Detailed vulnerability assessment with risk ratings and remediation guidance",
                    "file_reference": f"vulnerability_assessment_{self.scan_result.scan_id}.pdf"
                },
                {
                    "artifact_type": "Compliance Mapping",
                    "description": "Mapping of identified vulnerabilities to PCI DSS requirements",
                    "file_reference": f"pci_dss_mapping_{self.scan_result.scan_id}.xlsx"
                }
            ],
            "assessor_information": {
                "tool_name": "PromptStrike",
                "tool_version": "1.0",
                "methodology_standard": "OWASP Testing Guide v4.0",
                "assessment_scope": "AI/ML system security controls"
            },
            "data_retention": {
                "retention_period": "7 years",
                "storage_location": "Secure audit repository",
                "access_controls": "Role-based access with audit logging"
            }
        }
    
    def generate_pci_dss_executive_summary(self, pci_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary for PCI DSS report"""
        compliance_percentage = pci_report.get("compliance_percentage", 0)
        overall_status = pci_report.get("overall_compliance_status", "NON_COMPLIANT")
        merchant_level = pci_report.get("merchant_level", "Level 1")
        
        return {
            "compliance_overview": {
                "current_compliance_status": overall_status,
                "compliance_percentage": f"{compliance_percentage:.1f}%",
                "merchant_level": merchant_level,
                "assessment_scope": "AI/ML systems handling payment card data"
            },
            "key_findings": {
                "total_controls_tested": pci_report.get("tested_controls", 0),
                "compliant_controls": pci_report.get("compliant_controls", 0),
                "non_compliant_controls": pci_report.get("non_compliant_controls", 0),
                "critical_findings": len([f for f in self._generate_pci_detailed_findings() 
                                        if f.get("remediation_priority") == "IMMEDIATE"]),
                "high_priority_findings": len([f for f in self._generate_pci_detailed_findings() 
                                             if f.get("remediation_priority") == "HIGH"])
            },
            "business_impact": {
                "compliance_risk": "HIGH" if compliance_percentage < 80 else "MEDIUM" if compliance_percentage < 95 else "LOW",
                "operational_impact": self._assess_operational_impact(overall_status),
                "financial_implications": self._assess_financial_implications(overall_status, merchant_level),
                "reputational_risk": "HIGH" if overall_status == "NON_COMPLIANT" else "MEDIUM"
            },
            "immediate_actions_required": pci_report.get("recommendations", [])[:3],
            "next_steps": [
                "Review detailed findings and remediation roadmap",
                "Engage qualified security assessor (QSA) if required",
                "Implement high-priority security controls",
                "Schedule follow-up assessment"
            ]
        }
    
    def _assess_operational_impact(self, compliance_status: str) -> str:
        """Assess operational impact of compliance status"""
        if compliance_status == "NON_COMPLIANT":
            return "SEVERE - Potential payment processing suspension"
        elif compliance_status == "MOSTLY_COMPLIANT":
            return "MODERATE - Increased monitoring and validation required"
        else:
            return "MINIMAL - Standard compliance maintenance"
    
    def _assess_financial_implications(self, compliance_status: str, merchant_level: str) -> str:
        """Assess financial implications of compliance status"""
        if compliance_status == "NON_COMPLIANT":
            if "Level 1" in merchant_level:
                return "CRITICAL - Potential fines up to $500K and card brand penalties"
            else:
                return "HIGH - Potential fines up to $100K and increased transaction fees"
        elif compliance_status == "MOSTLY_COMPLIANT":
            return "MODERATE - Increased assessment costs and potential transaction fees"
        else:
            return "LOW - Standard compliance costs"