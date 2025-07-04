"""
Chaos Testing Reporting and Historical Tracking

Provides consistent reporting formats, historical tracking,
and integration with KPI dashboards.
"""

import json
import csv
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from .resilience_scorer import ResilienceReport, ResilienceMetrics


@dataclass
class ChaosTestExecution:
    """Single chaos test execution record"""
    execution_id: str
    timestamp: datetime
    environment: str
    test_type: str
    configuration: Dict[str, Any]
    resilience_score: float
    detailed_metrics: Dict[str, Any]
    duration: float
    status: str
    error_message: Optional[str] = None


@dataclass
class HistoricalTrend:
    """Historical trend analysis"""
    metric_name: str
    time_series: List[Dict[str, Any]]
    trend_direction: str  # "improving", "declining", "stable"
    change_percentage: float
    significant_events: List[Dict[str, Any]]


class ChaosReportingManager:
    """Manages chaos testing reports and historical tracking"""
    
    def __init__(self, 
                 output_path: str = "./test-results",
                 database_path: str = "./chaos-history.db"):
        self.output_path = Path(output_path)
        self.database_path = database_path
        self.output_path.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for historical tracking"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chaos_executions (
                execution_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                environment TEXT NOT NULL,
                test_type TEXT NOT NULL,
                configuration TEXT NOT NULL,
                resilience_score REAL NOT NULL,
                detailed_metrics TEXT NOT NULL,
                duration REAL NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resilience_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (execution_id) REFERENCES chaos_executions (execution_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trend_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                trend_direction TEXT NOT NULL,
                change_percentage REAL NOT NULL,
                baseline_period_days INTEGER NOT NULL,
                analysis_data TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_execution(self, execution: ChaosTestExecution):
        """Record a chaos test execution in the database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        try:
            # Insert main execution record
            cursor.execute('''
                INSERT OR REPLACE INTO chaos_executions 
                (execution_id, timestamp, environment, test_type, configuration, 
                 resilience_score, detailed_metrics, duration, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                execution.execution_id,
                execution.timestamp.isoformat(),
                execution.environment,
                execution.test_type,
                json.dumps(execution.configuration),
                execution.resilience_score,
                json.dumps(execution.detailed_metrics),
                execution.duration,
                execution.status,
                execution.error_message
            ))
            
            # Insert individual metrics
            if execution.detailed_metrics:
                for metric_name, metric_value in execution.detailed_metrics.items():
                    if isinstance(metric_value, (int, float)):
                        cursor.execute('''
                            INSERT INTO resilience_metrics 
                            (execution_id, metric_name, metric_value, timestamp)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            execution.execution_id,
                            metric_name,
                            metric_value,
                            execution.timestamp.isoformat()
                        ))
            
            conn.commit()
            
        except Exception as e:
            print(f"Error recording execution: {e}")
            conn.rollback()
            
        finally:
            conn.close()
    
    def generate_report(self, 
                       report: ResilienceReport,
                       format_type: str = "json",
                       include_trends: bool = True) -> str:
        """Generate comprehensive report with optional trend analysis"""
        
        # Record this execution
        execution = ChaosTestExecution(
            execution_id=f"exec_{int(datetime.now().timestamp())}",
            timestamp=report.timestamp,
            environment=os.getenv('CHAOS_ENVIRONMENT', 'development'),
            test_type="comprehensive",
            configuration=self._extract_configuration(),
            resilience_score=report.overall_resilience_score,
            detailed_metrics=asdict(report.detailed_metrics),
            duration=0.0,  # Will be updated if available
            status="completed"
        )
        self.record_execution(execution)
        
        # Generate report based on format
        if format_type.lower() == "json":
            return self._generate_json_report(report, include_trends)
        elif format_type.lower() == "csv":
            return self._generate_csv_report(report)
        elif format_type.lower() == "html":
            return self._generate_html_report(report, include_trends)
        elif format_type.lower() == "dashboard":
            return self._generate_dashboard_format(report)
        else:
            return self._generate_text_report(report, include_trends)
    
    def _generate_json_report(self, report: ResilienceReport, include_trends: bool) -> str:
        """Generate JSON report with optional trend data"""
        report_data = asdict(report)
        
        if include_trends:
            trends = self.analyze_trends(days=30)
            report_data["historical_trends"] = [asdict(trend) for trend in trends]
            report_data["trend_summary"] = self._summarize_trends(trends)
        
        # Add metadata
        report_data["report_metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "format": "json",
            "version": "1.0",
            "includes_trends": include_trends
        }
        
        return json.dumps(report_data, indent=2, default=str)
    
    def _generate_csv_report(self, report: ResilienceReport) -> str:
        """Generate CSV report suitable for spreadsheet analysis"""
        output_file = self.output_path / f"resilience_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Create summary data
        summary_data = []
        metrics = report.detailed_metrics
        
        summary_data.append({
            "Metric": "Overall Resilience Score",
            "Value": report.overall_resilience_score,
            "Status": self._get_score_status(report.overall_resilience_score),
            "Timestamp": report.timestamp.isoformat()
        })
        
        summary_data.append({
            "Metric": "Mutation Resilience", 
            "Value": metrics.mutation_resilience,
            "Status": self._get_score_status(metrics.mutation_resilience),
            "Timestamp": report.timestamp.isoformat()
        })
        
        summary_data.append({
            "Metric": "Chaos Resilience",
            "Value": metrics.chaos_resilience, 
            "Status": self._get_score_status(metrics.chaos_resilience),
            "Timestamp": report.timestamp.isoformat()
        })
        
        summary_data.append({
            "Metric": "Span Mutation Resilience",
            "Value": metrics.span_mutation_resilience,
            "Status": self._get_score_status(metrics.span_mutation_resilience), 
            "Timestamp": report.timestamp.isoformat()
        })
        
        summary_data.append({
            "Metric": "Gork Resilience",
            "Value": metrics.gork_resilience,
            "Status": self._get_score_status(metrics.gork_resilience),
            "Timestamp": report.timestamp.isoformat()
        })
        
        # Write to CSV
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ["Metric", "Value", "Status", "Timestamp"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summary_data)
        
        return str(output_file)
    
    def _generate_html_report(self, report: ResilienceReport, include_trends: bool) -> str:
        """Generate HTML report with visualizations"""
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Chaos Testing Resilience Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f4f4f4; padding: 20px; }}
                .metrics {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .metric-card {{ background: white; border: 1px solid #ddd; padding: 15px; text-align: center; width: 200px; }}
                .score {{ font-size: 2em; font-weight: bold; }}
                .good {{ color: green; }}
                .warning {{ color: orange; }}
                .critical {{ color: red; }}
                .recommendations {{ background-color: #fff3cd; padding: 15px; margin: 20px 0; }}
                .trends {{ margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Chaos Testing Resilience Report</h1>
                <p>Generated: {report.timestamp}</p>
                <p>Overall Resilience Score: <span class="score {self._get_css_class(report.overall_resilience_score)}">{report.overall_resilience_score:.3f}</span></p>
            </div>
            
            <div class="metrics">
                <div class="metric-card">
                    <h3>Mutation Resilience</h3>
                    <div class="score {self._get_css_class(report.detailed_metrics.mutation_resilience)}">{report.detailed_metrics.mutation_resilience:.3f}</div>
                </div>
                <div class="metric-card">
                    <h3>Chaos Resilience</h3>
                    <div class="score {self._get_css_class(report.detailed_metrics.chaos_resilience)}">{report.detailed_metrics.chaos_resilience:.3f}</div>
                </div>
                <div class="metric-card">
                    <h3>Span Mutation</h3>
                    <div class="score {self._get_css_class(report.detailed_metrics.span_mutation_resilience)}">{report.detailed_metrics.span_mutation_resilience:.3f}</div>
                </div>
                <div class="metric-card">
                    <h3>Gork Resilience</h3>
                    <div class="score {self._get_css_class(report.detailed_metrics.gork_resilience)}">{report.detailed_metrics.gork_resilience:.3f}</div>
                </div>
            </div>
            
            <h2>Test Summaries</h2>
            <table>
                <tr><th>Test Suite</th><th>Passed</th><th>Total</th><th>Success Rate</th></tr>
                {self._generate_test_summary_rows(report.test_summaries)}
            </table>
            
            <div class="recommendations">
                <h2>Recommendations</h2>
                <ul>
                    {self._generate_recommendation_list(report.recommendations)}
                </ul>
            </div>
            
            {self._generate_trends_section(include_trends)}
            
        </body>
        </html>
        """
        
        output_file = self.output_path / f"resilience_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(output_file, 'w') as f:
            f.write(html_template)
        
        return str(output_file)
    
    def _generate_dashboard_format(self, report: ResilienceReport) -> str:
        """Generate report in format suitable for KPI dashboards"""
        dashboard_data = {
            "timestamp": report.timestamp.isoformat(),
            "metrics": {
                "overall_resilience_score": {
                    "value": report.overall_resilience_score,
                    "unit": "score",
                    "target": 0.8,
                    "status": self._get_score_status(report.overall_resilience_score)
                },
                "mutation_resilience": {
                    "value": report.detailed_metrics.mutation_resilience,
                    "unit": "score",
                    "target": 0.75,
                    "status": self._get_score_status(report.detailed_metrics.mutation_resilience)
                },
                "chaos_resilience": {
                    "value": report.detailed_metrics.chaos_resilience,
                    "unit": "score", 
                    "target": 0.75,
                    "status": self._get_score_status(report.detailed_metrics.chaos_resilience)
                },
                "recovery_score": {
                    "value": report.detailed_metrics.recovery_score,
                    "unit": "score",
                    "target": 0.7,
                    "status": self._get_score_status(report.detailed_metrics.recovery_score)
                }
            },
            "alerts": [
                {
                    "level": "critical" if report.overall_resilience_score < 0.5 else 
                             "warning" if report.overall_resilience_score < 0.7 else "info",
                    "message": f"Overall resilience score: {report.overall_resilience_score:.3f}",
                    "timestamp": report.timestamp.isoformat()
                }
            ],
            "compliance_status": report.compliance_status,
            "environment": os.getenv('CHAOS_ENVIRONMENT', 'development')
        }
        
        return json.dumps(dashboard_data, indent=2, default=str)
    
    def analyze_trends(self, days: int = 30) -> List[HistoricalTrend]:
        """Analyze historical trends over specified period"""
        conn = sqlite3.connect(self.database_path)
        
        # Get data from last N days
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        query = '''
            SELECT metric_name, metric_value, timestamp
            FROM resilience_metrics 
            WHERE timestamp >= ?
            ORDER BY metric_name, timestamp
        '''
        
        df = pd.read_sql_query(query, conn, params=[cutoff_date])
        conn.close()
        
        if df.empty:
            return []
        
        trends = []
        
        # Analyze each metric
        for metric_name in df['metric_name'].unique():
            metric_data = df[df['metric_name'] == metric_name].copy()
            metric_data['timestamp'] = pd.to_datetime(metric_data['timestamp'])
            metric_data = metric_data.sort_values('timestamp')
            
            if len(metric_data) < 2:
                continue
            
            # Calculate trend
            first_value = metric_data.iloc[0]['metric_value']
            last_value = metric_data.iloc[-1]['metric_value']
            change_percentage = ((last_value - first_value) / first_value) * 100 if first_value != 0 else 0
            
            # Determine trend direction
            if abs(change_percentage) < 5:
                trend_direction = "stable"
            elif change_percentage > 0:
                trend_direction = "improving"
            else:
                trend_direction = "declining"
            
            # Create time series data
            time_series = []
            for _, row in metric_data.iterrows():
                time_series.append({
                    "timestamp": row['timestamp'].isoformat(),
                    "value": row['metric_value']
                })
            
            # Identify significant events (large changes)
            significant_events = []
            for i in range(1, len(metric_data)):
                prev_value = metric_data.iloc[i-1]['metric_value']
                curr_value = metric_data.iloc[i]['metric_value']
                change = abs(curr_value - prev_value) / prev_value * 100 if prev_value != 0 else 0
                
                if change > 20:  # 20% change threshold
                    significant_events.append({
                        "timestamp": metric_data.iloc[i]['timestamp'].isoformat(),
                        "change_percentage": change,
                        "description": f"{metric_name} changed by {change:.1f}%"
                    })
            
            trend = HistoricalTrend(
                metric_name=metric_name,
                time_series=time_series,
                trend_direction=trend_direction,
                change_percentage=change_percentage,
                significant_events=significant_events
            )
            trends.append(trend)
        
        return trends
    
    def generate_trend_visualization(self, days: int = 30, output_file: str = None):
        """Generate trend visualization charts"""
        trends = self.analyze_trends(days)
        
        if not trends:
            print("No trend data available")
            return
        
        # Set up the plot
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Chaos Testing Trends - Last {days} Days', fontsize=16)
        
        # Plot key metrics
        key_metrics = ['overall_resilience_score', 'mutation_resilience', 'chaos_resilience', 'recovery_score']
        
        for i, metric in enumerate(key_metrics):
            ax = axes[i // 2, i % 2]
            
            # Find trend data for this metric
            trend_data = next((t for t in trends if t.metric_name == metric), None)
            
            if trend_data:
                timestamps = [datetime.fromisoformat(ts['timestamp']) for ts in trend_data.time_series]
                values = [ts['value'] for ts in trend_data.time_series]
                
                ax.plot(timestamps, values, marker='o', linestyle='-', linewidth=2)
                ax.set_title(f'{metric.replace("_", " ").title()}')
                ax.set_ylabel('Score')
                ax.grid(True, alpha=0.3)
                
                # Add trend line
                if len(values) > 1:
                    z = np.polyfit(range(len(values)), values, 1)
                    trend_line = np.poly1d(z)
                    ax.plot(timestamps, trend_line(range(len(values))), "--", alpha=0.8, color='red')
                
                # Color code based on trend
                color = 'green' if trend_data.trend_direction == 'improving' else \
                       'red' if trend_data.trend_direction == 'declining' else 'blue'
                ax.set_facecolor(f'{color}', alpha=0.1)
            else:
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f'{metric.replace("_", " ").title()}')
        
        plt.tight_layout()
        
        if output_file is None:
            output_file = self.output_path / f"trends_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Trend visualization saved to {output_file}")
        return str(output_file)
    
    def cleanup_old_data(self, retention_days: int = 30):
        """Clean up old data based on retention policy"""
        cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        try:
            # Delete old metrics
            cursor.execute('DELETE FROM resilience_metrics WHERE timestamp < ?', [cutoff_date])
            
            # Delete old executions
            cursor.execute('DELETE FROM chaos_executions WHERE timestamp < ?', [cutoff_date])
            
            # Delete old trend analyses
            cursor.execute('DELETE FROM trend_analysis WHERE analysis_date < ?', [cutoff_date])
            
            conn.commit()
            print(f"Cleaned up data older than {retention_days} days")
            
        except Exception as e:
            print(f"Error cleaning up old data: {e}")
            conn.rollback()
            
        finally:
            conn.close()
    
    def export_historical_data(self, format_type: str = "csv", days: int = 90) -> str:
        """Export historical data for external analysis"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        conn = sqlite3.connect(self.database_path)
        
        if format_type.lower() == "csv":
            # Export to CSV files
            executions_df = pd.read_sql_query(
                'SELECT * FROM chaos_executions WHERE timestamp >= ?', 
                conn, params=[cutoff_date]
            )
            
            metrics_df = pd.read_sql_query(
                'SELECT * FROM resilience_metrics WHERE timestamp >= ?',
                conn, params=[cutoff_date]
            )
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            executions_file = self.output_path / f"chaos_executions_{timestamp}.csv"
            metrics_file = self.output_path / f"resilience_metrics_{timestamp}.csv"
            
            executions_df.to_csv(executions_file, index=False)
            metrics_df.to_csv(metrics_file, index=False)
            
            conn.close()
            return f"Exported to {executions_file} and {metrics_file}"
        
        else:
            # Export to JSON
            executions = []
            metrics = []
            
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM chaos_executions WHERE timestamp >= ?', [cutoff_date])
            for row in cursor.fetchall():
                executions.append(dict(zip([col[0] for col in cursor.description], row)))
            
            cursor.execute('SELECT * FROM resilience_metrics WHERE timestamp >= ?', [cutoff_date])
            for row in cursor.fetchall():
                metrics.append(dict(zip([col[0] for col in cursor.description], row)))
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "period_days": days,
                "executions": executions,
                "metrics": metrics
            }
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_file = self.output_path / f"chaos_historical_data_{timestamp}.json"
            
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            conn.close()
            return f"Exported to {export_file}"
    
    # Helper methods
    def _extract_configuration(self) -> Dict[str, Any]:
        """Extract current configuration for recording"""
        return {
            "environment": os.getenv('CHAOS_ENVIRONMENT', 'development'),
            "intensity": os.getenv('CHAOS_INTENSITY', '0.3'),
            "duration": os.getenv('CHAOS_DURATION', '120'),
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_score_status(self, score: float) -> str:
        """Get status string for a score"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.75:
            return "good"
        elif score >= 0.6:
            return "acceptable"
        elif score >= 0.4:
            return "needs_improvement"
        else:
            return "critical"
    
    def _get_css_class(self, score: float) -> str:
        """Get CSS class for score visualization"""
        if score >= 0.75:
            return "good"
        elif score >= 0.5:
            return "warning"
        else:
            return "critical"
    
    def _generate_test_summary_rows(self, test_summaries) -> str:
        """Generate HTML table rows for test summaries"""
        rows = []
        for summary in test_summaries:
            success_rate = summary.passed_tests / summary.total_tests if summary.total_tests > 0 else 0
            rows.append(f"""
                <tr>
                    <td>{summary.name}</td>
                    <td>{summary.passed_tests}</td>
                    <td>{summary.total_tests}</td>
                    <td>{success_rate:.1%}</td>
                </tr>
            """)
        return "".join(rows)
    
    def _generate_recommendation_list(self, recommendations) -> str:
        """Generate HTML list for recommendations"""
        items = []
        for rec in recommendations:
            items.append(f"<li>{rec}</li>")
        return "".join(items)
    
    def _generate_trends_section(self, include_trends: bool) -> str:
        """Generate trends section for HTML report"""
        if not include_trends:
            return ""
        
        return """
            <div class="trends">
                <h2>Historical Trends</h2>
                <p>Trend analysis is available in the detailed JSON report and visualization charts.</p>
                <p>Use the generate_trend_visualization() method to create trend charts.</p>
            </div>
        """
    
    def _summarize_trends(self, trends: List[HistoricalTrend]) -> Dict[str, Any]:
        """Summarize trends for report inclusion"""
        summary = {
            "total_metrics": len(trends),
            "improving": len([t for t in trends if t.trend_direction == "improving"]),
            "declining": len([t for t in trends if t.trend_direction == "declining"]),
            "stable": len([t for t in trends if t.trend_direction == "stable"]),
            "significant_events": sum(len(t.significant_events) for t in trends)
        }
        
        return summary
    
    def _generate_text_report(self, report: ResilienceReport, include_trends: bool) -> str:
        """Generate simple text report"""
        lines = []
        lines.append("=" * 60)
        lines.append("CHAOS TESTING RESILIENCE REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated: {report.timestamp}")
        lines.append("")
        
        lines.append(f"OVERALL RESILIENCE SCORE: {report.overall_resilience_score:.3f}")
        lines.append(f"Status: {self._get_score_status(report.overall_resilience_score).upper()}")
        lines.append("")
        
        lines.append("DETAILED METRICS:")
        lines.append("-" * 30)
        metrics = report.detailed_metrics
        lines.append(f"  Mutation Resilience:     {metrics.mutation_resilience:.3f}")
        lines.append(f"  Chaos Resilience:        {metrics.chaos_resilience:.3f}")
        lines.append(f"  Span Mutation:           {metrics.span_mutation_resilience:.3f}")
        lines.append(f"  Gork Resilience:         {metrics.gork_resilience:.3f}")
        lines.append(f"  Recovery Score:          {metrics.recovery_score:.3f}")
        lines.append("")
        
        if include_trends:
            trends = self.analyze_trends(days=30)
            if trends:
                lines.append("TREND ANALYSIS (30 days):")
                lines.append("-" * 30)
                for trend in trends[:5]:  # Show top 5 trends
                    lines.append(f"  {trend.metric_name}: {trend.trend_direction} ({trend.change_percentage:+.1f}%)")
                lines.append("")
        
        return "\n".join(lines)