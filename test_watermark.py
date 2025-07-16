#!/usr/bin/env python3
"""
Test the watermark functionality
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from redforge.core.report import ReportGenerator
from redforge.core.user_manager import UserManager
from redforge.models.scan_result import ScanResult, AttackResult, ScanMetadata, ComplianceReport, SeverityLevel, AttackCategory

def create_test_scan_result():
    """Create a test scan result"""
    
    # Create a test attack result
    attack_result = AttackResult(
        attack_id="test_attack_01",
        category=AttackCategory.PROMPT_INJECTION,
        description="Test watermark attack",
        severity=SeverityLevel.HIGH,
        prompt_used="Test prompt for watermark",
        response_received="Test response showing vulnerability",
        is_vulnerable=True,
        confidence_score=0.85,
        risk_score=7.5,
        attack_vector="Direct prompt injection",
        response_time_ms=1500
    )
    
    # Create scan metadata
    metadata = ScanMetadata(
        max_requests=100,
        timeout_seconds=30,
        attack_pack_version="1.0.0",
        total_attacks=1,
        successful_attacks=1,
        failed_attacks=0,
        vulnerabilities_found=1,
        total_duration_seconds=10.5,
        avg_response_time_ms=2100.0,
        total_cost_usd=0.05,
        cli_version="0.2.0",
        python_version="3.13.0",
        platform="darwin"
    )
    
    # Create compliance report
    compliance = ComplianceReport(audit_hash="test_hash_123")
    
    # Create scan result
    scan_result = ScanResult(
        scan_id="test_scan_watermark",
        target="test-model",
        attack_pack="test-pack",
        start_time=datetime.now(),
        end_time=datetime.now(),
        overall_risk_score=7.5,
        security_posture="poor",
        results=[attack_result],
        metadata=metadata,
        compliance=compliance
    )
    
    return scan_result

def test_free_tier_watermark():
    """Test free tier watermark"""
    
    print("🧪 Testing FREE tier watermark...")
    
    # Reset to free tier
    user_manager = UserManager()
    user_manager.set_user_tier("free")
    
    # Create reports directory
    reports_dir = Path("./test_reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Create report generator with free tier
    report_gen = ReportGenerator(reports_dir, user_tier="free")
    
    # Create test scan result
    scan_result = create_test_scan_result()
    
    # Generate HTML report
    html_path = report_gen.generate_html(scan_result)
    print(f"✅ HTML report with watermark: {html_path}")
    
    # Generate PDF report
    pdf_path = report_gen.generate_pdf(scan_result)
    print(f"✅ PDF report with watermark: {pdf_path}")
    
    # Check if watermark is in HTML
    with open(html_path, 'r') as f:
        html_content = f.read()
        if 'class="watermark free"' in html_content and '<div class="watermark free">FREE</div>' in html_content:
            print("✅ HTML watermark found!")
        else:
            print("❌ HTML watermark missing!")
    
    return html_path, pdf_path

def test_paid_tier_no_watermark():
    """Test paid tier without watermark"""
    
    print("\n🧪 Testing STARTER tier (no watermark)...")
    
    # Create reports directory
    reports_dir = Path("./test_reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Create report generator with starter tier
    report_gen = ReportGenerator(reports_dir, user_tier="starter")
    
    # Create test scan result
    scan_result = create_test_scan_result()
    
    # Generate HTML report
    html_path = report_gen.generate_html(scan_result)
    print(f"✅ HTML report without watermark: {html_path}")
    
    # Generate PDF report
    pdf_path = report_gen.generate_pdf(scan_result)
    print(f"✅ PDF report without watermark: {pdf_path}")
    
    # Check if watermark is NOT in HTML
    with open(html_path, 'r') as f:
        html_content = f.read()
        if '<div class="watermark free">FREE</div>' not in html_content:
            print("✅ HTML watermark correctly omitted!")
        else:
            print("❌ HTML watermark should not be present!")
    
    return html_path, pdf_path

if __name__ == "__main__":
    print("🔥 Testing RedForge Watermark System")
    print("=" * 50)
    
    # Test free tier watermark
    free_html, free_pdf = test_free_tier_watermark()
    
    # Test paid tier without watermark
    paid_html, paid_pdf = test_paid_tier_no_watermark()
    
    print("\n" + "=" * 50)
    print("🎯 TEST RESULTS:")
    print(f"📁 Reports saved to: ./test_reports/")
    print(f"🆓 Free tier reports: {free_html.name}, {free_pdf.name}")
    print(f"💳 Paid tier reports: {paid_html.name}, {paid_pdf.name}")
    print("\n💡 Open the HTML files to visually verify watermarks!")