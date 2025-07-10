#!/usr/bin/env python3
"""
Output validation script for RedForge CLI tests
Validates JSON schema, PDF content, and HTML structure
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse
from datetime import datetime

try:
    import PyPDF2
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False
    print("Warning: PyPDF2 not installed. PDF content validation will be limited.")

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("Warning: BeautifulSoup not installed. HTML validation will be limited.")

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("Warning: jsonschema not installed. Schema validation will be skipped.")


class OutputValidator:
    """Validates RedForge output files"""
    
    # Expected JSON schema (simplified)
    JSON_SCHEMA = {
        "type": "object",
        "required": ["scan_id", "target", "results", "metadata", "compliance"],
        "properties": {
            "scan_id": {"type": "string"},
            "target": {"type": "string"},
            "attack_pack": {"type": "string"},
            "start_time": {"type": "string"},
            "end_time": {"type": "string"},
            "overall_risk_score": {"type": "number", "minimum": 0, "maximum": 10},
            "security_posture": {"type": "string", "enum": ["excellent", "good", "fair", "poor", "critical"]},
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["attack_id", "category", "severity", "is_vulnerable"],
                    "properties": {
                        "attack_id": {"type": "string"},
                        "category": {"type": "string"},
                        "severity": {"type": "string"},
                        "is_vulnerable": {"type": "boolean"},
                        "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                        "risk_score": {"type": "number", "minimum": 0, "maximum": 10}
                    }
                }
            },
            "metadata": {
                "type": "object",
                "required": ["total_attacks", "successful_attacks", "vulnerabilities_found"]
            },
            "compliance": {
                "type": "object",
                "required": ["nist_rmf_controls_tested", "eu_ai_act_risk_category"]
            }
        }
    }
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.validation_results = []
        
    def validate_json(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate JSON output file"""
        errors = []
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Basic structure validation
            if not isinstance(data, dict):
                errors.append("JSON root must be an object")
                return False, errors
                
            # Check required fields
            required_fields = ["scan_id", "target", "results"]
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
                    
            # Validate schema if available
            if HAS_JSONSCHEMA and not errors:
                try:
                    jsonschema.validate(instance=data, schema=self.JSON_SCHEMA)
                except jsonschema.ValidationError as e:
                    errors.append(f"Schema validation error: {e.message}")
                    
            # Content validation
            if "results" in data:
                if not isinstance(data["results"], list):
                    errors.append("Results must be an array")
                elif len(data["results"]) == 0:
                    errors.append("Results array is empty")
                else:
                    # Validate each result
                    for i, result in enumerate(data["results"]):
                        if "attack_id" not in result:
                            errors.append(f"Result {i} missing attack_id")
                        if "is_vulnerable" not in result:
                            errors.append(f"Result {i} missing is_vulnerable")
                            
            # Check risk score range
            if "overall_risk_score" in data:
                score = data["overall_risk_score"]
                if not isinstance(score, (int, float)) or score < 0 or score > 10:
                    errors.append(f"Invalid overall_risk_score: {score}")
                    
            if self.verbose and not errors:
                print(f"✓ JSON validation passed: {file_path.name}")
                print(f"  - Scan ID: {data.get('scan_id', 'N/A')}")
                print(f"  - Target: {data.get('target', 'N/A')}")
                print(f"  - Results: {len(data.get('results', []))}")
                print(f"  - Risk Score: {data.get('overall_risk_score', 'N/A')}")
                
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {e}")
        except Exception as e:
            errors.append(f"Error reading file: {e}")
            
        return len(errors) == 0, errors
        
    def validate_pdf(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate PDF output file"""
        errors = []
        
        try:
            # Check file size
            file_size = file_path.stat().st_size
            if file_size < 1000:
                errors.append(f"PDF file too small: {file_size} bytes")
                return False, errors
                
            # Content validation if PyPDF2 is available
            if HAS_PYPDF:
                try:
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        num_pages = len(pdf_reader.pages)
                        
                        if num_pages == 0:
                            errors.append("PDF has no pages")
                        else:
                            # Check first page content
                            first_page = pdf_reader.pages[0]
                            text = first_page.extract_text()
                            
                            # Look for expected content
                            expected_content = ["RedForge", "Security", "Report"]
                            missing_content = []
                            
                            for content in expected_content:
                                if content.lower() not in text.lower():
                                    missing_content.append(content)
                                    
                            if missing_content:
                                errors.append(f"PDF missing expected content: {', '.join(missing_content)}")
                                
                    if self.verbose and not errors:
                        print(f"✓ PDF validation passed: {file_path.name}")
                        print(f"  - Size: {file_size:,} bytes")
                        print(f"  - Pages: {num_pages}")
                        
                except Exception as e:
                    errors.append(f"Error reading PDF content: {e}")
            else:
                # Basic validation only
                if self.verbose:
                    print(f"✓ PDF basic validation passed: {file_path.name}")
                    print(f"  - Size: {file_size:,} bytes")
                    
        except Exception as e:
            errors.append(f"Error accessing PDF file: {e}")
            
        return len(errors) == 0, errors
        
    def validate_html(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate HTML output file"""
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Basic HTML structure check
            if not content.strip():
                errors.append("HTML file is empty")
                return False, errors
                
            if "<html" not in content.lower():
                errors.append("Missing HTML tag")
                
            if "<head" not in content.lower():
                errors.append("Missing HEAD tag")
                
            if "<body" not in content.lower():
                errors.append("Missing BODY tag")
                
            # Content validation
            expected_content = ["RedForge", "Scan Report", "Risk Score"]
            missing_content = []
            
            for exp in expected_content:
                if exp.lower() not in content.lower():
                    missing_content.append(exp)
                    
            if missing_content and len(missing_content) == len(expected_content):
                errors.append(f"HTML missing expected content: {', '.join(missing_content)}")
                
            # Advanced validation with BeautifulSoup
            if HAS_BS4 and not errors:
                try:
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Check for report structure
                    if not soup.find(['h1', 'h2', 'h3']):
                        errors.append("No headers found in HTML")
                        
                    # Check for results table or divs
                    if not soup.find(['table', 'div']):
                        errors.append("No content structure found")
                        
                    if self.verbose and not errors:
                        print(f"✓ HTML validation passed: {file_path.name}")
                        print(f"  - Size: {len(content):,} bytes")
                        print(f"  - Title: {soup.title.string if soup.title else 'No title'}")
                        
                except Exception as e:
                    errors.append(f"Error parsing HTML: {e}")
            elif not errors and self.verbose:
                print(f"✓ HTML basic validation passed: {file_path.name}")
                print(f"  - Size: {len(content):,} bytes")
                
        except Exception as e:
            errors.append(f"Error reading HTML file: {e}")
            
        return len(errors) == 0, errors
        
    def validate_directory(self, directory: Path) -> Dict[str, Dict[str, int]]:
        """Validate all output files in a directory"""
        results = {
            "json": {"valid": 0, "invalid": 0, "errors": []},
            "pdf": {"valid": 0, "invalid": 0, "errors": []},
            "html": {"valid": 0, "invalid": 0, "errors": []}
        }
        
        # Find all output files
        for ext, validator in [
            ("json", self.validate_json),
            ("pdf", self.validate_pdf),
            ("html", self.validate_html)
        ]:
            for file_path in directory.rglob(f"*.{ext}"):
                is_valid, errors = validator(file_path)
                
                if is_valid:
                    results[ext]["valid"] += 1
                else:
                    results[ext]["invalid"] += 1
                    results[ext]["errors"].extend([f"{file_path.name}: {e}" for e in errors])
                    
                self.validation_results.append({
                    "file": str(file_path),
                    "type": ext,
                    "valid": is_valid,
                    "errors": errors
                })
                
        return results
        
    def generate_report(self, output_file: Optional[Path] = None):
        """Generate validation report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(self.validation_results),
            "valid_files": sum(1 for r in self.validation_results if r["valid"]),
            "invalid_files": sum(1 for r in self.validation_results if not r["valid"]),
            "details": self.validation_results
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
                
        return report


def main():
    parser = argparse.ArgumentParser(description="Validate RedForge output files")
    parser.add_argument("path", help="File or directory to validate")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-r", "--report", help="Generate validation report file")
    parser.add_argument("-t", "--type", choices=["json", "pdf", "html"], help="Validate specific file type only")
    
    args = parser.parse_args()
    
    validator = OutputValidator(verbose=args.verbose)
    path = Path(args.path)
    
    if path.is_file():
        # Validate single file
        ext = path.suffix[1:]
        if args.type and ext != args.type:
            print(f"File type {ext} doesn't match requested type {args.type}")
            sys.exit(1)
            
        if ext == "json":
            is_valid, errors = validator.validate_json(path)
        elif ext == "pdf":
            is_valid, errors = validator.validate_pdf(path)
        elif ext == "html":
            is_valid, errors = validator.validate_html(path)
        else:
            print(f"Unknown file type: {ext}")
            sys.exit(1)
            
        if is_valid:
            print(f"✓ Validation passed: {path.name}")
        else:
            print(f"✗ Validation failed: {path.name}")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
            
    elif path.is_dir():
        # Validate directory
        print(f"Validating files in: {path}")
        results = validator.validate_directory(path)
        
        # Print summary
        print("\nValidation Summary:")
        print("-" * 40)
        
        total_valid = 0
        total_invalid = 0
        
        for file_type, stats in results.items():
            if args.type and file_type != args.type:
                continue
                
            valid = stats["valid"]
            invalid = stats["invalid"]
            total = valid + invalid
            
            if total > 0:
                print(f"{file_type.upper()} files: {total} total, {valid} valid, {invalid} invalid")
                
                if invalid > 0 and args.verbose:
                    print(f"  Errors:")
                    for error in stats["errors"][:5]:  # Show first 5 errors
                        print(f"    - {error}")
                    if len(stats["errors"]) > 5:
                        print(f"    ... and {len(stats['errors']) - 5} more errors")
                        
            total_valid += valid
            total_invalid += invalid
            
        print("-" * 40)
        print(f"Total: {total_valid + total_invalid} files, {total_valid} valid, {total_invalid} invalid")
        
        # Generate report if requested
        if args.report:
            report = validator.generate_report(Path(args.report))
            print(f"\nValidation report saved to: {args.report}")
            
        # Exit with error if any files are invalid
        if total_invalid > 0:
            sys.exit(1)
            
    else:
        print(f"Path not found: {path}")
        sys.exit(1)


if __name__ == "__main__":
    main()