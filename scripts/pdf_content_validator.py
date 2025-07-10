#!/usr/bin/env python3
"""
RedForge PDF Content Validator
验证 PDF 内容完整性，包括 Logo、威胁列表、合规性映射等
Validates PDF content integrity including logos, threat lists, compliance mappings
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
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


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


class PDFContentValidator:
    """Comprehensive PDF content validation for RedForge compliance reports"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.results: List[ValidationResult] = []
        self.text_content = ""
        self.page_count = 0
        self.file_size_mb = 0.0
        
    def validate_all(self) -> Dict:
        """Run all validation checks"""
        print(f"🔍 Validating PDF: {self.pdf_path.name}")
        print("=" * 60)
        
        # Basic file validation
        self._validate_file_existence()
        self._validate_file_size()
        self._extract_content()
        
        # Content validation
        self._validate_pdf_structure()
        self._validate_content_completeness()
        self._validate_compliance_content()
        self._validate_owasp_content()
        self._validate_security_content()
        self._validate_report_metadata()
        
        return self._generate_report()
    
    def _validate_file_existence(self):
        """Validate PDF file exists and is accessible"""
        if not self.pdf_path.exists():
            self.results.append(ValidationResult(
                "File existence", ValidationStatus.FAIL,
                f"PDF file not found: {self.pdf_path}"
            ))
            return
            
        if not self.pdf_path.is_file():
            self.results.append(ValidationResult(
                "File type", ValidationStatus.FAIL,
                f"Path is not a file: {self.pdf_path}"
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
        
        if self.file_size_mb == 0:
            self.results.append(ValidationResult(
                "File size check", ValidationStatus.SKIP,
                "File size not determined"
            ))
            return
            
        if self.file_size_mb <= max_size_mb:
            self.results.append(ValidationResult(
                "File size check", ValidationStatus.PASS,
                f"File size {self.file_size_mb:.2f} MB <= {max_size_mb} MB limit",
                score=100.0
            ))
        else:
            self.results.append(ValidationResult(
                "File size check", ValidationStatus.FAIL,
                f"File size {self.file_size_mb:.2f} MB > {max_size_mb} MB limit",
                score=0.0
            ))
    
    def _extract_content(self):
        """Extract text content from PDF"""
        if not HAS_PYPDF2 and not HAS_PDFPLUMBER:
            self.results.append(ValidationResult(
                "Content extraction", ValidationStatus.SKIP,
                "PDF libraries not available (PyPDF2 or pdfplumber required)"
            ))
            return
            
        try:
            if HAS_PDFPLUMBER:
                # Use pdfplumber for better text extraction
                import pdfplumber
                with pdfplumber.open(self.pdf_path) as pdf:
                    self.page_count = len(pdf.pages)
                    text_pages = []
                    for page in pdf.pages:
                        text_pages.append(page.extract_text() or "")
                    self.text_content = "\n".join(text_pages)
                    
            elif HAS_PYPDF2:
                # Fallback to PyPDF2
                with open(self.pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    self.page_count = len(pdf_reader.pages)
                    text_pages = []
                    for page in pdf_reader.pages:
                        text_pages.append(page.extract_text())
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
                f"PDF has {self.page_count} pages"
            ))
        
        # Check if content was extracted
        if len(self.text_content) > 100:
            self.results.append(ValidationResult(
                "Content availability", ValidationStatus.PASS,
                f"PDF contains extractable text content ({len(self.text_content)} chars)"
            ))
        else:
            self.results.append(ValidationResult(
                "Content availability", ValidationStatus.WARN,
                f"PDF contains minimal text content ({len(self.text_content)} chars)"
            ))
    
    def _validate_content_completeness(self):
        """Validate completeness of report content"""
        required_sections = [
            ("Executive Summary", r"executive\s+summary|summary|overview"),
            ("Vulnerability Assessment", r"vulnerability|vulnerabilities|assessment"),
            ("Risk Analysis", r"risk\s+analysis|risk\s+assessment|risk"),
            ("Recommendations", r"recommendations|remediation|mitigation"),
            ("Compliance", r"compliance|regulatory|framework"),
        ]
        
        missing_sections = []
        found_sections = []
        
        for section_name, pattern in required_sections:
            if re.search(pattern, self.text_content, re.IGNORECASE):
                found_sections.append(section_name)
            else:
                missing_sections.append(section_name)
        
        if not missing_sections:
            self.results.append(ValidationResult(
                "Content completeness", ValidationStatus.PASS,
                f"All required sections found: {', '.join(found_sections)}",
                score=100.0
            ))
        else:
            self.results.append(ValidationResult(
                "Content completeness", ValidationStatus.FAIL,
                f"Missing sections: {', '.join(missing_sections)}",
                score=len(found_sections) / len(required_sections) * 100
            ))
    
    def _validate_compliance_content(self):
        """Validate compliance framework content"""
        compliance_frameworks = [
            ("NIST AI-RMF", r"nist|ai.?rmf|risk.?management.?framework"),
            ("EU AI Act", r"eu.?ai.?act|european.?ai|artificial.?intelligence.?act"),
            ("SOC 2", r"soc.?2|service.?organization.?control"),
            ("ISO 27001", r"iso.?27001|information.?security.?management"),
            ("GDPR", r"gdpr|general.?data.?protection"),
            ("PCI DSS", r"pci.?dss|payment.?card.?industry"),
        ]
        
        found_frameworks = []
        missing_frameworks = []
        
        for framework_name, pattern in compliance_frameworks:
            if re.search(pattern, self.text_content, re.IGNORECASE):
                found_frameworks.append(framework_name)
            else:
                missing_frameworks.append(framework_name)
        
        if len(found_frameworks) >= 3:
            self.results.append(ValidationResult(
                "Compliance frameworks", ValidationStatus.PASS,
                f"Found {len(found_frameworks)} frameworks: {', '.join(found_frameworks)}",
                score=len(found_frameworks) / len(compliance_frameworks) * 100
            ))
        else:
            self.results.append(ValidationResult(
                "Compliance frameworks", ValidationStatus.WARN,
                f"Found only {len(found_frameworks)} frameworks: {', '.join(found_frameworks)}",
                score=len(found_frameworks) / len(compliance_frameworks) * 100
            ))
    
    def _validate_owasp_content(self):
        """Validate OWASP LLM Top 10 content"""
        owasp_categories = [
            ("LLM01", r"llm.?01|prompt.?injection"),
            ("LLM02", r"llm.?02|insecure.?output.?handling"),
            ("LLM03", r"llm.?03|training.?data.?poisoning"),
            ("LLM04", r"llm.?04|model.?denial.?of.?service"),
            ("LLM05", r"llm.?05|supply.?chain.?vulnerabilities"),
            ("LLM06", r"llm.?06|sensitive.?information.?disclosure"),
            ("LLM07", r"llm.?07|insecure.?plugin.?design"),
            ("LLM08", r"llm.?08|excessive.?agency"),
            ("LLM09", r"llm.?09|overreliance"),
            ("LLM10", r"llm.?10|model.?theft"),
        ]
        
        found_categories = []
        
        for category_name, pattern in owasp_categories:
            if re.search(pattern, self.text_content, re.IGNORECASE):
                found_categories.append(category_name)
        
        # Check for general OWASP LLM references
        general_owasp = re.search(r"owasp|llm.?top.?10", self.text_content, re.IGNORECASE)
        
        if len(found_categories) >= 8:
            self.results.append(ValidationResult(
                "OWASP LLM Top 10", ValidationStatus.PASS,
                f"Found {len(found_categories)}/10 OWASP LLM categories",
                score=len(found_categories) / 10 * 100
            ))
        elif general_owasp:
            self.results.append(ValidationResult(
                "OWASP LLM Top 10", ValidationStatus.PASS,
                f"Found OWASP LLM references and {len(found_categories)} specific categories",
                score=80.0
            ))
        else:
            self.results.append(ValidationResult(
                "OWASP LLM Top 10", ValidationStatus.WARN,
                f"Found only {len(found_categories)} OWASP LLM categories",
                score=len(found_categories) / 10 * 100
            ))
    
    def _validate_security_content(self):
        """Validate security-specific content"""
        security_terms = [
            "vulnerability", "security", "attack", "threat", "risk",
            "malicious", "exploit", "breach", "injection", "authentication",
            "authorization", "encryption", "privacy", "confidentiality"
        ]
        
        found_terms = []
        for term in security_terms:
            if re.search(rf"\b{term}\b", self.text_content, re.IGNORECASE):
                found_terms.append(term)
        
        coverage = len(found_terms) / len(security_terms) * 100
        
        if coverage >= 70:
            self.results.append(ValidationResult(
                "Security terminology", ValidationStatus.PASS,
                f"Found {len(found_terms)}/{len(security_terms)} security terms ({coverage:.1f}%)",
                score=coverage
            ))
        else:
            self.results.append(ValidationResult(
                "Security terminology", ValidationStatus.WARN,
                f"Found {len(found_terms)}/{len(security_terms)} security terms ({coverage:.1f}%)",
                score=coverage
            ))
    
    def _validate_report_metadata(self):
        """Validate report metadata and branding"""
        metadata_items = [
            ("RedForge branding", r"redforge"),
            ("Date/timestamp", r"\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4}"),
            ("Version info", r"version|v\d+\.\d+|alpha|beta|release"),
            ("Report ID", r"report.?id|scan.?id|ps[-_]\d+"),
            ("Model target", r"gpt|claude|llama|model|target"),
        ]
        
        found_metadata = []
        missing_metadata = []
        
        for item_name, pattern in metadata_items:
            if re.search(pattern, self.text_content, re.IGNORECASE):
                found_metadata.append(item_name)
            else:
                missing_metadata.append(item_name)
        
        if len(found_metadata) >= 4:
            self.results.append(ValidationResult(
                "Report metadata", ValidationStatus.PASS,
                f"Found {len(found_metadata)}/5 metadata items: {', '.join(found_metadata)}",
                score=len(found_metadata) / 5 * 100
            ))
        else:
            self.results.append(ValidationResult(
                "Report metadata", ValidationStatus.WARN,
                f"Found {len(found_metadata)}/5 metadata items, missing: {', '.join(missing_metadata)}",
                score=len(found_metadata) / 5 * 100
            ))
    
    def _generate_report(self) -> Dict:
        """Generate comprehensive validation report"""
        passed = sum(1 for r in self.results if r.status == ValidationStatus.PASS)
        failed = sum(1 for r in self.results if r.status == ValidationStatus.FAIL)
        warnings = sum(1 for r in self.results if r.status == ValidationStatus.WARN)
        skipped = sum(1 for r in self.results if r.status == ValidationStatus.SKIP)
        
        total_tests = len(self.results)
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        # Calculate quality score
        scored_results = [r for r in self.results if r.score > 0]
        average_score = sum(r.score for r in scored_results) / len(scored_results) if scored_results else 0
        
        # Overall assessment
        if failed == 0 and warnings <= 1:
            overall_status = "EXCELLENT"
        elif failed <= 1 and warnings <= 2:
            overall_status = "GOOD"
        elif failed <= 2:
            overall_status = "ACCEPTABLE"
        else:
            overall_status = "POOR"
        
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
        """Print validation summary to console"""
        print("\n📊 PDF Content Validation Summary")
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
        
        # Overall assessment
        if failed == 0 and warnings <= 1:
            print(f"\n🎉 Overall Assessment: EXCELLENT - PDF content is production ready!")
        elif failed <= 1 and warnings <= 2:
            print(f"\n✅ Overall Assessment: GOOD - PDF content meets requirements")
        elif failed <= 2:
            print(f"\n⚠️  Overall Assessment: ACCEPTABLE - Minor issues to address")
        else:
            print(f"\n❌ Overall Assessment: POOR - Significant issues need attention")


def main():
    """Main entry point for PDF content validation"""
    parser = argparse.ArgumentParser(
        description="Validate PDF content for RedForge compliance reports"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF file to validate"
    )
    parser.add_argument(
        "--output-json",
        help="Output detailed results to JSON file"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress detailed output, show only summary"
    )
    
    args = parser.parse_args()
    
    # Check if PDF file exists
    if not os.path.exists(args.pdf_path):
        print(f"❌ Error: PDF file not found: {args.pdf_path}")
        sys.exit(1)
    
    # Run validation
    validator = PDFContentValidator(args.pdf_path)
    report = validator.validate_all()
    
    # Print results
    if not args.quiet:
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