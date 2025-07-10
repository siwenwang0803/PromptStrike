#!/usr/bin/env python3
"""
PromptStrike Nightly PDF Generation Monitor
监控夜间 PDF 生成任务的成功率和文件大小
Monitors nightly PDF generation success rate and file sizes
"""

import os
import json
import time
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PDFGenerationRecord:
    """Record of a PDF generation attempt"""
    timestamp: str
    workflow_run_id: str
    success: bool
    file_size_mb: float
    file_path: str
    generation_time_seconds: float
    error_message: Optional[str] = None
    compliance_frameworks: List[str] = None
    
    def __post_init__(self):
        if self.compliance_frameworks is None:
            self.compliance_frameworks = []


class NightlyPDFMonitor:
    """Monitor for nightly PDF generation jobs"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.records: List[PDFGenerationRecord] = []
        self.data_file = Path(self.config.get('data_file', 'pdf_generation_history.json'))
        self.max_file_size_mb = self.config.get('max_file_size_mb', 3.0)
        self.target_success_rate = self.config.get('target_success_rate', 100.0)
        
        # Load existing records
        self._load_records()
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load monitoring configuration"""
        default_config = {
            'github_token': os.environ.get('GITHUB_TOKEN'),
            'repo_owner': 'siwenwang0803',
            'repo_name': 'PromptStrike',
            'workflow_name': 'evidence.yml',
            'data_file': 'pdf_generation_history.json',
            'max_file_size_mb': 3.0,
            'target_success_rate': 100.0,
            'retention_days': 30,
            'alert_threshold': 80.0,
            'monitoring_enabled': True
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _load_records(self):
        """Load historical PDF generation records"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.records = [
                        PDFGenerationRecord(**record) 
                        for record in data.get('records', [])
                    ]
                logger.info(f"Loaded {len(self.records)} historical records")
            except Exception as e:
                logger.warning(f"Failed to load records: {e}")
                self.records = []
    
    def _save_records(self):
        """Save PDF generation records to file"""
        # Clean up old records
        cutoff_date = datetime.now() - timedelta(days=self.config['retention_days'])
        self.records = [
            record for record in self.records
            if datetime.fromisoformat(record.timestamp) > cutoff_date
        ]
        
        data = {
            'last_updated': datetime.now().isoformat(),
            'config': self.config,
            'records': [asdict(record) for record in self.records]
        }
        
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.records)} records to {self.data_file}")
        except Exception as e:
            logger.error(f"Failed to save records: {e}")
    
    def check_github_workflow_runs(self) -> List[Dict]:
        """Check recent GitHub workflow runs for evidence generation"""
        if not self.config.get('github_token'):
            logger.warning("GitHub token not provided, skipping workflow check")
            return []
        
        headers = {
            'Authorization': f"token {self.config['github_token']}",
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f"https://api.github.com/repos/{self.config['repo_owner']}/{self.config['repo_name']}/actions/runs"
        params = {
            'per_page': 50,
            'status': 'completed'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            runs = response.json().get('workflow_runs', [])
            # Filter for evidence workflow runs
            evidence_runs = [
                run for run in runs
                if 'evidence' in run.get('name', '').lower()
            ]
            
            logger.info(f"Found {len(evidence_runs)} evidence workflow runs")
            return evidence_runs
            
        except Exception as e:
            logger.error(f"Failed to check workflow runs: {e}")
            return []
    
    def check_workflow_artifacts(self, run_id: str) -> List[Dict]:
        """Check artifacts from a specific workflow run"""
        if not self.config.get('github_token'):
            return []
        
        headers = {
            'Authorization': f"token {self.config['github_token']}",
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f"https://api.github.com/repos/{self.config['repo_owner']}/{self.config['repo_name']}/actions/runs/{run_id}/artifacts"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            artifacts = response.json().get('artifacts', [])
            pdf_artifacts = [
                artifact for artifact in artifacts
                if 'pdf' in artifact.get('name', '').lower() or 'compliance' in artifact.get('name', '').lower()
            ]
            
            return pdf_artifacts
            
        except Exception as e:
            logger.error(f"Failed to check artifacts for run {run_id}: {e}")
            return []
    
    def analyze_local_pdfs(self, directory: str) -> List[PDFGenerationRecord]:
        """Analyze local PDF files for monitoring"""
        pdf_dir = Path(directory)
        if not pdf_dir.exists():
            logger.warning(f"PDF directory not found: {directory}")
            return []
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        records = []
        
        for pdf_file in pdf_files:
            try:
                stat = pdf_file.stat()
                file_size_mb = stat.st_size / (1024 * 1024)
                modification_time = datetime.fromtimestamp(stat.st_mtime)
                
                # Basic content analysis
                success = True
                error_message = None
                
                # Check file size
                if file_size_mb > self.max_file_size_mb:
                    success = False
                    error_message = f"File size {file_size_mb:.2f} MB exceeds {self.max_file_size_mb} MB limit"
                
                # Check if file is readable
                try:
                    with open(pdf_file, 'rb') as f:
                        header = f.read(8)
                        if not header.startswith(b'%PDF'):
                            success = False
                            error_message = "File is not a valid PDF"
                except Exception as e:
                    success = False
                    error_message = f"Cannot read PDF file: {e}"
                
                record = PDFGenerationRecord(
                    timestamp=modification_time.isoformat(),
                    workflow_run_id=f"local_{pdf_file.stem}",
                    success=success,
                    file_size_mb=file_size_mb,
                    file_path=str(pdf_file),
                    generation_time_seconds=0.0,
                    error_message=error_message
                )
                
                records.append(record)
                
            except Exception as e:
                logger.error(f"Failed to analyze {pdf_file}: {e}")
        
        return records
    
    def calculate_success_metrics(self, days: int = 7) -> Dict:
        """Calculate success metrics for the specified period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_records = [
            record for record in self.records
            if datetime.fromisoformat(record.timestamp) > cutoff_date
        ]
        
        if not recent_records:
            return {
                'period_days': days,
                'total_attempts': 0,
                'successful_attempts': 0,
                'success_rate': 0.0,
                'average_file_size_mb': 0.0,
                'max_file_size_mb': 0.0,
                'file_size_violations': 0,
                'average_generation_time': 0.0,
                'status': 'NO_DATA'
            }
        
        total_attempts = len(recent_records)
        successful_attempts = sum(1 for record in recent_records if record.success)
        success_rate = (successful_attempts / total_attempts) * 100
        
        file_sizes = [record.file_size_mb for record in recent_records if record.success]
        average_file_size = sum(file_sizes) / len(file_sizes) if file_sizes else 0
        max_file_size = max(file_sizes) if file_sizes else 0
        
        file_size_violations = sum(
            1 for record in recent_records 
            if record.file_size_mb > self.max_file_size_mb
        )
        
        generation_times = [
            record.generation_time_seconds for record in recent_records 
            if record.generation_time_seconds > 0
        ]
        average_generation_time = sum(generation_times) / len(generation_times) if generation_times else 0
        
        # Determine status
        if success_rate >= self.target_success_rate:
            status = 'EXCELLENT'
        elif success_rate >= 90:
            status = 'GOOD'
        elif success_rate >= self.config['alert_threshold']:
            status = 'ACCEPTABLE'
        else:
            status = 'POOR'
        
        return {
            'period_days': days,
            'total_attempts': total_attempts,
            'successful_attempts': successful_attempts,
            'success_rate': success_rate,
            'average_file_size_mb': average_file_size,
            'max_file_size_mb': max_file_size,
            'file_size_violations': file_size_violations,
            'average_generation_time': average_generation_time,
            'status': status,
            'target_success_rate': self.target_success_rate,
            'max_allowed_file_size': self.max_file_size_mb
        }
    
    def generate_monitoring_report(self) -> Dict:
        """Generate comprehensive monitoring report"""
        now = datetime.now()
        
        # Calculate metrics for different periods
        metrics_1d = self.calculate_success_metrics(1)
        metrics_7d = self.calculate_success_metrics(7)
        metrics_30d = self.calculate_success_metrics(30)
        
        # Recent failures
        recent_failures = [
            record for record in self.records[-10:]
            if not record.success
        ]
        
        # File size analysis
        all_sizes = [record.file_size_mb for record in self.records if record.success]
        size_stats = {
            'min': min(all_sizes) if all_sizes else 0,
            'max': max(all_sizes) if all_sizes else 0,
            'average': sum(all_sizes) / len(all_sizes) if all_sizes else 0,
            'violations': sum(1 for size in all_sizes if size > self.max_file_size_mb)
        }
        
        return {
            'generated_at': now.isoformat(),
            'monitoring_config': {
                'max_file_size_mb': self.max_file_size_mb,
                'target_success_rate': self.target_success_rate,
                'retention_days': self.config['retention_days']
            },
            'metrics': {
                'last_24h': metrics_1d,
                'last_7d': metrics_7d,
                'last_30d': metrics_30d
            },
            'file_size_analysis': size_stats,
            'recent_failures': [
                {
                    'timestamp': record.timestamp,
                    'error': record.error_message,
                    'file_size_mb': record.file_size_mb
                }
                for record in recent_failures
            ],
            'total_records': len(self.records),
            'recommendations': self._generate_recommendations(metrics_7d)
        }
    
    def _generate_recommendations(self, metrics: Dict) -> List[str]:
        """Generate recommendations based on metrics"""
        recommendations = []
        
        if metrics['success_rate'] < self.target_success_rate:
            recommendations.append(
                f"Success rate {metrics['success_rate']:.1f}% is below target {self.target_success_rate}%. "
                "Review recent failures and address root causes."
            )
        
        if metrics['file_size_violations'] > 0:
            recommendations.append(
                f"Found {metrics['file_size_violations']} file size violations. "
                "Consider optimizing PDF templates or compressing images."
            )
        
        if metrics['max_file_size_mb'] > self.max_file_size_mb * 0.9:
            recommendations.append(
                f"Maximum file size {metrics['max_file_size_mb']:.2f} MB is close to limit. "
                "Monitor template complexity and consider optimization."
            )
        
        if metrics['average_generation_time'] > 300:  # 5 minutes
            recommendations.append(
                f"Average generation time {metrics['average_generation_time']:.1f}s is high. "
                "Consider optimizing the report generation process."
            )
        
        if not recommendations:
            recommendations.append("All metrics are within acceptable ranges. Continue monitoring.")
        
        return recommendations
    
    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle"""
        logger.info("Starting PDF generation monitoring cycle")
        
        # Check GitHub workflow runs
        workflow_runs = self.check_github_workflow_runs()
        
        # Analyze local PDFs if available
        local_pdfs_dir = os.environ.get('PDF_REPORTS_DIR', 'reports/evidence')
        if os.path.exists(local_pdfs_dir):
            local_records = self.analyze_local_pdfs(local_pdfs_dir)
            self.records.extend(local_records)
        
        # Generate and save report
        report = self.generate_monitoring_report()
        
        # Save records
        self._save_records()
        
        # Print summary
        self._print_monitoring_summary(report)
        
        return report
    
    def _print_monitoring_summary(self, report: Dict):
        """Print monitoring summary to console"""
        print("\n📊 Nightly PDF Generation Monitoring Summary")
        print("=" * 60)
        
        metrics_7d = report['metrics']['last_7d']
        
        print(f"📈 7-Day Performance:")
        print(f"  Total attempts: {metrics_7d['total_attempts']}")
        print(f"  Successful: {metrics_7d['successful_attempts']}")
        print(f"  Success rate: {metrics_7d['success_rate']:.1f}%")
        print(f"  Target: {metrics_7d['target_success_rate']:.1f}%")
        print(f"  Status: {metrics_7d['status']}")
        
        print(f"\n📏 File Size Analysis:")
        print(f"  Average size: {metrics_7d['average_file_size_mb']:.2f} MB")
        print(f"  Max size: {metrics_7d['max_file_size_mb']:.2f} MB")
        print(f"  Size limit: {metrics_7d['max_allowed_file_size']:.2f} MB")
        print(f"  Violations: {metrics_7d['file_size_violations']}")
        
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
        
        # Overall status
        if metrics_7d['success_rate'] >= 100:
            print(f"\n🎉 Status: EXCELLENT - Target achieved!")
        elif metrics_7d['success_rate'] >= 90:
            print(f"\n✅ Status: GOOD - Performance acceptable")
        elif metrics_7d['success_rate'] >= 80:
            print(f"\n⚠️  Status: ACCEPTABLE - Needs improvement")
        else:
            print(f"\n❌ Status: POOR - Immediate attention required")


def main():
    """Main entry point for PDF generation monitoring"""
    parser = argparse.ArgumentParser(
        description="Monitor nightly PDF generation success rate and file sizes"
    )
    parser.add_argument(
        '--config',
        help='Path to configuration JSON file'
    )
    parser.add_argument(
        '--pdf-dir',
        help='Directory containing PDF files to analyze'
    )
    parser.add_argument(
        '--output-report',
        help='Save detailed report to JSON file'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run in continuous monitoring mode'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=3600,
        help='Monitoring interval in seconds (default: 3600)'
    )
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = NightlyPDFMonitor(args.config)
    
    # Set PDF directory if provided
    if args.pdf_dir:
        os.environ['PDF_REPORTS_DIR'] = args.pdf_dir
    
    if args.continuous:
        # Continuous monitoring mode
        logger.info(f"Starting continuous monitoring with {args.interval}s interval")
        while True:
            try:
                report = monitor.run_monitoring_cycle()
                if args.output_report:
                    with open(args.output_report, 'w') as f:
                        json.dump(report, f, indent=2)
                time.sleep(args.interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(60)  # Wait before retrying
    else:
        # Single monitoring run
        report = monitor.run_monitoring_cycle()
        
        if args.output_report:
            with open(args.output_report, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Detailed report saved to: {args.output_report}")
        
        # Exit with appropriate code
        metrics_7d = report['metrics']['last_7d']
        if metrics_7d['success_rate'] >= 100 and metrics_7d['file_size_violations'] == 0:
            exit(0)
        elif metrics_7d['success_rate'] >= 90:
            exit(1)
        else:
            exit(2)


if __name__ == "__main__":
    main()