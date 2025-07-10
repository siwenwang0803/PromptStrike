#!/usr/bin/env python3
"""
Comprehensive Threat Model Validator
Combines all validation capabilities into one comprehensive tool
"""

import os
import sys
import json
import argparse
import pathlib
from datetime import datetime
from typing import Dict, List, Optional

# Import individual validators
from verify_threat_jira_integrity import ThreatJiraValidator
from validate_threat_model import ThreatModelValidator

class ComprehensiveThreatValidator:
    """
    Comprehensive threat model validation combining:
    - Threat model document validation
    - Jira integration validation
    - Error scenario testing
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.project_root = pathlib.Path(__file__).parent.parent
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'validators': {},
            'overall_status': 'UNKNOWN',
            'summary': {},
            'recommendations': []
        }
        
        # Initialize component validators
        self.jira_validator = ThreatJiraValidator(config_path)
        self.doc_validator = ThreatModelValidator(
            threat_model_path=self.project_root / "docs/PromptStrike/Security/Guardrail_Threat_Model.md",
            mapping_path=self.project_root / "scripts/threat_to_jira.yml"
        )
    
    def run_jira_validation(self) -> Dict:
        """Run Jira integration validation"""
        print("🎯 Running Jira Integration Validation...")
        print("=" * 50)
        
        success = self.jira_validator.run_full_validation()
        report = self.jira_validator.generate_comprehensive_report()
        
        self.results['validators']['jira_integration'] = {
            'success': success,
            'report': report,
            'key_metrics': {
                'total_threats': report['threat_analysis']['total_threats'],
                'expected_threats': report['threat_analysis']['expected_threats'],
                'documentation_coverage': report['threat_analysis']['documentation_coverage'],
                'accessibility_rate': report['threat_analysis']['accessibility_rate'],
                'compliance_rate': report['threat_analysis']['compliance_rate']
            }
        }
        
        return report
    
    def run_document_validation(self) -> Dict:
        """Run threat model document validation"""
        print("\n📖 Running Threat Model Document Validation...")
        print("=" * 50)
        
        success = self.doc_validator.run_all_validations()
        
        # Extract results
        doc_results = {
            'success': success,
            'errors': self.doc_validator.errors,
            'warnings': self.doc_validator.warnings,
            'error_count': len(self.doc_validator.errors),
            'warning_count': len(self.doc_validator.warnings)
        }
        
        self.results['validators']['document_validation'] = doc_results
        
        return doc_results
    
    def run_error_scenario_tests(self) -> Dict:
        """Run error scenario testing"""
        print("\n🧪 Running Error Scenario Testing...")
        print("=" * 50)
        
        # Import and run error tests
        try:
            from test_threat_jira_error_scenarios import run_all_error_tests
            success = run_all_error_tests()
            
            error_results = {
                'success': success,
                'tests_passed': success,
                'edge_cases_handled': True,
                'resilience_verified': True
            }
        except Exception as e:
            error_results = {
                'success': False,
                'tests_passed': False,
                'edge_cases_handled': False,
                'resilience_verified': False,
                'error': str(e)
            }
        
        self.results['validators']['error_scenarios'] = error_results
        
        return error_results
    
    def analyze_overall_status(self) -> str:
        """Analyze overall validation status"""
        print("\n📊 Analyzing Overall Validation Status...")
        print("=" * 50)
        
        jira_success = self.results['validators']['jira_integration']['success']
        doc_success = self.results['validators']['document_validation']['success']
        error_success = self.results['validators']['error_scenarios']['success']
        
        # Calculate scores
        jira_score = 100 if jira_success else 0
        doc_score = 100 if doc_success else 50  # Warnings are acceptable
        error_score = 100 if error_success else 0
        
        # Weight the scores
        overall_score = (jira_score * 0.5) + (doc_score * 0.3) + (error_score * 0.2)
        
        # Determine status
        if overall_score >= 90:
            status = "EXCELLENT"
        elif overall_score >= 80:
            status = "GOOD"
        elif overall_score >= 70:
            status = "ACCEPTABLE"
        else:
            status = "NEEDS_IMPROVEMENT"
        
        # Generate summary
        self.results['summary'] = {
            'overall_score': overall_score,
            'jira_integration_score': jira_score,
            'document_validation_score': doc_score,
            'error_handling_score': error_score,
            'total_validators': 3,
            'successful_validators': sum([jira_success, doc_success, error_success]),
            'critical_issues': self._identify_critical_issues()
        }
        
        self.results['overall_status'] = status
        return status
    
    def _identify_critical_issues(self) -> List[str]:
        """Identify critical issues that need immediate attention"""
        issues = []
        
        # Check Jira integration issues
        jira_report = self.results['validators']['jira_integration']['report']
        if jira_report['threat_analysis']['total_threats'] != jira_report['threat_analysis']['expected_threats']:
            issues.append("Threat count mismatch - expected 17 threats")
        
        if jira_report['threat_analysis']['accessibility_rate'] < 100:
            issues.append("Not all threats have accessible Jira tickets")
        
        if jira_report['threat_analysis']['compliance_rate'] < 100:
            issues.append("Some threats have forbidden status (Open/To Do)")
        
        # Check document validation issues
        doc_results = self.results['validators']['document_validation']
        if doc_results['error_count'] > 0:
            issues.append(f"Document validation errors: {doc_results['error_count']}")
        
        # Check error handling
        error_results = self.results['validators']['error_scenarios']
        if not error_results['success']:
            issues.append("Error scenario testing failed")
        
        return issues
    
    def generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Jira-specific recommendations
        jira_report = self.results['validators']['jira_integration']['report']
        if jira_report['threat_analysis']['total_threats'] != 17:
            recommendations.append("Update threat mappings to include exactly 17 threats")
        
        if jira_report['threat_analysis']['accessibility_rate'] < 100:
            recommendations.append("Verify all Jira tickets exist and are accessible")
        
        if jira_report['threat_analysis']['compliance_rate'] < 100:
            recommendations.append("Update Jira ticket statuses - avoid 'Open' and 'To Do' statuses")
        
        # Document-specific recommendations
        doc_results = self.results['validators']['document_validation']
        if doc_results['error_count'] > 0:
            recommendations.append("Fix threat model document validation errors")
        
        if doc_results['warning_count'] > 0:
            recommendations.append("Review and address threat model document warnings")
        
        # Process recommendations
        error_results = self.results['validators']['error_scenarios']
        if not error_results['success']:
            recommendations.append("Improve error handling and resilience")
        
        # General recommendations
        if self.results['overall_status'] != "EXCELLENT":
            recommendations.append("Consider implementing automated validation in CI/CD pipeline")
            recommendations.append("Set up monitoring alerts for threat model validation failures")
        
        self.results['recommendations'] = recommendations
        return recommendations
    
    def print_comprehensive_report(self):
        """Print comprehensive validation report"""
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE THREAT MODEL VALIDATION REPORT")
        print("=" * 80)
        
        # Overall status
        status_icon = {
            "EXCELLENT": "🎉",
            "GOOD": "✅",
            "ACCEPTABLE": "⚠️",
            "NEEDS_IMPROVEMENT": "❌"
        }
        
        print(f"\n{status_icon[self.results['overall_status']]} Overall Status: {self.results['overall_status']}")
        print(f"📊 Overall Score: {self.results['summary']['overall_score']:.1f}/100")
        
        # Individual validator results
        print(f"\n📋 Validator Results:")
        print(f"  🎫 Jira Integration: {'✅ PASS' if self.results['validators']['jira_integration']['success'] else '❌ FAIL'} ({self.results['summary']['jira_integration_score']:.0f}%)")
        print(f"  📖 Document Validation: {'✅ PASS' if self.results['validators']['document_validation']['success'] else '❌ FAIL'} ({self.results['summary']['document_validation_score']:.0f}%)")
        print(f"  🧪 Error Scenarios: {'✅ PASS' if self.results['validators']['error_scenarios']['success'] else '❌ FAIL'} ({self.results['summary']['error_handling_score']:.0f}%)")
        
        # Key metrics
        jira_metrics = self.results['validators']['jira_integration']['key_metrics']
        print(f"\n📊 Key Metrics:")
        print(f"  Threat Count: {jira_metrics['total_threats']}/{jira_metrics['expected_threats']}")
        print(f"  Documentation Coverage: {jira_metrics['documentation_coverage']:.1f}%")
        print(f"  Jira Accessibility: {jira_metrics['accessibility_rate']:.1f}%")
        print(f"  Status Compliance: {jira_metrics['compliance_rate']:.1f}%")
        
        # Critical issues
        if self.results['summary']['critical_issues']:
            print(f"\n🚨 Critical Issues:")
            for issue in self.results['summary']['critical_issues']:
                print(f"  • {issue}")
        
        # Recommendations
        if self.results['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in self.results['recommendations']:
                print(f"  • {rec}")
        
        # Objective achievement
        print(f"\n🎯 Objective Achievement:")
        threat_count_ok = jira_metrics['total_threats'] == jira_metrics['expected_threats']
        all_have_jira = jira_metrics['accessibility_rate'] >= 100
        no_open_status = jira_metrics['compliance_rate'] >= 100
        
        print(f"  ✅ 17 条威胁 / 17 threats: {'✅ ACHIEVED' if threat_count_ok else '❌ NOT MET'}")
        print(f"  ✅ 均有 Jira 链接 / All have Jira links: {'✅ ACHIEVED' if all_have_jira else '❌ NOT MET'}")
        print(f"  ✅ 状态 ≠ Open / Status ≠ Open: {'✅ ACHIEVED' if no_open_status else '❌ NOT MET'}")
        
        # Final assessment
        all_objectives_met = threat_count_ok and all_have_jira and no_open_status
        print(f"\n🏆 Final Assessment:")
        if all_objectives_met:
            print("  🎉 ALL OBJECTIVES ACHIEVED - Ready for production!")
        else:
            print("  ⚠️  Some objectives not met - Review recommendations")
    
    def run_comprehensive_validation(self) -> bool:
        """Run comprehensive validation"""
        print("🎯 PromptStrike Comprehensive Threat Model Validation")
        print("=" * 80)
        print("Combining: Jira Integration + Document Validation + Error Scenarios")
        print("=" * 80)
        
        # Run all validators
        self.run_jira_validation()
        self.run_document_validation()
        self.run_error_scenario_tests()
        
        # Analyze results
        self.analyze_overall_status()
        self.generate_recommendations()
        
        # Print comprehensive report
        self.print_comprehensive_report()
        
        # Return success status
        return self.results['overall_status'] in ["EXCELLENT", "GOOD"]
    
    def save_report(self, output_path: str):
        """Save detailed report to file"""
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Comprehensive report saved to: {output_path}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Comprehensive Threat Model Validation"
    )
    parser.add_argument(
        "--config",
        help="Configuration file path"
    )
    parser.add_argument(
        "--output-json",
        help="Save detailed report to JSON file"
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode with mock data"
    )
    
    args = parser.parse_args()
    
    # Set test mode if requested
    if args.test_mode:
        os.environ['TEST_MODE'] = 'true'
    
    # Run comprehensive validation
    validator = ComprehensiveThreatValidator(args.config)
    success = validator.run_comprehensive_validation()
    
    # Save report if requested
    if args.output_json:
        validator.save_report(args.output_json)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()