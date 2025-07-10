#!/usr/bin/env python3
"""
Test the full flow from scan to report generation
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from redforge.core.scanner import LLMScanner
from redforge.core.attacks import AttackPackLoader
from redforge.core.report import ReportGenerator
from redforge.utils.config import Config
from redforge.models.scan_result import ScanResult, ScanMetadata, ComplianceReport

async def test_full_flow():
    """Test the complete scanning flow"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    # Create config
    config = Config()
    config.api_key = api_key
    
    # Create scanner
    scanner = LLMScanner(
        target="gpt-3.5-turbo",
        config=config,
        max_requests=3,  # Test with 3 attacks
        timeout=15,
        verbose=True
    )
    
    # Load attacks
    attack_loader = AttackPackLoader()
    attacks = attack_loader.load_pack("owasp-llm-top10")
    
    if not attacks:
        print("❌ No attacks loaded")
        return False
    
    # Limit to first 3 attacks for testing
    attacks = attacks[:3]
    print(f"Testing {len(attacks)} attacks")
    
    # Run attacks
    start_time = datetime.now()
    results = []
    
    try:
        async with scanner:
            for i, attack in enumerate(attacks):
                print(f"[{i+1}/{len(attacks)}] Testing {attack.id}: {attack.description}")
                result = await scanner.run_attack(attack)
                results.append(result)
                status = "🔴 VULNERABLE" if result.is_vulnerable else "🟢 SAFE"
                print(f"  Result: {status}")
                
    except Exception as e:
        print(f"❌ Error during scan: {e}")
        return False
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Create scan metadata
    vuln_count = sum(1 for r in results if r.is_vulnerable)
    
    metadata = ScanMetadata(
        max_requests=3,
        timeout_seconds=15,
        attack_pack_version="owasp-llm-top10-v1",
        total_attacks=len(attacks),
        successful_attacks=len(results),
        failed_attacks=0,
        vulnerabilities_found=vuln_count,
        total_duration_seconds=duration,
        avg_response_time_ms=sum(r.response_time_ms for r in results) / len(results) if results else 0,
        total_tokens_used=sum(r.tokens_used for r in results if r.tokens_used),
        total_cost_usd=sum(r.cost_usd for r in results if r.cost_usd),
        cli_version="0.1.0-alpha",
        python_version="3.13.5",
        platform="darwin"
    )
    
    # Create compliance report
    compliance = ComplianceReport(
        nist_rmf_controls_tested=["AI-RMF-1.1", "AI-RMF-2.1"],
        nist_rmf_gaps_identified=[],
        eu_ai_act_risk_category="limited",
        eu_ai_act_articles_relevant=["Article 13", "Article 15"],
        soc2_controls_impact=["CC6.1", "CC6.2"],
        evidence_artifacts=["scan_evidence.json"],
        audit_hash="test_hash_123"
    )
    
    # Create scan result
    scan_result = ScanResult(
        scan_id="test-scan-" + start_time.strftime("%Y%m%d-%H%M%S"),
        target="gpt-3.5-turbo",
        attack_pack="owasp-llm-top10",
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration,
        results=results,
        metadata=metadata,
        compliance=compliance,
        overall_risk_score=sum(r.risk_score for r in results) / len(results) if results else 0,
        security_posture="good" if vuln_count == 0 else "fair",
        vulnerability_count=vuln_count,
        immediate_actions=["Review security controls"] if vuln_count > 0 else [],
        recommended_controls=["Implement input validation", "Add output sanitization"]
    )
    
    print(f"\n📊 Scan Complete!")
    print(f"   Duration: {duration:.1f} seconds")
    print(f"   Vulnerabilities: {vuln_count}/{len(results)}")
    print(f"   Risk Score: {scan_result.overall_risk_score:.1f}/10")
    
    # Generate reports
    report_dir = Path("./test_reports")
    report_dir.mkdir(exist_ok=True)
    
    generator = ReportGenerator(report_dir)
    
    try:
        # Generate JSON report
        json_path = generator.generate_json(scan_result)
        print(f"📄 JSON Report: {json_path}")
        
        # Generate HTML report
        html_path = generator.generate_html(scan_result)
        print(f"🌐 HTML Report: {html_path}")
        
        # Generate PDF report
        pdf_path = generator.generate_pdf(scan_result)
        print(f"📋 PDF Report: {pdf_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating reports: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_full_flow())
    if success:
        print("\n✅ Full flow test successful!")
        print("🎉 RedForge CLI is working correctly!")
    else:
        print("\n❌ Full flow test failed")