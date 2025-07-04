"""
Test suite for PCI DSS compliance framework
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import json

from promptstrike.compliance.pci_dss_framework import (
    PCIDSSFramework,
    PCIDSSLevel,
    PCIDSSVersion,
    create_pci_dss_report,
    get_pci_dss_requirements_summary
)
from promptstrike.compliance.report_generator import ComplianceReportGenerator
from promptstrike.models.scan_result import ScanResult, AttackResult, SeverityLevel, AttackCategory


@pytest.fixture
def mock_scan_result():
    """Create mock scan result for testing"""
    attack_results = [
        AttackResult(
            attack_id="test_prompt_injection",
            category=AttackCategory.PROMPT_INJECTION,
            severity=SeverityLevel.HIGH,
            is_vulnerable=True,
            description="Successful prompt injection attack detected",
            prompt_used="Test injection prompt",
            response_received="Sensitive information leaked: card number 4111-1111-1111-1111",
            confidence_score=0.85,
            risk_score=8.5,
            attack_vector="SQL injection via prompt",
            response_time_ms=150,
            timestamp=datetime.now()
        ),
        AttackResult(
            attack_id="test_output_handling",
            category=AttackCategory.INSECURE_OUTPUT,
            severity=SeverityLevel.MEDIUM,
            is_vulnerable=True,
            description="Insecure output handling vulnerability",
            prompt_used="Test output handling",
            response_received="System information exposed",
            confidence_score=0.7,
            risk_score=6.0,
            attack_vector="Output manipulation",
            response_time_ms=120,
            timestamp=datetime.now()
        ),
        AttackResult(
            attack_id="test_secure_system",
            category=AttackCategory.MODEL_DOS,
            severity=SeverityLevel.LOW,
            is_vulnerable=False,
            description="System handled DoS attempt appropriately",
            prompt_used="DoS test prompt",
            response_received="Request rate limited",
            confidence_score=0.3,
            risk_score=2.0,
            attack_vector="Rate limiting test",
            response_time_ms=200,
            timestamp=datetime.now()
        )
    ]
    
    from promptstrike.models.scan_result import ScanMetadata, ComplianceReport
    
    # Create proper metadata and compliance objects
    scan_metadata = ScanMetadata(
        max_requests=100,
        timeout_seconds=30,
        attack_pack_version="1.0.0",
        total_attacks=len(attack_results),
        successful_attacks=2,
        failed_attacks=1,
        vulnerabilities_found=2,
        total_duration_seconds=300.0,
        avg_response_time_ms=156.7,
        total_tokens_used=1200,
        total_cost_usd=0.05,
        cli_version="1.0.0",
        python_version="3.13.5",
        platform="darwin"
    )
    
    compliance_report = ComplianceReport(
        audit_hash="test_hash_12345",
        compliance_score=0.75,
        risk_assessment={"overall_risk": "medium"}
    )
    
    start_time = datetime.now()
    end_time = start_time
    
    return ScanResult(
        scan_id="test_scan_pci_001",
        target="https://payment-api.example.com",
        attack_pack="owasp_llm_top_10",
        start_time=start_time,
        end_time=end_time,
        results=attack_results,
        metadata=scan_metadata,
        compliance=compliance_report,
        overall_risk_score=6.5,
        security_posture="fair"
    )


class TestPCIDSSFramework:
    """Test PCI DSS framework functionality"""
    
    def test_framework_initialization(self):
        """Test PCI DSS framework initialization"""
        framework = PCIDSSFramework(
            version=PCIDSSVersion.V4_0,
            merchant_level=PCIDSSLevel.LEVEL_1
        )
        
        assert framework.version == PCIDSSVersion.V4_0
        assert framework.merchant_level == PCIDSSLevel.LEVEL_1
        assert framework.framework_name == "PCI DSS 4.0"
        assert len(framework.controls) > 0
    
    def test_pci_dss_controls_loading(self):
        """Test loading of PCI DSS controls"""
        framework = PCIDSSFramework()
        
        # Check that key controls are loaded
        assert "6.1" in framework.controls  # Secure development
        assert "6.2" in framework.controls  # Custom software security
        assert "11.1" in framework.controls  # Security testing
        assert "11.3" in framework.controls  # Penetration testing
        
        # Check control structure
        control_6_1 = framework.controls["6.1"]
        assert control_6_1.requirement.value == "6"
        assert control_6_1.sub_requirement == "1"
        assert "secure" in control_6_1.title.lower()
        assert len(control_6_1.testing_procedures) > 0
    
    def test_attack_to_pci_mapping(self):
        """Test mapping of attack types to PCI DSS controls"""
        framework = PCIDSSFramework()
        mappings = framework._get_attack_to_pci_mappings()
        
        # Check key mappings exist
        assert "prompt_injection" in mappings
        assert "sql_injection" in mappings
        assert "insecure_output_handling" in mappings
        assert "sensitive_data_exposure" in mappings
        
        # Check mappings point to valid controls
        for attack_type, control_ids in mappings.items():
            for control_id in control_ids:
                assert control_id in framework.controls
    
    def test_promptstrike_findings_mapping(self, mock_scan_result):
        """Test mapping PromptStrike findings to PCI DSS controls"""
        framework = PCIDSSFramework()
        
        # Convert scan result to expected format
        scan_data = {
            "attack_results": [
                {
                    "attack_type": "prompt_injection",
                    "severity": "HIGH",
                    "success": True,
                    "description": "Test attack",
                    "response": "Sensitive data exposed"
                }
            ]
        }
        
        mappings = framework.map_promptstrike_findings(scan_data)
        
        assert len(mappings) > 0
        
        # Check mapping structure
        mapping = mappings[0]
        assert hasattr(mapping, 'control_id')
        assert hasattr(mapping, 'status')
        assert hasattr(mapping, 'severity')
        assert mapping.status in ["COMPLIANT", "NON_COMPLIANT"]
    
    def test_compliance_report_generation(self, mock_scan_result):
        """Test PCI DSS compliance report generation"""
        framework = PCIDSSFramework()
        
        scan_data = {
            "attack_results": [
                {
                    "attack_type": "prompt_injection",
                    "severity": "HIGH", 
                    "success": True,
                    "description": "Injection attack succeeded",
                    "response": "Card data: 4111-1111-1111-1111"
                },
                {
                    "attack_type": "insecure_output_handling",
                    "severity": "MEDIUM",
                    "success": True,
                    "description": "Output handling issue",
                    "response": "System info exposed"
                }
            ]
        }
        
        mappings = framework.map_promptstrike_findings(scan_data)
        report = framework.generate_compliance_report(mappings)
        
        # Check report structure
        assert "framework" in report
        assert "merchant_level" in report
        assert "assessment_date" in report
        assert "overall_compliance_status" in report
        assert "compliance_percentage" in report
        assert "findings_by_requirement" in report
        assert "executive_summary" in report
        assert "recommendations" in report
        
        # Check compliance calculation
        assert isinstance(report["compliance_percentage"], (int, float))
        assert 0 <= report["compliance_percentage"] <= 100
        assert report["overall_compliance_status"] in ["COMPLIANT", "MOSTLY_COMPLIANT", "NON_COMPLIANT"]


class TestPCIDSSReportGenerator:
    """Test PCI DSS report generation through ComplianceReportGenerator"""
    
    def test_pci_dss_report_generation(self, mock_scan_result):
        """Test PCI DSS report generation"""
        generator = ComplianceReportGenerator(mock_scan_result)
        
        report = generator.generate_pci_dss_report(
            merchant_level=PCIDSSLevel.LEVEL_1,
            version=PCIDSSVersion.V4_0
        )
        
        # Check report structure
        assert "framework" in report
        assert "merchant_level" in report
        assert "promptstrike_metadata" in report
        assert "detailed_findings" in report
        assert "remediation_roadmap" in report
        assert "audit_evidence" in report
        
        # Check PromptStrike metadata
        metadata = report["promptstrike_metadata"]
        assert metadata["scan_id"] == mock_scan_result.scan_id
        assert metadata["target_system"] == mock_scan_result.target
        assert len(metadata["attack_categories_tested"]) > 0
    
    def test_pci_detailed_findings(self, mock_scan_result):
        """Test generation of detailed PCI DSS findings"""
        generator = ComplianceReportGenerator(mock_scan_result)
        findings = generator._generate_pci_detailed_findings()
        
        assert len(findings) == len(mock_scan_result.results)
        
        # Check finding structure
        finding = findings[0]
        assert "finding_id" in finding
        assert "attack_type" in finding
        assert "severity" in finding
        assert "pci_dss_impact" in finding
        assert "cardholder_data_risk" in finding
        assert "remediation_priority" in finding
        assert "technical_details" in finding
        
        # Check PCI DSS impact assessment
        impact = finding["pci_dss_impact"]
        assert "cardholder_data_exposure_risk" in impact
        assert "system_compromise_risk" in impact
        assert "compliance_impact" in impact
        assert "affected_requirements" in impact
    
    def test_cardholder_data_risk_assessment(self, mock_scan_result):
        """Test cardholder data risk assessment"""
        generator = ComplianceReportGenerator(mock_scan_result)
        
        # Test high-risk attack with card data in response
        high_risk_result = mock_scan_result.results[0]  # Contains card number
        risk = generator._assess_cardholder_data_risk(high_risk_result)
        assert risk == "CRITICAL"
        
        # Test medium-risk attack
        medium_risk_result = mock_scan_result.results[1]  # System info only
        risk = generator._assess_cardholder_data_risk(medium_risk_result)
        assert risk == "MEDIUM"
        
        # Test low-risk (unsuccessful attack)
        low_risk_result = mock_scan_result.results[2]  # Failed attack
        risk = generator._assess_cardholder_data_risk(low_risk_result)
        assert risk == "LOW"
    
    def test_pci_remediation_roadmap(self, mock_scan_result):
        """Test PCI DSS remediation roadmap generation"""
        generator = ComplianceReportGenerator(mock_scan_result)
        
        # Mock PCI report with non-compliant status
        mock_pci_report = {
            "compliance_percentage": 65.0,
            "overall_compliance_status": "NON_COMPLIANT"
        }
        
        roadmap = generator._generate_pci_remediation_roadmap(mock_pci_report)
        
        assert "overall_timeframe" in roadmap
        assert "phases" in roadmap
        assert "milestone_deliverables" in roadmap
        assert "ongoing_requirements" in roadmap
        
        # Check phases
        phases = roadmap["phases"]
        assert "phase_1_critical" in phases
        assert "phase_2_implementation" in phases
        assert "phase_3_validation" in phases
        
        # Check phase structure
        phase1 = phases["phase_1_critical"]
        assert "duration" in phase1
        assert "focus" in phase1
        assert "activities" in phase1
        assert len(phase1["activities"]) > 0
    
    def test_pci_audit_evidence(self, mock_scan_result):
        """Test PCI DSS audit evidence generation"""
        generator = ComplianceReportGenerator(mock_scan_result)
        evidence = generator._generate_pci_audit_evidence()
        
        assert "evidence_collection_date" in evidence
        assert "testing_methodology" in evidence
        assert "evidence_artifacts" in evidence
        assert "assessor_information" in evidence
        assert "data_retention" in evidence
        
        # Check evidence artifacts
        artifacts = evidence["evidence_artifacts"]
        assert len(artifacts) > 0
        
        artifact = artifacts[0]
        assert "artifact_type" in artifact
        assert "description" in artifact
        assert "file_reference" in artifact
    
    def test_pci_executive_summary(self, mock_scan_result):
        """Test PCI DSS executive summary generation"""
        generator = ComplianceReportGenerator(mock_scan_result)
        
        mock_pci_report = {
            "compliance_percentage": 75.0,
            "overall_compliance_status": "MOSTLY_COMPLIANT",
            "merchant_level": "Level 1",
            "tested_controls": 8,
            "compliant_controls": 6,
            "non_compliant_controls": 2,
            "recommendations": ["Implement secure coding", "Conduct pen testing"]
        }
        
        summary = generator.generate_pci_dss_executive_summary(mock_pci_report)
        
        assert "compliance_overview" in summary
        assert "key_findings" in summary
        assert "business_impact" in summary
        assert "immediate_actions_required" in summary
        assert "next_steps" in summary
        
        # Check compliance overview
        overview = summary["compliance_overview"]
        assert overview["current_compliance_status"] == "MOSTLY_COMPLIANT"
        assert "75.0%" in overview["compliance_percentage"]
        assert overview["merchant_level"] == "Level 1"
        
        # Check business impact
        impact = summary["business_impact"]
        assert impact["compliance_risk"] in ["HIGH", "MEDIUM", "LOW"]
        assert impact["operational_impact"] is not None
        assert impact["financial_implications"] is not None


class TestPCIDSSConvenienceFunctions:
    """Test PCI DSS convenience functions"""
    
    def test_create_pci_dss_report(self):
        """Test create_pci_dss_report function"""
        scan_data = {
            "attack_results": [
                {
                    "attack_type": "prompt_injection",
                    "severity": "HIGH",
                    "success": True,
                    "description": "Test attack",
                    "response": "Data leaked"
                }
            ]
        }
        
        report = create_pci_dss_report(
            scan_results=scan_data,
            merchant_level=PCIDSSLevel.LEVEL_2,
            version=PCIDSSVersion.V4_0
        )
        
        assert "framework" in report
        assert "merchant_level" in report
        assert report["merchant_level"] == "Level 2"
        assert "PCI DSS 4.0" in report["framework"]
    
    def test_get_pci_dss_requirements_summary(self):
        """Test PCI DSS requirements summary"""
        summary = get_pci_dss_requirements_summary()
        
        assert "requirements" in summary
        assert "merchant_levels" in summary
        assert "compliance_validation" in summary
        
        # Check requirements
        requirements = summary["requirements"]
        assert "1" in requirements  # Network security
        assert "6" in requirements  # Secure development
        assert "11" in requirements  # Security testing
        
        # Check requirement structure
        req1 = requirements["1"]
        assert "title" in req1
        assert "description" in req1
        assert "key_controls" in req1
        
        # Check merchant levels
        levels = summary["merchant_levels"]
        assert "Level 1" in levels
        assert "Level 4" in levels
        assert "6 million" in levels["Level 1"]


class TestPCIDSSMerchantLevels:
    """Test PCI DSS merchant level specific functionality"""
    
    @pytest.mark.parametrize("merchant_level,expected_validation", [
        (PCIDSSLevel.LEVEL_1, "Annual Report on Compliance (ROC) by QSA"),
        (PCIDSSLevel.LEVEL_4, "Annual Self-Assessment Questionnaire (SAQ)")
    ])
    def test_merchant_level_validation_requirements(self, merchant_level, expected_validation):
        """Test validation requirements for different merchant levels"""
        summary = get_pci_dss_requirements_summary()
        validation = summary["compliance_validation"]
        
        level_name = merchant_level.value
        assert level_name in validation
        assert expected_validation in validation[level_name]
    
    def test_financial_implications_by_level(self, mock_scan_result):
        """Test financial implications vary by merchant level"""
        generator = ComplianceReportGenerator(mock_scan_result)
        
        # Test Level 1 implications
        level1_implications = generator._assess_financial_implications("NON_COMPLIANT", "Level 1")
        assert "$500K" in level1_implications
        
        # Test Level 4 implications  
        level4_implications = generator._assess_financial_implications("NON_COMPLIANT", "Level 4")
        assert "$100K" in level4_implications
        
        # Level 1 should have higher financial risk
        assert "CRITICAL" in level1_implications
        assert "HIGH" in level4_implications


class TestPCIDSSIntegration:
    """Test PCI DSS integration with PromptStrike"""
    
    def test_attack_category_mapping(self, mock_scan_result):
        """Test mapping of PromptStrike attack categories to PCI DSS types"""
        generator = ComplianceReportGenerator(mock_scan_result)
        
        # Test all OWASP LLM Top 10 categories
        test_mappings = {
            "prompt_injection": "prompt_injection",
            "insecure_output_handling": "insecure_output_handling", 
            "training_data_poisoning": "system_prompt_leakage",
            "model_denial_of_service": "model_denial_of_service",
            "supply_chain_vulnerabilities": "insecure_configuration",
            "sensitive_information_disclosure": "sensitive_data_exposure"
        }
        
        for category, expected_type in test_mappings.items():
            # Create mock attack category
            mock_category = Mock()
            mock_category.value = category
            
            result = generator._map_attack_category_to_type(mock_category)
            assert result == expected_type
    
    def test_full_report_generation_workflow(self, mock_scan_result):
        """Test complete PCI DSS report generation workflow"""
        generator = ComplianceReportGenerator(mock_scan_result)
        
        # Generate complete PCI DSS report
        report = generator.generate_pci_dss_report(
            merchant_level=PCIDSSLevel.LEVEL_1,
            version=PCIDSSVersion.V4_0,
            include_detailed_findings=True
        )
        
        # Verify all sections are present
        required_sections = [
            "framework", "merchant_level", "assessment_date",
            "overall_compliance_status", "compliance_percentage",
            "promptstrike_metadata", "detailed_findings",
            "remediation_roadmap", "audit_evidence"
        ]
        
        for section in required_sections:
            assert section in report, f"Missing required section: {section}"
        
        # Verify data consistency
        metadata = report["promptstrike_metadata"]
        assert metadata["scan_id"] == mock_scan_result.scan_id
        assert len(metadata["attack_categories_tested"]) > 0
        
        # Verify compliance calculation is reasonable
        compliance_pct = report["compliance_percentage"]
        assert isinstance(compliance_pct, (int, float))
        assert 0 <= compliance_pct <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])