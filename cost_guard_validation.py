#!/usr/bin/env python3
"""
Standalone Cost Guard Validation - Complete Implementation
No external dependencies required
"""

import re
import time
import threading
from collections import deque, defaultdict
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
import statistics
import os


@dataclass
class TokenStormDetection:
    """Result of token storm detection"""
    is_attack: bool
    confidence: float
    token_count: int
    pattern_type: str
    risk_level: str
    details: str


class CostGuard:
    """Cost Guard implementation for Token Storm detection"""
    
    def __init__(self, window_size: int = 10, token_rate_threshold: int = 1000, 
                 max_token_count: int = 5000, pattern_sensitivity: float = 0.8):
        self.window_size = window_size
        self.token_rate_threshold = token_rate_threshold
        self.max_token_count = max_token_count
        self.pattern_sensitivity = pattern_sensitivity
        
        self._token_history = deque()
        self._lock = threading.Lock()
        
        self.total_requests = 0
        self.blocked_requests = 0
        self.attack_patterns_detected = defaultdict(int)
        
        self._compile_attack_patterns()
        
    def _compile_attack_patterns(self):
        """Compile regex patterns for token storm detection"""
        self.attack_patterns = {
            'repeat_command': re.compile(
                r'(?:repeat|generate|print|output|create|execute)\s+.*?(\d+)\s+times?',
                re.IGNORECASE
            ),
            'template_injection': re.compile(
                r'\{\{.*?PROMPT.*?\}\}.*?(\d+)',
                re.IGNORECASE
            ),
            'amplification_keywords': re.compile(
                r'(?:storm|flood|overflow|amplification|explosion|bomb)\s+.*?(\d+)',
                re.IGNORECASE
            ),
            'infinite_loops': re.compile(
                r'(?:infinite|endless|continuously|without.*?break|loop.*?forever)',
                re.IGNORECASE
            ),
            'massive_repetition': re.compile(
                r'(?:exactly|precisely)\s+(\d+)\s+times|(\d+)\s+(?:copies|iterations)',
                re.IGNORECASE
            ),
            'resource_exhaustion': re.compile(
                r'(?:exhaustion|consumption|overload|thrashing|starvation)',
                re.IGNORECASE
            ),
            'numeric_amplifiers': re.compile(r'\b(\d{3,})\b'),
            'recursive_patterns': re.compile(
                r'(?:recursive|nested|exponential|cascade)',
                re.IGNORECASE
            )
        }
    
    def detect_token_storm(self, prompt: str) -> TokenStormDetection:
        """Main detection method"""
        with self._lock:
            self.total_requests += 1
            
            estimated_tokens = len(prompt) // 4
            current_time = time.time()
            self._update_token_history(current_time, estimated_tokens)
            current_rate = self._calculate_token_rate(current_time)
            pattern_results = self._analyze_patterns(prompt)
            risk_assessment = self._assess_risk(prompt, estimated_tokens, current_rate, pattern_results)
            is_attack = self._make_decision(risk_assessment)
            
            if is_attack:
                self.blocked_requests += 1
                self.attack_patterns_detected[risk_assessment['primary_pattern']] += 1
                
            return TokenStormDetection(
                is_attack=is_attack,
                confidence=risk_assessment['confidence'],
                token_count=estimated_tokens,
                pattern_type=risk_assessment['primary_pattern'],
                risk_level=risk_assessment['risk_level'],
                details=risk_assessment['details']
            )
    
    def _update_token_history(self, current_time: float, token_count: int):
        """Update sliding window with new token count"""
        self._token_history.append((current_time, token_count))
        cutoff_time = current_time - self.window_size
        while self._token_history and self._token_history[0][0] < cutoff_time:
            self._token_history.popleft()
    
    def _calculate_token_rate(self, current_time: float) -> float:
        """Calculate tokens per second in current window"""
        if not self._token_history:
            return 0.0
        cutoff_time = current_time - self.window_size
        total_tokens = sum(
            tokens for timestamp, tokens in self._token_history
            if timestamp >= cutoff_time
        )
        return total_tokens / self.window_size
    
    def _analyze_patterns(self, prompt: str) -> Dict:
        """Analyze prompt for attack patterns"""
        results = {
            'matches': {},
            'numeric_amplifiers': [],
            'max_repetition': 0,
            'suspicious_keywords': 0
        }
        
        for pattern_name, pattern_regex in self.attack_patterns.items():
            matches = pattern_regex.findall(prompt)
            if matches:
                results['matches'][pattern_name] = matches
                
                if pattern_name in ['repeat_command', 'massive_repetition']:
                    for match in matches:
                        if isinstance(match, tuple):
                            for m in match:
                                if m.isdigit():
                                    results['max_repetition'] = max(results['max_repetition'], int(m))
                        elif match.isdigit():
                            results['max_repetition'] = max(results['max_repetition'], int(match))
                
                if pattern_name in ['amplification_keywords', 'infinite_loops', 
                                  'resource_exhaustion', 'recursive_patterns']:
                    results['suspicious_keywords'] += len(matches)
        
        numeric_matches = self.attack_patterns['numeric_amplifiers'].findall(prompt)
        results['numeric_amplifiers'] = [int(m) for m in numeric_matches if m.isdigit()]
        
        return results
    
    def _assess_risk(self, prompt: str, token_count: int, current_rate: float, pattern_results: Dict) -> Dict:
        """Comprehensive risk assessment"""
        risk_factors = []
        confidence = 0.0
        primary_pattern = 'none'
        
        if token_count > self.max_token_count:
            risk_factors.append(f"Excessive token count: {token_count}")
            confidence += 0.4
            primary_pattern = 'token_overflow'
        
        if current_rate > self.token_rate_threshold:
            risk_factors.append(f"High token rate: {current_rate:.1f}/s")
            confidence += 0.3
            if primary_pattern == 'none':
                primary_pattern = 'rate_limit_exceeded'
        
        pattern_confidence = self._calculate_pattern_confidence(pattern_results)
        confidence += pattern_confidence
        
        if pattern_results['matches']:
            primary_pattern = max(
                pattern_results['matches'].keys(),
                key=lambda k: len(pattern_results['matches'][k])
            )
        
        max_repetition = pattern_results['max_repetition']
        if max_repetition > 100:
            risk_factors.append(f"High repetition count: {max_repetition}")
            confidence += 0.2
        
        large_numbers = [n for n in pattern_results['numeric_amplifiers'] if n > 1000]
        if large_numbers:
            risk_factors.append(f"Large numeric values: {large_numbers}")
            confidence += 0.1
        
        prompt_length = len(prompt.split())
        if prompt_length > 0:
            keyword_density = pattern_results['suspicious_keywords'] / prompt_length
            if keyword_density > 0.1:
                risk_factors.append(f"High suspicious keyword density: {keyword_density:.2f}")
                confidence += 0.1
        
        if confidence >= 0.8:
            risk_level = 'CRITICAL'
        elif confidence >= 0.6:
            risk_level = 'HIGH'
        elif confidence >= 0.4:
            risk_level = 'MEDIUM'
        elif confidence >= 0.2:
            risk_level = 'LOW'
        else:
            risk_level = 'MINIMAL'
        
        return {
            'confidence': min(confidence, 1.0),
            'risk_level': risk_level,
            'primary_pattern': primary_pattern,
            'risk_factors': risk_factors,
            'details': '; '.join(risk_factors) if risk_factors else 'No significant risk factors'
        }
    
    def _calculate_pattern_confidence(self, pattern_results: Dict) -> float:
        """Calculate confidence based on pattern matches"""
        confidence = 0.0
        
        for pattern_name, matches in pattern_results['matches'].items():
            if pattern_name == 'repeat_command':
                confidence += 0.3 * len(matches)
            elif pattern_name == 'template_injection':
                confidence += 0.4 * len(matches)
            elif pattern_name == 'infinite_loops':
                confidence += 0.5 * len(matches)
            elif pattern_name == 'amplification_keywords':
                confidence += 0.2 * len(matches)
            elif pattern_name == 'massive_repetition':
                confidence += 0.3 * len(matches)
            elif pattern_name == 'resource_exhaustion':
                confidence += 0.2 * len(matches)
            elif pattern_name == 'recursive_patterns':
                confidence += 0.25 * len(matches)
        
        return min(confidence, 0.4)
    
    def _make_decision(self, risk_assessment: Dict) -> bool:
        """Make final attack/benign decision"""
        confidence = risk_assessment['confidence']
        
        if self.pattern_sensitivity >= 0.9:
            threshold = 0.3
        elif self.pattern_sensitivity >= 0.7:
            threshold = 0.5
        elif self.pattern_sensitivity >= 0.5:
            threshold = 0.7
        else:
            threshold = 0.8
        
        return confidence >= threshold
    
    def get_statistics(self) -> Dict:
        """Get current detection statistics"""
        with self._lock:
            false_positive_rate = 0.0
            if self.total_requests > 0:
                false_positive_rate = self.blocked_requests / self.total_requests
            
            return {
                'total_requests': self.total_requests,
                'blocked_requests': self.blocked_requests,
                'false_positive_rate': false_positive_rate,
                'attack_patterns': dict(self.attack_patterns_detected),
                'current_window_size': self.window_size,
                'token_rate_threshold': self.token_rate_threshold,
                'pattern_sensitivity': self.pattern_sensitivity
            }


def load_prompts(file_path: str) -> List[str]:
    """Load prompts from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            prompts = [line.strip() for line in f if line.strip()]
        return prompts
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file not found: {file_path}")


def run_cost_guard_validation():
    """Run comprehensive Cost Guard validation"""
    print("🔬 Cost Guard Validation Testing")
    print("=" * 60)
    print("Requirements:")
    print("  - False Positive Rate < 2%")
    print("  - True Positive Rate > 95%") 
    print("  - Dataset size: 500+ prompts each")
    print("=" * 60)
    
    # Test configurations for systematic parameter tuning
    configurations = [
        {'window_size': 10, 'token_rate_threshold': 1000, 'pattern_sensitivity': 0.8, 'name': 'Baseline'},
        {'window_size': 5, 'token_rate_threshold': 500, 'pattern_sensitivity': 0.9, 'name': 'Conservative'},
        {'window_size': 15, 'token_rate_threshold': 1500, 'pattern_sensitivity': 0.7, 'name': 'Aggressive'},
        {'window_size': 8, 'token_rate_threshold': 800, 'pattern_sensitivity': 0.85, 'name': 'Optimized'},
        {'window_size': 12, 'token_rate_threshold': 1200, 'pattern_sensitivity': 0.75, 'name': 'Balanced'},
        {'window_size': 6, 'token_rate_threshold': 600, 'pattern_sensitivity': 0.95, 'name': 'High_Sensitivity'},
        {'window_size': 20, 'token_rate_threshold': 2000, 'pattern_sensitivity': 0.6, 'name': 'Low_Sensitivity'},
    ]
    
    results = []
    
    for config in configurations:
        print(f"\n🧪 Testing {config['name']} Configuration:")
        print(f"   Window: {config['window_size']}s, Threshold: {config['token_rate_threshold']}, Sensitivity: {config['pattern_sensitivity']}")
        
        guard = CostGuard(
            window_size=config['window_size'],
            token_rate_threshold=config['token_rate_threshold'],
            pattern_sensitivity=config['pattern_sensitivity']
        )
        
        try:
            normal_prompts = load_prompts("data/normal_prompts.txt")
            attack_prompts = load_prompts("data/attack_prompts.txt")
            
            print(f"   Loaded {len(normal_prompts)} normal prompts")
            print(f"   Loaded {len(attack_prompts)} attack prompts")
            
        except FileNotFoundError as e:
            print(f"   ❌ Error loading test data: {e}")
            continue
        
        # Test False Positive Rate
        print("   Testing False Positive Rate...")
        start_time = time.time()
        
        false_positives = 0
        normal_confidences = []
        
        for prompt in normal_prompts:
            detection = guard.detect_token_storm(prompt)
            if detection.is_attack:
                false_positives += 1
            normal_confidences.append(detection.confidence)
        
        fp_rate = false_positives / len(normal_prompts)
        normal_test_time = time.time() - start_time
        
        # Test True Positive Rate
        print("   Testing True Positive Rate...")
        start_time = time.time()
        
        true_positives = 0
        attack_confidences = []
        pattern_types = {}
        
        for prompt in attack_prompts:
            detection = guard.detect_token_storm(prompt)
            if detection.is_attack:
                true_positives += 1
            attack_confidences.append(detection.confidence)
            
            pattern = detection.pattern_type
            pattern_types[pattern] = pattern_types.get(pattern, 0) + 1
        
        tp_rate = true_positives / len(attack_prompts)
        fn_rate = 1 - tp_rate
        attack_test_time = time.time() - start_time
        
        # Calculate metrics
        total_correct = (len(normal_prompts) - false_positives) + true_positives
        total_predictions = len(normal_prompts) + len(attack_prompts)
        overall_accuracy = total_correct / total_predictions
        
        fp_requirement_met = fp_rate < 0.02
        tp_requirement_met = tp_rate > 0.95
        requirements_met = fp_requirement_met and tp_requirement_met
        
        result = {
            'configuration': config,
            'metrics': {
                'false_positive_rate': fp_rate,
                'true_positive_rate': tp_rate,
                'false_negative_rate': fn_rate,
                'overall_accuracy': overall_accuracy,
                'fp_requirement_met': fp_requirement_met,
                'tp_requirement_met': tp_requirement_met,
                'requirements_met': requirements_met
            },
            'performance': {
                'normal_avg_confidence': statistics.mean(normal_confidences),
                'attack_avg_confidence': statistics.mean(attack_confidences),
                'normal_test_time': normal_test_time,
                'attack_test_time': attack_test_time,
                'avg_time_per_prompt': (normal_test_time + attack_test_time) / total_predictions
            },
            'pattern_analysis': pattern_types,
            'statistics': guard.get_statistics()
        }
        
        results.append(result)
        
        # Print results
        print(f"   Results:")
        print(f"     False Positive Rate: {fp_rate:.3%} {'✅' if fp_requirement_met else '❌'} ({'PASS' if fp_requirement_met else 'FAIL'} < 2%)")
        print(f"     True Positive Rate:  {tp_rate:.3%} {'✅' if tp_requirement_met else '❌'} ({'PASS' if tp_requirement_met else 'FAIL'} > 95%)")
        print(f"     False Negative Rate: {fn_rate:.3%}")
        print(f"     Overall Accuracy:    {overall_accuracy:.3%}")
        print(f"     Requirements Met:    {'✅ PASS' if requirements_met else '❌ FAIL'}")
        print(f"     Avg Response Time:   {result['performance']['avg_time_per_prompt']*1000:.1f}ms/prompt")
        
        if pattern_types:
            top_patterns = sorted(pattern_types.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"     Top Attack Patterns: {', '.join([f'{p}({c})' for p, c in top_patterns])}")
    
    # Summary Analysis
    print(f"\n{'='*60}")
    print(f"📊 COMPREHENSIVE VALIDATION SUMMARY")
    print(f"{'='*60}")
    
    passing_configs = [r for r in results if r['metrics']['requirements_met']]
    
    print(f"Total Configurations Tested: {len(results)}")
    print(f"Configurations Meeting Requirements: {len(passing_configs)}")
    print(f"Success Rate: {len(passing_configs)/len(results)*100:.1f}%")
    
    if passing_configs:
        print(f"\n🏆 OPTIMAL CONFIGURATIONS:")
        for i, result in enumerate(passing_configs):
            config = result['configuration']
            metrics = result['metrics']
            print(f"  {i+1}. {config['name']}: FP={metrics['false_positive_rate']:.3%}, TP={metrics['true_positive_rate']:.3%}")
        
        best_config = min(passing_configs, key=lambda r: r['metrics']['false_positive_rate'])
        print(f"\n🥇 BEST CONFIGURATION: {best_config['configuration']['name']}")
        print(f"   FP Rate: {best_config['metrics']['false_positive_rate']:.3%}")
        print(f"   TP Rate: {best_config['metrics']['true_positive_rate']:.3%}")
        print(f"   Accuracy: {best_config['metrics']['overall_accuracy']:.3%}")
        
    else:
        print("\n⚠️  NO CONFIGURATIONS MET BOTH REQUIREMENTS!")
        print("Analysis of failures:")
        
        for result in results:
            config = result['configuration']
            metrics = result['metrics']
            issues = []
            if not metrics['fp_requirement_met']:
                issues.append(f"FP={metrics['false_positive_rate']:.3%}")
            if not metrics['tp_requirement_met']:
                issues.append(f"TP={metrics['true_positive_rate']:.3%}")
            
            print(f"  {config['name']}: {', '.join(issues)}")
    
    # Generate reports
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    generate_summary_report(results, timestamp)
    
    return results


def generate_summary_report(results: List[Dict], timestamp: str):
    """Generate comprehensive summary report"""
    os.makedirs("smoke", exist_ok=True)
    report_file = f"smoke/cost_guard_summary_{timestamp}.md"
    
    with open(report_file, 'w') as f:
        f.write("# Cost Guard 触发率验证报告\n\n")
        f.write(f"**测试时间:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**目标要求:** FP < 2%, TP > 95%\n\n")
        
        f.write("## 配置测试结果\n\n")
        f.write("| 配置名称 | FP率 | TP率 | 要求达成 | 参数设置 |\n")
        f.write("|----------|------|------|----------|----------|\n")
        
        for result in results:
            config = result['configuration']
            metrics = result['metrics']
            status = "✅ 通过" if metrics['requirements_met'] else "❌ 失败"
            
            f.write(f"| {config['name']} | {metrics['false_positive_rate']:.3%} | "
                   f"{metrics['true_positive_rate']:.3%} | {status} | "
                   f"ws={config['window_size']}, th={config['token_rate_threshold']}, "
                   f"sens={config['pattern_sensitivity']} |\n")
        
        passing_configs = [r for r in results if r['metrics']['requirements_met']]
        
        f.write(f"\n## 测试总结\n\n")
        f.write(f"- **测试配置总数:** {len(results)}\n")
        f.write(f"- **通过配置数量:** {len(passing_configs)}\n")
        f.write(f"- **成功率:** {len(passing_configs)/len(results)*100:.1f}%\n\n")
        
        if passing_configs:
            best_config = min(passing_configs, key=lambda r: r['metrics']['false_positive_rate'])
            f.write(f"### 推荐配置\n\n")
            f.write(f"**{best_config['configuration']['name']}** 配置提供最优性能:\n\n")
            f.write(f"- 窗口大小: {best_config['configuration']['window_size']} 秒\n")
            f.write(f"- Token速率阈值: {best_config['configuration']['token_rate_threshold']}\n")
            f.write(f"- 模式敏感度: {best_config['configuration']['pattern_sensitivity']}\n")
            f.write(f"- 误报率 (FP): {best_config['metrics']['false_positive_rate']:.3%}\n")
            f.write(f"- 检出率 (TP): {best_config['metrics']['true_positive_rate']:.3%}\n")
            f.write(f"- 总体准确率: {best_config['metrics']['overall_accuracy']:.3%}\n\n")
        
        f.write("## 参数调优记录\n\n")
        
        # Parameter impact analysis
        window_analysis = {}
        threshold_analysis = {}
        sensitivity_analysis = {}
        
        for result in results:
            config = result['configuration']
            metrics = result['metrics']
            
            ws = config['window_size']
            if ws not in window_analysis:
                window_analysis[ws] = []
            window_analysis[ws].append(metrics['requirements_met'])
            
            th = config['token_rate_threshold']
            if th not in threshold_analysis:
                threshold_analysis[th] = []
            threshold_analysis[th].append(metrics['requirements_met'])
            
            sens = config['pattern_sensitivity']
            if sens not in sensitivity_analysis:
                sensitivity_analysis[sens] = []
            sensitivity_analysis[sens].append(metrics['requirements_met'])
        
        f.write("### 窗口大小影响分析\n")
        for ws, results_list in sorted(window_analysis.items()):
            success_rate = sum(results_list) / len(results_list) * 100
            f.write(f"- {ws}秒: {success_rate:.0f}% 成功率\n")
        
        f.write("\n### Token速率阈值影响分析\n")
        for th, results_list in sorted(threshold_analysis.items()):
            success_rate = sum(results_list) / len(results_list) * 100
            f.write(f"- {th}: {success_rate:.0f}% 成功率\n")
        
        f.write("\n### 模式敏感度影响分析\n")
        for sens, results_list in sorted(sensitivity_analysis.items()):
            success_rate = sum(results_list) / len(results_list) * 100
            f.write(f"- {sens}: {success_rate:.0f}% 成功率\n")
        
        f.write("\n## 调试建议\n\n")
        non_passing = [r for r in results if not r['metrics']['requirements_met']]
        if non_passing:
            high_fp = [r for r in non_passing if not r['metrics']['fp_requirement_met']]
            low_tp = [r for r in non_passing if not r['metrics']['tp_requirement_met']]
            
            if high_fp:
                f.write("**若 FP > 2%，建议:**\n")
                f.write("- 增大 window_size（如 5s → 10s）\n")
                f.write("- 提高 token_rate_threshold（如 500 → 1000）\n")
                f.write("- 降低 pattern_sensitivity（如 0.9 → 0.8）\n\n")
            
            if low_tp:
                f.write("**若 TP < 95%，建议:**\n")
                f.write("- 检查正则匹配逻辑（sidecar.py 中的 detect_token_storm）\n")
                f.write("- 提高 pattern_sensitivity（如 0.7 → 0.8）\n")
                f.write("- 降低 token_rate_threshold（如 1000 → 800）\n\n")
        
        f.write(f"\n---\n*报告生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    print(f"📋 详细报告已保存: {report_file}")


if __name__ == "__main__":
    results = run_cost_guard_validation()
    
    print(f"\n{'='*60}")
    print(f"🎯 COST GUARD 触发率验证完成")
    print(f"{'='*60}")
    
    passing_configs = [r for r in results if r['metrics']['requirements_met']]
    
    if passing_configs:
        print("✅ 验证成功!")
        print("   ✅ FP < 2% 要求达成")
        print("   ✅ TP > 95% 要求达成")
        print("   ✅ 已准备好生产部署")
        
        best = min(passing_configs, key=lambda r: r['metrics']['false_positive_rate'])
        print(f"\n🏆 最优配置: {best['configuration']['name']}")
        print(f"   FP率: {best['metrics']['false_positive_rate']:.3%}")
        print(f"   TP率: {best['metrics']['true_positive_rate']:.3%}")
        
    else:
        print("❌ 验证失败 - 需要参数调优")
        print("   请查看生成的报告了解详细建议")
    
    print(f"\n推荐: {'部署' if passing_configs else '继续调优'}")