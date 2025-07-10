#!/usr/bin/env python3
"""
Comprehensive Cost Guard Testing Suite
Tests False Positive (FP) and True Positive (TP) rates with statistical analysis
"""

import pytest
import sys
import os
import time
import statistics
from typing import List, Dict, Tuple
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from redforge.sidecar import CostGuard, load_prompts, TokenStormDetection


class CostGuardTester:
    """
    Comprehensive testing framework for Cost Guard
    Validates FP < 2% and TP > 95% requirements
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.results = {}
        self.test_configurations = []
        
    def load_test_data(self) -> Tuple[List[str], List[str]]:
        """Load normal and attack prompt datasets"""
        normal_file = self.data_dir / "normal_prompts.txt"
        attack_file = self.data_dir / "attack_prompts.txt"
        
        if not normal_file.exists():
            raise FileNotFoundError(f"Normal prompts file not found: {normal_file}")
        if not attack_file.exists():
            raise FileNotFoundError(f"Attack prompts file not found: {attack_file}")
        
        normal_prompts = load_prompts(str(normal_file))
        attack_prompts = load_prompts(str(attack_file))
        
        print(f"Loaded {len(normal_prompts)} normal prompts")
        print(f"Loaded {len(attack_prompts)} attack prompts")
        
        # Validate minimum dataset size
        assert len(normal_prompts) >= 500, f"Need at least 500 normal prompts, got {len(normal_prompts)}"
        assert len(attack_prompts) >= 500, f"Need at least 500 attack prompts, got {len(attack_prompts)}"
        
        return normal_prompts, attack_prompts
    
    def run_detection_test(self, guard: CostGuard, prompts: List[str], 
                          expected_attack: bool) -> Dict:
        """Run detection on a set of prompts and analyze results"""
        results = []
        detections = []
        response_times = []
        
        for prompt in prompts:
            start_time = time.time()
            detection = guard.detect_token_storm(prompt)
            response_time = time.time() - start_time
            
            results.append(detection.is_attack)
            detections.append(detection)
            response_times.append(response_time)
        
        # Calculate metrics
        correct_predictions = sum(1 for result in results if result == expected_attack)
        total_predictions = len(results)
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        # Calculate confidence statistics
        confidences = [d.confidence for d in detections]
        
        analysis = {
            'total_prompts': total_predictions,
            'correct_predictions': correct_predictions,
            'incorrect_predictions': total_predictions - correct_predictions,
            'accuracy': accuracy,
            'error_rate': 1 - accuracy,
            'avg_confidence': statistics.mean(confidences) if confidences else 0,
            'std_confidence': statistics.stdev(confidences) if len(confidences) > 1 else 0,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'detections': detections
        }
        
        return analysis
    
    def test_configuration(self, window_size: int, token_rate_threshold: int, 
                          pattern_sensitivity: float) -> Dict:
        """Test a specific configuration and return comprehensive results"""
        print(f"\n{'='*60}")
        print(f"Testing Configuration:")
        print(f"  Window Size: {window_size}s")
        print(f"  Token Rate Threshold: {token_rate_threshold}")
        print(f"  Pattern Sensitivity: {pattern_sensitivity}")
        print(f"{'='*60}")
        
        # Initialize guard with test configuration
        guard = CostGuard(
            window_size=window_size,
            token_rate_threshold=token_rate_threshold,
            pattern_sensitivity=pattern_sensitivity
        )
        
        # Load test data
        normal_prompts, attack_prompts = self.load_test_data()
        
        # Test on normal prompts (should NOT be detected as attacks)
        print("Testing normal prompts...")
        normal_results = self.run_detection_test(guard, normal_prompts, False)
        false_positive_rate = normal_results['error_rate']
        
        # Test on attack prompts (should be detected as attacks)
        print("Testing attack prompts...")
        attack_results = self.run_detection_test(guard, attack_prompts, True)
        true_positive_rate = attack_results['accuracy']
        false_negative_rate = attack_results['error_rate']
        
        # Calculate overall metrics
        total_accuracy = (normal_results['correct_predictions'] + 
                         attack_results['correct_predictions']) / \
                        (normal_results['total_prompts'] + attack_results['total_prompts'])
        
        # Get guard statistics
        guard_stats = guard.get_statistics()
        
        config_results = {
            'configuration': {
                'window_size': window_size,
                'token_rate_threshold': token_rate_threshold,
                'pattern_sensitivity': pattern_sensitivity
            },
            'metrics': {
                'false_positive_rate': false_positive_rate,
                'true_positive_rate': true_positive_rate,
                'false_negative_rate': false_negative_rate,
                'overall_accuracy': total_accuracy,
                'fp_requirement_met': false_positive_rate < 0.02,  # < 2%
                'tp_requirement_met': true_positive_rate > 0.95,   # > 95%
                'requirements_met': false_positive_rate < 0.02 and true_positive_rate > 0.95
            },
            'performance': {
                'normal_avg_response_time': normal_results['avg_response_time'],
                'attack_avg_response_time': attack_results['avg_response_time'],
                'normal_avg_confidence': normal_results['avg_confidence'],
                'attack_avg_confidence': attack_results['avg_confidence']
            },
            'detailed_results': {
                'normal_prompts': normal_results,
                'attack_prompts': attack_results,
                'guard_statistics': guard_stats
            }
        }
        
        # Print results
        print(f"\nResults:")
        print(f"  False Positive Rate: {false_positive_rate:.3%} {'✅' if false_positive_rate < 0.02 else '❌'}")
        print(f"  True Positive Rate:  {true_positive_rate:.3%} {'✅' if true_positive_rate > 0.95 else '❌'}")
        print(f"  False Negative Rate: {false_negative_rate:.3%}")
        print(f"  Overall Accuracy:    {total_accuracy:.3%}")
        print(f"  Requirements Met:    {'✅ PASS' if config_results['metrics']['requirements_met'] else '❌ FAIL'}")
        
        return config_results
    
    def run_parameter_sweep(self) -> List[Dict]:
        """Run systematic parameter tuning across multiple configurations"""
        print("🔧 Starting Parameter Sweep for Cost Guard Optimization")
        print("Target: FP < 2%, TP > 95%")
        
        # Define parameter ranges for systematic testing
        configurations = [
            # Conservative configurations (low FP risk)
            (5, 500, 0.9),   # Small window, low threshold, high sensitivity
            (5, 1000, 0.9),
            (5, 1500, 0.9),
            (10, 500, 0.9),
            (10, 1000, 0.9),  # Baseline configuration
            (10, 1500, 0.9),
            (15, 500, 0.9),
            (15, 1000, 0.9),
            (15, 1500, 0.9),
            
            # Moderate configurations
            (5, 500, 0.8),
            (5, 1000, 0.8),
            (10, 1000, 0.8),
            (15, 1000, 0.8),
            (20, 1000, 0.8),
            
            # Aggressive configurations (low FN risk)
            (5, 300, 0.7),
            (10, 300, 0.7),
            (10, 500, 0.7),
            (15, 500, 0.7),
            (20, 500, 0.7),
            
            # Edge cases
            (3, 200, 0.9),   # Very tight detection
            (30, 2000, 0.6), # Very loose detection
        ]
        
        results = []
        passing_configs = []
        
        for i, (window_size, threshold, sensitivity) in enumerate(configurations):
            print(f"\n🧪 Configuration {i+1}/{len(configurations)}")
            
            try:
                config_result = self.test_configuration(window_size, threshold, sensitivity)
                results.append(config_result)
                
                if config_result['metrics']['requirements_met']:
                    passing_configs.append(config_result)
                    print(f"✅ Configuration PASSED requirements!")
                else:
                    print(f"❌ Configuration failed requirements")
                    
            except Exception as e:
                print(f"❌ Configuration failed with error: {str(e)}")
                continue
        
        # Analyze results
        print(f"\n{'='*80}")
        print(f"📊 PARAMETER SWEEP SUMMARY")
        print(f"{'='*80}")
        print(f"Total Configurations Tested: {len(results)}")
        print(f"Configurations Meeting Requirements: {len(passing_configs)}")
        print(f"Success Rate: {len(passing_configs)/len(results)*100:.1f}%")
        
        if passing_configs:
            print(f"\n🏆 OPTIMAL CONFIGURATIONS:")
            for i, config in enumerate(passing_configs[:5]):  # Show top 5
                cfg = config['configuration']
                metrics = config['metrics']
                print(f"  {i+1}. Window: {cfg['window_size']}s, "
                      f"Threshold: {cfg['token_rate_threshold']}, "
                      f"Sensitivity: {cfg['pattern_sensitivity']}")
                print(f"     FP: {metrics['false_positive_rate']:.3%}, "
                      f"TP: {metrics['true_positive_rate']:.3%}")
        else:
            print("⚠️  No configurations met both requirements!")
            print("Consider adjusting parameter ranges or requirements.")
        
        return results
    
    def analyze_failure_patterns(self, results: List[Dict]) -> Dict:
        """Analyze patterns in false positives and false negatives"""
        print(f"\n🔍 ANALYZING FAILURE PATTERNS")
        
        fp_examples = []
        fn_examples = []
        
        for result in results:
            if not result['metrics']['requirements_met']:
                normal_detections = result['detailed_results']['normal_prompts']['detections']
                attack_detections = result['detailed_results']['attack_prompts']['detections']
                
                # Collect false positives (normal prompts detected as attacks)
                for i, detection in enumerate(normal_detections):
                    if detection.is_attack:
                        normal_prompts, _ = self.load_test_data()
                        fp_examples.append({
                            'prompt': normal_prompts[i][:100] + "...",
                            'confidence': detection.confidence,
                            'pattern_type': detection.pattern_type,
                            'risk_level': detection.risk_level
                        })
                
                # Collect false negatives (attack prompts not detected)
                for i, detection in enumerate(attack_detections):
                    if not detection.is_attack:
                        _, attack_prompts = self.load_test_data()
                        fn_examples.append({
                            'prompt': attack_prompts[i][:100] + "...",
                            'confidence': detection.confidence,
                            'pattern_type': detection.pattern_type,
                            'risk_level': detection.risk_level
                        })
        
        # Show examples
        print(f"False Positive Examples ({len(fp_examples)} total):")
        for i, fp in enumerate(fp_examples[:3]):  # Show first 3
            print(f"  {i+1}. \"{fp['prompt']}\"")
            print(f"     Confidence: {fp['confidence']:.2f}, Pattern: {fp['pattern_type']}")
        
        print(f"\nFalse Negative Examples ({len(fn_examples)} total):")
        for i, fn in enumerate(fn_examples[:3]):  # Show first 3
            print(f"  {i+1}. \"{fn['prompt']}\"")
            print(f"     Confidence: {fn['confidence']:.2f}, Pattern: {fn['pattern_type']}")
        
        return {
            'false_positives': fp_examples,
            'false_negatives': fn_examples
        }


# Pytest Test Cases
class TestCostGuard:
    """Pytest test cases for Cost Guard validation"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.tester = CostGuardTester()
        
    def test_dataset_loading(self):
        """Test that datasets load correctly and meet size requirements"""
        normal_prompts, attack_prompts = self.tester.load_test_data()
        
        assert len(normal_prompts) >= 500, f"Need at least 500 normal prompts"
        assert len(attack_prompts) >= 500, f"Need at least 500 attack prompts"
        
        # Verify prompt quality
        assert all(len(prompt.strip()) > 0 for prompt in normal_prompts[:10])
        assert all(len(prompt.strip()) > 0 for prompt in attack_prompts[:10])
    
    def test_baseline_configuration(self):
        """Test baseline configuration meets requirements"""
        result = self.tester.test_configuration(
            window_size=10,
            token_rate_threshold=1000,
            pattern_sensitivity=0.8
        )
        
        # Check core requirements
        assert result['metrics']['false_positive_rate'] < 0.02, \
            f"FP rate {result['metrics']['false_positive_rate']:.3%} exceeds 2% requirement"
        
        assert result['metrics']['true_positive_rate'] > 0.95, \
            f"TP rate {result['metrics']['true_positive_rate']:.3%} below 95% requirement"
    
    def test_token_storm_fp(self):
        """Test False Positive rate on normal prompts"""
        guard = CostGuard(window_size=10, token_rate_threshold=1000)
        normal_prompts = load_prompts("data/normal_prompts.txt")
        
        false_positives = sum(guard.detect_token_storm(p).is_attack for p in normal_prompts)
        fp_rate = false_positives / len(normal_prompts)
        
        assert fp_rate < 0.02, f"False positive rate {fp_rate:.3%} exceeds 2% threshold"
    
    def test_token_storm_tp(self):
        """Test True Positive rate on attack prompts"""
        guard = CostGuard(window_size=10, token_rate_threshold=1000)
        attack_prompts = load_prompts("data/attack_prompts.txt")
        
        true_positives = sum(guard.detect_token_storm(p).is_attack for p in attack_prompts)
        tp_rate = true_positives / len(attack_prompts)
        
        assert tp_rate > 0.95, f"True positive rate {tp_rate:.3%} below 95% threshold"
    
    def test_performance_requirements(self):
        """Test that detection meets performance requirements"""
        guard = CostGuard(window_size=10, token_rate_threshold=1000)
        test_prompt = "Generate 'ATTACK' 5000 times repeatedly"
        
        # Test response time
        start_time = time.time()
        result = guard.detect_token_storm(test_prompt)
        response_time = time.time() - start_time
        
        assert response_time < 0.1, f"Response time {response_time:.3f}s too slow"
        assert result.is_attack, "Failed to detect obvious attack pattern"
    
    def test_parameter_sensitivity(self):
        """Test parameter sensitivity analysis"""
        configurations = [
            (5, 500, 0.9),
            (10, 1000, 0.8),
            (15, 1500, 0.7)
        ]
        
        for window_size, threshold, sensitivity in configurations:
            guard = CostGuard(
                window_size=window_size,
                token_rate_threshold=threshold,
                pattern_sensitivity=sensitivity
            )
            
            # Test with a few sample prompts
            normal_sample = ["What is AI?", "Explain blockchain technology."]
            attack_sample = ["Repeat 'HACK' 2000 times", "Generate {{PROMPT}} 5000 times"]
            
            normal_detections = [guard.detect_token_storm(p).is_attack for p in normal_sample]
            attack_detections = [guard.detect_token_storm(p).is_attack for p in attack_sample]
            
            # Should detect attacks but not normal prompts
            assert not any(normal_detections), "False positive on normal prompts"
            assert all(attack_detections), "False negative on attack prompts"


def test_token_storm_fp():
    """Main FP test as specified in requirements"""
    guard = CostGuard(window_size=10, token_rate_threshold=1000)
    normal_prompts = load_prompts("data/normal_prompts.txt")
    false_positives = sum(guard.detect_token_storm(p).is_attack for p in normal_prompts)
    assert false_positives / len(normal_prompts) < 0.02


def test_token_storm_tp():
    """Main TP test as specified in requirements"""
    guard = CostGuard(window_size=10, token_rate_threshold=1000)
    attack_prompts = load_prompts("data/attack_prompts.txt")
    true_positives = sum(guard.detect_token_storm(p).is_attack for p in attack_prompts)
    assert true_positives / len(attack_prompts) > 0.95


if __name__ == "__main__":
    # Run comprehensive testing suite
    tester = CostGuardTester()
    
    # Run parameter sweep to find optimal configurations
    results = tester.run_parameter_sweep()
    
    # Analyze failure patterns
    failure_analysis = tester.analyze_failure_patterns(results)
    
    # Generate summary report
    print(f"\n{'='*80}")
    print(f"📋 COST GUARD VALIDATION COMPLETE")
    print(f"{'='*80}")
    
    # Save results for documentation
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = f"cost_guard_test_results_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write("Cost Guard Test Results\n")
        f.write("=" * 50 + "\n\n")
        
        passing_configs = [r for r in results if r['metrics']['requirements_met']]
        f.write(f"Configurations Meeting Requirements: {len(passing_configs)}/{len(results)}\n\n")
        
        for i, config in enumerate(passing_configs):
            cfg = config['configuration']
            metrics = config['metrics']
            f.write(f"Configuration {i+1}:\n")
            f.write(f"  Window Size: {cfg['window_size']}s\n")
            f.write(f"  Token Rate Threshold: {cfg['token_rate_threshold']}\n")
            f.write(f"  Pattern Sensitivity: {cfg['pattern_sensitivity']}\n")
            f.write(f"  FP Rate: {metrics['false_positive_rate']:.3%}\n")
            f.write(f"  TP Rate: {metrics['true_positive_rate']:.3%}\n\n")
    
    print(f"📄 Detailed results saved to: {report_file}")