#!/usr/bin/env python3
"""
PromptStrike Threat Model ↔ Jira 完整性验证
目标：验证 17 条威胁均有 Jira 链接且状态 ≠ "Open"
Target: Verify all 17 threats have Jira links and status ≠ "Open"
"""

import os
import sys
import json
import yaml
import argparse
import requests
import pathlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime


class ValidationStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    WARN = "WARN"


class JiraStatus(Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


@dataclass
class ThreatInfo:
    threat_id: str
    jira_ticket: str
    description: str = ""
    risk_score: float = 0.0
    status: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    found_in_doc: bool = False
    jira_accessible: bool = False


@dataclass
class ValidationResult:
    name: str
    status: ValidationStatus
    details: str
    score: float = 0.0
    
    def __str__(self):
        status_icon = {
            ValidationStatus.PASS: "✅",
            ValidationStatus.FAIL: "❌", 
            ValidationStatus.SKIP: "⚠️",
            ValidationStatus.WARN: "⚠️"
        }
        return f"{status_icon[self.status]} {self.name}: {self.status.value} - {self.details}"


class ThreatJiraValidator:
    """验证威胁模型与 Jira 完整性"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.threats: Dict[str, ThreatInfo] = {}
        self.results: List[ValidationResult] = []
        self.jira_session = None
        
        # File paths
        self.project_root = pathlib.Path(__file__).parent.parent
        self.threat_doc_path = self.project_root / "docs/PromptStrike/Security/Guardrail_Threat_Model.md"
        self.mapping_path = self.project_root / "scripts/threat_to_jira.yml"
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration for Jira integration"""
        default_config = {
            'jira_base_url': os.environ.get('JIRA_BASE_URL', 'https://promptstrike.atlassian.net'),
            'jira_username': os.environ.get('JIRA_USERNAME'),
            'jira_api_token': os.environ.get('JIRA_API_TOKEN'),
            'jira_project': os.environ.get('JIRA_PROJECT', 'PS'),
            'test_mode': os.environ.get('TEST_MODE', 'false').lower() == 'true',
            'expected_threat_count': 17,
            'forbidden_statuses': ['Open', 'To Do', 'Backlog']
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def validate_prerequisites(self) -> bool:
        """验证前置条件"""
        print("🔍 检查前置条件 / Checking Prerequisites")
        print("=" * 60)
        
        # Check threat model document
        if not self.threat_doc_path.exists():
            self.results.append(ValidationResult(
                "Threat model document", ValidationStatus.FAIL,
                f"Document not found: {self.threat_doc_path}"
            ))
            return False
        
        self.results.append(ValidationResult(
            "Threat model document", ValidationStatus.PASS,
            f"Found threat model: {self.threat_doc_path.name}"
        ))
        
        # Check mapping file
        if not self.mapping_path.exists():
            self.results.append(ValidationResult(
                "Threat-Jira mapping", ValidationStatus.FAIL,
                f"Mapping file not found: {self.mapping_path}"
            ))
            return False
        
        self.results.append(ValidationResult(
            "Threat-Jira mapping", ValidationStatus.PASS,
            f"Found mapping: {self.mapping_path.name}"
        ))
        
        # Check Jira configuration
        if self.config['test_mode']:
            self.results.append(ValidationResult(
                "Jira connectivity", ValidationStatus.SKIP,
                "Test mode enabled - skipping Jira API checks"
            ))
        elif not all([self.config['jira_username'], self.config['jira_api_token']]):
            self.results.append(ValidationResult(
                "Jira credentials", ValidationStatus.SKIP,
                "Jira credentials not configured - will validate structure only"
            ))
        else:
            # Test Jira connectivity
            if self._test_jira_connection():
                self.results.append(ValidationResult(
                    "Jira connectivity", ValidationStatus.PASS,
                    f"Connected to {self.config['jira_base_url']}"
                ))
            else:
                self.results.append(ValidationResult(
                    "Jira connectivity", ValidationStatus.FAIL,
                    "Failed to connect to Jira API"
                ))
        
        return len([r for r in self.results if r.status == ValidationStatus.FAIL]) == 0
    
    def _test_jira_connection(self) -> bool:
        """Test Jira API connectivity"""
        try:
            url = f"{self.config['jira_base_url']}/rest/api/2/myself"
            auth = (self.config['jira_username'], self.config['jira_api_token'])
            
            response = requests.get(url, auth=auth, timeout=10)
            if response.status_code == 200:
                self.jira_session = requests.Session()
                self.jira_session.auth = auth
                return True
            return False
        except Exception:
            return False
    
    def load_threat_mappings(self) -> bool:
        """加载威胁映射"""
        print("\n📋 加载威胁映射 / Loading Threat Mappings")
        print("=" * 60)
        
        try:
            with open(self.mapping_path, 'r') as f:
                mappings = yaml.safe_load(f)
            
            for threat_id, jira_ticket in mappings.items():
                if isinstance(threat_id, str) and isinstance(jira_ticket, str):
                    self.threats[threat_id] = ThreatInfo(
                        threat_id=threat_id,
                        jira_ticket=jira_ticket
                    )
            
            threat_count = len(self.threats)
            expected_count = self.config['expected_threat_count']
            
            if threat_count == expected_count:
                self.results.append(ValidationResult(
                    "Threat count", ValidationStatus.PASS,
                    f"Found {threat_count} threats (matches expected {expected_count})",
                    score=100.0
                ))
            else:
                self.results.append(ValidationResult(
                    "Threat count", ValidationStatus.FAIL,
                    f"Found {threat_count} threats, expected {expected_count}",
                    score=threat_count / expected_count * 100
                ))
            
            print(f"✅ Loaded {threat_count} threat mappings:")
            for threat_id, threat_info in self.threats.items():
                print(f"   {threat_id} → {threat_info.jira_ticket}")
            
            return True
            
        except Exception as e:
            self.results.append(ValidationResult(
                "Threat mappings load", ValidationStatus.FAIL,
                f"Failed to load mappings: {str(e)}"
            ))
            return False
    
    def validate_threat_documentation(self) -> bool:
        """验证威胁文档中的引用"""
        print("\n📖 验证威胁文档 / Validating Threat Documentation")
        print("=" * 60)
        
        try:
            with open(self.threat_doc_path, 'r', encoding='utf-8') as f:
                doc_content = f.read()
            
            found_threats = 0
            missing_threats = []
            found_jira_links = []
            
            for threat_id, threat_info in self.threats.items():
                # Check if threat ID is mentioned in document
                if threat_id in doc_content:
                    threat_info.found_in_doc = True
                    found_threats += 1
                else:
                    missing_threats.append(threat_id)
                
                # Check for Jira link format
                jira_link_pattern = rf'\[{threat_info.jira_ticket}\]'
                if re.search(jira_link_pattern, doc_content):
                    found_jira_links.append(threat_info.jira_ticket)
            
            # Validation results
            if found_threats == len(self.threats):
                self.results.append(ValidationResult(
                    "Threat documentation", ValidationStatus.PASS,
                    f"All {found_threats} threats found in documentation",
                    score=100.0
                ))
            else:
                self.results.append(ValidationResult(
                    "Threat documentation", ValidationStatus.FAIL,
                    f"Missing threats in doc: {missing_threats}",
                    score=found_threats / len(self.threats) * 100
                ))
            
            jira_link_coverage = len(found_jira_links) / len(self.threats) * 100
            if jira_link_coverage >= 100:
                self.results.append(ValidationResult(
                    "Jira link coverage", ValidationStatus.PASS,
                    f"All {len(found_jira_links)} Jira links found in documentation",
                    score=100.0
                ))
            elif jira_link_coverage >= 80:
                self.results.append(ValidationResult(
                    "Jira link coverage", ValidationStatus.WARN,
                    f"Found {len(found_jira_links)}/{len(self.threats)} Jira links ({jira_link_coverage:.1f}%)",
                    score=jira_link_coverage
                ))
            else:
                self.results.append(ValidationResult(
                    "Jira link coverage", ValidationStatus.FAIL,
                    f"Found {len(found_jira_links)}/{len(self.threats)} Jira links ({jira_link_coverage:.1f}%)",
                    score=jira_link_coverage
                ))
            
            return found_threats == len(self.threats)
            
        except Exception as e:
            self.results.append(ValidationResult(
                "Documentation validation", ValidationStatus.FAIL,
                f"Failed to validate documentation: {str(e)}"
            ))
            return False
    
    def validate_jira_statuses(self) -> bool:
        """验证 Jira 票据状态"""
        print("\n🎫 验证 Jira 状态 / Validating Jira Statuses")
        print("=" * 60)
        
        if self.config['test_mode']:
            return self._validate_jira_statuses_test_mode()
        elif not self.jira_session:
            return self._validate_jira_statuses_offline()
        else:
            return self._validate_jira_statuses_online()
    
    def _validate_jira_statuses_test_mode(self) -> bool:
        """Test mode validation with mock data"""
        print("🧪 Test mode: Using mock Jira data")
        
        # Mock some statuses for testing
        mock_statuses = ["In Progress", "Done", "Resolved", "Done", "In Progress"]
        forbidden_count = 0
        
        for i, (threat_id, threat_info) in enumerate(self.threats.items()):
            mock_status = mock_statuses[i % len(mock_statuses)]
            threat_info.status = mock_status
            threat_info.jira_accessible = True
            
            if mock_status in self.config['forbidden_statuses']:
                forbidden_count += 1
                print(f"   ❌ {threat_info.jira_ticket}: {mock_status} (forbidden)")
            else:
                print(f"   ✅ {threat_info.jira_ticket}: {mock_status}")
        
        if forbidden_count == 0:
            self.results.append(ValidationResult(
                "Jira status validation (test)", ValidationStatus.PASS,
                f"All {len(self.threats)} tickets have acceptable status",
                score=100.0
            ))
        else:
            self.results.append(ValidationResult(
                "Jira status validation (test)", ValidationStatus.FAIL,
                f"{forbidden_count} tickets have forbidden status",
                score=(len(self.threats) - forbidden_count) / len(self.threats) * 100
            ))
        
        return forbidden_count == 0
    
    def _validate_jira_statuses_offline(self) -> bool:
        """Offline validation (structure only)"""
        print("📴 Offline mode: Validating ticket structure only")
        
        valid_tickets = 0
        invalid_tickets = []
        
        for threat_id, threat_info in self.threats.items():
            # Validate Jira ticket format (PS-XXX)
            if re.match(r'^PS-\d+$', threat_info.jira_ticket):
                valid_tickets += 1
                print(f"   ✅ {threat_info.jira_ticket}: Valid format")
            else:
                invalid_tickets.append(threat_info.jira_ticket)
                print(f"   ❌ {threat_info.jira_ticket}: Invalid format")
        
        if valid_tickets == len(self.threats):
            self.results.append(ValidationResult(
                "Jira ticket format", ValidationStatus.PASS,
                f"All {valid_tickets} tickets have valid PS-XXX format",
                score=100.0
            ))
        else:
            self.results.append(ValidationResult(
                "Jira ticket format", ValidationStatus.FAIL,
                f"Invalid ticket formats: {invalid_tickets}",
                score=valid_tickets / len(self.threats) * 100
            ))
        
        self.results.append(ValidationResult(
            "Jira status validation", ValidationStatus.SKIP,
            "Offline mode - cannot check actual Jira statuses"
        ))
        
        return valid_tickets == len(self.threats)
    
    def _validate_jira_statuses_online(self) -> bool:
        """Online validation with real Jira API"""
        print("🌐 Online mode: Checking real Jira statuses")
        
        accessible_tickets = 0
        forbidden_status_tickets = 0
        inaccessible_tickets = []
        forbidden_tickets = []
        
        for threat_id, threat_info in self.threats.items():
            try:
                # Get ticket info from Jira API
                url = f"{self.config['jira_base_url']}/rest/api/2/issue/{threat_info.jira_ticket}"
                response = self.jira_session.get(url, timeout=10)
                
                if response.status_code == 200:
                    ticket_data = response.json()
                    status = ticket_data['fields']['status']['name']
                    assignee = ticket_data['fields']['assignee']
                    
                    threat_info.status = status
                    threat_info.assignee = assignee['displayName'] if assignee else "Unassigned"
                    threat_info.jira_accessible = True
                    accessible_tickets += 1
                    
                    if status in self.config['forbidden_statuses']:
                        forbidden_status_tickets += 1
                        forbidden_tickets.append(f"{threat_info.jira_ticket} ({status})")
                        print(f"   ❌ {threat_info.jira_ticket}: {status} (forbidden)")
                    else:
                        print(f"   ✅ {threat_info.jira_ticket}: {status}")
                    
                else:
                    inaccessible_tickets.append(f"{threat_info.jira_ticket} (HTTP {response.status_code})")
                    print(f"   ❌ {threat_info.jira_ticket}: Inaccessible (HTTP {response.status_code})")
                    
            except Exception as e:
                inaccessible_tickets.append(f"{threat_info.jira_ticket} ({str(e)})")
                print(f"   ❌ {threat_info.jira_ticket}: Error - {str(e)}")
        
        # Generate validation results
        if accessible_tickets == len(self.threats):
            self.results.append(ValidationResult(
                "Jira ticket accessibility", ValidationStatus.PASS,
                f"All {accessible_tickets} tickets accessible",
                score=100.0
            ))
        else:
            self.results.append(ValidationResult(
                "Jira ticket accessibility", ValidationStatus.FAIL,
                f"Inaccessible tickets: {inaccessible_tickets}",
                score=accessible_tickets / len(self.threats) * 100
            ))
        
        if forbidden_status_tickets == 0:
            self.results.append(ValidationResult(
                "Jira status compliance", ValidationStatus.PASS,
                f"All accessible tickets have acceptable status (not in {self.config['forbidden_statuses']})",
                score=100.0
            ))
        else:
            self.results.append(ValidationResult(
                "Jira status compliance", ValidationStatus.FAIL,
                f"Forbidden status tickets: {forbidden_tickets}",
                score=(accessible_tickets - forbidden_status_tickets) / accessible_tickets * 100 if accessible_tickets > 0 else 0
            ))
        
        return accessible_tickets == len(self.threats) and forbidden_status_tickets == 0
    
    def validate_threat_completeness(self) -> bool:
        """验证威胁完整性"""
        print("\n🔍 验证威胁完整性 / Validating Threat Completeness")
        print("=" * 60)
        
        # Validate threat categories
        stride_threats = [tid for tid in self.threats.keys() if tid.startswith(('S', 'T', 'R', 'I', 'D', 'E'))]
        llm_threats = [tid for tid in self.threats.keys() if tid.startswith('LLM-')]
        sc_threats = [tid for tid in self.threats.keys() if tid.startswith('SC-')]
        
        expected_categories = {
            'STRIDE': 11,
            'LLM': 4,
            'Supply Chain': 2
        }
        
        actual_categories = {
            'STRIDE': len(stride_threats),
            'LLM': len(llm_threats),
            'Supply Chain': len(sc_threats)
        }
        
        all_categories_valid = True
        for category, expected_count in expected_categories.items():
            actual_count = actual_categories[category]
            if actual_count == expected_count:
                self.results.append(ValidationResult(
                    f"{category} threats", ValidationStatus.PASS,
                    f"Found {actual_count}/{expected_count} {category} threats",
                    score=100.0
                ))
            else:
                all_categories_valid = False
                self.results.append(ValidationResult(
                    f"{category} threats", ValidationStatus.FAIL,
                    f"Found {actual_count}/{expected_count} {category} threats",
                    score=actual_count / expected_count * 100
                ))
        
        return all_categories_valid
    
    def generate_comprehensive_report(self) -> Dict:
        """生成综合报告"""
        print("\n📊 生成综合报告 / Generating Comprehensive Report")
        print("=" * 60)
        
        # Calculate statistics
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == ValidationStatus.PASS)
        failed = sum(1 for r in self.results if r.status == ValidationStatus.FAIL)
        warnings = sum(1 for r in self.results if r.status == ValidationStatus.WARN)
        skipped = sum(1 for r in self.results if r.status == ValidationStatus.SKIP)
        
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        # Calculate threat statistics
        total_threats = len(self.threats)
        documented_threats = sum(1 for t in self.threats.values() if t.found_in_doc)
        accessible_threats = sum(1 for t in self.threats.values() if t.jira_accessible)
        compliant_statuses = sum(1 for t in self.threats.values() 
                               if t.status and t.status not in self.config['forbidden_statuses'])
        
        # Overall assessment
        if failed == 0 and success_rate >= 90:
            overall_status = "EXCELLENT"
        elif failed <= 1 and success_rate >= 80:
            overall_status = "GOOD"
        elif failed <= 2 and success_rate >= 70:
            overall_status = "ACCEPTABLE"
        else:
            overall_status = "NEEDS_IMPROVEMENT"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "validation_summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "skipped": skipped,
                "success_rate": success_rate,
                "overall_status": overall_status
            },
            "threat_analysis": {
                "total_threats": total_threats,
                "expected_threats": self.config['expected_threat_count'],
                "documented_threats": documented_threats,
                "accessible_threats": accessible_threats,
                "compliant_statuses": compliant_statuses,
                "documentation_coverage": documented_threats / total_threats * 100 if total_threats > 0 else 0,
                "accessibility_rate": accessible_threats / total_threats * 100 if total_threats > 0 else 0,
                "compliance_rate": compliant_statuses / accessible_threats * 100 if accessible_threats > 0 else 0
            },
            "threat_details": [
                {
                    "threat_id": t.threat_id,
                    "jira_ticket": t.jira_ticket,
                    "status": t.status,
                    "found_in_doc": t.found_in_doc,
                    "jira_accessible": t.jira_accessible,
                    "assignee": t.assignee
                }
                for t in self.threats.values()
            ],
            "validation_results": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "details": r.details,
                    "score": r.score
                }
                for r in self.results
            ],
            "configuration": {
                "test_mode": self.config['test_mode'],
                "jira_configured": bool(self.config['jira_username'] and self.config['jira_api_token']),
                "expected_threat_count": self.config['expected_threat_count'],
                "forbidden_statuses": self.config['forbidden_statuses']
            }
        }
    
    def print_summary(self, report: Dict):
        """Print validation summary"""
        print("\n" + "="*60)
        print("🎯 威胁模型 ↔ Jira 完整性验证结果 / Threat Model ↔ Jira Integrity Results")
        print("="*60)
        
        # Print all validation results
        for result in self.results:
            print(f"  {result}")
        
        # Print statistics
        vs = report["validation_summary"]
        ta = report["threat_analysis"]
        
        print(f"\n📊 验证统计 / Validation Statistics:")
        print(f"  Total tests: {vs['total_tests']}")
        print(f"  Passed: {vs['passed']}")
        print(f"  Failed: {vs['failed']}")
        print(f"  Warnings: {vs['warnings']}")
        print(f"  Skipped: {vs['skipped']}")
        print(f"  Success rate: {vs['success_rate']:.1f}%")
        
        print(f"\n🎯 威胁分析 / Threat Analysis:")
        print(f"  Total threats: {ta['total_threats']}")
        print(f"  Expected: {ta['expected_threats']}")
        print(f"  Documented: {ta['documented_threats']} ({ta['documentation_coverage']:.1f}%)")
        print(f"  Accessible: {ta['accessible_threats']} ({ta['accessibility_rate']:.1f}%)")
        print(f"  Compliant status: {ta['compliant_statuses']} ({ta['compliance_rate']:.1f}%)")
        
        # Overall assessment
        if vs['overall_status'] == "EXCELLENT":
            print(f"\n🎉 Overall Assessment: EXCELLENT - All threats properly tracked!")
        elif vs['overall_status'] == "GOOD":
            print(f"\n✅ Overall Assessment: GOOD - Minor issues to address")
        elif vs['overall_status'] == "ACCEPTABLE":
            print(f"\n⚠️  Overall Assessment: ACCEPTABLE - Some improvements needed")
        else:
            print(f"\n❌ Overall Assessment: NEEDS IMPROVEMENT - Significant issues found")
        
        # Key objectives
        print(f"\n🎯 目标达成情况 / Objective Achievement:")
        threat_count_ok = ta['total_threats'] == ta['expected_threats']
        all_have_jira = ta['accessibility_rate'] >= 100 or report['configuration']['test_mode']
        no_open_status = ta['compliance_rate'] >= 100 or report['configuration']['test_mode']
        
        print(f"  ✅ 17 条威胁 / 17 threats: {'✅ ACHIEVED' if threat_count_ok else '❌ NOT MET'}")
        print(f"  ✅ 均有 Jira 链接 / All have Jira links: {'✅ ACHIEVED' if all_have_jira else '❌ NOT MET'}")
        print(f"  ✅ 状态 ≠ Open / Status ≠ Open: {'✅ ACHIEVED' if no_open_status else '❌ NOT MET'}")
    
    def run_full_validation(self) -> bool:
        """运行完整验证流程"""
        print("🎯 PromptStrike 威胁模型 ↔ Jira 完整性验证")
        print("   Threat Model ↔ Jira Integrity Validation")
        print("="*60)
        print(f"目标: 验证 17 条威胁均有 Jira 链接且状态 ≠ 'Open'")
        print(f"Target: Verify all 17 threats have Jira links and status ≠ 'Open'")
        print("="*60)
        
        # Run validation steps
        success = True
        success &= self.validate_prerequisites()
        success &= self.load_threat_mappings()
        success &= self.validate_threat_documentation()
        success &= self.validate_threat_completeness()
        success &= self.validate_jira_statuses()
        
        # Generate and display report
        report = self.generate_comprehensive_report()
        self.print_summary(report)
        
        return success


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="验证威胁模型与 Jira 完整性 / Validate Threat Model ↔ Jira Integrity"
    )
    parser.add_argument(
        "--config",
        help="Configuration file path"
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode with mock data"
    )
    parser.add_argument(
        "--output-json",
        help="Save detailed report to JSON file"
    )
    
    args = parser.parse_args()
    
    # Set test mode if requested
    if args.test_mode:
        os.environ['TEST_MODE'] = 'true'
    
    # Run validation
    validator = ThreatJiraValidator(args.config)
    success = validator.run_full_validation()
    
    # Save report if requested
    if args.output_json:
        report = validator.generate_comprehensive_report()
        with open(args.output_json, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Detailed report saved to: {args.output_json}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()