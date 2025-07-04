"""
Resilience Scorer for Chaos Testing Results

Analyzes chaos testing results and generates comprehensive resilience scores
and recommendations for system improvements.
"""

import json
import os
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import xml.etree.ElementTree as ET


@dataclass
class TestSummary:
    """Summary of a test suite execution"""
    name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    execution_time: float
    error_messages: List[str]


@dataclass
class ResilienceMetrics:
    """Comprehensive resilience metrics"""
    overall_score: float
    mutation_resilience: float
    chaos_resilience: float
    span_mutation_resilience: float
    gork_resilience: float
    recovery_score: float
    fault_tolerance_score: float
    error_handling_score: float


@dataclass
class ResilienceReport:
    """Complete resilience assessment report"""
    timestamp: datetime
    overall_resilience_score: float
    detailed_metrics: ResilienceMetrics
    test_summaries: List[TestSummary]
    recommendations: List[str]
    risk_areas: List[str]
    improvement_priorities: List[str]
    compliance_status: Dict[str, str]


class ResilienceScorer:
    """
    Analyzes chaos testing results and calculates comprehensive resilience scores.
    """
    
    def __init__(self):
        self.scoring_weights = {
            "mutation_tests": 0.25,
            "chaos_replay": 0.30,
            "span_mutation": 0.20,
            "gork_generation": 0.15,
            "error_handling": 0.10
        }
        
        # Resilience thresholds
        self.thresholds = {
            "excellent": 0.9,
            "good": 0.75,
            "acceptable": 0.6,
            "needs_improvement": 0.4,
            "critical": 0.0
        }
    
    def analyze_test_results(self, results_path: str) -> ResilienceReport:
        """
        Analyze all test results and generate resilience report.
        
        Args:
            results_path: Path to directory containing test results
            
        Returns:
            ResilienceReport with comprehensive analysis
        """
        results_dir = Path(results_path)
        
        # Parse test result files
        test_summaries = []
        test_summaries.extend(self._parse_junit_results(results_dir))
        
        # Calculate resilience metrics
        metrics = self._calculate_resilience_metrics(test_summaries)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, test_summaries)
        risk_areas = self._identify_risk_areas(metrics, test_summaries)
        priorities = self._prioritize_improvements(metrics, test_summaries)
        
        # Compliance assessment
        compliance = self._assess_compliance(metrics)
        
        return ResilienceReport(
            timestamp=datetime.now(),
            overall_resilience_score=metrics.overall_score,
            detailed_metrics=metrics,
            test_summaries=test_summaries,
            recommendations=recommendations,
            risk_areas=risk_areas,
            improvement_priorities=priorities,
            compliance_status=compliance
        )
    
    def _parse_junit_results(self, results_dir: Path) -> List[TestSummary]:
        """Parse JUnit XML results"""
        summaries = []
        
        for xml_file in results_dir.glob("**/*.xml"):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Extract test suite information
                test_suite = root.find('testsuite') or root
                
                name = test_suite.get('name', xml_file.stem)
                total = int(test_suite.get('tests', 0))
                failures = int(test_suite.get('failures', 0))
                errors = int(test_suite.get('errors', 0))
                skipped = int(test_suite.get('skipped', 0))
                time = float(test_suite.get('time', 0))
                
                passed = total - failures - errors - skipped
                
                # Extract error messages
                error_messages = []
                for testcase in test_suite.findall('testcase'):
                    failure = testcase.find('failure')
                    error = testcase.find('error')
                    if failure is not None:
                        error_messages.append(failure.get('message', 'Unknown failure'))
                    if error is not None:
                        error_messages.append(error.get('message', 'Unknown error'))
                
                summary = TestSummary(
                    name=name,
                    total_tests=total,
                    passed_tests=passed,
                    failed_tests=failures + errors,
                    skipped_tests=skipped,
                    execution_time=time,
                    error_messages=error_messages
                )
                
                summaries.append(summary)
                
            except Exception as e:
                print(f"Error parsing {xml_file}: {e}")
        
        return summaries
    
    def _calculate_resilience_metrics(self, test_summaries: List[TestSummary]) -> ResilienceMetrics:
        """Calculate comprehensive resilience metrics"""
        
        # Initialize scores
        mutation_score = 0.0
        chaos_score = 0.0
        span_mutation_score = 0.0
        gork_score = 0.0
        recovery_score = 0.0
        fault_tolerance_score = 0.0
        error_handling_score = 0.0
        
        mutation_tests = [s for s in test_summaries if 'mutation' in s.name.lower()]
        chaos_tests = [s for s in test_summaries if 'chaos' in s.name.lower()]
        span_tests = [s for s in test_summaries if 'span' in s.name.lower()]
        gork_tests = [s for s in test_summaries if 'gork' in s.name.lower()]
        
        # Calculate mutation resilience
        if mutation_tests:
            mutation_score = self._calculate_test_suite_score(mutation_tests)
        
        # Calculate chaos resilience
        if chaos_tests:
            chaos_score = self._calculate_test_suite_score(chaos_tests)
            recovery_score = self._calculate_recovery_score(chaos_tests)
        
        # Calculate span mutation resilience
        if span_tests:
            span_mutation_score = self._calculate_test_suite_score(span_tests)
        
        # Calculate gork resilience
        if gork_tests:
            gork_score = self._calculate_test_suite_score(gork_tests)
        
        # Calculate fault tolerance and error handling
        all_tests = test_summaries
        if all_tests:
            fault_tolerance_score = self._calculate_fault_tolerance_score(all_tests)
            error_handling_score = self._calculate_error_handling_score(all_tests)
        
        # Calculate overall score
        component_scores = {
            "mutation_tests": mutation_score,
            "chaos_replay": chaos_score,
            "span_mutation": span_mutation_score,
            "gork_generation": gork_score,
            "error_handling": error_handling_score
        }
        
        overall_score = sum(
            score * self.scoring_weights[component]
            for component, score in component_scores.items()
        )
        
        return ResilienceMetrics(
            overall_score=overall_score,
            mutation_resilience=mutation_score,
            chaos_resilience=chaos_score,
            span_mutation_resilience=span_mutation_score,
            gork_resilience=gork_score,
            recovery_score=recovery_score,
            fault_tolerance_score=fault_tolerance_score,
            error_handling_score=error_handling_score
        )
    
    def _calculate_test_suite_score(self, test_summaries: List[TestSummary]) -> float:
        """Calculate score for a test suite"""
        if not test_summaries:
            return 0.0
        
        total_tests = sum(s.total_tests for s in test_summaries)
        passed_tests = sum(s.passed_tests for s in test_summaries)
        
        if total_tests == 0:
            return 0.0
        
        pass_rate = passed_tests / total_tests
        
        # Adjust score based on execution time (penalize very slow tests)
        avg_time = sum(s.execution_time for s in test_summaries) / len(test_summaries)
        time_penalty = min(0.1, avg_time / 600)  # Max 10% penalty for 10+ minute tests
        
        return max(0.0, pass_rate - time_penalty)
    
    def _calculate_recovery_score(self, chaos_tests: List[TestSummary]) -> float:
        """Calculate recovery score based on chaos test results"""
        if not chaos_tests:
            return 0.0
        
        # Recovery score based on how well the system handles chaos
        total_failures = sum(s.failed_tests for s in chaos_tests)
        total_tests = sum(s.total_tests for s in chaos_tests)
        
        if total_tests == 0:
            return 0.0
        
        # Recovery is better when there are fewer unexpected failures
        # Some failures are expected in chaos testing
        expected_failure_rate = 0.2  # 20% failures are acceptable
        actual_failure_rate = total_failures / total_tests
        
        if actual_failure_rate <= expected_failure_rate:
            return 1.0
        else:
            # Penalize excessive failures
            excess_failures = actual_failure_rate - expected_failure_rate
            return max(0.0, 1.0 - (excess_failures * 2))
    
    def _calculate_fault_tolerance_score(self, test_summaries: List[TestSummary]) -> float:
        """Calculate fault tolerance score"""
        if not test_summaries:
            return 0.0
        
        # Fault tolerance based on graceful degradation
        total_tests = sum(s.total_tests for s in test_summaries)
        catastrophic_failures = 0
        
        # Count catastrophic failures (specific error patterns)
        for summary in test_summaries:
            for error in summary.error_messages:
                if any(pattern in error.lower() for pattern in [
                    'segmentation fault', 'core dumped', 'stack overflow',
                    'out of memory', 'deadlock', 'panic'
                ]):
                    catastrophic_failures += 1
        
        if total_tests == 0:
            return 0.0
        
        catastrophic_rate = catastrophic_failures / total_tests
        return max(0.0, 1.0 - (catastrophic_rate * 10))  # Heavy penalty for catastrophic failures
    
    def _calculate_error_handling_score(self, test_summaries: List[TestSummary]) -> float:
        """Calculate error handling score"""
        if not test_summaries:
            return 0.0
        
        total_failures = sum(s.failed_tests for s in test_summaries)
        handled_errors = 0
        
        # Count properly handled errors (expected error patterns)
        for summary in test_summaries:
            for error in summary.error_messages:
                if any(pattern in error.lower() for pattern in [
                    'assertion', 'expected', 'validation', 'timeout',
                    'connection refused', 'service unavailable'
                ]):
                    handled_errors += 1
        
        if total_failures == 0:
            return 1.0  # No failures = perfect error handling
        
        handling_rate = handled_errors / total_failures
        return handling_rate
    
    def _generate_recommendations(self, metrics: ResilienceMetrics, 
                                test_summaries: List[TestSummary]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Overall score recommendations
        if metrics.overall_score < self.thresholds["acceptable"]:
            recommendations.append(
                "CRITICAL: Overall resilience score is below acceptable threshold. "
                "Immediate attention required for system stability."
            )
        
        # Component-specific recommendations
        if metrics.mutation_resilience < 0.7:
            recommendations.append(
                "Improve mutation testing resilience by enhancing input validation "
                "and error handling for malformed data."
            )
        
        if metrics.chaos_resilience < 0.7:
            recommendations.append(
                "Enhance chaos resilience by implementing better retry mechanisms, "
                "circuit breakers, and graceful degradation patterns."
            )
        
        if metrics.recovery_score < 0.6:
            recommendations.append(
                "Improve recovery mechanisms by implementing health checks, "
                "automatic failover, and faster error detection."
            )
        
        if metrics.error_handling_score < 0.8:
            recommendations.append(
                "Strengthen error handling by implementing comprehensive exception "
                "handling, logging, and user-friendly error messages."
            )
        
        # Specific test failure analysis
        high_failure_tests = [s for s in test_summaries if s.failed_tests > s.total_tests * 0.3]
        if high_failure_tests:
            test_names = [s.name for s in high_failure_tests]
            recommendations.append(
                f"Focus on improving tests with high failure rates: {', '.join(test_names)}"
            )
        
        return recommendations
    
    def _identify_risk_areas(self, metrics: ResilienceMetrics, 
                           test_summaries: List[TestSummary]) -> List[str]:
        """Identify high-risk areas"""
        risk_areas = []
        
        if metrics.mutation_resilience < 0.5:
            risk_areas.append("Input validation and data corruption handling")
        
        if metrics.chaos_resilience < 0.5:
            risk_areas.append("Network partition and service failure handling")
        
        if metrics.span_mutation_resilience < 0.5:
            risk_areas.append("Distributed tracing data integrity")
        
        if metrics.gork_resilience < 0.5:
            risk_areas.append("Binary data corruption and encoding issues")
        
        if metrics.fault_tolerance_score < 0.5:
            risk_areas.append("System stability under resource pressure")
        
        return risk_areas
    
    def _prioritize_improvements(self, metrics: ResilienceMetrics, 
                               test_summaries: List[TestSummary]) -> List[str]:
        """Prioritize improvement areas"""
        priorities = []
        
        # Priority 1: Critical resilience issues
        if metrics.overall_score < 0.4:
            priorities.append("P1: Address critical resilience failures immediately")
        
        # Priority 2: Component-specific issues
        component_scores = [
            ("Mutation Testing", metrics.mutation_resilience),
            ("Chaos Engineering", metrics.chaos_resilience),
            ("Span Mutation", metrics.span_mutation_resilience),
            ("Gork Testing", metrics.gork_resilience),
            ("Error Handling", metrics.error_handling_score)
        ]
        
        # Sort by lowest scores first
        component_scores.sort(key=lambda x: x[1])
        
        for component, score in component_scores:
            if score < 0.7:
                priority = "P2" if score > 0.5 else "P1"
                priorities.append(f"{priority}: Improve {component} (Score: {score:.2f})")
        
        return priorities
    
    def _assess_compliance(self, metrics: ResilienceMetrics) -> Dict[str, str]:
        """Assess compliance with resilience standards"""
        compliance = {}
        
        # Overall resilience compliance
        if metrics.overall_score >= 0.8:
            compliance["Overall"] = "COMPLIANT"
        elif metrics.overall_score >= 0.6:
            compliance["Overall"] = "PARTIALLY_COMPLIANT"
        else:
            compliance["Overall"] = "NON_COMPLIANT"
        
        # Component compliance
        components = {
            "Chaos Engineering": metrics.chaos_resilience,
            "Fault Tolerance": metrics.fault_tolerance_score,
            "Error Handling": metrics.error_handling_score,
            "Recovery": metrics.recovery_score
        }
        
        for component, score in components.items():
            if score >= 0.75:
                compliance[component] = "COMPLIANT"
            elif score >= 0.5:
                compliance[component] = "PARTIALLY_COMPLIANT"
            else:
                compliance[component] = "NON_COMPLIANT"
        
        return compliance
    
    def generate_report(self, report: ResilienceReport, output_format: str = "json") -> str:
        """Generate formatted report"""
        if output_format.lower() == "json":
            return json.dumps(asdict(report), indent=2, default=str)
        
        elif output_format.lower() == "yaml":
            import yaml
            return yaml.dump(asdict(report), default_flow_style=False)
        
        elif output_format.lower() == "csv":
            return self._generate_csv_report(report)
        
        else:
            return self._generate_text_report(report)
    
    def _generate_csv_report(self, report: ResilienceReport) -> str:
        """Generate CSV format report"""
        lines = []
        lines.append("Metric,Score,Status")
        lines.append(f"Overall Resilience,{report.overall_resilience_score:.3f},{self._get_score_status(report.overall_resilience_score)}")
        lines.append(f"Mutation Resilience,{report.detailed_metrics.mutation_resilience:.3f},{self._get_score_status(report.detailed_metrics.mutation_resilience)}")
        lines.append(f"Chaos Resilience,{report.detailed_metrics.chaos_resilience:.3f},{self._get_score_status(report.detailed_metrics.chaos_resilience)}")
        lines.append(f"Recovery Score,{report.detailed_metrics.recovery_score:.3f},{self._get_score_status(report.detailed_metrics.recovery_score)}")
        lines.append(f"Error Handling,{report.detailed_metrics.error_handling_score:.3f},{self._get_score_status(report.detailed_metrics.error_handling_score)}")
        
        return "\n".join(lines)
    
    def _generate_text_report(self, report: ResilienceReport) -> str:
        """Generate human-readable text report"""
        lines = []
        lines.append("=" * 60)
        lines.append("CHAOS TESTING RESILIENCE REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated: {report.timestamp}")
        lines.append("")
        
        # Overall score
        lines.append(f"OVERALL RESILIENCE SCORE: {report.overall_resilience_score:.3f}")
        lines.append(f"Status: {self._get_score_status(report.overall_resilience_score)}")
        lines.append("")
        
        # Detailed metrics
        lines.append("DETAILED METRICS:")
        lines.append("-" * 30)
        metrics = report.detailed_metrics
        lines.append(f"  Mutation Resilience:     {metrics.mutation_resilience:.3f}")
        lines.append(f"  Chaos Resilience:        {metrics.chaos_resilience:.3f}")
        lines.append(f"  Span Mutation:           {metrics.span_mutation_resilience:.3f}")
        lines.append(f"  Gork Resilience:         {metrics.gork_resilience:.3f}")
        lines.append(f"  Recovery Score:          {metrics.recovery_score:.3f}")
        lines.append(f"  Fault Tolerance:         {metrics.fault_tolerance_score:.3f}")
        lines.append(f"  Error Handling:          {metrics.error_handling_score:.3f}")
        lines.append("")
        
        # Test summaries
        lines.append("TEST SUMMARIES:")
        lines.append("-" * 30)
        for summary in report.test_summaries:
            pass_rate = summary.passed_tests / summary.total_tests if summary.total_tests > 0 else 0
            lines.append(f"  {summary.name}: {summary.passed_tests}/{summary.total_tests} ({pass_rate:.1%})")
        lines.append("")
        
        # Recommendations
        if report.recommendations:
            lines.append("RECOMMENDATIONS:")
            lines.append("-" * 30)
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"  {i}. {rec}")
            lines.append("")
        
        # Risk areas
        if report.risk_areas:
            lines.append("RISK AREAS:")
            lines.append("-" * 30)
            for risk in report.risk_areas:
                lines.append(f"  • {risk}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_score_status(self, score: float) -> str:
        """Get status string for a score"""
        if score >= self.thresholds["excellent"]:
            return "EXCELLENT"
        elif score >= self.thresholds["good"]:
            return "GOOD"
        elif score >= self.thresholds["acceptable"]:
            return "ACCEPTABLE"
        elif score >= self.thresholds["needs_improvement"]:
            return "NEEDS_IMPROVEMENT"
        else:
            return "CRITICAL"


def main():
    """Command line interface for resilience scorer"""
    parser = argparse.ArgumentParser(description="Analyze chaos testing results and calculate resilience scores")
    parser.add_argument("--results-path", required=True, help="Path to test results directory")
    parser.add_argument("--output-path", help="Output file path (default: stdout)")
    parser.add_argument("--format", choices=["json", "yaml", "csv", "text"], default="json", help="Output format")
    
    args = parser.parse_args()
    
    scorer = ResilienceScorer()
    report = scorer.analyze_test_results(args.results_path)
    output = scorer.generate_report(report, args.format)
    
    if args.output_path:
        with open(args.output_path, 'w') as f:
            f.write(output)
        print(f"Report written to {args.output_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()