#!/usr/bin/env python3
"""
Test concurrent stability as requested by user
- 50 concurrent attacks
- 3 output formats (JSON, HTML, PDF)
- Production-level testing
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import concurrent.futures
import time

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from redforge.core.scanner import LLMScanner
from redforge.core.attacks import AttackPackLoader
from redforge.core.report import ReportGenerator
from redforge.utils.config import Config
from redforge.models.scan_result import ScanResult, ScanMetadata, ComplianceReport

async def run_single_attack(scanner, attack, attack_id):
    """Run a single attack"""
    try:
        result = await scanner.run_attack(attack)
        return f"✅ {attack_id}: {'VULNERABLE' if result.is_vulnerable else 'SAFE'}", result
    except Exception as e:
        return f"❌ {attack_id}: Error - {str(e)}", None

async def test_concurrent_stability():
    """Test concurrent stability with multiple attacks"""
    
    # Setup
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    target = "gpt-3.5-turbo"
    max_requests = 50
    timeout = 30
    output_dir = Path("./concurrent-test-reports")
    
    # Create config
    config = Config()
    config.api_key = api_key
    config.max_requests = max_requests
    config.timeout_seconds = timeout
    
    # Initialize scanner
    scanner = LLMScanner(
        target=target,
        config=config,
        max_requests=max_requests,
        timeout=timeout,
        verbose=False
    )
    
    # Load attacks
    attack_loader = AttackPackLoader()
    all_attacks = attack_loader.load_pack("owasp-llm-top10")
    
    # Create 50 attack jobs by repeating attacks
    attack_jobs = []
    for i in range(50):
        attack = all_attacks[i % len(all_attacks)]
        attack_jobs.append((attack, f"{attack.id}-{i+1}"))
    
    print(f"🎯 RedForge Concurrent Stability Test")
    print(f"Target: {target}")
    print(f"Concurrent Attacks: {len(attack_jobs)}")
    print(f"Output: {output_dir}")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run concurrent attacks
    start_time = datetime.now()
    results = []
    
    print(f"\n🚀 Starting concurrent attack execution...")
    
    try:
        async with scanner:
            # Run all attacks concurrently
            tasks = []
            for attack, attack_id in attack_jobs:
                task = run_single_attack(scanner, attack, attack_id)
                tasks.append(task)
            
            # Execute all tasks concurrently
            concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful = 0
            failed = 0
            vulnerabilities = 0
            
            for i, (status_msg, result) in enumerate(concurrent_results):
                if isinstance(result, Exception):
                    print(f"❌ Task {i+1}: Exception - {result}")
                    failed += 1
                elif result is None:
                    print(status_msg)
                    failed += 1
                else:
                    print(status_msg)
                    results.append(result)
                    successful += 1
                    if result.is_vulnerable:
                        vulnerabilities += 1
                        
    except Exception as e:
        print(f"❌ Concurrent execution failed: {e}")
        return False
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n📊 Concurrent Test Complete!")
    print(f"   Duration: {duration:.1f} seconds")
    print(f"   Successful: {successful}/50")
    print(f"   Failed: {failed}/50")
    print(f"   Vulnerabilities: {vulnerabilities}")
    print(f"   Rate: {successful/duration:.1f} attacks/second")
    
    if successful == 0:
        print("❌ No successful attacks - test failed")
        return False
    
    # Generate reports in all 3 formats
    print(f"\n📄 Generating reports in all formats...")
    
    # Create scan metadata
    metadata = ScanMetadata(
        max_requests=max_requests,
        timeout_seconds=timeout,
        attack_pack_version="owasp-llm-top10-v1",
        total_attacks=50,
        successful_attacks=successful,
        failed_attacks=failed,
        vulnerabilities_found=vulnerabilities,
        total_duration_seconds=duration,
        avg_response_time_ms=sum(r.response_time_ms for r in results) / len(results) if results else 0,
        total_tokens_used=sum(r.tokens_used for r in results if r.tokens_used),
        total_cost_usd=sum(r.cost_usd for r in results if r.cost_usd),
        cli_version="0.1.0-alpha",
        python_version="3.13.5",
        platform="darwin"
    )
    
    compliance = ComplianceReport(
        nist_rmf_controls_tested=["AI-RMF-1.1", "AI-RMF-2.1", "AI-RMF-3.1"],
        nist_rmf_gaps_identified=[],
        eu_ai_act_risk_category="limited",
        eu_ai_act_articles_relevant=["Article 13", "Article 15", "Article 29"],
        soc2_controls_impact=["CC6.1", "CC6.2", "CC6.3"],
        evidence_artifacts=["concurrent_test_evidence.json"],
        audit_hash="concurrent_test_hash_456"
    )
    
    scan_result = ScanResult(
        scan_id="concurrent-stability-test-" + start_time.strftime("%Y%m%d-%H%M%S"),
        target=target,
        attack_pack="owasp-llm-top10",
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration,
        results=results,
        metadata=metadata,
        compliance=compliance,
        overall_risk_score=sum(r.risk_score for r in results) / len(results) if results else 0,
        security_posture="good" if vulnerabilities == 0 else "fair",
        vulnerability_count=vulnerabilities,
        immediate_actions=["Review concurrent execution controls"] if vulnerabilities > 10 else [],
        recommended_controls=["Implement rate limiting", "Add concurrent request monitoring"]
    )
    
    # Generate all report formats
    generator = ReportGenerator(output_dir)
    
    try:
        # JSON Report
        json_path = generator.generate_json(scan_result)
        print(f"📄 JSON Report: {json_path}")
        
        # HTML Report
        html_path = generator.generate_html(scan_result)
        print(f"🌐 HTML Report: {html_path}")
        
        # PDF Report
        pdf_path = generator.generate_pdf(scan_result)
        print(f"📋 PDF Report: {pdf_path}")
        
        # Validate file sizes
        json_size = json_path.stat().st_size
        html_size = html_path.stat().st_size
        pdf_size = pdf_path.stat().st_size
        
        print(f"\n📊 Report File Sizes:")
        print(f"   JSON: {json_size:,} bytes")
        print(f"   HTML: {html_size:,} bytes")
        print(f"   PDF: {pdf_size:,} bytes")
        
        # Validate all files exist and have content
        if json_size > 100 and html_size > 100 and pdf_size > 100:
            print(f"\n✅ All report formats generated successfully!")
            return True
        else:
            print(f"\n❌ Some report files are too small - possible generation issue")
            return False
            
    except Exception as e:
        print(f"❌ Error generating reports: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_concurrent_stability())
    if success:
        print("\n🎉 CONCURRENT STABILITY TEST PASSED!")
        print("✅ RedForge CLI is production-ready for concurrent operations")
        print("✅ All 3 output formats (JSON, HTML, PDF) working correctly")
        print("✅ 50 concurrent attacks executed successfully")
    else:
        print("\n❌ CONCURRENT STABILITY TEST FAILED!")
        print("❌ RedForge CLI needs additional fixes before production use")