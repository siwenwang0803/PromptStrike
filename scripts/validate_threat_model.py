#!/usr/bin/env python3
"""
validate_threat_model.py

Validates the threat model for consistency, DREAD scores, Jira links, and compliance.

Usage:
    python scripts/validate_threat_model.py
    python scripts/validate_threat_model.py --check-all
"""

import re
import yaml
import argparse
import pathlib
import sys
from typing import List, Dict, Tuple
from datetime import datetime


class ThreatModelValidator:
    def __init__(self, threat_model_path: pathlib.Path, mapping_path: pathlib.Path):
        self.threat_model_path = threat_model_path
        self.mapping_path = mapping_path
        self.content = ""
        self.mapping = {}
        self.errors = []
        self.warnings = []
        
    def load_files(self):
        """Load threat model and mapping files."""
        try:
            self.content = self.threat_model_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            sys.exit(f"❌ Threat model file not found: {self.threat_model_path}")
        
        try:
            self.mapping = yaml.safe_load(self.mapping_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            sys.exit(f"❌ Mapping file not found: {self.mapping_path}")
    
    def validate_dread_scores(self) -> bool:
        """Validate DREAD scores follow the formula and are within range."""
        print("🔍 Validating DREAD scores...")
        
        # Pattern to match DREAD breakdowns
        dread_pattern = r'#### DREAD Breakdown\s*\n- \*\*Damage\*\*:\s*(\d+).*?\n- \*\*Reproducibility\*\*:\s*(\d+).*?\n- \*\*Exploitability\*\*:\s*(\d+).*?\n- \*\*Affected Users\*\*:\s*(\d+).*?\n- \*\*Discoverability\*\*:\s*(\d+)'
        
        # Pattern to match final scores
        score_pattern = r'\*\*DREAD Score\*\*:\s*(\d+\.\d+)\/10'
        
        dread_matches = re.findall(dread_pattern, self.content, re.MULTILINE)
        score_matches = re.findall(score_pattern, self.content)
        
        valid_scores = 0
        for i, (d, r, e, a, d2) in enumerate(dread_matches):
            # Convert to integers
            factors = [int(d), int(r), int(e), int(a), int(d2)]
            
            # Check factor ranges
            for j, factor in enumerate(factors):
                if not 1 <= factor <= 10:
                    self.errors.append(f"DREAD factor {j+1} out of range [1-10]: {factor}")
                    continue
            
            # Calculate expected score
            expected_score = sum(factors) / 5
            
            # Find corresponding final score if available
            if i < len(score_matches):
                actual_score = float(score_matches[i])
                if abs(expected_score - actual_score) > 0.1:
                    self.errors.append(
                        f"DREAD calculation mismatch: expected {expected_score:.1f}, got {actual_score:.1f}"
                    )
                else:
                    valid_scores += 1
        
        print(f"✅ Validated {valid_scores} DREAD scores")
        return len(self.errors) == 0
    
    def validate_jira_links(self) -> bool:
        """Validate Jira links are properly formatted and consistent."""
        print("🔗 Validating Jira links...")
        
        # Find all Jira links
        jira_links = re.findall(r'\[PS-(\d+)\]\([^)]+\)', self.content)
        orphaned_refs = re.findall(r'(?<!\[)PS-(\d+)(?!\])', self.content)
        
        # Check for proper link format
        malformed_links = re.findall(r'PS-\d+(?!\]|\s|\.)', self.content)
        
        if malformed_links:
            self.warnings.append(f"Found {len(malformed_links)} potentially malformed Jira references")
        
        # Check mapping consistency
        missing_mappings = []
        for threat_id, jira_id in self.mapping.items():
            expected_link = f"[{jira_id}]"
            if expected_link not in self.content:
                missing_mappings.append(f"{threat_id} -> {jira_id}")
        
        if missing_mappings:
            self.warnings.append(f"Missing Jira links in content: {missing_mappings}")
        
        print(f"✅ Found {len(jira_links)} properly formatted Jira links")
        if orphaned_refs:
            print(f"⚠️  Found {len(orphaned_refs)} orphaned PS- references")
        
        return True
    
    def validate_risk_matrix_consistency(self) -> bool:
        """Validate risk matrix tables are consistent."""
        print("📊 Validating risk matrix consistency...")
        
        # Find risk matrix tables
        table_pattern = r'\|.*?Threat ID.*?\|.*?\n\|.*?\n((?:\|.*?\n)+)'
        tables = re.findall(table_pattern, self.content, re.MULTILINE)
        
        all_threats = set()
        duplicate_threats = set()
        
        for table in tables:
            rows = table.strip().split('\n')
            for row in rows:
                if '|' in row:
                    cols = [col.strip() for col in row.split('|')[1:-1]]  # Remove empty first/last
                    if len(cols) >= 2:
                        threat_id = cols[0].strip()
                        if threat_id and not threat_id.startswith('-'):  # Skip separator rows
                            if threat_id in all_threats:
                                duplicate_threats.add(threat_id)
                            all_threats.add(threat_id)
        
        if duplicate_threats:
            self.errors.append(f"Duplicate threats in tables: {duplicate_threats}")
        
        print(f"✅ Found {len(all_threats)} unique threats in risk matrices")
        return len(duplicate_threats) == 0
    
    def validate_due_dates(self) -> bool:
        """Validate due dates are reasonable and follow SLA."""
        print("📅 Validating due dates...")
        
        # Find due dates
        date_pattern = r'Due.*?(\d{4}-\d{2}-\d{2})'
        dates = re.findall(date_pattern, self.content)
        
        current_date = datetime.now()
        past_due = []
        
        for date_str in dates:
            try:
                due_date = datetime.strptime(date_str, '%Y-%m-%d')
                if due_date < current_date:
                    past_due.append(date_str)
            except ValueError:
                self.errors.append(f"Invalid date format: {date_str}")
        
        if past_due:
            self.warnings.append(f"Found {len(past_due)} past due dates: {past_due}")
        
        print(f"✅ Validated {len(dates)} due dates")
        return True
    
    def validate_compliance_mapping(self) -> bool:
        """Validate compliance framework mappings."""
        print("🏛️ Validating compliance mappings...")
        
        # Check for required compliance frameworks
        required_frameworks = ['NIST', 'EU AI Act', 'SOC 2']
        found_frameworks = []
        
        for framework in required_frameworks:
            if framework.lower().replace(' ', '') in self.content.lower().replace(' ', ''):
                found_frameworks.append(framework)
        
        missing_frameworks = set(required_frameworks) - set(found_frameworks)
        if missing_frameworks:
            self.warnings.append(f"Missing compliance frameworks: {missing_frameworks}")
        
        print(f"✅ Found compliance mappings for: {found_frameworks}")
        return True
    
    def validate_threat_categories(self) -> bool:
        """Validate threat categories are complete."""
        print("🏷️ Validating threat categories...")
        
        # Expected categories from feedback
        expected_llm_threats = ['LLM-1', 'LLM-2', 'LLM-3', 'LLM-4']
        expected_supply_chain = ['SC-1', 'SC-2']
        expected_stride = ['S1', 'S2', 'T1', 'T2', 'R1', 'I1', 'I2', 'D1', 'D2', 'E1', 'E2']
        
        all_expected = expected_llm_threats + expected_supply_chain + expected_stride
        
        found_threats = []
        for threat_id in all_expected:
            if threat_id in self.content:
                found_threats.append(threat_id)
        
        missing_threats = set(all_expected) - set(found_threats)
        if missing_threats:
            self.errors.append(f"Missing expected threats: {missing_threats}")
        
        print(f"✅ Found {len(found_threats)}/{len(all_expected)} expected threats")
        return len(missing_threats) == 0
    
    def run_all_validations(self) -> bool:
        """Run all validation checks."""
        self.load_files()
        
        print("🔍 Starting threat model validation...")
        print(f"📄 File: {self.threat_model_path}")
        print(f"🗂️  Mapping: {self.mapping_path}")
        print()
        
        validations = [
            self.validate_threat_categories(),
            self.validate_dread_scores(),
            self.validate_jira_links(),
            self.validate_risk_matrix_consistency(),
            self.validate_due_dates(),
            self.validate_compliance_mapping()
        ]
        
        print()
        print("="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        if self.errors:
            print("❌ ERRORS:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if not self.errors and not self.warnings:
            print("✅ All validations passed!")
        elif not self.errors:
            print("✅ All critical validations passed (warnings only)")
        else:
            print("❌ Validation failed with errors")
        
        print(f"\n📊 Results: {sum(validations)}/{len(validations)} checks passed")
        
        return len(self.errors) == 0


def main():
    parser = argparse.ArgumentParser(
        description="Validate threat model for consistency and completeness"
    )
    parser.add_argument(
        "--doc",
        type=pathlib.Path,
        default="docs/RedForge/Security/Guardrail_Threat_Model.md",
        help="Path to threat model markdown file"
    )
    parser.add_argument(
        "--map",
        type=pathlib.Path,
        default="scripts/threat_to_jira.yml",
        help="Path to threat-to-jira mapping YAML file"
    )
    parser.add_argument(
        "--check-all",
        action="store_true",
        help="Run all validation checks (default)"
    )
    
    args = parser.parse_args()
    
    validator = ThreatModelValidator(args.doc, args.map)
    success = validator.run_all_validations()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()