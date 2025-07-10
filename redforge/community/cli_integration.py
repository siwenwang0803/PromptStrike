"""
CLI Integration for Community Feedback

Provides command-line interface for community feedback management,
analytics, and integration planning.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich import print as rprint

from .feedback_collector import (
    CommunityFeedbackManager,
    FeedbackType,
    FeedbackPriority,
    FeedbackStatus
)
from .integration_engine import (
    FeedbackIntegrationEngine,
    IntegrationPlan,
    IntegrationAction
)


def create_community_cli() -> typer.Typer:
    """Create community feedback CLI application"""
    app = typer.Typer(
        name="community",
        help="🤝 Community feedback management and integration",
        no_args_is_help=True
    )
    
    @app.command()
    def collect(
        days: int = typer.Option(30, "--days", "-d", help="Days of feedback to collect"),
        github_repo: Optional[str] = typer.Option(None, "--repo", "-r", help="GitHub repository (owner/repo)"),
        output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for feedback data")
    ):
        """📥 Collect community feedback from all sources"""
        console = Console()
        
        with console.status("[bold green]Collecting community feedback..."):
            # Run async collection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                manager = CommunityFeedbackManager(github_repo=github_repo)
                new_feedback_count = loop.run_until_complete(
                    manager.collect_all_feedback(days)
                )
                analytics = manager.analyze_feedback_trends(days)
                
                console.print(f"\n[bold green]✅ Collection Complete[/bold green]")
                console.print(f"   New feedback items: {new_feedback_count}")
                console.print(f"   Total feedback (last {days} days): {analytics.total_feedback}")
                console.print(f"   Implementation rate: {analytics.implementation_rate:.1f}%")
                
                # Show feedback breakdown
                if analytics.total_feedback > 0:
                    table = Table(title=f"Feedback Breakdown (Last {days} Days)")
                    table.add_column("Type", style="cyan")
                    table.add_column("Count", justify="right")
                    table.add_column("Percentage", justify="right")
                    
                    for feedback_type, count in analytics.feedback_by_type.items():
                        if count > 0:
                            percentage = (count / analytics.total_feedback) * 100
                            table.add_row(
                                feedback_type.replace('_', ' ').title(),
                                str(count),
                                f"{percentage:.1f}%"
                            )
                    
                    console.print(table)
                
                # Show trending topics
                if analytics.trending_topics:
                    console.print(f"\n[bold]🔥 Trending Topics:[/bold]")
                    for i, topic in enumerate(analytics.trending_topics[:5], 1):
                        console.print(f"   {i}. {topic}")
                
                # Export data if requested
                if output:
                    output_path = Path(output)
                    feedback_data = {
                        'analytics': {
                            'total_feedback': analytics.total_feedback,
                            'feedback_by_type': analytics.feedback_by_type,
                            'feedback_by_priority': analytics.feedback_by_priority,
                            'feedback_by_status': analytics.feedback_by_status,
                            'trending_topics': analytics.trending_topics,
                            'implementation_rate': analytics.implementation_rate,
                            'period_start': analytics.period_start.isoformat(),
                            'period_end': analytics.period_end.isoformat()
                        },
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    with open(output_path, 'w') as f:
                        json.dump(feedback_data, f, indent=2)
                    
                    console.print(f"\n[green]💾 Feedback data exported to: {output_path}[/green]")
                
            finally:
                loop.close()
    
    @app.command()
    def analyze(
        days: int = typer.Option(90, "--days", "-d", help="Days of feedback to analyze"),
        format: str = typer.Option("table", "--format", "-f", help="Output format (table, json, summary)"),
        insights_only: bool = typer.Option(False, "--insights", help="Show only insights, not raw data")
    ):
        """🔍 Analyze community feedback patterns and generate insights"""
        console = Console()
        
        with console.status("[bold blue]Analyzing feedback patterns..."):
            manager = CommunityFeedbackManager()
            engine = FeedbackIntegrationEngine(manager)
            
            insights = engine.analyze_feedback_patterns(days)
            analytics = manager.analyze_feedback_trends(days)
        
        if format == "json":
            insights_data = [
                {
                    'type': insight.insight_type,
                    'description': insight.description,
                    'confidence': insight.confidence,
                    'feedback_count': insight.supporting_feedback_count,
                    'actions': insight.suggested_actions,
                    'timeline': insight.timeline_recommendation.value,
                    'business_value': insight.business_value
                }
                for insight in insights
            ]
            console.print_json(data=insights_data)
            return
        
        if not insights_only:
            # Show analytics summary
            console.print(f"\n[bold]📊 Feedback Analytics (Last {days} Days)[/bold]")
            
            summary_panel = Panel(
                f"Total Feedback: {analytics.total_feedback}\\n"
                f"Implementation Rate: {analytics.implementation_rate:.1f}%\\n"
                f"Avg Response Time: {analytics.average_response_time:.1f} days\\n"
                f"Analysis Period: {analytics.period_start.strftime('%Y-%m-%d')} to {analytics.period_end.strftime('%Y-%m-%d')}",
                title="Summary",
                border_style="blue"
            )
            console.print(summary_panel)
        
        # Show insights
        if insights:
            console.print(f"\n[bold]💡 Community Insights[/bold]")
            
            for insight in insights:
                # Color code by confidence
                confidence_color = "green" if insight.confidence > 0.7 else "yellow" if insight.confidence > 0.4 else "red"
                business_color = "green" if insight.business_value == "High" else "yellow" if insight.business_value == "Medium" else "red"
                
                insight_panel = Panel(
                    f"[bold]{insight.description}[/bold]\\n\\n"
                    f"[{confidence_color}]Confidence: {insight.confidence:.1%}[/{confidence_color}] | "
                    f"[{business_color}]Business Value: {insight.business_value}[/{business_color}] | "
                    f"Supporting Feedback: {insight.supporting_feedback_count}\\n\\n"
                    f"[bold]Suggested Actions:[/bold]\\n" +
                    "\\n".join(f"• {action}" for action in insight.suggested_actions) +
                    f"\\n\\n[dim]Timeline: {insight.timeline_recommendation.value.replace('_', ' ').title()}[/dim]",
                    title=f"{insight.insight_type.replace('_', ' ').title()}",
                    border_style=confidence_color
                )
                console.print(insight_panel)
        else:
            console.print("[yellow]💭 No significant patterns found in recent feedback[/yellow]")
    
    @app.command()
    def priorities(
        limit: int = typer.Option(15, "--limit", "-l", help="Number of items to show"),
        status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
        type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by feedback type"),
        format: str = typer.Option("table", "--format", "-f", help="Output format (table, json)")
    ):
        """🎯 Show prioritized community feedback for action"""
        console = Console()
        
        manager = CommunityFeedbackManager()
        priority_feedback = manager.get_prioritized_feedback(limit * 2)  # Get more for filtering
        
        # Apply filters
        if status:
            try:
                status_filter = FeedbackStatus(status.lower())
                priority_feedback = [f for f in priority_feedback if f.status == status_filter]
            except ValueError:
                console.print(f"[red]❌ Invalid status: {status}[/red]")
                return
        
        if type:
            try:
                type_filter = FeedbackType(type.lower())
                priority_feedback = [f for f in priority_feedback if f.feedback_type == type_filter]
            except ValueError:
                console.print(f"[red]❌ Invalid type: {type}[/red]")
                return
        
        # Limit results
        priority_feedback = priority_feedback[:limit]
        
        if format == "json":
            feedback_data = [
                {
                    'id': f.feedback_id,
                    'type': f.feedback_type.value,
                    'title': f.title,
                    'priority': f.priority.value,
                    'status': f.status.value,
                    'votes': f.votes,
                    'created': f.created_at.isoformat(),
                    'source': f.source
                }
                for f in priority_feedback
            ]
            console.print_json(data=feedback_data)
            return
        
        if not priority_feedback:
            console.print("[yellow]📭 No feedback items match the criteria[/yellow]")
            return
        
        # Create priority table
        table = Table(title="🎯 Prioritized Community Feedback")
        table.add_column("ID", style="dim", width=12)
        table.add_column("Type", style="cyan", width=15)
        table.add_column("Title", style="bold", width=40)
        table.add_column("Priority", justify="center", width=10)
        table.add_column("Status", justify="center", width=12)
        table.add_column("Votes", justify="right", width=8)
        table.add_column("Age", justify="right", width=8)
        table.add_column("Source", justify="center", width=10)
        
        for feedback in priority_feedback:
            # Color code by priority
            priority_color = {
                FeedbackPriority.CRITICAL: "red",
                FeedbackPriority.HIGH: "orange3",
                FeedbackPriority.MEDIUM: "yellow",
                FeedbackPriority.LOW: "blue",
                FeedbackPriority.ENHANCEMENT: "green"
            }.get(feedback.priority, "white")
            
            # Color code by status
            status_color = {
                FeedbackStatus.NEW: "red",
                FeedbackStatus.TRIAGED: "yellow",
                FeedbackStatus.IN_PROGRESS: "blue",
                FeedbackStatus.IMPLEMENTED: "green",
                FeedbackStatus.REJECTED: "dim"
            }.get(feedback.status, "white")
            
            # Calculate age
            age_days = (datetime.now() - feedback.created_at).days
            age_str = f"{age_days}d" if age_days < 30 else f"{age_days//30}mo"
            
            # Truncate title if too long
            title = feedback.title[:37] + "..." if len(feedback.title) > 40 else feedback.title
            
            table.add_row(
                feedback.feedback_id[:10],
                feedback.feedback_type.value.replace('_', ' ').title(),
                title,
                f"[{priority_color}]{feedback.priority.value.title()}[/{priority_color}]",
                f"[{status_color}]{feedback.status.value.replace('_', ' ').title()}[/{status_color}]",
                str(feedback.votes) if feedback.votes > 0 else "—",
                age_str,
                feedback.source.title()
            )
        
        console.print(table)
        
        # Show summary statistics
        priority_counts = {}
        status_counts = {}
        
        for feedback in priority_feedback:
            priority_counts[feedback.priority] = priority_counts.get(feedback.priority, 0) + 1
            status_counts[feedback.status] = status_counts.get(feedback.status, 0) + 1
        
        console.print(f"\\n[bold]📈 Summary:[/bold]")
        console.print(f"   Total items: {len(priority_feedback)}")
        console.print(f"   Critical/High priority: {priority_counts.get(FeedbackPriority.CRITICAL, 0) + priority_counts.get(FeedbackPriority.HIGH, 0)}")
        console.print(f"   New/Triaged items: {status_counts.get(FeedbackStatus.NEW, 0) + status_counts.get(FeedbackStatus.TRIAGED, 0)}")
    
    @app.command()
    def roadmap(
        quarters: int = typer.Option(4, "--quarters", "-q", help="Number of quarters to plan"),
        github_repo: Optional[str] = typer.Option(None, "--repo", "-r", help="GitHub repository"),
        output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for roadmap"),
        format: str = typer.Option("tree", "--format", "-f", help="Output format (tree, json, table)")
    ):
        """🗺️ Generate development roadmap based on community feedback"""
        console = Console()
        
        with console.status("[bold green]Generating community-driven roadmap..."):
            # Run async collection first
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                manager = CommunityFeedbackManager(github_repo=github_repo)
                loop.run_until_complete(manager.collect_all_feedback(90))
                
                engine = FeedbackIntegrationEngine(manager)
                insights = engine.analyze_feedback_patterns(90)
                tasks = engine.generate_integration_tasks(insights)
                roadmap = engine.create_development_roadmap(quarters)
                
            finally:
                loop.close()
        
        if format == "json":
            if output:
                with open(output, 'w') as f:
                    json.dump(roadmap, f, indent=2)
                console.print(f"[green]💾 Roadmap exported to: {output}[/green]")
            else:
                console.print_json(data=roadmap)
            return
        
        # Display roadmap
        console.print(f"\\n[bold]🗺️  Community-Driven Development Roadmap[/bold]")
        
        # Show community metrics
        metrics = roadmap["community_metrics"]
        metrics_panel = Panel(
            f"Total Feedback: {metrics['total_feedback']}\\n"
            f"Implementation Rate: {metrics['implementation_rate']:.1f}%\\n"
            f"Priority Items: {metrics['priority_feedback_count']}\\n"
            f"Trending: {', '.join(metrics['trending_topics'][:3])}",
            title="📊 Community Metrics",
            border_style="blue"
        )
        console.print(metrics_panel)
        
        if format == "tree":
            # Create tree view
            tree = Tree("🗺️ Development Roadmap")
            
            for quarter, quarter_data in roadmap["quarters"].items():
                if not quarter_data["tasks"]:
                    continue
                    
                capacity_pct = (quarter_data["capacity_used"] / 120) * 100  # Assuming 120h max
                quarter_node = tree.add(
                    f"[bold]{quarter}[/bold] "
                    f"({quarter_data['capacity_used']}h, {capacity_pct:.0f}% capacity)"
                )
                
                # Group tasks by action type
                tasks_by_action = {}
                for task in quarter_data["tasks"]:
                    action = task["action"]
                    if action not in tasks_by_action:
                        tasks_by_action[action] = []
                    tasks_by_action[action].append(task)
                
                for action, tasks in tasks_by_action.items():
                    action_node = quarter_node.add(f"[cyan]{action.replace('_', ' ').title()}[/cyan]")
                    
                    for task in tasks:
                        priority_color = "red" if task["priority"] > 80 else "yellow" if task["priority"] > 50 else "green"
                        action_node.add(
                            f"[{priority_color}]•[/{priority_color}] {task['title']} "
                            f"[dim]({task['effort']}h)[/dim]"
                        )
            
            console.print(tree)
        
        elif format == "table":
            # Create quarter tables
            for quarter, quarter_data in roadmap["quarters"].items():
                if not quarter_data["tasks"]:
                    continue
                
                table = Table(title=f"📅 {quarter}")
                table.add_column("Task", style="bold", width=40)
                table.add_column("Action", style="cyan", width=20)
                table.add_column("Effort", justify="right", width=8)
                table.add_column("Priority", justify="right", width=10)
                
                for task in sorted(quarter_data["tasks"], key=lambda t: -t["priority"]):
                    priority_color = "red" if task["priority"] > 80 else "yellow" if task["priority"] > 50 else "green"
                    
                    table.add_row(
                        task["title"][:37] + "..." if len(task["title"]) > 40 else task["title"],
                        task["action"].replace('_', ' ').title(),
                        f"{task['effort']}h",
                        f"[{priority_color}]{task['priority']:.0f}[/{priority_color}]"
                    )
                
                console.print(table)
                console.print(f"   Total capacity: {quarter_data['capacity_used']}h\\n")
        
        # Export if requested
        if output and format != "json":
            with open(output, 'w') as f:
                json.dump(roadmap, f, indent=2)
            console.print(f"\\n[green]💾 Roadmap data exported to: {output}[/green]")
    
    @app.command()
    def update(
        feedback_id: str = typer.Argument(..., help="Feedback ID to update"),
        status: str = typer.Option(..., "--status", "-s", help="New status"),
        notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Implementation notes")
    ):
        """✅ Update feedback status and implementation notes"""
        console = Console()
        
        try:
            status_enum = FeedbackStatus(status.lower())
        except ValueError:
            console.print(f"[red]❌ Invalid status: {status}[/red]")
            console.print(f"Valid statuses: {', '.join([s.value for s in FeedbackStatus])}")
            return
        
        manager = CommunityFeedbackManager()
        success = manager.update_feedback_status(feedback_id, status_enum, notes)
        
        if success:
            console.print(f"[green]✅ Updated feedback {feedback_id} to status: {status}[/green]")
            if notes:
                console.print(f"   Notes: {notes}")
        else:
            console.print(f"[red]❌ Feedback ID not found: {feedback_id}[/red]")
    
    @app.command()
    def stats(
        days: int = typer.Option(30, "--days", "-d", help="Days to analyze"),
        export: Optional[str] = typer.Option(None, "--export", "-e", help="Export stats to file")
    ):
        """📈 Show community feedback statistics and trends"""
        console = Console()
        
        manager = CommunityFeedbackManager()
        analytics = manager.analyze_feedback_trends(days)
        
        # Overview
        console.print(f"\\n[bold]📈 Community Feedback Statistics (Last {days} Days)[/bold]")
        
        overview_table = Table()
        overview_table.add_column("Metric", style="bold")
        overview_table.add_column("Value", justify="right")
        
        overview_table.add_row("Total Feedback", str(analytics.total_feedback))
        overview_table.add_row("Implementation Rate", f"{analytics.implementation_rate:.1f}%")
        overview_table.add_row("Avg Response Time", f"{analytics.average_response_time:.1f} days")
        
        console.print(overview_table)
        
        # Feedback by type
        if analytics.feedback_by_type:
            type_table = Table(title="📝 Feedback by Type")
            type_table.add_column("Type", style="cyan")
            type_table.add_column("Count", justify="right")
            type_table.add_column("Percentage", justify="right")
            
            total = sum(analytics.feedback_by_type.values())
            for feedback_type, count in analytics.feedback_by_type.items():
                if count > 0:
                    percentage = (count / total) * 100
                    type_table.add_row(
                        feedback_type.replace('_', ' ').title(),
                        str(count),
                        f"{percentage:.1f}%"
                    )
            
            console.print(type_table)
        
        # Feedback by priority
        if analytics.feedback_by_priority:
            priority_table = Table(title="🎯 Feedback by Priority")
            priority_table.add_column("Priority", style="bold")
            priority_table.add_column("Count", justify="right")
            priority_table.add_column("Percentage", justify="right")
            
            total = sum(analytics.feedback_by_priority.values())
            for priority, count in analytics.feedback_by_priority.items():
                if count > 0:
                    percentage = (count / total) * 100
                    priority_color = {
                        "critical": "red",
                        "high": "orange3",
                        "medium": "yellow",
                        "low": "blue",
                        "enhancement": "green"
                    }.get(priority, "white")
                    
                    priority_table.add_row(
                        f"[{priority_color}]{priority.title()}[/{priority_color}]",
                        str(count),
                        f"{percentage:.1f}%"
                    )
            
            console.print(priority_table)
        
        # Trending topics
        if analytics.trending_topics:
            console.print(f"\\n[bold]🔥 Trending Topics:[/bold]")
            for i, topic in enumerate(analytics.trending_topics[:10], 1):
                console.print(f"   {i:2d}. {topic}")
        
        # Export if requested
        if export:
            stats_data = {
                'period': {
                    'start': analytics.period_start.isoformat(),
                    'end': analytics.period_end.isoformat(),
                    'days': days
                },
                'totals': {
                    'total_feedback': analytics.total_feedback,
                    'implementation_rate': analytics.implementation_rate,
                    'average_response_time': analytics.average_response_time
                },
                'breakdown': {
                    'by_type': analytics.feedback_by_type,
                    'by_priority': analytics.feedback_by_priority,
                    'by_status': analytics.feedback_by_status
                },
                'trending_topics': analytics.trending_topics,
                'generated_at': datetime.now().isoformat()
            }
            
            with open(export, 'w') as f:
                json.dump(stats_data, f, indent=2)
            
            console.print(f"\\n[green]💾 Statistics exported to: {export}[/green]")
    
    return app


# Create the CLI app instance
community_app = create_community_cli()