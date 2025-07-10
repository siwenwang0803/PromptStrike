#!/usr/bin/env python3
"""
RedForge Cost Guard - Token Storm Protection & Budget Management

Production-ready cost protection system with configurable thresholds,
rate limiting, and comprehensive monitoring for LLM applications.

Features:
- Token storm detection with model-specific thresholds
- Daily/hourly/per-request budget enforcement
- Rate limiting with sliding windows
- Cost projection and alerting
- Historical spending analysis
- Multi-tenant support

Usage:
    from guardrail.cost_guard import CostGuard, CostGuardConfig
    
    config = CostGuardConfig(
        daily_budget=1000.0,
        hourly_limit=100.0,
        token_storm_threshold=5000
    )
    
    cost_guard = CostGuard(config)
    result = cost_guard.check_request(request)
"""

import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, deque
from enum import Enum
import json
import threading
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class BlockReason(str, Enum):
    """Reasons for blocking a request"""
    DAILY_BUDGET_EXCEEDED = "daily_budget_exceeded"
    HOURLY_LIMIT_EXCEEDED = "hourly_limit_exceeded"
    PER_REQUEST_LIMIT_EXCEEDED = "per_request_limit_exceeded"
    TOKEN_STORM_DETECTED = "token_storm_detected"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    USER_QUOTA_EXCEEDED = "user_quota_exceeded"
    VELOCITY_LIMIT_EXCEEDED = "velocity_limit_exceeded"
    SUSPICIOUS_PATTERN = "suspicious_pattern"


class CostAlert(str, Enum):
    """Cost alert types"""
    BUDGET_WARNING = "budget_warning"          # 80% of budget consumed
    BUDGET_CRITICAL = "budget_critical"        # 90% of budget consumed
    UNUSUAL_SPENDING = "unusual_spending"      # Spike in spending rate
    TOKEN_STORM_WARNING = "token_storm_warning"  # Near token storm threshold
    RATE_ANOMALY = "rate_anomaly"             # Unusual request patterns


@dataclass
class ModelPricing:
    """Pricing information for different models"""
    input_price_per_1k: float    # Price per 1K input tokens
    output_price_per_1k: float   # Price per 1K output tokens
    token_storm_threshold: int   # Model-specific threshold
    max_context_tokens: int      # Maximum context window
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for given token counts"""
        input_cost = (input_tokens / 1000) * self.input_price_per_1k
        output_cost = (output_tokens / 1000) * self.output_price_per_1k
        return input_cost + output_cost


# Default model pricing (as of 2024)
DEFAULT_MODEL_PRICING = {
    "gpt-4": ModelPricing(
        input_price_per_1k=0.03,
        output_price_per_1k=0.06,
        token_storm_threshold=8000,
        max_context_tokens=128000
    ),
    "gpt-4-turbo": ModelPricing(
        input_price_per_1k=0.01,
        output_price_per_1k=0.03,
        token_storm_threshold=8000,
        max_context_tokens=128000
    ),
    "gpt-3.5-turbo": ModelPricing(
        input_price_per_1k=0.0005,
        output_price_per_1k=0.0015,
        token_storm_threshold=4000,
        max_context_tokens=16385
    ),
    "claude-3-opus": ModelPricing(
        input_price_per_1k=0.015,
        output_price_per_1k=0.075,
        token_storm_threshold=10000,
        max_context_tokens=200000
    ),
    "claude-3-sonnet": ModelPricing(
        input_price_per_1k=0.003,
        output_price_per_1k=0.015,
        token_storm_threshold=8000,
        max_context_tokens=200000
    ),
    "claude-3-haiku": ModelPricing(
        input_price_per_1k=0.00025,
        output_price_per_1k=0.00125,
        token_storm_threshold=4000,
        max_context_tokens=200000
    ),
    # Default for unknown models
    "default": ModelPricing(
        input_price_per_1k=0.01,
        output_price_per_1k=0.02,
        token_storm_threshold=5000,
        max_context_tokens=32000
    )
}


@dataclass
class CostGuardConfig:
    """Configuration for CostGuard"""
    # Budget limits
    daily_budget: float = 1000.0
    hourly_limit: float = 100.0
    per_request_limit: float = 10.0
    
    # Token storm protection
    token_storm_threshold: int = 5000  # Default, overridden by model-specific
    token_storm_multiplier: float = 2.0  # How much to multiply threshold for warnings
    
    # Rate limiting
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    max_tokens_per_minute: int = 100000
    max_tokens_per_hour: int = 1000000
    
    # User quotas
    enable_user_quotas: bool = True
    default_user_daily_budget: float = 100.0
    default_user_hourly_limit: float = 20.0
    
    # Alerting
    alert_threshold_percentage: float = 0.8  # Alert at 80% of budget
    critical_threshold_percentage: float = 0.9  # Critical at 90%
    
    # Storage
    persist_spending_history: bool = True
    history_retention_days: int = 30
    history_file_path: str = "cost_guard_history.json"
    
    # Advanced
    enable_velocity_tracking: bool = True
    velocity_window_minutes: int = 5
    velocity_spike_threshold: float = 3.0  # 3x normal rate
    
    # Model pricing overrides
    model_pricing_overrides: Dict[str, ModelPricing] = field(default_factory=dict)


@dataclass
class SpendingRecord:
    """Record of a spending event"""
    timestamp: datetime
    user_id: str
    request_id: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    blocked: bool
    block_reason: Optional[BlockReason] = None


@dataclass
class CostGuardResult:
    """Result from cost guard check"""
    request_id: str
    should_block: bool
    block_reason: Optional[BlockReason]
    risk_factors: List[str]
    
    # Budget status
    current_daily_spend: float
    current_hourly_spend: float
    daily_budget_remaining: float
    hourly_budget_remaining: float
    
    # Projections
    projected_cost: float
    projected_daily_spend: float
    
    # Alerts
    alerts: List[CostAlert]
    
    # Recommendations
    recommendations: List[str]
    
    # Metrics
    tokens_requested: int
    rate_limit_remaining: int
    velocity_score: float  # 1.0 = normal, >1.0 = above normal


class RateLimiter:
    """Token bucket rate limiter with sliding window"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self.lock = threading.Lock()
    
    def check_and_update(self, request_id: str) -> Tuple[bool, int]:
        """Check if request is allowed and update state"""
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds
            
            # Remove old requests outside window
            while self.requests and self.requests[0][0] < cutoff_time:
                self.requests.popleft()
            
            # Check if we can accept new request
            if len(self.requests) >= self.max_requests:
                return False, 0
            
            # Add new request
            self.requests.append((current_time, request_id))
            return True, self.max_requests - len(self.requests)
    
    def get_remaining(self) -> int:
        """Get remaining requests in current window"""
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds
            
            # Remove old requests
            while self.requests and self.requests[0][0] < cutoff_time:
                self.requests.popleft()
            
            return self.max_requests - len(self.requests)


class TokenRateLimiter:
    """Token-based rate limiter with sliding window"""
    
    def __init__(self, max_tokens: int, window_seconds: int):
        self.max_tokens = max_tokens
        self.window_seconds = window_seconds
        self.token_usage = deque()  # (timestamp, request_id, token_count)
        self.lock = threading.Lock()
    
    def check_and_update(self, request_id: str, token_count: int) -> Tuple[bool, int]:
        """Check if request tokens are allowed and update state"""
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds
            
            # Remove old requests outside window
            while self.token_usage and self.token_usage[0][0] < cutoff_time:
                self.token_usage.popleft()
            
            # Calculate current token usage
            current_usage = sum(tokens for _, _, tokens in self.token_usage)
            
            # Check if we can accept new request
            if current_usage + token_count > self.max_tokens:
                return False, max(0, self.max_tokens - current_usage)
            
            # Add new request
            self.token_usage.append((current_time, request_id, token_count))
            return True, self.max_tokens - current_usage - token_count
    
    def get_remaining_tokens(self) -> int:
        """Get remaining tokens in current window"""
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds
            
            # Remove old requests
            while self.token_usage and self.token_usage[0][0] < cutoff_time:
                self.token_usage.popleft()
            
            current_usage = sum(tokens for _, _, tokens in self.token_usage)
            return max(0, self.max_tokens - current_usage)


class VelocityTracker:
    """Track spending velocity to detect anomalies"""
    
    def __init__(self, window_minutes: int = 5, spike_threshold: float = 3.0):
        self.window_minutes = window_minutes
        self.spike_threshold = spike_threshold
        self.spending_history = deque()
        self.baseline_rate = 0.0
        self.lock = threading.Lock()
    
    def add_spending(self, amount: float, timestamp: Optional[datetime] = None):
        """Add a spending event"""
        if timestamp is None:
            timestamp = datetime.now()
        
        with self.lock:
            self.spending_history.append((timestamp, amount))
            self._clean_old_entries()
            self._update_baseline()
    
    def get_velocity_score(self) -> float:
        """Get current velocity score (1.0 = normal)"""
        with self.lock:
            self._clean_old_entries()
            
            if not self.spending_history or self.baseline_rate == 0:
                return 1.0
            
            # Calculate current rate
            current_rate = sum(amount for _, amount in self.spending_history)
            
            # Return velocity score
            return current_rate / self.baseline_rate if self.baseline_rate > 0 else 1.0
    
    def is_anomaly(self) -> bool:
        """Check if current velocity is anomalous"""
        return self.get_velocity_score() > self.spike_threshold
    
    def _clean_old_entries(self):
        """Remove entries outside the window"""
        cutoff_time = datetime.now() - timedelta(minutes=self.window_minutes)
        while self.spending_history and self.spending_history[0][0] < cutoff_time:
            self.spending_history.popleft()
    
    def _update_baseline(self):
        """Update baseline spending rate"""
        if len(self.spending_history) >= 10:  # Need minimum samples
            # Use median of last 10 windows as baseline
            window_sums = []
            for i in range(min(10, len(self.spending_history))):
                window_sum = sum(amount for _, amount in list(self.spending_history)[i:i+10])
                window_sums.append(window_sum)
            
            self.baseline_rate = sorted(window_sums)[len(window_sums) // 2]  # Median


class CostGuard:
    """
    Main cost guard implementation with comprehensive protection.

    This class provides a robust system for monitoring and controlling LLM-related
    costs. It includes features for budget management, token storm detection, rate
    limiting, and velocity tracking to prevent unexpected spending.

    Configuration is managed through the CostGuardConfig dataclass, allowing for
    fine-tuned control over various thresholds and behaviors.
    """
    
    def __init__(self, config: Optional[CostGuardConfig] = None):
        self.config = config or CostGuardConfig()
        self.model_pricing = {**DEFAULT_MODEL_PRICING, **self.config.model_pricing_overrides}
        
        # Spending tracking
        self.spending_history: Dict[str, List[SpendingRecord]] = defaultdict(list)
        self.user_spending: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        # Rate limiters
        self.request_limiter = RateLimiter(
            self.config.max_requests_per_minute, 60
        )
        self.token_limiter = TokenRateLimiter(
            self.config.max_tokens_per_minute, 60
        )
        
        # Velocity tracking
        self.velocity_tracker = VelocityTracker(
            self.config.velocity_window_minutes,
            self.config.velocity_spike_threshold
        ) if self.config.enable_velocity_tracking else None
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Load historical data if configured
        if self.config.persist_spending_history:
            self._load_history()
    
    def check_request(self, 
                     request_id: str,
                     user_id: str,
                     model: str,
                     estimated_input_tokens: int,
                     estimated_output_tokens: int = 0,
                     metadata: Optional[Dict[str, Any]] = None) -> CostGuardResult:
        """
        Check if a request should be allowed based on cost constraints
        
        Args:
            request_id: Unique request identifier
            user_id: User making the request
            model: Model being used
            estimated_input_tokens: Estimated input token count
            estimated_output_tokens: Estimated output token count
            metadata: Additional request metadata
            
        Returns:
            CostGuardResult with decision and details
        """
        
        # Get model pricing
        pricing = self.model_pricing.get(model, self.model_pricing["default"])
        
        # Calculate costs
        estimated_cost = pricing.calculate_cost(estimated_input_tokens, estimated_output_tokens)
        total_tokens = estimated_input_tokens + estimated_output_tokens
        
        # Initialize result
        risk_factors = []
        alerts = []
        recommendations = []
        should_block = False
        block_reason = None
        
        # Get current spending
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        current_day = datetime.now().strftime("%Y-%m-%d")
        
        with self.lock:
            hourly_spend = self._get_period_spend(current_hour)
            daily_spend = self._get_period_spend(current_day)
            user_daily_spend = self.user_spending[user_id].get(current_day, 0.0)
            user_hourly_spend = self.user_spending[user_id].get(current_hour, 0.0)
        
        # Check per-request limit
        if estimated_cost > self.config.per_request_limit:
            should_block = True
            block_reason = BlockReason.PER_REQUEST_LIMIT_EXCEEDED
            risk_factors.append(f"Request cost ${estimated_cost:.2f} exceeds limit ${self.config.per_request_limit:.2f}")
            recommendations.append("Consider breaking this into smaller requests")
        
        # Check token storm
        model_threshold = pricing.token_storm_threshold
        if total_tokens > model_threshold:
            should_block = True
            block_reason = BlockReason.TOKEN_STORM_DETECTED
            risk_factors.append(f"Token count {total_tokens} exceeds {model} threshold {model_threshold}")
            recommendations.append(f"Reduce prompt/response size below {model_threshold} tokens")
            alerts.append(CostAlert.TOKEN_STORM_WARNING)
        elif total_tokens > model_threshold * 0.8:
            alerts.append(CostAlert.TOKEN_STORM_WARNING)
            recommendations.append(f"Approaching token limit ({total_tokens}/{model_threshold})")
        
        # Check daily budget
        projected_daily = daily_spend + estimated_cost
        if projected_daily > self.config.daily_budget:
            should_block = True
            block_reason = BlockReason.DAILY_BUDGET_EXCEEDED
            risk_factors.append(f"Would exceed daily budget: ${projected_daily:.2f} > ${self.config.daily_budget:.2f}")
            recommendations.append("Daily budget exhausted, try again tomorrow")
        elif projected_daily > self.config.daily_budget * self.config.critical_threshold_percentage:
            alerts.append(CostAlert.BUDGET_CRITICAL)
            recommendations.append(f"Critical: {(projected_daily/self.config.daily_budget)*100:.1f}% of daily budget used")
        elif projected_daily > self.config.daily_budget * self.config.alert_threshold_percentage:
            alerts.append(CostAlert.BUDGET_WARNING)
            recommendations.append(f"Warning: {(projected_daily/self.config.daily_budget)*100:.1f}% of daily budget used")
        
        # Check hourly limit
        projected_hourly = hourly_spend + estimated_cost
        if projected_hourly > self.config.hourly_limit:
            should_block = True
            if not block_reason:  # Don't override daily budget exceeded
                block_reason = BlockReason.HOURLY_LIMIT_EXCEEDED
            risk_factors.append(f"Would exceed hourly limit: ${projected_hourly:.2f} > ${self.config.hourly_limit:.2f}")
            recommendations.append("Hourly limit reached, please wait")
        
        # Check user quotas if enabled
        if self.config.enable_user_quotas:
            if user_daily_spend + estimated_cost > self.config.default_user_daily_budget:
                should_block = True
                block_reason = BlockReason.USER_QUOTA_EXCEEDED
                risk_factors.append(f"User daily quota exceeded")
                recommendations.append("Your daily quota is exhausted")
            elif user_hourly_spend + estimated_cost > self.config.default_user_hourly_limit:
                should_block = True
                block_reason = BlockReason.USER_QUOTA_EXCEEDED
                risk_factors.append(f"User hourly quota exceeded")
                recommendations.append("Your hourly quota is exhausted")
        
        # Check rate limits
        request_allowed, requests_remaining = self.request_limiter.check_and_update(request_id)
        if not request_allowed:
            should_block = True
            block_reason = BlockReason.RATE_LIMIT_EXCEEDED
            risk_factors.append("Request rate limit exceeded")
            recommendations.append(f"Max {self.config.max_requests_per_minute} requests/minute")
        
        # Check token rate limits
        token_allowed, tokens_remaining = self.token_limiter.check_and_update(request_id, total_tokens)
        if not token_allowed:
            should_block = True
            block_reason = BlockReason.RATE_LIMIT_EXCEEDED
            risk_factors.append("Token rate limit exceeded")
            recommendations.append(f"Max {self.config.max_tokens_per_minute} tokens/minute")
        
        # Check velocity if enabled
        velocity_score = 1.0
        if self.velocity_tracker and not should_block:
            velocity_score = self.velocity_tracker.get_velocity_score()
            if self.velocity_tracker.is_anomaly():
                alerts.append(CostAlert.UNUSUAL_SPENDING)
                risk_factors.append(f"Spending velocity {velocity_score:.1f}x normal")
                recommendations.append("Unusual spending pattern detected")
                
                # Don't block on velocity alone, but flag it
                if velocity_score > self.config.velocity_spike_threshold * 2:
                    should_block = True
                    block_reason = BlockReason.VELOCITY_LIMIT_EXCEEDED
                    risk_factors.append("Extreme spending velocity detected")
        
        # Create result
        result = CostGuardResult(
            request_id=request_id,
            should_block=should_block,
            block_reason=block_reason,
            risk_factors=risk_factors,
            current_daily_spend=daily_spend,
            current_hourly_spend=hourly_spend,
            daily_budget_remaining=max(0, self.config.daily_budget - daily_spend),
            hourly_budget_remaining=max(0, self.config.hourly_limit - hourly_spend),
            projected_cost=estimated_cost,
            projected_daily_spend=projected_daily,
            alerts=alerts,
            recommendations=recommendations,
            tokens_requested=total_tokens,
            rate_limit_remaining=requests_remaining,
            velocity_score=velocity_score
        )
        
        # Record the request attempt (even if blocked)
        self._record_spending(
            SpendingRecord(
                timestamp=datetime.now(),
                user_id=user_id,
                request_id=request_id,
                model=model,
                input_tokens=estimated_input_tokens,
                output_tokens=estimated_output_tokens,
                cost=estimated_cost,
                blocked=should_block,
                block_reason=block_reason
            )
        )
        
        return result
    
    def record_actual_usage(self,
                           request_id: str,
                           user_id: str,
                           model: str,
                           actual_input_tokens: int,
                           actual_output_tokens: int,
                           metadata: Optional[Dict[str, Any]] = None):
        """Record actual token usage after request completion"""
        pricing = self.model_pricing.get(model, self.model_pricing["default"])
        actual_cost = pricing.calculate_cost(actual_input_tokens, actual_output_tokens)
        
        with self.lock:
            # Update spending records
            record = SpendingRecord(
                timestamp=datetime.now(),
                user_id=user_id,
                request_id=f"{request_id}_actual",
                model=model,
                input_tokens=actual_input_tokens,
                output_tokens=actual_output_tokens,
                cost=actual_cost,
                blocked=False
            )
            self._record_spending(record)
            
            # Update velocity tracking
            if self.velocity_tracker:
                self.velocity_tracker.add_spending(actual_cost)
    
    def get_spending_summary(self, user_id: Optional[str] = None, 
                           period: Optional[str] = None) -> Dict[str, Any]:
        """Get spending summary for user or period"""
        with self.lock:
            if period:
                period_spend = self._get_period_spend(period)
                period_records = self._get_period_records(period)
                
                return {
                    "period": period,
                    "total_spend": period_spend,
                    "request_count": len(period_records),
                    "blocked_count": sum(1 for r in period_records if r.blocked),
                    "average_cost": period_spend / len(period_records) if period_records else 0,
                    "top_models": self._get_top_models(period_records)
                }
            
            # Current day summary
            current_day = datetime.now().strftime("%Y-%m-%d")
            current_hour = datetime.now().strftime("%Y-%m-%d-%H")
            
            summary = {
                "current_day": current_day,
                "daily_spend": self._get_period_spend(current_day),
                "hourly_spend": self._get_period_spend(current_hour),
                "daily_budget_remaining": max(0, self.config.daily_budget - self._get_period_spend(current_day)),
                "hourly_budget_remaining": max(0, self.config.hourly_limit - self._get_period_spend(current_hour))
            }
            
            if user_id:
                summary["user_daily_spend"] = self.user_spending[user_id].get(current_day, 0.0)
                summary["user_hourly_spend"] = self.user_spending[user_id].get(current_hour, 0.0)
            
            return summary
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current active alerts"""
        alerts = []
        current_day = datetime.now().strftime("%Y-%m-%d")
        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        
        daily_spend = self._get_period_spend(current_day)
        hourly_spend = self._get_period_spend(current_hour)
        
        # Budget alerts
        if daily_spend > self.config.daily_budget * self.config.critical_threshold_percentage:
            alerts.append({
                "type": CostAlert.BUDGET_CRITICAL,
                "message": f"Critical: Daily spending at {(daily_spend/self.config.daily_budget)*100:.1f}%",
                "severity": "critical"
            })
        elif daily_spend > self.config.daily_budget * self.config.alert_threshold_percentage:
            alerts.append({
                "type": CostAlert.BUDGET_WARNING,
                "message": f"Warning: Daily spending at {(daily_spend/self.config.daily_budget)*100:.1f}%",
                "severity": "warning"
            })
        
        # Velocity alerts
        if self.velocity_tracker and self.velocity_tracker.is_anomaly():
            velocity_score = self.velocity_tracker.get_velocity_score()
            alerts.append({
                "type": CostAlert.UNUSUAL_SPENDING,
                "message": f"Unusual spending velocity: {velocity_score:.1f}x normal rate",
                "severity": "warning"
            })
        
        return alerts
    
    def _record_spending(self, record: SpendingRecord):
        """Record a spending event"""
        # Add to history
        period_key = record.timestamp.strftime("%Y-%m-%d")
        self.spending_history[period_key].append(record)
        
        # Update user spending
        if not record.blocked:
            hour_key = record.timestamp.strftime("%Y-%m-%d-%H")
            day_key = record.timestamp.strftime("%Y-%m-%d")
            
            self.user_spending[record.user_id][hour_key] += record.cost
            self.user_spending[record.user_id][day_key] += record.cost
            
            # Update velocity tracking
            if self.velocity_tracker:
                self.velocity_tracker.add_spending(record.cost, record.timestamp)
        
        # Clean old records
        self._clean_old_records()
        
        # Persist if configured
        if self.config.persist_spending_history:
            self._save_history()
    
    def _get_period_spend(self, period: str) -> float:
        """Get total spending for a period"""
        records = self._get_period_records(period)
        return sum(r.cost for r in records if not r.blocked)
    
    def _get_period_records(self, period: str) -> List[SpendingRecord]:
        """Get all records for a specific period (day or hour)."""
        records = []
        # Handle hourly period
        if len(period.split('-')) == 4:
            day_period = "-".join(period.split("-")[:3])
            if day_period in self.spending_history:
                hour = int(period.split("-")[3])
                for record in self.spending_history[day_period]:
                    if record.timestamp.hour == hour:
                        records.append(record)
        # Handle daily period
        elif period in self.spending_history:
            records.extend(self.spending_history[period])
        return records
    
    def _get_top_models(self, records: List[SpendingRecord], limit: int = 5) -> List[Dict[str, Any]]:
        """Get top models by usage from records"""
        model_costs = defaultdict(float)
        model_counts = defaultdict(int)
        
        for record in records:
            if not record.blocked:
                model_costs[record.model] += record.cost
                model_counts[record.model] += 1
        
        top_models = []
        for model in sorted(model_costs.keys(), key=lambda m: model_costs[m], reverse=True)[:limit]:
            top_models.append({
                "model": model,
                "total_cost": model_costs[model],
                "request_count": model_counts[model],
                "average_cost": model_costs[model] / model_counts[model]
            })
        
        return top_models
    
    def _clean_old_records(self):
        """Remove records older than retention period based on timestamp."""
        if not self.config.history_retention_days:
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.config.history_retention_days)
        
        # Clean spending_history (daily records)
        keys_to_delete = []
        for period_key, records in self.spending_history.items():
            # Assuming period_key is 'YYYY-MM-DD'
            period_date = datetime.strptime(period_key, "%Y-%m-%d")
            if period_date < cutoff_date:
                keys_to_delete.append(period_key)
        for key in keys_to_delete:
            del self.spending_history[key]
        
        # Clean user_spending (hourly and daily records)
        for user_id in list(self.user_spending.keys()):
            periods_to_delete = []
            for period_key in self.user_spending[user_id].keys():
                # Period key can be 'YYYY-MM-DD' or 'YYYY-MM-DD-HH'
                try:
                    if len(period_key.split('-')) == 4:
                        record_date = datetime.strptime(period_key, "%Y-%m-%d-%H")
                    else:
                        record_date = datetime.strptime(period_key, "%Y-%m-%d")
                    
                    if record_date < cutoff_date:
                        periods_to_delete.append(period_key)
                except ValueError:
                    # Handle malformed period keys if any
                    logger.warning(f"Malformed period key found: {period_key}")
                    continue
            
            for period_key in periods_to_delete:
                del self.user_spending[user_id][period_key]
            
            # Remove user if no spending records remain
            if not self.user_spending[user_id]:
                del self.user_spending[user_id]
    
    def _save_history(self):
        """Save spending history to file"""
        try:
            history_path = Path(self.config.history_file_path)
            
            # Convert to serializable format
            serializable_history = {}
            for period, records in self.spending_history.items():
                serializable_history[period] = [
                    {
                        **asdict(record),
                        "timestamp": record.timestamp.isoformat(),
                        "block_reason": record.block_reason.value if record.block_reason else None
                    }
                    for record in records
                ]
            
            with open(history_path, 'w') as f:
                json.dump({
                    "history": serializable_history,
                    "user_spending": dict(self.user_spending),
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save cost guard history: {e}")
    
    def _load_history(self):
        """Load spending history from file"""
        try:
            history_path = Path(self.config.history_file_path)
            if not history_path.exists():
                return
            
            with open(history_path, 'r') as f:
                data = json.load(f)
            
            # Convert from serializable format
            for period, records in data.get("history", {}).items():
                self.spending_history[period] = [
                    SpendingRecord(
                        timestamp=datetime.fromisoformat(r["timestamp"]),
                        user_id=r["user_id"],
                        request_id=r["request_id"],
                        model=r["model"],
                        input_tokens=r["input_tokens"],
                        output_tokens=r["output_tokens"],
                        cost=r["cost"],
                        blocked=r["blocked"],
                        block_reason=BlockReason(r["block_reason"]) if r.get("block_reason") else None
                    )
                    for r in records
                ]
            
            # Load user spending
            self.user_spending = defaultdict(lambda: defaultdict(float))
            for user_id, spending in data.get("user_spending", {}).items():
                self.user_spending[user_id] = defaultdict(float, spending)
                
            logger.info(f"Loaded cost guard history from {history_path}")
            
        except Exception as e:
            logger.error(f"Failed to load cost guard history: {e}")
    
    def reset_period(self, period: str):
        """Reset spending for a specific period (admin function)"""
        with self.lock:
            if period in self.spending_history:
                del self.spending_history[period]
            
            # Reset user spending for this period
            for user_id in self.user_spending:
                if period in self.user_spending[user_id]:
                    del self.user_spending[user_id][period]
            
            logger.info(f"Reset spending for period: {period}")


# Convenience functions
def create_cost_guard(daily_budget: float = 1000.0,
                     hourly_limit: float = 100.0,
                     token_storm_threshold: int = 5000,
                     **kwargs) -> CostGuard:
    """Create a cost guard with common configuration"""
    config = CostGuardConfig(
        daily_budget=daily_budget,
        hourly_limit=hourly_limit,
        token_storm_threshold=token_storm_threshold,
        **kwargs
    )
    return CostGuard(config)


def estimate_cost(model: str, input_tokens: int, output_tokens: int = 0) -> float:
    """Estimate cost for a model and token count"""
    pricing = DEFAULT_MODEL_PRICING.get(model, DEFAULT_MODEL_PRICING["default"])
    return pricing.calculate_cost(input_tokens, output_tokens)


if __name__ == "__main__":
    # Example usage
    import uuid
    
    # Create cost guard with configuration
    config = CostGuardConfig(
        daily_budget=100.0,
        hourly_limit=20.0,
        per_request_limit=5.0,
        enable_velocity_tracking=True
    )
    
    cost_guard = CostGuard(config)
    
    # Test various scenarios
    test_cases = [
        # Normal request
        ("normal", "user1", "gpt-3.5-turbo", 1000, 500),
        # Expensive request
        ("expensive", "user1", "gpt-4", 8000, 2000),
        # Token storm
        ("storm", "user2", "gpt-4", 15000, 5000),
        # Multiple rapid requests
        ("rapid1", "user3", "gpt-3.5-turbo", 500, 200),
        ("rapid2", "user3", "gpt-3.5-turbo", 500, 200),
        ("rapid3", "user3", "gpt-3.5-turbo", 500, 200),
    ]
    
    print("Cost Guard Test Results")
    print("=" * 80)
    
    for test_name, user_id, model, input_tokens, output_tokens in test_cases:
        request_id = f"test_{test_name}_{uuid.uuid4()}"
        
        result = cost_guard.check_request(
            request_id=request_id,
            user_id=user_id,
            model=model,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens
        )
        
        print(f"\nTest: {test_name}")
        print(f"Model: {model}, Tokens: {input_tokens}+{output_tokens}")
        print(f"Estimated Cost: ${result.projected_cost:.4f}")
        print(f"Blocked: {result.should_block}")
        if result.should_block:
            print(f"Reason: {result.block_reason}")
        print(f"Daily Budget Remaining: ${result.daily_budget_remaining:.2f}")
        print(f"Alerts: {result.alerts}")
        print(f"Recommendations: {result.recommendations[:2]}")
    
    # Show spending summary
    print("\n" + "=" * 80)
    print("Spending Summary")
    summary = cost_guard.get_spending_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # Show active alerts
    print("\n" + "=" * 80)
    print("Active Alerts")
    alerts = cost_guard.get_alerts()
    for alert in alerts:
        print(f"- [{alert['severity'].upper()}] {alert['message']}")