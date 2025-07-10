#!/usr/bin/env python3
"""
Simple CLI test without progress bar to isolate the issue
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from promptstrike.core.scanner import LLMScanner
from promptstrike.core.attacks import AttackPackLoader
from promptstrike.core.report import ReportGenerator
from promptstrike.utils.config import Config
from promptstrike.models.scan_result import ScanResult, ScanMetadata, ComplianceReport

def main():
    """Main function replicating CLI behavior"""
    
    # Set up environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return
    
    target = "gpt-3.5-turbo"
    max_requests = 3
    timeout = 30
    output_dir = Path("./test-cli-simple")
    
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
        verbose=True
    )
    
    # Load attacks
    attack_loader = AttackPackLoader()
    attacks = attack_loader.load_pack("owasp-llm-top10")
    
    # Limit attacks for testing
    attacks = attacks[:3]
    
    print(f"🎯 PromptStrike CLI v0.1.0")
    print(f"Target: {target}")
    print(f"Attack Pack: owasp-llm-top10 ({len(attacks)} attacks)")
    print(f"Output: {output_dir}")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run scan without progress bar
    async def run_scan():
        results = []
        successful_attacks = 0
        failed_attacks = 0
        
        async with scanner:
            for i, attack in enumerate(attacks):
                print(f"[{i+1}/{len(attacks)}] Testing {attack.category.value}: {attack.id}")
                
                try:
                    result = await scanner.run_attack(attack)
                    results.append(result)
                    successful_attacks += 1
                    
                    status = "🔴 VULNERABLE" if result.is_vulnerable else "🟢 SAFE"
                    print(f"  {attack.id}: {status}")
                    
                except Exception as e:
                    failed_attacks += 1
                    print(f"  ❌ {attack.id}: Error - {str(e)}")
        
        return results, successful_attacks, failed_attacks
    
    # Run the scan
    scan_start_time = datetime.now()
    
    try:
        results, successful_attacks, failed_attacks = asyncio.run(run_scan())
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        return
    
    scan_end_time = datetime.now()
    
    print(f"\n📊 Scan Complete!")
    print(f"   Duration: {(scan_end_time - scan_start_time).total_seconds():.1f} seconds")
    print(f"   Successful: {successful_attacks}")
    print(f"   Failed: {failed_attacks}")
    print(f"   Vulnerabilities: {sum(1 for r in results if r.is_vulnerable)}")
    
    # Generate JSON report
    if results:
        # Create basic scan metadata
        vuln_count = sum(1 for r in results if r.is_vulnerable)
        duration = (scan_end_time - scan_start_time).total_seconds()
        
        metadata = ScanMetadata(
            max_requests=max_requests,
            timeout_seconds=timeout,
            attack_pack_version="owasp-llm-top10-v1",
            total_attacks=len(attacks),
            successful_attacks=successful_attacks,
            failed_attacks=failed_attacks,
            vulnerabilities_found=vuln_count,
            total_duration_seconds=duration,
            avg_response_time_ms=sum(r.response_time_ms for r in results) / len(results) if results else 0,
            total_tokens_used=sum(r.tokens_used for r in results if r.tokens_used),
            total_cost_usd=sum(r.cost_usd for r in results if r.cost_usd),
            cli_version="0.1.0-alpha",
            python_version="3.13.5",
            platform="darwin"
        )
        
        compliance = ComplianceReport(
            nist_rmf_controls_tested=["AI-RMF-1.1", "AI-RMF-2.1"],
            nist_rmf_gaps_identified=[],
            eu_ai_act_risk_category="limited",
            eu_ai_act_articles_relevant=["Article 13", "Article 15"],
            soc2_controls_impact=["CC6.1", "CC6.2"],
            evidence_artifacts=["scan_evidence.json"],
            audit_hash="test_hash_123"
        )
        
        scan_result = ScanResult(
            scan_id="test-cli-simple-" + scan_start_time.strftime("%Y%m%d-%H%M%S"),
            target=target,
            attack_pack="owasp-llm-top10",
            start_time=scan_start_time,
            end_time=scan_end_time,
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
        
        # Generate report
        generator = ReportGenerator(output_dir)
        json_path = generator.generate_json(scan_result)
        print(f"📄 JSON Report: {json_path}")
        
        print("\n✅ CLI Test Successful!")
    
if __name__ == "__main__":
    main()