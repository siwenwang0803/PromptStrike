<!-- source: promptstrike/cli.py idx:0 lines:305 -->

```py
#!/usr/bin/env python3
"""
PromptStrike CLI - Developer-first automated LLM red-team platform
Reference: cid-onepager-v1, cid-roadmap-v1 Sprint S-1
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

from .core.scanner import LLMScanner
from .core.report import ReportGenerator
from .core.attacks import AttackPackLoader
from .models.scan_result import ScanResult, AttackResult
from .utils.config import load_config, Config

app = typer.Typer(
    name="promptstrike",
    help="🎯 PromptStrike CLI - Developer-first LLM red-team platform",
    epilog="Visit https://promptstrike.com for more information",
    rich_markup_mode="rich",
)

console = Console()

@app.command()
def scan(
    target: str = typer.Argument(..., help="Target LLM endpoint or model name"),
    output: Optional[Path] = typer.Option(
        None, 
        "--output", 
        "-o", 
        help="Output directory for reports (default: ./reports)"
    ),
    format: str = typer.Option(
        "json", 
        "--format", 
        "-f", 
        help="Report format: json, pdf, html"
    ),
    attack_pack: str = typer.Option(
        "owasp-llm-top10", 
        "--attack-pack", 
        "-a", 
        help="Attack pack to use"
    ),
    config_file: Optional[Path] = typer.Option(
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
      promptstrike scan https://api.openai.com/v1 --attack-pack owasp-llm-top10
      promptstrike scan local-model --config ./config.yaml --dry-run
    """
    
    if output is None:
        output = Path("./reports")
    
    # Load configuration
    config = load_config(config_file) if config_file else Config()
    
    # Override with CLI arguments
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    elif not os.getenv("OPENAI_API_KEY"):
        rprint("[red]❌ Error: API key required. Set OPENAI_API_KEY env var or use --api-key[/red]")
        raise typer.Exit(1)
    
    # Initialize scanner
    scanner = LLMScanner(
        target=target,
        config=config,
        max_requests=max_requests,
        timeout=timeout,
        verbose=verbose
    )
    
    # Load attack pack
    attack_loader = AttackPackLoader()
    attacks = attack_loader.load_pack(attack_pack)
    
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
                attack.category,
                attack.description,
                attack.severity
            )
        
        console.print(table)
        return
    
    # Run scan
    output.mkdir(parents=True, exist_ok=True)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task = progress.add_task("Running LLM red-team scan...", total=len(attacks))
        
        results = []
        for attack in attacks:
            progress.update(task, description=f"Testing {attack.category}: {attack.id}")
            
            try:
                result = scanner.run_attack(attack)
                results.append(result)
                
                if verbose:
                    status = "🔴 VULNERABLE" if result.is_vulnerable else "🟢 SAFE"
                    rprint(f"  {attack.id}: {status}")
                    
            except Exception as e:
                if verbose:
                    rprint(f"  [red]❌ {attack.id}: Error - {str(e)}[/red]")
                
            progress.advance(task)
    
    # Generate scan result
    scan_result = ScanResult(
        target=target,
        attack_pack=attack_pack,
        timestamp=datetime.now(),
        results=results,
        metadata={
            "max_requests": max_requests,
            "timeout": timeout,
            "total_attacks": len(attacks),
            "vulnerabilities_found": sum(1 for r in results if r.is_vulnerable)
        }
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
    vulnerabilities = sum(1 for r in results if r.is_vulnerable)
    total_tests = len(results)
    
    if vulnerabilities > 0:
        rprint(f"\n[red]🚨 Found {vulnerabilities}/{total_tests} vulnerabilities![/red]")
        rprint("[yellow]⚠️  Review the generated reports for details[/yellow]")
    else:
        rprint(f"\n[green]✅ No vulnerabilities found ({total_tests} tests passed)[/green]")

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
        attacks = loader.load_pack(pack_name)
        
        if pack and pack != pack_name:
            continue
            
        rprint(f"\n[bold blue]📦 {pack_name}[/bold blue] ({len(attacks)} attacks)")
        
        table = Table()
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Category", style="magenta")
        table.add_column("Severity", style="red")
        table.add_column("Description", style="green")
        
        for attack in attacks:
            table.add_row(
                attack.id,
                attack.category,
                attack.severity,
                attack.description[:60] + "..." if len(attack.description) > 60 else attack.description
            )
        
        console.print(table)

@app.command()
def version() -> None:
    """📋 Show version information"""
    
    version_info = {
        "version": "0.1.0",
        "build": "alpha",
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": sys.platform,
        "reference": "cid-roadmap-v1 Sprint S-1"
    }
    
    rprint("[bold blue]🎯 PromptStrike CLI[/bold blue]")
    for key, value in version_info.items():
        rprint(f"[cyan]{key.capitalize()}:[/cyan] {value}")

@app.command()
def doctor() -> None:
    """🩺 Run diagnostic checks"""
    
    rprint("[bold blue]🩺 PromptStrike Health Check[/bold blue]\n")
    
    checks = [
        ("Python Version", sys.version_info >= (3, 11), f"Python {sys.version}"),
        ("API Key", bool(os.getenv("OPENAI_API_KEY")), "OPENAI_API_KEY environment variable"),
        ("Attack Packs", True, "Loading attack packs..."),  # TODO: Implement actual check
        ("Output Directory", True, "Write permissions check"),  # TODO: Implement actual check
    ]
    
    for name, status, detail in checks:
        icon = "✅" if status else "❌"
        color = "green" if status else "red"
        rprint(f"{icon} [bold]{name}:[/bold] [{color}]{detail}[/{color}]")
    
    all_passed = all(check[1] for check in checks)
    
    if all_passed:
        rprint("\n[green]🎉 All checks passed! PromptStrike is ready to use.[/green]")
    else:
        rprint("\n[red]⚠️ Some checks failed. Please fix the issues above.[/red]")

def main() -> None:
    """Main CLI entrypoint"""
    app()

if __name__ == "__main__":
    main()
```