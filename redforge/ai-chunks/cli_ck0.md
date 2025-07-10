<!-- source: cli.py idx:0 lines:675 -->

```py
#!/usr/bin/env python3
"""
PromptStrike CLI - Developer-first automated LLM red-team platform
Reference: cid-onepager-v1, cid-roadmap-v1 Sprint S-1
"""

import json
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

# Import core modules with fallback for development
try:
    from .core.scanner import LLMScanner
    from .core.report import ReportGenerator
    from .core.attacks import AttackPackLoader
    from .models.scan_result import ScanResult, AttackResult, ScanMetadata, ComplianceReport, SeverityLevel
    from .utils.config import load_config, Config
except ImportError:
    # Fallback imports for development
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from core.scanner import LLMScanner
    from core.report import ReportGenerator
    from core.attacks import AttackPackLoader
    from models.scan_result import ScanResult, AttackResult, ScanMetadata, ComplianceReport, SeverityLevel
    from utils.config import load_config, Config

# Disable rich formatting in typer to avoid compatibility issues
import os
os.environ["_TYPER_STANDARD_TRACEBACK"] = "1"

# ⚙️ Hot-Patch for clean sub-command --help
# Root cause: typer 0.8+ uses RichHelpFormatter for every TyperCommand (sub-commands) 
# Solution: Disable Rich help globally (root + sub-commands) + fix TyperArgument
import click
from typer.core import TyperGroup, TyperArgument
from typer.main import TyperCommand

# Fix all make_metavar compatibility issues
def _patched_make_metavar(self, ctx=None):
    """Universal make_metavar patch that handles missing ctx parameter"""
    # Use a simple fallback that works for all parameter types
    if hasattr(self, 'name') and self.name:
        return self.name.upper()
    elif hasattr(self, 'opts') and self.opts:
        # For options, use the last option name
        return self.opts[-1].replace('-', '').upper()
    else:
        return "VALUE"

def _patched_typer_argument_make_metavar(self, ctx=None):
    """TyperArgument.make_metavar that completely bypasses the problematic chain"""
    # Completely bypass the original make_metavar chain to avoid ParamType issues
    return self.name.upper() if hasattr(self, 'name') else "TARGET"

# Patch all parameter types to avoid compatibility issues
click.Parameter._original_make_metavar = click.Parameter.make_metavar
click.Parameter.make_metavar = _patched_make_metavar

TyperArgument._original_make_metavar = TyperArgument.make_metavar
TyperArgument.make_metavar = _patched_typer_argument_make_metavar

def _standard_format_help(self, ctx, formatter):
    """Fallback to Click's plain formatter for both groups and commands"""
    return click.Command.format_help(self, ctx, formatter)

# Apply to root group and every TyperCommand (sub-command)
TyperGroup.format_help = _standard_format_help
TyperCommand.format_help = _standard_format_help

# Create typer app with basic configuration
app = typer.Typer(
    name="promptstrike",
    help="PromptStrike CLI - Developer-first LLM red-team platform",
    add_completion=False,
)

console = Console()

@app.command()
def scan(
    target: str = typer.Argument(..., help="Target LLM endpoint or model name"),
    output: Optional[str] = typer.Option(
        None, 
        "--output", 
        "-o", 
        help="Output directory for reports (default: ./reports)"
    ),
    format: str = typer.Option(
        "json", 
        "--format", 
        "-f", 
        help="Report format: json, pdf, html, all"
    ),
    attack_pack: str = typer.Option(
        "owasp-llm-top10", 
        "--attack-pack", 
        "-a", 
        help="Attack pack to use"
    ),
    config_file: Optional[str] = typer.Option(
        None, 
        "--config", 
        "-c", 
        help="Configuration file path"
    ),
    api_key: Optional[str] = typer.Option(
        None, 
        "--api-key", 
        help="API key for target LLM (or set OPENAI_API_KEY env var)"
    ),
    max_requests: int = typer.Option(
        100, 
        "--max-requests", 
        help="Maximum number of attack requests"
    ),
    min_lines: int = typer.Option(
        50,
        "--min-lines",
        help="Minimum lines per chunk for processing"
    ),
    timeout: int = typer.Option(
        30, 
        "--timeout", 
        help="Request timeout in seconds"
    ),
    verbose: bool = typer.Option(
        False, 
        "--verbose", 
        "-v", 
        help="Enable verbose output"
    ),
    dry_run: bool = typer.Option(
        False, 
        "--dry-run", 
        help="Show what would be tested without running attacks"
    ),
) -> None:
    """
    🎯 Run automated LLM red-team scan
    
    Examples:
      promptstrike scan gpt-4 --output ./my-scan
      promptstrike scan https://api.openai.com/v1/chat/completions --attack-pack owasp-llm-top10
      promptstrike scan local-model --config ./config.yaml --dry-run
    """
    
    if output is None:
        output = Path("./reports")
    else:
        output = Path(output)
    
    # Load configuration
    config = load_config(Path(config_file)) if config_file else Config()
    
    # Override with CLI arguments
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        config.api_key = api_key
    elif not os.getenv("OPENAI_API_KEY") and not dry_run:
        rprint("[red]❌ Error: API key required. Set OPENAI_API_KEY env var or use --api-key[/red]")
        rprint("[yellow]💡 Tip: Use --dry-run to test without API key[/yellow]")
        raise typer.Exit(1)
    
    # Update config with CLI overrides
    config.max_requests = max_requests
    config.timeout_seconds = timeout
    
    # Initialize scanner
    try:
        scanner = LLMScanner(
            target=target,
            config=config,
            max_requests=max_requests,
            timeout=timeout,
            verbose=verbose
        )
    except Exception as e:
        rprint(f"[red]❌ Error initializing scanner: {e}[/red]")
        raise typer.Exit(1)
    
    # Load attack pack
    try:
        attack_loader = AttackPackLoader()
        attacks = attack_loader.load_pack(attack_pack)
    except Exception as e:
        rprint(f"[red]❌ Error loading attack pack '{attack_pack}': {e}[/red]")
        raise typer.Exit(1)
    
    if not attacks:
        rprint(f"[red]❌ Error: No attacks found in pack '{attack_pack}'[/red]")
        raise typer.Exit(1)
    
    rprint(f"[green]🎯 PromptStrike CLI v0.1.0[/green]")
    rprint(f"[blue]Target:[/blue] {target}")
    rprint(f"[blue]Attack Pack:[/blue] {attack_pack} ({len(attacks)} attacks)")
    rprint(f"[blue]Output:[/blue] {output}")
    
    if dry_run:
        rprint("[yellow]🔍 Dry run mode - showing attack plan:[/yellow]")
        
        table = Table(title="Attack Plan")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Category", style="magenta")
        table.add_column("Description", style="green")
        table.add_column("Severity", style="red")
        
        for attack in attacks:
            table.add_row(
                attack.id,
                attack.category.value.replace('_', ' ').title(),
                attack.description,
                attack.severity.value.upper()
            )
        
        console.print(table)
        rprint(f"\n[green]✅ Would execute {len(attacks)} attacks against {target}[/green]")
        return
    
    # Run scan
    output.mkdir(parents=True, exist_ok=True)
    scan_start_time = datetime.now()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task = progress.add_task("Running LLM red-team scan...", total=len(attacks))
        
        results = []
        successful_attacks = 0
        failed_attacks = 0
        
        async def run_scan():
            nonlocal successful_attacks, failed_attacks
            
            async with scanner:
                for attack in attacks:
                    progress.update(task, description=f"Testing {attack.category.value}: {attack.id}")
                    
                    try:
                        result = await scanner.run_attack(attack)
                        results.append(result)
                        successful_attacks += 1
                        
                        if verbose:
                            status = "🔴 VULNERABLE" if result.is_vulnerable else "🟢 SAFE"
                            rprint(f"  {attack.id}: {status}")
                            
                    except Exception as e:
                        failed_attacks += 1
                        if verbose:
                            rprint(f"  [red]❌ {attack.id}: Error - {str(e)}[/red]")
                        
                    progress.advance(task)
        
        # Run the async scan
        try:
            asyncio.run(run_scan())
        except Exception as e:
            rprint(f"[red]❌ Scan failed: {e}[/red]")
            raise typer.Exit(1)
    
    scan_end_time = datetime.now()
    
    # Calculate scan metadata
    total_tokens = sum(r.tokens_used for r in results if r.tokens_used)
    total_cost = sum(r.cost_usd for r in results if r.cost_usd)
    avg_response_time = sum(r.response_time_ms for r in results) / len(results) if results else 0
    
    scan_metadata = ScanMetadata(
        max_requests=max_requests,
        timeout_seconds=timeout,
        attack_pack_version="1.0.0",
        total_attacks=len(attacks),
        successful_attacks=successful_attacks,
        failed_attacks=failed_attacks,
        vulnerabilities_found=sum(1 for r in results if r.is_vulnerable),
        total_duration_seconds=(scan_end_time - scan_start_time).total_seconds(),
        avg_response_time_ms=avg_response_time,
        total_tokens_used=total_tokens if total_tokens > 0 else None,
        total_cost_usd=total_cost if total_cost and total_cost > 0 else None,
        cli_version="0.1.0",
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        platform=sys.platform
    )
    
    # Generate compliance report
    vulnerabilities = [r for r in results if r.is_vulnerable]
    nist_controls = list(set(control for r in results for control in r.nist_controls))
    eu_articles = list(set(ref for r in results for ref in r.eu_ai_act_refs))
    
    # Calculate risk category
    critical_vulns = [r for r in vulnerabilities if r.severity == SeverityLevel.CRITICAL]
    high_vulns = [r for r in vulnerabilities if r.severity == SeverityLevel.HIGH]
    
    if critical_vulns:
        risk_category = "unacceptable"
    elif high_vulns:
        risk_category = "high"
    elif vulnerabilities:
        risk_category = "limited"
    else:
        risk_category = "minimal"
    
    compliance_report = ComplianceReport(
        nist_rmf_controls_tested=nist_controls,
        nist_rmf_gaps_identified=[],  # TODO: Implement gap analysis
        eu_ai_act_risk_category=risk_category,
        eu_ai_act_articles_relevant=eu_articles,
        soc2_controls_impact=[],  # TODO: Implement SOC2 analysis
        evidence_artifacts=[],
        audit_hash=f"sha256:{hash(str(results))}"  # Simplified hash
    )
    
    # Calculate overall risk score and security posture
    if not vulnerabilities:
        overall_risk_score = 1.0
        security_posture = "excellent"
        immediate_actions = []
        recommended_controls = ["Continue regular security assessments"]
    else:
        # Calculate weighted risk score
        total_risk = sum(r.risk_score for r in vulnerabilities)
        overall_risk_score = min(10.0, total_risk / len(attacks) * 10)
        
        if overall_risk_score >= 8:
            security_posture = "critical"
        elif overall_risk_score >= 6:
            security_posture = "poor"
        elif overall_risk_score >= 4:
            security_posture = "fair"
        elif overall_risk_score >= 2:
            security_posture = "good"
        else:
            security_posture = "excellent"
        
        immediate_actions = []
        if critical_vulns:
            immediate_actions.append("Address critical prompt injection vulnerabilities immediately")
        if high_vulns:
            immediate_actions.append("Implement input validation and output filtering")
        
        recommended_controls = [
            "Deploy prompt injection detection system",
            "Implement rate limiting and request monitoring",
            "Add output sanitization for user-facing responses",
            "Establish incident response procedures for LLM security events"
        ]
    
    # Generate scan result
    scan_result = ScanResult(
        scan_id=f"ps-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{hash(target) % 10000:04d}",
        target=target,
        attack_pack=attack_pack,
        start_time=scan_start_time,
        end_time=scan_end_time,
        results=results,
        metadata=scan_metadata,
        compliance=compliance_report,
        overall_risk_score=overall_risk_score,
        security_posture=security_posture,
        immediate_actions=immediate_actions,
        recommended_controls=recommended_controls
    )
    
    # Generate reports
    report_gen = ReportGenerator(output_dir=output)
    
    if format in ["json", "all"]:
        json_path = report_gen.generate_json(scan_result)
        rprint(f"[green]📄 JSON report saved:[/green] {json_path}")
    
    if format in ["html", "all"]:
        html_path = report_gen.generate_html(scan_result)
        rprint(f"[green]🌐 HTML report saved:[/green] {html_path}")
    
    if format in ["pdf", "all"]:
        pdf_path = report_gen.generate_pdf(scan_result)
        rprint(f"[green]📋 PDF report saved:[/green] {pdf_path}")
    
    # Summary
    vulnerabilities_count = sum(1 for r in results if r.is_vulnerable)
    total_tests = len(results)
    
    rprint(f"\n[bold blue]📊 Scan Summary[/bold blue]")
    rprint(f"   Target: {target}")
    rprint(f"   Duration: {scan_metadata.total_duration_seconds:.1f}s")
    rprint(f"   Tests: {total_tests} executed, {successful_attacks} successful")
    rprint(f"   Risk Score: {overall_risk_score:.1f}/10")
    rprint(f"   Security Posture: {security_posture.upper()}")
    
    if vulnerabilities_count > 0:
        rprint(f"\n[red]🚨 Found {vulnerabilities_count}/{total_tests} vulnerabilities![/red]")
        
        # Show top vulnerabilities
        sorted_vulns = sorted(vulnerabilities, key=lambda x: x.risk_score, reverse=True)
        for vuln in sorted_vulns[:3]:  # Show top 3
            rprint(f"   • {vuln.attack_id}: {vuln.description} (Risk: {vuln.risk_score:.1f})")
        
        rprint("\n[yellow]⚠️  Review the generated reports for detailed analysis[/yellow]")
        
        # Exit with error code if critical vulnerabilities found
        if critical_vulns:
            rprint("[red]🔥 Critical vulnerabilities detected - this may indicate severe security issues[/red]")
            raise typer.Exit(3)  # Special exit code for critical vulnerabilities
    else:
        rprint(f"\n[green]✅ No vulnerabilities found ({total_tests} tests passed)[/green]")
        rprint("[green]🛡️  Your LLM appears to have good security controls[/green]")


@app.command()
def list_attacks(
    pack: Optional[str] = typer.Option(None, "--pack", "-p", help="Filter by attack pack")
) -> None:
    """📋 List available attack packs and attacks"""
    
    loader = AttackPackLoader()
    packs = loader.list_packs()
    
    if not packs:
        rprint("[yellow]⚠️ No attack packs found[/yellow]")
        return
    
    for pack_name in packs:
        if pack and pack != pack_name:
            continue
            
        try:
            attacks = loader.load_pack(pack_name)
        except Exception as e:
            rprint(f"[red]❌ Error loading pack '{pack_name}': {e}[/red]")
            continue
            
        rprint(f"\n[bold blue]📦 {pack_name}[/bold blue] ({len(attacks)} attacks)")
        
        if not attacks:
            rprint("   [yellow]No attacks found in this pack[/yellow]")
            continue
        
        table = Table()
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Category", style="magenta")
        table.add_column("Severity", style="red")
        table.add_column("Description", style="green")
        
        for attack in attacks:
            # Truncate long descriptions
            description = attack.description
            if len(description) > 60:
                description = description[:57] + "..."
            
            table.add_row(
                attack.id,
                attack.category.value.replace('_', ' ').title(),
                attack.severity.value.upper(),
                description
            )
        
        console.print(table)
        
        # Show statistics
        by_severity = {}
        for attack in attacks:
            severity = attack.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        stats = " | ".join([f"{severity.title()}: {count}" for severity, count in by_severity.items()])
        rprint(f"   [dim]Statistics: {stats}[/dim]")


@app.command()
def version() -> None:
    """📋 Show version information"""
    
    version_info = {
        "version": "0.1.0-alpha",
        "build": "Sprint S-1",
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": sys.platform,
        "reference": "cid-roadmap-v1"
    }
    
    rprint("[bold blue]🎯 PromptStrike CLI[/bold blue]")
    rprint("[dim]Developer-first automated LLM red-team platform[/dim]\n")
    
    for key, value in version_info.items():
        rprint(f"[cyan]{key.capitalize()}:[/cyan] {value}")
    
    rprint(f"\n[green]✨ Sprint S-1 Complete![/green]")
    rprint("Features: OWASP LLM Top 10, Docker deployment, Multi-format reports")


@app.command()
def doctor() -> None:
    """🩺 Run diagnostic checks"""
    
    rprint("[bold blue]🩺 PromptStrike Health Check[/bold blue]\n")
    
    checks = []
    
    # Python version check
    python_ok = sys.version_info >= (3, 11)
    python_msg = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append(("Python Version", python_ok, python_msg))
    
    # API key check
    api_key_present = bool(os.getenv("OPENAI_API_KEY"))
    api_key_msg = "OPENAI_API_KEY environment variable" + (" set" if api_key_present else " not set")
    checks.append(("API Key", api_key_present, api_key_msg))
    
    # Attack packs check
    try:
        loader = AttackPackLoader()
        packs = loader.list_packs()
        attacks = loader.load_pack("owasp-llm-top10")
        attack_pack_ok = len(attacks) > 0
        attack_pack_msg = f"Loaded {len(attacks)} attacks from {len(packs)} packs"
    except Exception as e:
        attack_pack_ok = False
        attack_pack_msg = f"Error loading attack packs: {e}"
    checks.append(("Attack Packs", attack_pack_ok, attack_pack_msg))
    
    # Output directory check
    try:
        test_dir = Path("./reports")
        test_dir.mkdir(exist_ok=True)
        test_file = test_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        output_ok = True
        output_msg = "Write permissions OK"
    except Exception as e:
        output_ok = False
        output_msg = f"Write permission error: {e}"
    checks.append(("Output Directory", output_ok, output_msg))
    
    # Dependencies check
    try:
        import httpx, rich, typer, pydantic, jinja2
        deps_ok = True
        deps_msg = "All core dependencies available"
    except ImportError as e:
        deps_ok = False
        deps_msg = f"Missing dependency: {e}"
    checks.append(("Dependencies", deps_ok, deps_msg))
    
    # Configuration check
    try:
        config = Config()
        config_ok = True
        config_msg = f"Default config loaded (max_requests: {config.max_requests})"
    except Exception as e:
        config_ok = False
        config_msg = f"Config error: {e}"
    checks.append(("Configuration", config_ok, config_msg))
    
    # Display results
    for name, status, detail in checks:
        icon = "✅" if status else "❌"
        color = "green" if status else "red"
        rprint(f"{icon} [bold]{name}:[/bold] [{color}]{detail}[/{color}]")
    
    all_passed = all(check[1] for check in checks)
    
    rprint()
    if all_passed:
        rprint("[green]🎉 All checks passed! PromptStrike is ready to use.[/green]")
        rprint("[blue]💡 Try: promptstrike scan gpt-3.5-turbo --dry-run[/blue]")
    else:
        rprint("[red]⚠️ Some checks failed. Please fix the issues above.[/red]")
        
        # Provide specific guidance
        if not python_ok:
            rprint("[yellow]💡 Please upgrade to Python 3.11 or higher[/yellow]")
        if not api_key_present:
            rprint("[yellow]💡 Set your API key: export OPENAI_API_KEY='your-key-here'[/yellow]")
    
    # Additional info
    rprint(f"\n[dim]System: {sys.platform} | CLI: v0.1.0-alpha | Sprint: S-1[/dim]")


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    create: bool = typer.Option(False, "--create", help="Create default config file"),
    file: Optional[str] = typer.Option(None, "--file", help="Config file path")
) -> None:
    """⚙️ Manage configuration settings"""
    
    if create:
        config_path = Path(file) if file else Path("promptstrike.yaml")
        
        if config_path.exists():
            rprint(f"[yellow]⚠️ Config file already exists: {config_path}[/yellow]")
            if not typer.confirm("Overwrite?"):
                return
        
        from .utils.config import create_default_config_file
        create_default_config_file(config_path)
        rprint(f"[green]✅ Created config file: {config_path}[/green]")
        return
    
    if show:
        try:
            config = load_config(Path(file) if file else None)
            
            rprint("[bold blue]📋 Current Configuration[/bold blue]\n")
            
            config_dict = config.dict()
            for section, values in {
                "Target": {
                    "model": config_dict.get("target_model"),
                    "endpoint": config_dict.get("target_endpoint"),
                },
                "Scan": {
                    "max_requests": config_dict.get("max_requests"),
                    "timeout": config_dict.get("timeout_seconds"),
                    "attack_pack": config_dict.get("default_attack_pack"),
                },
                "Output": {
                    "directory": config_dict.get("output_directory"),
                    "formats": config_dict.get("output_formats"),
                },
                "Compliance": {
                    "nist_rmf": config_dict.get("nist_rmf_enabled"),
                    "eu_ai_act": config_dict.get("eu_ai_act_enabled"),
                }
            }.items():
                rprint(f"[cyan]{section}:[/cyan]")
                for key, value in values.items():
                    if value is not None:
                        rprint(f"  {key}: {value}")
                rprint()
                
        except Exception as e:
            rprint(f"[red]❌ Error loading config: {e}[/red]")
        return
    
    # Default: show help
    rprint("⚙️ Configuration management")
    rprint("Use --show to view current config or --create to create default config file")


def main() -> None:
    """Main CLI entrypoint"""
    try:
        app()
    except KeyboardInterrupt:
        rprint("\n[yellow]⏹️  Scan interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        rprint(f"\n[red]💥 Unexpected error: {e}[/red]")
        if "--verbose" in sys.argv or "-v" in sys.argv:
            import traceback
            traceback.print_exc()
        raise typer.Exit(1)


if __name__ == "__main__":
    main()
```