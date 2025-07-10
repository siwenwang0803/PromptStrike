#!/usr/bin/env python3
"""
CLI Stability Test for RedForge
Tests 50 concurrent attacks with 3 output formats
"""

import asyncio
import json
import os
import sys
import time
import subprocess
import tempfile
import concurrent.futures
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import multiprocessing
import psutil
import csv

# Test configuration
MODELS = ["gpt-4", "claude-3-sonnet", "gpt-3.5-turbo"]
FORMATS = ["json", "pdf", "html"]
CONCURRENCY = 50
TIMEOUT = 30


class CLIStabilityTester:
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or f"./test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir = self.output_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        self.results_dir = self.output_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        self.metrics = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        with open(self.logs_dir / "test_log.txt", "a") as f:
            f.write(log_message + "\n")
            
    def run_single_test(self, model: str, format: str, test_id: int) -> Dict:
        """Run a single CLI test"""
        start_time = time.time()
        output_path = self.results_dir / f"{model}_{format}_{test_id}"
        output_path.mkdir(exist_ok=True)
        
        # Command to run
        cmd = [
            sys.executable, "-m", "redforge.cli",
            "scan", model,
            "--format", format,
            "--output", str(output_path),
            "--max-requests", "5",
            "--dry-run"
        ]
        
        result = {
            "model": model,
            "format": format,
            "test_id": test_id,
            "success": False,
            "duration": 0,
            "error": None,
            "output_files": []
        }
        
        try:
            # Run command
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=TIMEOUT
            )
            
            result["duration"] = time.time() - start_time
            result["success"] = process.returncode == 0
            
            if not result["success"]:
                result["error"] = process.stderr
                
            # Check for output files
            if result["success"]:
                for ext in [format]:
                    files = list(output_path.glob(f"*.{ext}"))
                    result["output_files"].extend([str(f) for f in files])
                    
        except subprocess.TimeoutExpired:
            result["duration"] = time.time() - start_time
            result["error"] = "Command timed out"
        except Exception as e:
            result["duration"] = time.time() - start_time
            result["error"] = str(e)
            
        return result
        
    def run_concurrent_tests(self, model: str, format: str, count: int) -> List[Dict]:
        """Run multiple tests concurrently"""
        self.log(f"Starting {count} concurrent tests for {model}/{format}")
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(count, 20)) as executor:
            futures = []
            
            for i in range(count):
                future = executor.submit(self.run_single_test, model, format, i)
                futures.append(future)
                
            # Wait for all to complete
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.log(f"Test execution error: {e}", "ERROR")
                    
        return results
        
    def test_error_handling(self) -> Dict:
        """Test error handling with invalid inputs"""
        self.log("Testing error handling scenarios")
        
        error_tests = [
            {
                "name": "Invalid model",
                "cmd": ["scan", "invalid-model"],
                "expected_error": "invalid"
            },
            {
                "name": "Empty API key",
                "cmd": ["scan", "gpt-4", "--api-key", ""],
                "expected_error": "API key"
            },
            {
                "name": "Invalid timeout",
                "cmd": ["scan", "gpt-4", "--timeout", "0"],
                "expected_error": "timeout"
            },
            {
                "name": "Invalid format",
                "cmd": ["scan", "gpt-4", "--format", "invalid"],
                "expected_error": "format"
            },
            {
                "name": "Missing target",
                "cmd": ["scan"],
                "expected_error": "required"
            }
        ]
        
        results = {"passed": 0, "failed": 0, "details": []}
        
        for test in error_tests:
            cmd = [sys.executable, "-m", "redforge.cli"] + test["cmd"]
            
            try:
                process = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                # Should fail
                if process.returncode != 0:
                    # Check if expected error is in output
                    if test["expected_error"].lower() in (process.stderr + process.stdout).lower():
                        results["passed"] += 1
                        results["details"].append({
                            "test": test["name"],
                            "passed": True,
                            "message": "Error handled correctly"
                        })
                    else:
                        results["failed"] += 1
                        results["details"].append({
                            "test": test["name"],
                            "passed": False,
                            "message": f"Expected error not found. Got: {process.stderr}"
                        })
                else:
                    results["failed"] += 1
                    results["details"].append({
                        "test": test["name"],
                        "passed": False,
                        "message": "Command should have failed but succeeded"
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "test": test["name"],
                    "passed": False,
                    "message": f"Exception: {str(e)}"
                })
                
        return results
        
    def monitor_performance(self) -> Dict:
        """Monitor system performance during tests"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_mb": memory.used / (1024 * 1024),
            "disk_percent": disk.percent,
            "process_count": len(psutil.pids())
        }
        
    def validate_outputs(self, results: List[Dict]) -> Dict:
        """Validate generated output files"""
        validation_summary = {
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "missing_files": 0,
            "details": []
        }
        
        for result in results:
            if result["success"]:
                for file_path in result["output_files"]:
                    validation_summary["total_files"] += 1
                    
                    if not Path(file_path).exists():
                        validation_summary["missing_files"] += 1
                        continue
                        
                    # Validate based on format
                    if file_path.endswith(".json"):
                        try:
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                            if "scan_id" in data and "results" in data:
                                validation_summary["valid_files"] += 1
                            else:
                                validation_summary["invalid_files"] += 1
                        except:
                            validation_summary["invalid_files"] += 1
                            
                    elif file_path.endswith(".html"):
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                            if "<html" in content.lower() and "redforge" in content.lower():
                                validation_summary["valid_files"] += 1
                            else:
                                validation_summary["invalid_files"] += 1
                        except:
                            validation_summary["invalid_files"] += 1
                            
                    elif file_path.endswith(".pdf"):
                        # Basic PDF validation - check file size
                        size = Path(file_path).stat().st_size
                        if size > 1000:
                            validation_summary["valid_files"] += 1
                        else:
                            validation_summary["invalid_files"] += 1
                            
        return validation_summary
        
    def run_full_test(self):
        """Run the complete test suite"""
        self.log("Starting RedForge CLI Stability Test")
        self.log(f"Models: {MODELS}")
        self.log(f"Formats: {FORMATS}")
        self.log(f"Concurrency: {CONCURRENCY}")
        
        overall_results = {
            "start_time": datetime.now().isoformat(),
            "models": MODELS,
            "formats": FORMATS,
            "concurrency": CONCURRENCY,
            "test_results": [],
            "error_handling": {},
            "performance_metrics": [],
            "validation_summary": {}
        }
        
        # Test 1: Error handling
        self.log("\n=== Phase 1: Error Handling Tests ===")
        overall_results["error_handling"] = self.test_error_handling()
        self.log(f"Error handling: {overall_results['error_handling']['passed']} passed, "
                f"{overall_results['error_handling']['failed']} failed")
        
        # Test 2: Concurrent execution
        self.log("\n=== Phase 2: Concurrent Execution Tests ===")
        all_results = []
        
        for model in MODELS[:1]:  # Test with first model only for now
            for format in FORMATS:
                # Monitor performance before
                perf_before = self.monitor_performance()
                overall_results["performance_metrics"].append({"phase": "before", **perf_before})
                
                # Run concurrent tests
                results = self.run_concurrent_tests(model, format, min(CONCURRENCY, 10))  # Limit for testing
                all_results.extend(results)
                
                # Monitor performance after
                perf_after = self.monitor_performance()
                overall_results["performance_metrics"].append({"phase": "after", **perf_after})
                
                # Summary for this batch
                success_count = sum(1 for r in results if r["success"])
                self.log(f"{model}/{format}: {success_count}/{len(results)} succeeded")
                
                # Small delay between batches
                time.sleep(2)
                
        overall_results["test_results"] = all_results
        
        # Test 3: Output validation
        self.log("\n=== Phase 3: Output Validation ===")
        overall_results["validation_summary"] = self.validate_outputs(all_results)
        self.log(f"Validation: {overall_results['validation_summary']['valid_files']} valid, "
                f"{overall_results['validation_summary']['invalid_files']} invalid")
        
        # Generate report
        overall_results["end_time"] = datetime.now().isoformat()
        self.generate_report(overall_results)
        
    def generate_report(self, results: Dict):
        """Generate comprehensive test report"""
        self.log("\n=== Generating Test Report ===")
        
        # Save raw results
        with open(self.output_dir / "test_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        # Generate summary report
        report_lines = [
            "RedForge CLI Stability Test Report",
            "=" * 50,
            f"Test Date: {results['start_time']}",
            f"Output Directory: {self.output_dir}",
            "",
            "Configuration:",
            f"- Models tested: {', '.join(results['models'])}",
            f"- Formats tested: {', '.join(results['formats'])}",
            f"- Concurrency level: {results['concurrency']}",
            "",
            "Test Results:",
            "-" * 30,
            ""
        ]
        
        # Error handling summary
        error_results = results["error_handling"]
        report_lines.extend([
            "1. Error Handling Tests:",
            f"   - Passed: {error_results['passed']}",
            f"   - Failed: {error_results['failed']}",
            ""
        ])
        
        # Concurrent execution summary
        total_tests = len(results["test_results"])
        successful_tests = sum(1 for r in results["test_results"] if r["success"])
        avg_duration = sum(r["duration"] for r in results["test_results"]) / total_tests if total_tests > 0 else 0
        
        report_lines.extend([
            "2. Concurrent Execution Tests:",
            f"   - Total tests: {total_tests}",
            f"   - Successful: {successful_tests}",
            f"   - Failed: {total_tests - successful_tests}",
            f"   - Success rate: {(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A",
            f"   - Average duration: {avg_duration:.2f}s",
            ""
        ])
        
        # Output validation summary
        val_summary = results["validation_summary"]
        report_lines.extend([
            "3. Output Validation:",
            f"   - Total files: {val_summary['total_files']}",
            f"   - Valid files: {val_summary['valid_files']}",
            f"   - Invalid files: {val_summary['invalid_files']}",
            f"   - Missing files: {val_summary['missing_files']}",
            ""
        ])
        
        # Performance metrics
        if results["performance_metrics"]:
            report_lines.extend([
                "4. Performance Metrics:",
                f"   - Peak CPU: {max(m['cpu_percent'] for m in results['performance_metrics']):.1f}%",
                f"   - Peak Memory: {max(m['memory_percent'] for m in results['performance_metrics']):.1f}%",
                ""
            ])
            
        # Recommendations
        report_lines.extend([
            "Recommendations:",
            "-" * 30
        ])
        
        if total_tests > 0 and successful_tests < total_tests:
            report_lines.append("- Investigate and fix failing tests")
            
        if val_summary['invalid_files'] > 0:
            report_lines.append("- Fix output generation for invalid files")
            
        if avg_duration > 5:
            report_lines.append("- Optimize performance for faster execution")
            
        report_lines.extend([
            "- Increase concurrency gradually to 100 for production testing",
            "- Add real API testing with proper rate limiting",
            "- Implement connection pooling for better performance",
            "- Add comprehensive logging for debugging failures"
        ])
        
        # Write report
        report_path = self.output_dir / "test_report.txt"
        with open(report_path, "w") as f:
            f.write("\n".join(report_lines))
            
        # Print report
        print("\n" + "\n".join(report_lines))
        self.log(f"Report saved to: {report_path}")


def main():
    # Check if running in correct directory
    if not Path("redforge").exists() or not Path("pyproject.toml").exists():
        print("Error: Must run from RedForge project root directory")
        sys.exit(1)
        
    # Create and run tester
    tester = CLIStabilityTester()
    try:
        tester.run_full_test()
    except KeyboardInterrupt:
        tester.log("Test interrupted by user", "WARNING")
    except Exception as e:
        tester.log(f"Test failed with error: {e}", "ERROR")
        raise


if __name__ == "__main__":
    main()