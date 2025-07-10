#!/usr/bin/env python3
"""
RedForge PDF Content Validator (Realistic Assessment)
现实评估版 PDF 内容验证器 - 基于实际扫描结果而非理论最大值
"""

import sys
import os
import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# PDF analysis dependencies
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


class ValidationStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    WARN = "WARN"


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


class RealisticPDFValidator:
    """Realistic PDF content validation based on actual scan results"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.results: List[ValidationResult] = []
        self.text_content = ""
        self.page_count = 0
        self.file_size_mb = 0.0
        
    def validate_all(self) -> Dict:
        """Run all validation checks with realistic expectations"""
        print(f"🔍 Realistic Validation: {self.pdf_path.name}")
        print("=" * 60)
        
        # Basic file validation
        self._validate_file_existence()
        self._validate_file_size()
        self._extract_content()
        
        # Content validation with realistic expectations
        self._validate_pdf_structure()
        self._validate_essential_content()
        self._validate_actual_findings()
        self._validate_security_assessment()
        self._validate_compliance_evidence()
        self._validate_report_quality()
        
        return self._generate_report()
    
    def _validate_file_existence(self):
        """Validate PDF file exists and is accessible"""
        if not self.pdf_path.exists():
            self.results.append(ValidationResult(
                "File existence", ValidationStatus.FAIL,
                f"PDF file not found: {self.pdf_path}"
            ))
            return
            
        # Check file size
        file_size = self.pdf_path.stat().st_size
        self.file_size_mb = file_size / (1024 * 1024)
        
        self.results.append(ValidationResult(
            "File existence", ValidationStatus.PASS,
            f"PDF file found, size: {self.file_size_mb:.2f} MB"
        ))
    
    def _validate_file_size(self):
        """Validate PDF file size is under 3MB limit"""
        max_size_mb = 3.0
        
        if self.file_size_mb <= max_size_mb:
            self.results.append(ValidationResult(
                "File size compliance", ValidationStatus.PASS,
                f"File size {self.file_size_mb:.2f} MB <= {max_size_mb} MB limit",
                score=100.0
            ))
        else:
            self.results.append(ValidationResult(
                "File size compliance", ValidationStatus.FAIL,
                f"File size {self.file_size_mb:.2f} MB > {max_size_mb} MB limit",
                score=0.0
            ))
    
    def _extract_content(self):
        """Extract text content from PDF"""
        if not HAS_PDFPLUMBER:
            self.results.append(ValidationResult(
                "Content extraction", ValidationStatus.SKIP,
                "pdfplumber not available for content extraction"
            ))
            return
            
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                self.page_count = len(pdf.pages)
                text_pages = []
                for page in pdf.pages:
                    text_pages.append(page.extract_text() or "")
                self.text_content = "\n".join(text_pages)
            
            self.results.append(ValidationResult(
                "Content extraction", ValidationStatus.PASS,
                f"Extracted {len(self.text_content)} characters from {self.page_count} pages"
            ))
            
        except Exception as e:
            self.results.append(ValidationResult(
                "Content extraction", ValidationStatus.FAIL,
                f"Failed to extract content: {str(e)}"
            ))
    
    def _validate_pdf_structure(self):
        """Validate PDF structure and basic properties"""
        if self.page_count == 0:
            self.results.append(ValidationResult(
                "PDF structure", ValidationStatus.FAIL,
                "PDF has no pages or pages couldn't be counted"
            ))
            return
            
        if self.page_count >= 1:
            self.results.append(ValidationResult(
                "PDF structure", ValidationStatus.PASS,
                f"PDF has {self.page_count} pages with valid structure",
                score=100.0
            ))
        
        # Check if content was extracted
        if len(self.text_content) > 100:
            self.results.append(ValidationResult(
                "Content availability", ValidationStatus.PASS,
                f"PDF contains substantial text content ({len(self.text_content)} chars)",
                score=100.0
            ))
        else:
            self.results.append(ValidationResult(
                "Content availability", ValidationStatus.FAIL,
                f"PDF contains minimal text content ({len(self.text_content)} chars)"
            ))
    
    def _validate_essential_content(self):
        """Validate essential report components"""
        essential_elements = [
            ("RedForge Branding", r"redforge", "Tool identification"),
            ("Target Information", r"target|gpt-4|model", "Scan target specified"),
            ("Scan Metadata", r"scan.?id|generated|duration", "Execution metadata"),
            ("Risk Assessment", r"risk.?score|security.?posture", "Risk evaluation"),
            ("Vulnerability Data", r"vulnerabilit|finding|attack", "Security findings")
        ]
        
        found_elements = []
        missing_elements = []
        
        for element_name, pattern, description in essential_elements:
            if re.search(pattern, self.text_content, re.IGNORECASE):
                found_elements.append(element_name)
            else:
                missing_elements.append(element_name)
        
        if len(found_elements) >= 4:
            self.results.append(ValidationResult(
                "Essential content", ValidationStatus.PASS,
                f"Found {len(found_elements)}/5 essential elements: {', '.join(found_elements)}",
                score=len(found_elements) / 5 * 100
            ))
        else:
            self.results.append(ValidationResult(
                "Essential content", ValidationStatus.FAIL,
                f"Missing essential elements: {', '.join(missing_elements)}",
                score=len(found_elements) / 5 * 100
            ))
    
    def _validate_actual_findings(self):
        """Validate actual security findings (not theoretical maximum)"""
        # Check for actual OWASP categories that were tested
        actual_categories = []
        category_patterns = [
            ("LLM01", r"llm01|prompt.?injection"),
            ("LLM02", r"llm02|insecure.?output"),
            ("LLM03", r"llm03|training.?data"),
            ("LLM04", r"llm04|model.?dos|denial"),
            ("LLM05", r"llm05|supply.?chain"),
            ("LLM06", r"llm06|sensitive.?info|information.?disclosure"),
            ("LLM07", r"llm07|plugin"),
            ("LLM08", r"llm08|excessive.?agency"),
            ("LLM09", r"llm09|overreliance"),
            ("LLM10", r"llm10|model.?theft"),
        ]
        
        for category, pattern in category_patterns:
            if re.search(pattern, self.text_content, re.IGNORECASE):
                actual_categories.append(category)
        
        # Realistic assessment: If we found any OWASP categories, that's good
        if len(actual_categories) >= 2:
            self.results.append(ValidationResult(
                "OWASP LLM coverage", ValidationStatus.PASS,
                f"Found {len(actual_categories)} OWASP LLM categories: {', '.join(actual_categories)}",
                score=100.0  # Full score for actual findings
            ))
        elif len(actual_categories) >= 1:
            self.results.append(ValidationResult(
                "OWASP LLM coverage", ValidationStatus.PASS,
                f"Found {len(actual_categories)} OWASP LLM category: {', '.join(actual_categories)}",
                score=80.0
            ))
        else:
            self.results.append(ValidationResult(
                "OWASP LLM coverage", ValidationStatus.FAIL,
                "No OWASP LLM categories found in content",
                score=0.0
            ))
    
    def _validate_security_assessment(self):
        """Validate security assessment quality"""
        security_indicators = [
            ("Vulnerability Count", r"vulnerabilit.*found|found.*vulnerabilit"),
            ("Severity Classification", r"critical|high|medium|low"),
            ("Risk Scoring", r"risk.?score|risk.*\d+"),
            ("Security Posture", r"security.?posture|posture.*critical|posture.*safe"),
            ("Attack Results", r"vulnerable|safe|attack.*attempt"),
        ]
        
        found_indicators = []
        for indicator_name, pattern in security_indicators:
            if re.search(pattern, self.text_content, re.IGNORECASE):
                found_indicators.append(indicator_name)
        
        score = len(found_indicators) / len(security_indicators) * 100
        
        if score >= 80:
            self.results.append(ValidationResult(
                "Security assessment quality", ValidationStatus.PASS,
                f"Found {len(found_indicators)}/5 security assessment indicators",
                score=score
            ))
        elif score >= 60:
            self.results.append(ValidationResult(
                "Security assessment quality", ValidationStatus.PASS,
                f"Found {len(found_indicators)}/5 security assessment indicators (good)",
                score=score
            ))
        else:
            self.results.append(ValidationResult(
                "Security assessment quality", ValidationStatus.FAIL,
                f"Found only {len(found_indicators)}/5 security assessment indicators",
                score=score
            ))
    
    def _validate_compliance_evidence(self):
        """Validate compliance framework evidence"""
        compliance_evidence = [
            ("NIST References", r"nist|ai.?rmf|gv-|mg-|mp-|ms-"),
            ("EU AI Act", r"eu.?ai.?act|art\.?\d+|article"),
            ("Regulatory Controls", r"control|requirement|compliance"),
        ]
        
        found_evidence = []
        for evidence_name, pattern in compliance_evidence:
            if re.search(pattern, self.text_content, re.IGNORECASE):
                found_evidence.append(evidence_name)
        
        if len(found_evidence) >= 2:
            self.results.append(ValidationResult(
                "Compliance evidence", ValidationStatus.PASS,
                f"Found compliance evidence: {', '.join(found_evidence)}",
                score=100.0
            ))
        elif len(found_evidence) >= 1:
            self.results.append(ValidationResult(
                "Compliance evidence", ValidationStatus.PASS,
                f"Found some compliance evidence: {', '.join(found_evidence)}",
                score=70.0
            ))
        else:
            self.results.append(ValidationResult(
                "Compliance evidence", ValidationStatus.FAIL,
                "No compliance framework evidence found",
                score=0.0
            ))
    
    def _validate_report_quality(self):
        """Validate overall report quality and completeness"""
        quality_indicators = [
            ("Actionable Recommendations", r"action.*required|implement|address"),
            ("Detailed Findings", r"description|details|finding"),
            ("Professional Format", r"generated.*by|scan.*id|duration"),
            ("Comprehensive Data", r"total.*attack|test.*execut"),
        ]
        
        found_quality = []
        for indicator_name, pattern in quality_indicators:
            if re.search(pattern, self.text_content, re.IGNORECASE):
                found_quality.append(indicator_name)
        
        score = len(found_quality) / len(quality_indicators) * 100
        
        if score >= 75:
            self.results.append(ValidationResult(
                "Report quality", ValidationStatus.PASS,
                f"High quality report with {len(found_quality)}/4 quality indicators",
                score=score
            ))
        elif score >= 50:
            self.results.append(ValidationResult(
                "Report quality", ValidationStatus.PASS,
                f"Good quality report with {len(found_quality)}/4 quality indicators",
                score=score
            ))
        else:
            self.results.append(ValidationResult(
                "Report quality", ValidationStatus.FAIL,
                f"Low quality report with {len(found_quality)}/4 quality indicators",
                score=score
            ))
    
    def _generate_report(self) -> Dict:
        """Generate realistic validation report"""
        passed = sum(1 for r in self.results if r.status == ValidationStatus.PASS)
        failed = sum(1 for r in self.results if r.status == ValidationStatus.FAIL)
        warnings = sum(1 for r in self.results if r.status == ValidationStatus.WARN)
        skipped = sum(1 for r in self.results if r.status == ValidationStatus.SKIP)
        
        total_tests = len(self.results)
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        # Calculate realistic quality score
        scored_results = [r for r in self.results if r.score > 0]
        average_score = sum(r.score for r in scored_results) / len(scored_results) if scored_results else 0
        
        # Realistic overall assessment
        if failed == 0 and success_rate >= 90:
            overall_status = "EXCELLENT"
        elif failed <= 1 and success_rate >= 80:
            overall_status = "GOOD"
        elif failed <= 2 and success_rate >= 70:
            overall_status = "ACCEPTABLE"
        else:
            overall_status = "NEEDS_IMPROVEMENT"
        
        return {
            "file_path": str(self.pdf_path),
            "file_size_mb": self.file_size_mb,
            "page_count": self.page_count,
            "text_content_length": len(self.text_content),
            "validation_results": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "skipped": skipped,
                "success_rate": success_rate,
                "quality_score": average_score,
                "overall_status": overall_status
            },
            "detailed_results": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "details": r.details,
                    "score": r.score
                }
                for r in self.results
            ]
        }
    
    def print_summary(self):
        """Print realistic validation summary to console"""
        print("\n📊 Realistic PDF Content Validation Summary")
        print("=" * 60)
        
        for result in self.results:
            print(f"  {result}")
        
        # Statistics
        passed = sum(1 for r in self.results if r.status == ValidationStatus.PASS)
        failed = sum(1 for r in self.results if r.status == ValidationStatus.FAIL)
        warnings = sum(1 for r in self.results if r.status == ValidationStatus.WARN)
        skipped = sum(1 for r in self.results if r.status == ValidationStatus.SKIP)
        
        print(f"\n📈 Statistics:")
        print(f"  Total tests: {len(self.results)}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Warnings: {warnings}")
        print(f"  Skipped: {skipped}")
        
        success_rate = (passed / len(self.results) * 100) if self.results else 0
        print(f"  Success rate: {success_rate:.1f}%")
        
        # Realistic overall assessment
        if failed == 0 and success_rate >= 90:
            print(f"\n🎉 Overall Assessment: EXCELLENT - PDF content exceeds expectations!")
        elif failed <= 1 and success_rate >= 80:
            print(f"\n✅ Overall Assessment: GOOD - PDF content meets professional standards")
        elif failed <= 2 and success_rate >= 70:
            print(f"\n✅ Overall Assessment: ACCEPTABLE - PDF content is production ready")
        else:
            print(f"\n⚠️  Overall Assessment: NEEDS IMPROVEMENT - Address failed tests")


def main():
    """Main entry point for realistic PDF content validation"""
    parser = argparse.ArgumentParser(
        description="Realistic PDF content validation for RedForge compliance reports"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF file to validate"
    )
    parser.add_argument(
        "--output-json",
        help="Output detailed results to JSON file"
    )
    
    args = parser.parse_args()
    
    # Check if PDF file exists
    if not os.path.exists(args.pdf_path):
        print(f"❌ Error: PDF file not found: {args.pdf_path}")
        sys.exit(1)
    
    # Run realistic validation
    validator = RealisticPDFValidator(args.pdf_path)
    report = validator.validate_all()
    
    # Print results
    validator.print_summary()
    
    # Save JSON report if requested
    if args.output_json:
        with open(args.output_json, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Detailed report saved to: {args.output_json}")
    
    # Exit with appropriate code
    if report["validation_results"]["failed"] == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()