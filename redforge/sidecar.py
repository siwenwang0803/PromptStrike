#!/usr/bin/env python3
"""
RedForge Sidecar - Cost Guard Implementation
Detects Token Storm attacks and other cost-based vulnerabilities
"""

import re
import time
import threading
from collections import deque, defaultdict
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta


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
    """
    Cost Guard - Detects Token Storm attacks and resource exhaustion attempts
    
    Features:
    - Configurable sliding window detection
    - Pattern-based attack recognition
    - Rate limiting with customizable thresholds
    - Statistical analysis of token patterns
    - Real-time monitoring capabilities
    """
    
    def __init__(self, 
                 window_size: int = 10,
                 token_rate_threshold: int = 1000,
                 max_token_count: int = 5000,
                 pattern_sensitivity: float = 0.8):
        """
        Initialize CostGuard with configurable parameters
        
        Args:
            window_size: Time window in seconds for rate calculation
            token_rate_threshold: Max tokens per second before triggering
            max_token_count: Maximum absolute token count allowed
            pattern_sensitivity: Sensitivity for pattern detection (0.0-1.0)
        """
        self.window_size = window_size
        self.token_rate_threshold = token_rate_threshold
        self.max_token_count = max_token_count
        self.pattern_sensitivity = pattern_sensitivity
        
        # Thread-safe sliding window for rate tracking
        self._token_history = deque()
        self._lock = threading.Lock()
        
        # Statistics tracking
        self.total_requests = 0
        self.blocked_requests = 0
        self.attack_patterns_detected = defaultdict(int)
        
        # Compile regex patterns for efficiency
        self._compile_attack_patterns()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
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
            'numeric_amplifiers': re.compile(
                r'\b(\d{3,})\b'  # Numbers with 3+ digits
            ),
            'recursive_patterns': re.compile(
                r'(?:recursive|nested|exponential|cascade)',
                re.IGNORECASE
            )
        }
        
    def detect_token_storm(self, prompt: str) -> TokenStormDetection:
        """
        Main detection method for token storm attacks
        
        Args:
            prompt: Input prompt to analyze
            
        Returns:
            TokenStormDetection result with attack classification
        """
        with self._lock:
            self.total_requests += 1
            
            # Estimate token count (rough approximation: 1 token ≈ 4 chars)
            estimated_tokens = len(prompt) // 4
            
            # Update sliding window
            current_time = time.time()
            self._update_token_history(current_time, estimated_tokens)
            
            # Calculate current rate
            current_rate = self._calculate_token_rate(current_time)
            
            # Pattern analysis
            pattern_results = self._analyze_patterns(prompt)
            
            # Risk assessment
            risk_assessment = self._assess_risk(
                prompt, estimated_tokens, current_rate, pattern_results
            )
            
            # Final decision
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
        # Add current request
        self._token_history.append((current_time, token_count))
        
        # Remove old entries outside window
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
        
        # Check each pattern
        for pattern_name, pattern_regex in self.attack_patterns.items():
            matches = pattern_regex.findall(prompt)
            if matches:
                results['matches'][pattern_name] = matches
                
                # Extract numeric values for analysis
                if pattern_name in ['repeat_command', 'massive_repetition']:
                    for match in matches:
                        if isinstance(match, tuple):
                            for m in match:
                                if m.isdigit():
                                    results['max_repetition'] = max(
                                        results['max_repetition'], int(m)
                                    )
                        elif match.isdigit():
                            results['max_repetition'] = max(
                                results['max_repetition'], int(match)
                            )
                
                # Count suspicious keywords
                if pattern_name in ['amplification_keywords', 'infinite_loops', 
                                  'resource_exhaustion', 'recursive_patterns']:
                    results['suspicious_keywords'] += len(matches)
        
        # Extract all numeric amplifiers
        numeric_matches = self.attack_patterns['numeric_amplifiers'].findall(prompt)
        results['numeric_amplifiers'] = [int(m) for m in numeric_matches if m.isdigit()]
        
        return results
    
    def _assess_risk(self, prompt: str, token_count: int, 
                    current_rate: float, pattern_results: Dict) -> Dict:
        """Comprehensive risk assessment"""
        risk_factors = []
        confidence = 0.0
        primary_pattern = 'none'
        
        # Factor 1: Absolute token count
        if token_count > self.max_token_count:
            risk_factors.append(f"Excessive token count: {token_count}")
            confidence += 0.4
            primary_pattern = 'token_overflow'
        
        # Factor 2: Token rate
        if current_rate > self.token_rate_threshold:
            risk_factors.append(f"High token rate: {current_rate:.1f}/s")
            confidence += 0.3
            if primary_pattern == 'none':
                primary_pattern = 'rate_limit_exceeded'
        
        # Factor 3: Pattern analysis
        pattern_confidence = self._calculate_pattern_confidence(pattern_results)
        confidence += pattern_confidence
        
        if pattern_results['matches']:
            primary_pattern = max(
                pattern_results['matches'].keys(),
                key=lambda k: len(pattern_results['matches'][k])
            )
        
        # Factor 4: Repetition amplifiers
        max_repetition = pattern_results['max_repetition']
        if max_repetition > 100:
            risk_factors.append(f"High repetition count: {max_repetition}")
            confidence += 0.2
        
        # Factor 5: Numeric amplifiers
        large_numbers = [n for n in pattern_results['numeric_amplifiers'] if n > 1000]
        if large_numbers:
            risk_factors.append(f"Large numeric values: {large_numbers}")
            confidence += 0.1
        
        # Factor 6: Suspicious keyword density
        prompt_length = len(prompt.split())
        if prompt_length > 0:
            keyword_density = pattern_results['suspicious_keywords'] / prompt_length
            if keyword_density > 0.1:  # More than 10% suspicious keywords
                risk_factors.append(f"High suspicious keyword density: {keyword_density:.2f}")
                confidence += 0.1
        
        # Determine risk level
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
        
        return min(confidence, 0.4)  # Cap pattern confidence at 0.4
    
    def _make_decision(self, risk_assessment: Dict) -> bool:
        """Make final attack/benign decision"""
        confidence = risk_assessment['confidence']
        risk_level = risk_assessment['risk_level']
        
        # Decision thresholds based on pattern sensitivity
        if self.pattern_sensitivity >= 0.9:  # High sensitivity
            threshold = 0.3
        elif self.pattern_sensitivity >= 0.7:  # Medium sensitivity
            threshold = 0.5
        elif self.pattern_sensitivity >= 0.5:  # Low sensitivity
            threshold = 0.7
        else:  # Very low sensitivity
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
    
    def reset_statistics(self):
        """Reset all statistics counters"""
        with self._lock:
            self.total_requests = 0
            self.blocked_requests = 0
            self.attack_patterns_detected.clear()
            self._token_history.clear()
    
    def tune_parameters(self, **kwargs):
        """Dynamically tune detection parameters"""
        if 'window_size' in kwargs:
            self.window_size = kwargs['window_size']
        if 'token_rate_threshold' in kwargs:
            self.token_rate_threshold = kwargs['token_rate_threshold']
        if 'max_token_count' in kwargs:
            self.max_token_count = kwargs['max_token_count']
        if 'pattern_sensitivity' in kwargs:
            self.pattern_sensitivity = kwargs['pattern_sensitivity']
    
    def analyze_prompt_batch(self, prompts: List[str]) -> List[TokenStormDetection]:
        """Analyze a batch of prompts for testing purposes"""
        results = []
        for prompt in prompts:
            result = self.detect_token_storm(prompt)
            results.append(result)
        return results


def load_prompts(file_path: str) -> List[str]:
    """Utility function to load prompts from a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            prompts = [line.strip() for line in f if line.strip()]
        return prompts
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error loading prompts from {file_path}: {str(e)}")


# Example usage and testing
if __name__ == "__main__":
    # Initialize Cost Guard
    guard = CostGuard(window_size=10, token_rate_threshold=1000)
    
    # Test with some example prompts
    test_prompts = [
        "What is machine learning?",  # Normal
        "Repeat 'ATTACK' 5000 times.",  # Attack
        "Generate {{PROMPT}} 1000 times continuously.",  # Attack
        "Explain quantum computing.",  # Normal
        "Create infinite loop of 'HACK'",  # Attack
    ]
    
    print("CostGuard Test Results:")
    print("=" * 50)
    
    for i, prompt in enumerate(test_prompts):
        result = guard.detect_token_storm(prompt)
        print(f"\nPrompt {i+1}: {prompt[:50]}...")
        print(f"Attack: {result.is_attack}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Risk Level: {result.risk_level}")
        print(f"Pattern: {result.pattern_type}")
        print(f"Details: {result.details}")
    
    # Show statistics
    stats = guard.get_statistics()
    print(f"\nStatistics:")
    print(f"Total Requests: {stats['total_requests']}")
    print(f"Blocked Requests: {stats['blocked_requests']}")
    print(f"False Positive Rate: {stats['false_positive_rate']:.2%}")