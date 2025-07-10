"""
Community Feedback Collection System

Collects, analyzes, and manages community feedback to improve RedForge.
Supports multiple feedback channels including GitHub issues, surveys, telemetry,
and direct user submissions.
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib
import asyncio
from contextlib import asynccontextmanager

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import github
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False


class FeedbackType(Enum):
    """Types of community feedback"""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    PERFORMANCE_ISSUE = "performance_issue"
    DOCUMENTATION = "documentation"
    USER_EXPERIENCE = "user_experience"
    SECURITY_CONCERN = "security_concern"
    INTEGRATION_REQUEST = "integration_request"
    GENERAL_FEEDBACK = "general_feedback"


class FeedbackPriority(Enum):
    """Priority levels for community feedback"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ENHANCEMENT = "enhancement"


class FeedbackStatus(Enum):
    """Status of feedback processing"""
    NEW = "new"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    NEED_MORE_INFO = "need_more_info"


@dataclass
class FeedbackItem:
    """Individual feedback item"""
    feedback_id: str
    feedback_type: FeedbackType
    title: str
    description: str
    priority: FeedbackPriority
    status: FeedbackStatus
    source: str  # github, survey, telemetry, direct
    source_id: Optional[str] = None  # Issue number, survey ID, etc.
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    votes: int = 0
    implementation_notes: Optional[str] = None
    related_issues: List[str] = field(default_factory=list)


@dataclass
class FeedbackAnalytics:
    """Analytics for community feedback"""
    total_feedback: int
    feedback_by_type: Dict[str, int]
    feedback_by_priority: Dict[str, int]
    feedback_by_status: Dict[str, int]
    trending_topics: List[str]
    implementation_rate: float
    average_response_time: float
    user_satisfaction_score: Optional[float] = None
    period_start: datetime = field(default_factory=lambda: datetime.now() - timedelta(days=30))
    period_end: datetime = field(default_factory=datetime.now)


class GitHubFeedbackCollector:
    """Collects feedback from GitHub issues and discussions"""
    
    def __init__(self, repo_name: str, access_token: Optional[str] = None):
        self.repo_name = repo_name
        self.access_token = access_token or os.getenv("GITHUB_TOKEN")
        self.github_client = None
        
        if GITHUB_AVAILABLE and self.access_token:
            self.github_client = github.Github(self.access_token)
    
    async def collect_issues(self, since: Optional[datetime] = None) -> List[FeedbackItem]:
        """Collect feedback from GitHub issues"""
        if not self.github_client:
            return []
        
        try:
            repo = self.github_client.get_repo(self.repo_name)
            issues = repo.get_issues(
                state="all",
                since=since or datetime.now() - timedelta(days=30)
            )
            
            feedback_items = []
            for issue in issues:
                feedback_type = self._classify_issue_type(issue)
                priority = self._determine_priority(issue)
                status = self._map_issue_status(issue)
                
                feedback_item = FeedbackItem(
                    feedback_id=f"gh_{issue.number}",
                    feedback_type=feedback_type,
                    title=issue.title,
                    description=issue.body or "",
                    priority=priority,
                    status=status,
                    source="github",
                    source_id=str(issue.number),
                    user_id=issue.user.login,
                    created_at=issue.created_at,
                    updated_at=issue.updated_at,
                    tags=[label.name for label in issue.labels],
                    votes=issue.reactions["thumbs_up"] - issue.reactions["thumbs_down"],
                    metadata={
                        "url": issue.html_url,
                        "comments": issue.comments,
                        "assignees": [a.login for a in issue.assignees],
                        "milestone": issue.milestone.title if issue.milestone else None
                    }
                )
                feedback_items.append(feedback_item)
            
            return feedback_items
            
        except Exception as e:
            print(f"Error collecting GitHub issues: {e}")
            return []
    
    def _classify_issue_type(self, issue) -> FeedbackType:
        """Classify GitHub issue into feedback type"""
        labels = [label.name.lower() for label in issue.labels]
        title_lower = issue.title.lower()
        
        if any(label in labels for label in ["bug", "defect", "error"]):
            return FeedbackType.BUG_REPORT
        elif any(label in labels for label in ["enhancement", "feature", "feature-request"]):
            return FeedbackType.FEATURE_REQUEST
        elif any(label in labels for label in ["performance", "optimization"]):
            return FeedbackType.PERFORMANCE_ISSUE
        elif any(label in labels for label in ["documentation", "docs"]):
            return FeedbackType.DOCUMENTATION
        elif any(label in labels for label in ["ux", "ui", "usability"]):
            return FeedbackType.USER_EXPERIENCE
        elif any(label in labels for label in ["security", "vulnerability"]):
            return FeedbackType.SECURITY_CONCERN
        elif "integration" in title_lower or "api" in title_lower:
            return FeedbackType.INTEGRATION_REQUEST
        else:
            return FeedbackType.GENERAL_FEEDBACK
    
    def _determine_priority(self, issue) -> FeedbackPriority:
        """Determine priority from GitHub issue"""
        labels = [label.name.lower() for label in issue.labels]
        
        if any(label in labels for label in ["critical", "urgent", "p0"]):
            return FeedbackPriority.CRITICAL
        elif any(label in labels for label in ["high", "important", "p1"]):
            return FeedbackPriority.HIGH
        elif any(label in labels for label in ["medium", "p2"]):
            return FeedbackPriority.MEDIUM
        elif any(label in labels for label in ["low", "p3"]):
            return FeedbackPriority.LOW
        else:
            return FeedbackPriority.ENHANCEMENT
    
    def _map_issue_status(self, issue) -> FeedbackStatus:
        """Map GitHub issue state to feedback status"""
        if issue.state == "closed":
            labels = [label.name.lower() for label in issue.labels]
            if "duplicate" in labels:
                return FeedbackStatus.DUPLICATE
            elif "wontfix" in labels or "rejected" in labels:
                return FeedbackStatus.REJECTED
            else:
                return FeedbackStatus.IMPLEMENTED
        else:
            labels = [label.name.lower() for label in issue.labels]
            if "in-progress" in labels or "assigned" in labels:
                return FeedbackStatus.IN_PROGRESS
            elif "need-info" in labels or "question" in labels:
                return FeedbackStatus.NEED_MORE_INFO
            elif "triaged" in labels:
                return FeedbackStatus.TRIAGED
            else:
                return FeedbackStatus.NEW


class TelemetryFeedbackCollector:
    """Collects implicit feedback from usage telemetry"""
    
    def __init__(self, telemetry_data_path: Optional[str] = None):
        self.telemetry_data_path = telemetry_data_path or "~/.redforge/telemetry"
        self.data_path = Path(self.telemetry_data_path).expanduser()
        self.data_path.mkdir(parents=True, exist_ok=True)
    
    def collect_usage_feedback(self, days_back: int = 30) -> List[FeedbackItem]:
        """Extract feedback signals from usage telemetry"""
        feedback_items = []
        
        # Analyze error patterns
        error_feedback = self._analyze_error_patterns(days_back)
        feedback_items.extend(error_feedback)
        
        # Analyze performance issues
        performance_feedback = self._analyze_performance_patterns(days_back)
        feedback_items.extend(performance_feedback)
        
        # Analyze feature usage
        feature_feedback = self._analyze_feature_usage(days_back)
        feedback_items.extend(feature_feedback)
        
        return feedback_items
    
    def _analyze_error_patterns(self, days_back: int) -> List[FeedbackItem]:
        """Analyze error patterns to identify common issues"""
        try:
            error_log_path = self.data_path / "errors.json"
            if not error_log_path.exists():
                return []
            
            with open(error_log_path) as f:
                error_data = json.load(f)
            
            # Group errors by type and frequency
            error_counts = {}
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for error in error_data:
                error_date = datetime.fromisoformat(error.get("timestamp", ""))
                if error_date < cutoff_date:
                    continue
                    
                error_type = error.get("error_type", "unknown")
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
            feedback_items = []
            for error_type, count in error_counts.items():
                if count >= 5:  # Only report frequently occurring errors
                    feedback_item = FeedbackItem(
                        feedback_id=f"tel_error_{hashlib.md5(error_type.encode()).hexdigest()[:8]}",
                        feedback_type=FeedbackType.BUG_REPORT,
                        title=f"Frequent error: {error_type}",
                        description=f"Error '{error_type}' occurred {count} times in the last {days_back} days",
                        priority=FeedbackPriority.HIGH if count >= 20 else FeedbackPriority.MEDIUM,
                        status=FeedbackStatus.NEW,
                        source="telemetry",
                        metadata={
                            "error_count": count,
                            "error_type": error_type,
                            "analysis_period_days": days_back
                        }
                    )
                    feedback_items.append(feedback_item)
            
            return feedback_items
            
        except Exception as e:
            print(f"Error analyzing error patterns: {e}")
            return []
    
    def _analyze_performance_patterns(self, days_back: int) -> List[FeedbackItem]:
        """Analyze performance metrics to identify slow operations"""
        try:
            perf_log_path = self.data_path / "performance.json"
            if not perf_log_path.exists():
                return []
            
            with open(perf_log_path) as f:
                perf_data = json.load(f)
            
            slow_operations = {}
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for metric in perf_data:
                metric_date = datetime.fromisoformat(metric.get("timestamp", ""))
                if metric_date < cutoff_date:
                    continue
                
                operation = metric.get("operation", "unknown")
                duration = metric.get("duration_ms", 0)
                
                if duration > 5000:  # Operations taking more than 5 seconds
                    if operation not in slow_operations:
                        slow_operations[operation] = []
                    slow_operations[operation].append(duration)
            
            feedback_items = []
            for operation, durations in slow_operations.items():
                if len(durations) >= 3:  # Multiple slow instances
                    avg_duration = sum(durations) / len(durations)
                    feedback_item = FeedbackItem(
                        feedback_id=f"tel_perf_{hashlib.md5(operation.encode()).hexdigest()[:8]}",
                        feedback_type=FeedbackType.PERFORMANCE_ISSUE,
                        title=f"Slow operation: {operation}",
                        description=f"Operation '{operation}' is consistently slow (avg: {avg_duration:.0f}ms, {len(durations)} instances)",
                        priority=FeedbackPriority.MEDIUM,
                        status=FeedbackStatus.NEW,
                        source="telemetry",
                        metadata={
                            "operation": operation,
                            "average_duration_ms": avg_duration,
                            "slow_instances": len(durations),
                            "analysis_period_days": days_back
                        }
                    )
                    feedback_items.append(feedback_item)
            
            return feedback_items
            
        except Exception as e:
            print(f"Error analyzing performance patterns: {e}")
            return []
    
    def _analyze_feature_usage(self, days_back: int) -> List[FeedbackItem]:
        """Analyze feature usage to identify unused or problematic features"""
        try:
            usage_log_path = self.data_path / "feature_usage.json"
            if not usage_log_path.exists():
                return []
            
            with open(usage_log_path) as f:
                usage_data = json.load(f)
            
            feature_usage = {}
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for usage in usage_data:
                usage_date = datetime.fromisoformat(usage.get("timestamp", ""))
                if usage_date < cutoff_date:
                    continue
                
                feature = usage.get("feature", "unknown")
                feature_usage[feature] = feature_usage.get(feature, 0) + 1
            
            # Identify underused features that might need improvement
            total_sessions = sum(feature_usage.values())
            feedback_items = []
            
            for feature, usage_count in feature_usage.items():
                usage_percentage = (usage_count / total_sessions) * 100 if total_sessions > 0 else 0
                
                if usage_percentage < 5 and usage_count > 0:  # Low usage features
                    feedback_item = FeedbackItem(
                        feedback_id=f"tel_usage_{hashlib.md5(feature.encode()).hexdigest()[:8]}",
                        feedback_type=FeedbackType.USER_EXPERIENCE,
                        title=f"Underutilized feature: {feature}",
                        description=f"Feature '{feature}' has low usage ({usage_percentage:.1f}%) - may need UX improvements",
                        priority=FeedbackPriority.LOW,
                        status=FeedbackStatus.NEW,
                        source="telemetry",
                        metadata={
                            "feature": feature,
                            "usage_count": usage_count,
                            "usage_percentage": usage_percentage,
                            "analysis_period_days": days_back
                        }
                    )
                    feedback_items.append(feedback_item)
            
            return feedback_items
            
        except Exception as e:
            print(f"Error analyzing feature usage: {e}")
            return []


class CommunityFeedbackManager:
    """Main manager for community feedback collection and analysis"""
    
    def __init__(self, 
                 storage_path: Optional[str] = None,
                 github_repo: Optional[str] = None,
                 github_token: Optional[str] = None):
        self.storage_path = Path(storage_path or "~/.redforge/feedback").expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize collectors
        self.github_collector = GitHubFeedbackCollector(
            repo_name=github_repo or "siwenwang0803/RedForge",
            access_token=github_token
        ) if github_repo else None
        
        self.telemetry_collector = TelemetryFeedbackCollector()
        
        # Load existing feedback
        self.feedback_items: List[FeedbackItem] = self._load_feedback()
    
    async def collect_all_feedback(self, days_back: int = 30) -> int:
        """Collect feedback from all sources"""
        new_feedback_count = 0
        
        # Collect from GitHub
        if self.github_collector:
            try:
                github_feedback = await self.github_collector.collect_issues(
                    since=datetime.now() - timedelta(days=days_back)
                )
                new_feedback_count += self._merge_feedback(github_feedback)
            except Exception as e:
                print(f"Error collecting GitHub feedback: {e}")
        
        # Collect from telemetry
        try:
            telemetry_feedback = self.telemetry_collector.collect_usage_feedback(days_back)
            new_feedback_count += self._merge_feedback(telemetry_feedback)
        except Exception as e:
            print(f"Error collecting telemetry feedback: {e}")
        
        # Save updated feedback
        self._save_feedback()
        
        return new_feedback_count
    
    def analyze_feedback_trends(self, days_back: int = 30) -> FeedbackAnalytics:
        """Analyze feedback trends and generate analytics"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_feedback = [
            f for f in self.feedback_items 
            if f.created_at >= cutoff_date
        ]
        
        # Count by type
        feedback_by_type = {}
        for feedback_type in FeedbackType:
            count = sum(1 for f in recent_feedback if f.feedback_type == feedback_type)
            feedback_by_type[feedback_type.value] = count
        
        # Count by priority
        feedback_by_priority = {}
        for priority in FeedbackPriority:
            count = sum(1 for f in recent_feedback if f.priority == priority)
            feedback_by_priority[priority.value] = count
        
        # Count by status
        feedback_by_status = {}
        for status in FeedbackStatus:
            count = sum(1 for f in recent_feedback if f.status == status)
            feedback_by_status[status.value] = count
        
        # Identify trending topics from tags
        all_tags = []
        for f in recent_feedback:
            all_tags.extend(f.tags)
        
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        trending_topics = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        trending_topics = [tag for tag, count in trending_topics]
        
        # Calculate implementation rate
        implemented = sum(1 for f in recent_feedback if f.status == FeedbackStatus.IMPLEMENTED)
        total_actionable = sum(1 for f in recent_feedback 
                             if f.status not in [FeedbackStatus.DUPLICATE, FeedbackStatus.REJECTED])
        implementation_rate = (implemented / total_actionable * 100) if total_actionable > 0 else 0
        
        # Calculate average response time (mock for now)
        avg_response_time = 2.5  # Average days to first response
        
        return FeedbackAnalytics(
            total_feedback=len(recent_feedback),
            feedback_by_type=feedback_by_type,
            feedback_by_priority=feedback_by_priority,
            feedback_by_status=feedback_by_status,
            trending_topics=trending_topics,
            implementation_rate=implementation_rate,
            average_response_time=avg_response_time,
            period_start=cutoff_date,
            period_end=datetime.now()
        )
    
    def get_prioritized_feedback(self, limit: int = 20) -> List[FeedbackItem]:
        """Get prioritized list of feedback items for action"""
        # Priority scoring: Critical=100, High=75, Medium=50, Low=25, Enhancement=10
        priority_scores = {
            FeedbackPriority.CRITICAL: 100,
            FeedbackPriority.HIGH: 75,
            FeedbackPriority.MEDIUM: 50,
            FeedbackPriority.LOW: 25,
            FeedbackPriority.ENHANCEMENT: 10
        }
        
        # Status scoring: New=20, Triaged=15, InProgress=10, Others=0
        status_scores = {
            FeedbackStatus.NEW: 20,
            FeedbackStatus.TRIAGED: 15,
            FeedbackStatus.IN_PROGRESS: 10
        }
        
        def score_feedback(feedback: FeedbackItem) -> float:
            score = priority_scores.get(feedback.priority, 0)
            score += status_scores.get(feedback.status, 0)
            score += min(feedback.votes, 20)  # Max 20 points from votes
            
            # Boost recent feedback
            days_old = (datetime.now() - feedback.created_at).days
            if days_old <= 7:
                score *= 1.2
            elif days_old <= 30:
                score *= 1.1
            
            return score
        
        actionable_feedback = [
            f for f in self.feedback_items 
            if f.status not in [FeedbackStatus.IMPLEMENTED, FeedbackStatus.REJECTED, FeedbackStatus.DUPLICATE]
        ]
        
        sorted_feedback = sorted(actionable_feedback, key=score_feedback, reverse=True)
        return sorted_feedback[:limit]
    
    def update_feedback_status(self, feedback_id: str, status: FeedbackStatus, 
                             implementation_notes: Optional[str] = None) -> bool:
        """Update the status of a feedback item"""
        for feedback in self.feedback_items:
            if feedback.feedback_id == feedback_id:
                feedback.status = status
                feedback.updated_at = datetime.now()
                if implementation_notes:
                    feedback.implementation_notes = implementation_notes
                self._save_feedback()
                return True
        return False
    
    def _merge_feedback(self, new_feedback: List[FeedbackItem]) -> int:
        """Merge new feedback with existing, avoiding duplicates"""
        existing_ids = {f.feedback_id for f in self.feedback_items}
        new_count = 0
        
        for feedback in new_feedback:
            if feedback.feedback_id not in existing_ids:
                self.feedback_items.append(feedback)
                new_count += 1
            else:
                # Update existing feedback if it's newer
                for i, existing in enumerate(self.feedback_items):
                    if existing.feedback_id == feedback.feedback_id:
                        if feedback.updated_at > existing.updated_at:
                            self.feedback_items[i] = feedback
                        break
        
        return new_count
    
    def _load_feedback(self) -> List[FeedbackItem]:
        """Load feedback from storage"""
        feedback_file = self.storage_path / "feedback.json"
        if not feedback_file.exists():
            return []
        
        try:
            with open(feedback_file) as f:
                data = json.load(f)
            
            feedback_items = []
            for item_data in data:
                # Convert string enums back to enum objects
                item_data['feedback_type'] = FeedbackType(item_data['feedback_type'])
                item_data['priority'] = FeedbackPriority(item_data['priority'])
                item_data['status'] = FeedbackStatus(item_data['status'])
                
                # Convert ISO strings back to datetime
                item_data['created_at'] = datetime.fromisoformat(item_data['created_at'])
                item_data['updated_at'] = datetime.fromisoformat(item_data['updated_at'])
                
                feedback_items.append(FeedbackItem(**item_data))
            
            return feedback_items
            
        except Exception as e:
            print(f"Error loading feedback: {e}")
            return []
    
    def _save_feedback(self):
        """Save feedback to storage"""
        feedback_file = self.storage_path / "feedback.json"
        
        try:
            # Convert to JSON-serializable format
            data = []
            for feedback in self.feedback_items:
                item_data = {
                    'feedback_id': feedback.feedback_id,
                    'feedback_type': feedback.feedback_type.value,
                    'title': feedback.title,
                    'description': feedback.description,
                    'priority': feedback.priority.value,
                    'status': feedback.status.value,
                    'source': feedback.source,
                    'source_id': feedback.source_id,
                    'user_id': feedback.user_id,
                    'user_email': feedback.user_email,
                    'created_at': feedback.created_at.isoformat(),
                    'updated_at': feedback.updated_at.isoformat(),
                    'tags': feedback.tags,
                    'metadata': feedback.metadata,
                    'votes': feedback.votes,
                    'implementation_notes': feedback.implementation_notes,
                    'related_issues': feedback.related_issues
                }
                data.append(item_data)
            
            with open(feedback_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving feedback: {e}")


# Convenience functions for CLI integration
async def collect_community_feedback(days_back: int = 30, 
                                   github_repo: Optional[str] = None) -> Tuple[int, FeedbackAnalytics]:
    """Collect community feedback and return analytics"""
    manager = CommunityFeedbackManager(github_repo=github_repo)
    new_feedback_count = await manager.collect_all_feedback(days_back)
    analytics = manager.analyze_feedback_trends(days_back)
    return new_feedback_count, analytics


def get_feedback_priorities(limit: int = 10) -> List[Dict[str, Any]]:
    """Get prioritized feedback for development planning"""
    manager = CommunityFeedbackManager()
    prioritized = manager.get_prioritized_feedback(limit)
    
    return [
        {
            'id': f.feedback_id,
            'type': f.feedback_type.value,
            'title': f.title,
            'priority': f.priority.value,
            'status': f.status.value,
            'votes': f.votes,
            'created': f.created_at.strftime('%Y-%m-%d'),
            'source': f.source
        }
        for f in prioritized
    ]


def update_feedback_implementation(feedback_id: str, implemented: bool = True, 
                                 notes: Optional[str] = None) -> bool:
    """Mark feedback as implemented"""
    manager = CommunityFeedbackManager()
    status = FeedbackStatus.IMPLEMENTED if implemented else FeedbackStatus.IN_PROGRESS
    return manager.update_feedback_status(feedback_id, status, notes)