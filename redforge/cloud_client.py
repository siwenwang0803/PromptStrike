#!/usr/bin/env python3
"""
RedForge Cloud Client - Open-Core Integration
Handles cloud-based scanning with API keys and usage tracking
"""

import os
import time
import json
import asyncio
import httpx
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
import backoff

console = Console()

class CloudClient:
    """Client for RedForge Cloud API"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.redforge.ai"):
        self.api_key = api_key or os.getenv("REDFORGE_API_KEY")
        self.base_url = base_url
        self.session = httpx.Client(timeout=30.0)
        
        if self.api_key:
            self.session.headers["X-API-Key"] = self.api_key
    
    def is_configured(self) -> bool:
        """Check if API key is configured"""
        return bool(self.api_key)
    
    def test_connection(self) -> bool:
        """Test API connection and key validity"""
        try:
            response = self.session.get(f"{self.base_url}/")
            return response.status_code == 200
        except Exception:
            return False
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.TimeoutException, httpx.ConnectError),
        max_tries=3,
        max_time=30
    )
    def create_scan(self, target: str, attack_pack: str = "owasp-top-10", dry_run: bool = False, format: str = "json") -> Dict[str, Any]:
        """Create a new scan with retry logic"""
        try:
            response = self.session.post(f"{self.base_url}/scan", json={
                "target": target,
                "attack_pack": attack_pack,
                "dry_run": dry_run,
                "format": format
            })
            
            if response.status_code == 401:
                console.print("[red]❌ Invalid API key[/red]")
                console.print("Generate a new one at: [cyan]https://redforge.solvas.ai/dashboard[/cyan]")
                raise Exception("Invalid API key")
            elif response.status_code == 402:
                console.print("[yellow]💳 Free tier limit reached[/yellow]")
                console.print("Upgrade at: [cyan]https://redforge.solvas.ai/pricing[/cyan]")
                raise Exception("Tier limit reached")
            elif response.status_code == 429:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                detail = error_data.get("detail", "Rate limit exceeded")
                console.print(f"[yellow]⏳ Rate limited: {detail}[/yellow]")
                
                # Handle different types of rate limits
                if "concurrent" in detail.lower():
                    console.print("Wait for current scans to complete, then try again.")
                elif "revoked" in detail.lower():
                    console.print("Generate a new API key at: [cyan]https://redforge.solvas.ai/dashboard[/cyan]")
                else:
                    console.print("Please wait a moment and try again.")
                
                raise Exception(f"Rate limited: {detail}")
            elif response.status_code != 200:
                try:
                    error_data = response.json()
                    detail = error_data.get("detail", response.text)
                except:
                    detail = response.text
                raise Exception(f"API error ({response.status_code}): {detail}")
            
            return response.json()
        except httpx.RequestError as e:
            console.print(f"[red]🌐 Connection error: {e}[/red]")
            raise Exception(f"Connection error: {e}")
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.TimeoutException, httpx.ConnectError),
        max_tries=3,
        max_time=10
    )
    def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        """Get scan status with retry logic"""
        try:
            response = self.session.get(f"{self.base_url}/scan/{scan_id}/status")
            
            if response.status_code == 404:
                raise Exception("Scan not found")
            elif response.status_code == 401:
                raise Exception("Invalid API key")
            elif response.status_code != 200:
                raise Exception(f"API error: {response.status_code}")
                
            return response.json()
        except httpx.RequestError as e:
            raise Exception(f"Connection error: {e}")
    
    def get_scan_report(self, scan_id: str) -> str:
        """Get scan report download URL"""
        try:
            response = self.session.get(f"{self.base_url}/scan/{scan_id}/report")
            response.raise_for_status()
            return response.json()["download_url"]
        except httpx.RequestError as e:
            raise Exception(f"Connection error: {e}")
    
    def download_report(self, report_url: str, output_file: str):
        """Download report to file"""
        try:
            response = self.session.get(report_url)
            response.raise_for_status()
            
            with open(output_file, 'wb') as f:
                f.write(response.content)
        except httpx.RequestError as e:
            raise Exception(f"Download error: {e}")
    
    def monitor_scan(self, scan_id: str, output_dir: str = "./reports") -> str:
        """Monitor scan progress and download report when complete"""
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Scanning...", total=100)
            
            while True:
                try:
                    status = self.get_scan_status(scan_id)
                    
                    # Update progress
                    progress_percent = int(status["progress"] * 100)
                    current_attack = status.get("current_attack", "Initializing...")
                    
                    progress.update(
                        task,
                        completed=progress_percent,
                        description=f"[cyan]{current_attack}[/cyan]"
                    )
                    
                    if status["status"] == "completed":
                        progress.update(task, completed=100, description="[green]✅ Scan completed![/green]")
                        break
                    elif status["status"] == "failed":
                        error_msg = status.get("error", "Unknown error")
                        progress.update(task, description=f"[red]❌ Scan failed: {error_msg}[/red]")
                        raise Exception(f"Scan failed: {error_msg}")
                    
                    time.sleep(2)  # Poll every 2 seconds
                    
                except Exception as e:
                    # Don't fail immediately on transient errors
                    if "Connection error" in str(e) or "timeout" in str(e).lower():
                        progress.update(task, description=f"[yellow]⚠️ Connection issue, retrying...[/yellow]")
                        time.sleep(5)  # Wait longer before retry
                        continue
                    else:
                        progress.update(task, description=f"[red]❌ Error: {e}[/red]")
                        raise
        
        # Download report
        try:
            report_url = self.get_scan_report(scan_id)
            
            # Create output directory
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = f"{output_dir}/redforge_scan_{timestamp}.json"
            
            # Download
            self.download_report(report_url, output_file)
            
            return output_file
            
        except Exception as e:
            raise Exception(f"Failed to download report: {e}")

def run_cloud_scan(
    target: str,
    api_key: Optional[str] = None,
    attack_pack: str = "owasp-top-10",
    dry_run: bool = False,
    format: str = "json",
    output_dir: str = "./reports"
) -> str:
    """Run a cloud-based scan"""
    
    client = CloudClient(api_key)
    
    if not client.is_configured():
        console.print(Panel(
            "[red]❌ No API key configured![/red]\n\n"
            "Get your API key at: [cyan]https://redforge.solvas.ai/dashboard[/cyan]\n\n"
            "Then set it as:\n"
            "• Environment variable: [yellow]export REDFORGE_API_KEY='your_key'[/yellow]\n"
            "• Command line: [yellow]--api-key your_key[/yellow]",
            title="API Key Required",
            border_style="red"
        ))
        raise Exception("API key required for cloud scanning")
    
    # Test connection
    if not client.test_connection():
        console.print("[red]❌ Cannot connect to RedForge Cloud API[/red]")
        raise Exception("Connection failed")
    
    console.print(f"[green]🔥 Starting cloud scan for:[/green] [cyan]{target}[/cyan]")
    
    # Create scan
    try:
        scan_response = client.create_scan(target, attack_pack, dry_run, format)
        scan_id = scan_response["scan_id"]
        
        console.print(f"[green]✅ Scan created:[/green] [yellow]{scan_id}[/yellow]")
        
        # Monitor and download
        output_file = client.monitor_scan(scan_id, output_dir)
        
        return output_file
        
    except Exception as e:
        console.print(f"[red]❌ Scan failed: {e}[/red]")
        raise

def run_offline_scan(target: str, output_dir: str = "./reports") -> str:
    """Run limited offline scan (free tier)"""
    
    console.print(Panel(
        "[yellow]🔓 Running offline mode (limited)[/yellow]\n\n"
        "• Only 1 sample attack will be executed\n"
        "• Report will be watermarked\n"
        "• For full scanning, get an API key at: [cyan]https://redforge.solvas.ai[/cyan]",
        title="Offline Mode",
        border_style="yellow"
    ))
    
    # Import local scanner
    from redforge.core.scanner import LLMScanner
    from redforge.core.attacks import AttackPackLoader
    from redforge.core.report import ReportGenerator
    
    # Load limited attacks
    attack_loader = AttackPackLoader()
    attacks = attack_loader.load_pack("owasp-llm-top10")[:1]  # Only 1 attack
    
    # Run scan
    from redforge.utils.config import Config
    config = Config(target_endpoint=target, max_requests=1, timeout_seconds=30)
    scanner = LLMScanner(target=target, config=config)
    results = []
    
    console.print(f"[cyan]🧪 Running sample attack...[/cyan]")
    
    for attack in attacks:
        try:
            result = asyncio.run(scanner.run_attack(attack))
            results.append(result)
            console.print(f"[green]✅ {attack.id}[/green]")
        except Exception as e:
            console.print(f"[red]❌ {attack.id}: {e}[/red]")
    
    # Generate proper ScanResult
    from datetime import datetime
    from redforge.models.scan_result import ScanResult, ScanMetadata, ComplianceReport
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"{output_dir}/redforge_scan_{timestamp}.json"
    
    # Create complete ScanResult with all required fields
    scan_metadata = ScanMetadata(
        max_requests=1,
        timeout_seconds=30,
        attack_pack_version="v1.0",
        total_attacks=1,
        successful_attacks=len([r for r in results if r.is_vulnerable]),
        failed_attacks=len([r for r in results if not r.is_vulnerable]),
        vulnerabilities_found=len([r for r in results if r.is_vulnerable]),
        total_duration_seconds=30.0,
        avg_response_time_ms=2000.0,
        total_tokens_used=sum(getattr(r, 'tokens_used', 0) for r in results),
        total_cost_usd=sum(getattr(r, 'cost_usd', 0.0) for r in results),
        cli_version="v0.3.0",
        python_version="3.9+",
        platform="offline"
    )
    
    compliance_report = ComplianceReport(
        nist_rmf_controls_tested=["GV-1.1", "MP-2.3"],
        nist_rmf_gaps_identified=[],
        eu_ai_act_risk_category="minimal",
        eu_ai_act_articles_relevant=["Article 13"],
        soc2_controls_impact=["CC6.1"],
        evidence_artifacts=[],
        audit_hash="offline_scan_limited"
    )
    
    scan_result = ScanResult(
        scan_id=f"offline_{timestamp}",
        target=target,
        attack_pack="owasp-llm-top10",
        start_time=datetime.now(),
        end_time=datetime.now(),
        duration_seconds=30.0,
        overall_risk_score=max([getattr(r, 'risk_score', 0.0) for r in results] + [0.0]),
        security_posture="poor",
        vulnerability_count=len([r for r in results if getattr(r, 'is_vulnerable', False)]),
        results=results,
        metadata=scan_metadata,
        compliance=compliance_report,
        immediate_actions=["Upgrade to full scan for complete assessment"],
        recommended_controls=["Implement comprehensive security testing"]
    )
    
    # Use ReportGenerator to create properly formatted JSON
    report_generator = ReportGenerator(output_dir=Path(output_dir), user_tier="free")
    output_path = report_generator.generate_json(scan_result)
    
    # Add watermark to the JSON file
    with open(output_path, 'r') as f:
        data = json.load(f)
    data["watermark"] = "⚠️ This is a limited offline scan. For full scanning, visit https://redforge.solvas.ai"
    data["tier"] = "free"
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    console.print(f"[green]✅ Offline scan completed:[/green] [yellow]{output_path}[/yellow]")
    
    return str(output_path)

def show_upgrade_message():
    """Show upgrade message for full functionality"""
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Feature", style="cyan")
    table.add_column("Free (Offline)", style="red")
    table.add_column("Starter ($29/mo)", style="green")
    table.add_column("Pro ($99/mo)", style="gold1")
    
    table.add_row("Attack Count", "1 sample", "50 (OWASP Top 10)", "100+ (All packs)")
    table.add_row("Report Format", "JSON only", "JSON, HTML, PDF", "All formats")
    table.add_row("Watermark", "Yes", "No", "No")
    table.add_row("Cloud Scanning", "No", "Yes", "Yes")
    table.add_row("Support", "Community", "Priority", "Priority")
    
    console.print(table)
    console.print("\n[cyan]🚀 Upgrade at: https://redforge.solvas.ai/pricing[/cyan]")