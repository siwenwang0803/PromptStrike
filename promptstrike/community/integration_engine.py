"""
Community Feedback Integration Engine

Integrates community feedback into PromptStrike development process.
Provides automated feedback processing, priority scheduling, and
implementation tracking.
"""

import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib
from collections import defaultdict

from .feedback_collector import (
    CommunityFeedbackManager,
    FeedbackType,
    FeedbackPriority,
    FeedbackStatus,
    FeedbackItem,
    FeedbackAnalytics
)


class IntegrationAction(Enum):
    """Actions that can be taken on feedback"""
    SCHEDULE_DEVELOPMENT = "schedule_development"
    CREATE_DOCUMENTATION = "create_documentation"
    UPDATE_TUTORIAL = "update_tutorial"
    IMPROVE_ERROR_MESSAGE = "improve_error_message"
    ADD_FEATURE_FLAG = "add_feature_flag"
    CREATE_EXAMPLE = "create_example"
    OPTIMIZE_PERFORMANCE = "optimize_performance"
    FIX_BUG = "fix_bug"
    ENHANCE_UX = "enhance_ux"
    ADD_INTEGRATION = "add_integration"


class IntegrationPlan(Enum):
    """Implementation timeline plans"""
    IMMEDIATE = "immediate"     # Next patch (1-2 weeks)
    SHORT_TERM = "short_term"   # Next minor release (1-2 months)
    MEDIUM_TERM = "medium_term" # Next major release (3-6 months)
    LONG_TERM = "long_term"     # Future releases (6+ months)
    BACKLOG = "backlog"         # No immediate plans


@dataclass
class IntegrationTask:
    """Task for integrating community feedback"""
    task_id: str
    feedback_id: str
    action: IntegrationAction
    plan: IntegrationPlan
    title: str
    description: str
    estimated_effort: int  # Hours
    priority_score: float
    dependencies: List[str] = field(default_factory=list)
    assignee: Optional[str] = None
    milestone: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed: bool = False
    implementation_notes: Optional[str] = None
    related_files: List[str] = field(default_factory=list)
    test_requirements: List[str] = field(default_factory=list)


@dataclass
class ReleaseImpact:
    """Impact assessment for releases"""
    user_satisfaction_improvement: float
    feature_adoption_potential: float
    technical_debt_reduction: float
    maintenance_overhead: float
    breaking_changes: bool
    documentation_updates_required: int
    test_coverage_impact: float


@dataclass
class CommunityInsight:
    """Insights derived from community feedback"""
    insight_type: str
    description: str
    confidence: float
    supporting_feedback_count: int
    suggested_actions: List[str]
    timeline_recommendation: IntegrationPlan
    business_value: str  # High, Medium, Low


class FeedbackIntegrationEngine:
    """Engine for processing and integrating community feedback"""
    
    def __init__(self, feedback_manager: CommunityFeedbackManager, load_existing: bool = True):
        self.feedback_manager = feedback_manager
        self.integration_tasks: List[IntegrationTask] = []
        self.community_insights: List[CommunityInsight] = []
        
        # Load existing tasks and insights
        if load_existing:
            self._load_integration_data()
    
    def analyze_feedback_patterns(self, days_back: int = 90) -> List[CommunityInsight]:
        """Analyze feedback patterns to generate actionable insights"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_feedback = [
            f for f in self.feedback_manager.feedback_items
            if f.created_at >= cutoff_date
        ]
        
        insights = []
        
        # Pattern 1: Recurring bug reports
        bug_insights = self._analyze_bug_patterns(recent_feedback)
        insights.extend(bug_insights)
        
        # Pattern 2: Feature request clusters
        feature_insights = self._analyze_feature_clusters(recent_feedback)
        insights.extend(feature_insights)
        
        # Pattern 3: Performance pain points
        performance_insights = self._analyze_performance_issues(recent_feedback)
        insights.extend(performance_insights)
        
        # Pattern 4: Documentation gaps
        doc_insights = self._analyze_documentation_gaps(recent_feedback)
        insights.extend(doc_insights)
        
        # Pattern 5: UX friction points
        ux_insights = self._analyze_ux_friction(recent_feedback)
        insights.extend(ux_insights)
        
        self.community_insights.extend(insights)
        self._save_integration_data()
        
        return insights
    
    def _analyze_bug_patterns(self, feedback: List[FeedbackItem]) -> List[CommunityInsight]:
        """Analyze patterns in bug reports"""
        bug_reports = [f for f in feedback if f.feedback_type == FeedbackType.BUG_REPORT]
        
        # Group by error patterns in descriptions
        error_patterns = defaultdict(list)
        for bug in bug_reports:
            # Simple keyword extraction for demo
            keywords = self._extract_keywords(bug.description.lower())
            for keyword in keywords:
                error_patterns[keyword].append(bug)
        
        insights = []
        for pattern, bugs in error_patterns.items():
            if len(bugs) >= 3:  # Pattern appearing in multiple reports
                total_votes = sum(bug.votes for bug in bugs)
                confidence = min(len(bugs) / 10.0, 1.0)  # Max confidence at 10 reports
                
                insight = CommunityInsight(
                    insight_type="recurring_bug",
                    description=f"Recurring issue pattern: '{pattern}' - reported {len(bugs)} times",
                    confidence=confidence,
                    supporting_feedback_count=len(bugs),
                    suggested_actions=[
                        f"Investigate root cause of {pattern} errors",
                        "Improve error handling and user messaging",
                        "Add automated tests for this scenario",
                        "Update documentation with troubleshooting"
                    ],
                    timeline_recommendation=IntegrationPlan.IMMEDIATE if len(bugs) >= 5 else IntegrationPlan.SHORT_TERM,
                    business_value="High" if total_votes > 20 else "Medium"
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_feature_clusters(self, feedback: List[FeedbackItem]) -> List[CommunityInsight]:
        """Analyze feature request patterns"""
        feature_requests = [f for f in feedback if f.feedback_type == FeedbackType.FEATURE_REQUEST]
        
        # Group by feature categories using tags and keywords
        feature_clusters = defaultdict(list)
        for request in feature_requests:
            # Use tags and extract keywords from title/description
            categories = set(request.tags)
            keywords = self._extract_keywords(request.title.lower())
            categories.update(keywords)
            
            for category in categories:
                feature_clusters[category].append(request)
        
        insights = []
        for category, requests in feature_clusters.items():
            if len(requests) >= 2:  # At least 2 requests in same category
                total_votes = sum(req.votes for req in requests)
                avg_votes = total_votes / len(requests)
                
                # High demand features get higher confidence
                confidence = min((len(requests) * avg_votes) / 50.0, 1.0)
                
                insight = CommunityInsight(
                    insight_type="feature_demand",
                    description=f"High demand for {category} features - {len(requests)} requests, {total_votes} total votes",
                    confidence=confidence,
                    supporting_feedback_count=len(requests),
                    suggested_actions=[
                        f"Design {category} feature specification",
                        "Research implementation approaches",
                        "Create user stories and acceptance criteria",
                        f"Prototype {category} functionality"
                    ],
                    timeline_recommendation=self._recommend_feature_timeline(total_votes, len(requests)),
                    business_value="High" if total_votes > 30 else "Medium" if total_votes > 10 else "Low"
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_performance_issues(self, feedback: List[FeedbackItem]) -> List[CommunityInsight]:
        """Analyze performance-related feedback"""
        perf_feedback = [f for f in feedback if f.feedback_type == FeedbackType.PERFORMANCE_ISSUE]
        
        if len(perf_feedback) >= 2:
            # Analyze common performance complaints
            slow_operations = defaultdict(int)
            for perf in perf_feedback:
                keywords = self._extract_keywords(perf.description.lower())
                for keyword in keywords:
                    if keyword in ['scan', 'report', 'load', 'startup', 'response']:
                        slow_operations[keyword] += 1
            
            insights = []
            for operation, count in slow_operations.items():
                if count >= 2:
                    insight = CommunityInsight(
                        insight_type="performance_bottleneck",
                        description=f"Performance issues with {operation} operations - {count} reports",
                        confidence=min(count / 5.0, 1.0),
                        supporting_feedback_count=count,
                        suggested_actions=[
                            f"Profile {operation} performance",
                            f"Optimize {operation} algorithms",
                            "Add performance monitoring",
                            "Implement caching where appropriate"
                        ],
                        timeline_recommendation=IntegrationPlan.SHORT_TERM,
                        business_value="High"
                    )
                    insights.append(insight)
            
            return insights
        
        return []
    
    def _analyze_documentation_gaps(self, feedback: List[FeedbackItem]) -> List[CommunityInsight]:
        """Analyze documentation-related feedback"""
        doc_feedback = [f for f in feedback if f.feedback_type == FeedbackType.DOCUMENTATION]
        
        if len(doc_feedback) >= 2:
            # Group by documentation areas
            doc_areas = defaultdict(int)
            for doc in doc_feedback:
                keywords = self._extract_keywords(doc.description.lower())
                for keyword in keywords:
                    if keyword in ['api', 'cli', 'config', 'install', 'tutorial', 'example']:
                        doc_areas[keyword] += 1
            
            insights = []
            for area, count in doc_areas.items():
                insight = CommunityInsight(
                    insight_type="documentation_gap",
                    description=f"Documentation gaps in {area} - {count} requests",
                    confidence=min(count / 3.0, 1.0),
                    supporting_feedback_count=count,
                    suggested_actions=[
                        f"Review and improve {area} documentation",
                        f"Add more {area} examples",
                        f"Create {area} tutorial",
                        "Update getting started guide"
                    ],
                    timeline_recommendation=IntegrationPlan.SHORT_TERM,
                    business_value="Medium"
                )
                insights.append(insight)
            
            return insights
        
        return []
    
    def _analyze_ux_friction(self, feedback: List[FeedbackItem]) -> List[CommunityInsight]:
        """Analyze user experience friction points"""
        ux_feedback = [f for f in feedback if f.feedback_type == FeedbackType.USER_EXPERIENCE]
        
        if len(ux_feedback) >= 2:
            insight = CommunityInsight(
                insight_type="ux_friction",
                description=f"User experience friction points - {len(ux_feedback)} reports",
                confidence=min(len(ux_feedback) / 5.0, 1.0),
                supporting_feedback_count=len(ux_feedback),
                suggested_actions=[
                    "Conduct UX review of reported areas",
                    "Improve error messages and guidance",
                    "Simplify complex workflows",
                    "Add progress indicators and feedback"
                ],
                timeline_recommendation=IntegrationPlan.MEDIUM_TERM,
                business_value="High"
            )
            return [insight]
        
        return []
    
    def generate_integration_tasks(self, insights: Optional[List[CommunityInsight]] = None) -> List[IntegrationTask]:
        """Generate specific integration tasks from insights and feedback"""
        if insights is None:
            insights = self.community_insights
        
        tasks = []
        
        for insight in insights:
            # Generate tasks based on insight type and suggested actions
            for i, action_desc in enumerate(insight.suggested_actions):
                task = IntegrationTask(
                    task_id=f"{insight.insight_type}_{hashlib.md5(action_desc.encode()).hexdigest()[:8]}",
                    feedback_id=f"insight_{insight.insight_type}",
                    action=self._map_action_description(action_desc),
                    plan=insight.timeline_recommendation,
                    title=f"{action_desc.capitalize()}",
                    description=f"Based on insight: {insight.description}",
                    estimated_effort=self._estimate_effort(action_desc, insight),
                    priority_score=self._calculate_priority_score(insight)
                )
                tasks.append(task)
        
        # Generate tasks from high-priority individual feedback
        priority_feedback = self.feedback_manager.get_prioritized_feedback(20)
        for feedback in priority_feedback:
            if feedback.status == FeedbackStatus.NEW:
                task = self._create_task_from_feedback(feedback)
                tasks.append(task)
        
        self.integration_tasks.extend(tasks)
        self._save_integration_data()
        
        return tasks
    
    def create_development_roadmap(self, quarters: int = 4) -> Dict[str, Any]:
        """Create development roadmap based on community feedback"""
        roadmap = {
            "quarters": {},
            "ongoing_initiatives": [],
            "community_metrics": {},
            "feedback_integration_plan": {}
        }
        
        # Sort tasks by plan and priority
        sorted_tasks = sorted(
            self.integration_tasks,
            key=lambda t: (t.plan.value, -t.priority_score)
        )
        
        # Distribute tasks across quarters
        quarter_names = [f"Q{i+1} {datetime.now().year}" for i in range(quarters)]
        quarter_capacity = [100, 120, 100, 80]  # Hours per quarter
        
        for i, quarter in enumerate(quarter_names):
            roadmap["quarters"][quarter] = {
                "themes": [],
                "tasks": [],
                "capacity_used": 0,
                "community_impact": "Medium"
            }
        
        current_quarter = 0
        used_capacity = 0
        
        for task in sorted_tasks:
            if task.completed:
                continue
                
            # Assign to quarters based on plan
            if task.plan == IntegrationPlan.IMMEDIATE:
                target_quarter = 0
            elif task.plan == IntegrationPlan.SHORT_TERM:
                target_quarter = min(1, quarters - 1)
            elif task.plan == IntegrationPlan.MEDIUM_TERM:
                target_quarter = min(2, quarters - 1)
            else:
                target_quarter = min(3, quarters - 1)
            
            # Check capacity
            quarter_key = quarter_names[target_quarter]
            if (roadmap["quarters"][quarter_key]["capacity_used"] + task.estimated_effort 
                <= quarter_capacity[target_quarter]):
                
                roadmap["quarters"][quarter_key]["tasks"].append({
                    "id": task.task_id,
                    "title": task.title,
                    "effort": task.estimated_effort,
                    "priority": task.priority_score,
                    "action": task.action.value
                })
                roadmap["quarters"][quarter_key]["capacity_used"] += task.estimated_effort
        
        # Add community metrics
        analytics = self.feedback_manager.analyze_feedback_trends(90)
        roadmap["community_metrics"] = {
            "total_feedback": analytics.total_feedback,
            "implementation_rate": analytics.implementation_rate,
            "trending_topics": analytics.trending_topics[:5],
            "priority_feedback_count": len(self.feedback_manager.get_prioritized_feedback())
        }
        
        return roadmap
    
    def assess_release_impact(self, planned_tasks: List[str]) -> ReleaseImpact:
        """Assess the impact of implementing planned tasks"""
        relevant_tasks = [t for t in self.integration_tasks if t.task_id in planned_tasks]
        
        # Calculate impact metrics based on task types and feedback
        user_satisfaction = 0.0
        feature_adoption = 0.0
        tech_debt_reduction = 0.0
        maintenance_overhead = 0.0
        breaking_changes = False
        doc_updates = 0
        test_coverage = 0.0
        
        for task in relevant_tasks:
            # Rough impact scoring based on action type
            if task.action in [IntegrationAction.FIX_BUG, IntegrationAction.IMPROVE_ERROR_MESSAGE]:
                user_satisfaction += 0.15
                tech_debt_reduction += 0.1
            elif task.action in [IntegrationAction.SCHEDULE_DEVELOPMENT, IntegrationAction.ADD_INTEGRATION]:
                feature_adoption += 0.2
                maintenance_overhead += 0.05
            elif task.action in [IntegrationAction.CREATE_DOCUMENTATION, IntegrationAction.UPDATE_TUTORIAL]:
                user_satisfaction += 0.1
                doc_updates += 1
            elif task.action == IntegrationAction.OPTIMIZE_PERFORMANCE:
                user_satisfaction += 0.2
                tech_debt_reduction += 0.15
            elif task.action == IntegrationAction.ENHANCE_UX:
                user_satisfaction += 0.25
                feature_adoption += 0.1
            
            # All tasks should improve test coverage
            test_coverage += 0.05
        
        return ReleaseImpact(
            user_satisfaction_improvement=min(user_satisfaction, 1.0),
            feature_adoption_potential=min(feature_adoption, 1.0),
            technical_debt_reduction=min(tech_debt_reduction, 1.0),
            maintenance_overhead=min(maintenance_overhead, 0.5),
            breaking_changes=breaking_changes,
            documentation_updates_required=doc_updates,
            test_coverage_impact=min(test_coverage, 1.0)
        )
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract relevant keywords from feedback text"""
        # Simple keyword extraction - could be enhanced with NLP
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'cannot', 'cant', 'wont', 'dont', 'doesnt', 'didnt', 'havent', 'hasnt', 'hadnt', 'wouldnt', 'couldnt', 'shouldnt', 'a', 'an', 'when', 'where', 'why', 'how', 'what', 'who', 'which', 'that', 'this', 'these', 'those', 'it', 'its', 'they', 'them', 'their', 'there', 'then', 'than', 'as', 'so', 'if', 'some', 'any', 'all', 'each', 'every', 'no', 'not', 'only', 'very', 'just', 'also', 'too', 'much', 'many', 'more', 'most', 'less', 'least', 'few', 'little', 'big', 'small', 'good', 'bad', 'new', 'old', 'first', 'last', 'same', 'different', 'other', 'another', 'such'}
        
        words = text.lower().split()
        keywords = set()
        
        for word in words:
            # Clean word
            word = word.strip('.,!?;:"()[]{}')
            if len(word) > 2 and word not in common_words:
                keywords.add(word)
        
        return keywords
    
    def _recommend_feature_timeline(self, votes: int, requests: int) -> IntegrationPlan:
        """Recommend timeline for feature implementation"""
        priority_score = votes + (requests * 2)
        
        if priority_score >= 50:
            return IntegrationPlan.SHORT_TERM
        elif priority_score >= 20:
            return IntegrationPlan.MEDIUM_TERM
        elif priority_score >= 10:
            return IntegrationPlan.LONG_TERM
        else:
            return IntegrationPlan.BACKLOG
    
    def _map_action_description(self, action_desc: str) -> IntegrationAction:
        """Map action description to IntegrationAction enum"""
        action_lower = action_desc.lower()
        
        if 'document' in action_lower:
            return IntegrationAction.CREATE_DOCUMENTATION
        elif 'tutorial' in action_lower:
            return IntegrationAction.UPDATE_TUTORIAL
        elif 'error' in action_lower or 'message' in action_lower:
            return IntegrationAction.IMPROVE_ERROR_MESSAGE
        elif 'performance' in action_lower or 'optimize' in action_lower:
            return IntegrationAction.OPTIMIZE_PERFORMANCE
        elif 'bug' in action_lower or 'fix' in action_lower:
            return IntegrationAction.FIX_BUG
        elif 'ux' in action_lower or 'user' in action_lower:
            return IntegrationAction.ENHANCE_UX
        elif 'example' in action_lower:
            return IntegrationAction.CREATE_EXAMPLE
        elif 'integration' in action_lower or 'api' in action_lower:
            return IntegrationAction.ADD_INTEGRATION
        else:
            return IntegrationAction.SCHEDULE_DEVELOPMENT
    
    def _estimate_effort(self, action_desc: str, insight: CommunityInsight) -> int:
        """Estimate effort in hours for an action"""
        base_efforts = {
            IntegrationAction.CREATE_DOCUMENTATION: 8,
            IntegrationAction.UPDATE_TUTORIAL: 12,
            IntegrationAction.IMPROVE_ERROR_MESSAGE: 4,
            IntegrationAction.OPTIMIZE_PERFORMANCE: 24,
            IntegrationAction.FIX_BUG: 16,
            IntegrationAction.ENHANCE_UX: 20,
            IntegrationAction.CREATE_EXAMPLE: 6,
            IntegrationAction.ADD_INTEGRATION: 32,
            IntegrationAction.SCHEDULE_DEVELOPMENT: 40
        }
        
        action = self._map_action_description(action_desc)
        base_effort = base_efforts.get(action, 16)
        
        # Adjust based on insight confidence and supporting feedback
        if insight.confidence > 0.8:
            base_effort = int(base_effort * 1.2)  # High confidence = more thorough implementation
        
        return base_effort
    
    def _calculate_priority_score(self, insight: CommunityInsight) -> float:
        """Calculate priority score for insight"""
        score = insight.confidence * 100
        score += insight.supporting_feedback_count * 10
        
        if insight.business_value == "High":
            score *= 1.5
        elif insight.business_value == "Medium":
            score *= 1.2
        
        return score
    
    def _create_task_from_feedback(self, feedback: FeedbackItem) -> IntegrationTask:
        """Create integration task from individual feedback"""
        action = IntegrationAction.FIX_BUG
        if feedback.feedback_type == FeedbackType.FEATURE_REQUEST:
            action = IntegrationAction.SCHEDULE_DEVELOPMENT
        elif feedback.feedback_type == FeedbackType.DOCUMENTATION:
            action = IntegrationAction.CREATE_DOCUMENTATION
        elif feedback.feedback_type == FeedbackType.PERFORMANCE_ISSUE:
            action = IntegrationAction.OPTIMIZE_PERFORMANCE
        elif feedback.feedback_type == FeedbackType.USER_EXPERIENCE:
            action = IntegrationAction.ENHANCE_UX
        
        # Determine plan based on priority and votes
        if feedback.priority == FeedbackPriority.CRITICAL or feedback.votes >= 20:
            plan = IntegrationPlan.IMMEDIATE
        elif feedback.priority == FeedbackPriority.HIGH or feedback.votes >= 10:
            plan = IntegrationPlan.SHORT_TERM
        elif feedback.priority == FeedbackPriority.MEDIUM or feedback.votes >= 5:
            plan = IntegrationPlan.MEDIUM_TERM
        else:
            plan = IntegrationPlan.LONG_TERM
        
        return IntegrationTask(
            task_id=f"fb_{feedback.feedback_id}",
            feedback_id=feedback.feedback_id,
            action=action,
            plan=plan,
            title=feedback.title,
            description=feedback.description[:200] + "..." if len(feedback.description) > 200 else feedback.description,
            estimated_effort=self._estimate_effort_from_feedback(feedback),
            priority_score=self._calculate_feedback_priority_score(feedback)
        )
    
    def _estimate_effort_from_feedback(self, feedback: FeedbackItem) -> int:
        """Estimate effort for implementing feedback"""
        base_efforts = {
            FeedbackType.BUG_REPORT: 12,
            FeedbackType.FEATURE_REQUEST: 32,
            FeedbackType.PERFORMANCE_ISSUE: 20,
            FeedbackType.DOCUMENTATION: 8,
            FeedbackType.USER_EXPERIENCE: 16,
            FeedbackType.SECURITY_CONCERN: 24,
            FeedbackType.INTEGRATION_REQUEST: 28,
            FeedbackType.GENERAL_FEEDBACK: 8
        }
        
        base = base_efforts.get(feedback.feedback_type, 16)
        
        # Adjust based on priority
        if feedback.priority == FeedbackPriority.CRITICAL:
            base = int(base * 1.5)
        elif feedback.priority == FeedbackPriority.HIGH:
            base = int(base * 1.2)
        
        return base
    
    def _calculate_feedback_priority_score(self, feedback: FeedbackItem) -> float:
        """Calculate priority score for feedback item"""
        priority_scores = {
            FeedbackPriority.CRITICAL: 100,
            FeedbackPriority.HIGH: 80,
            FeedbackPriority.MEDIUM: 60,
            FeedbackPriority.LOW: 40,
            FeedbackPriority.ENHANCEMENT: 20
        }
        
        score = priority_scores.get(feedback.priority, 50)
        score += feedback.votes * 5
        
        # Boost score for recent feedback
        days_old = (datetime.now() - feedback.created_at).days
        if days_old <= 7:
            score *= 1.3
        elif days_old <= 30:
            score *= 1.1
        
        return score
    
    def _load_integration_data(self):
        """Load integration tasks and insights from storage"""
        storage_path = Path("~/.promptstrike/community").expanduser()
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Load tasks
        tasks_file = storage_path / "integration_tasks.json"
        if tasks_file.exists():
            try:
                with open(tasks_file) as f:
                    tasks_data = json.load(f)
                
                for task_data in tasks_data:
                    task_data['action'] = IntegrationAction(task_data['action'])
                    task_data['plan'] = IntegrationPlan(task_data['plan'])
                    task_data['created_at'] = datetime.fromisoformat(task_data['created_at'])
                    task_data['updated_at'] = datetime.fromisoformat(task_data['updated_at'])
                    
                    self.integration_tasks.append(IntegrationTask(**task_data))
            except Exception as e:
                print(f"Error loading integration tasks: {e}")
        
        # Load insights
        insights_file = storage_path / "community_insights.json"
        if insights_file.exists():
            try:
                with open(insights_file) as f:
                    insights_data = json.load(f)
                
                for insight_data in insights_data:
                    insight_data['timeline_recommendation'] = IntegrationPlan(insight_data['timeline_recommendation'])
                    self.community_insights.append(CommunityInsight(**insight_data))
            except Exception as e:
                print(f"Error loading community insights: {e}")
    
    def _save_integration_data(self):
        """Save integration tasks and insights to storage"""
        storage_path = Path("~/.promptstrike/community").expanduser()
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Save tasks
        tasks_file = storage_path / "integration_tasks.json"
        try:
            tasks_data = []
            for task in self.integration_tasks:
                task_data = {
                    'task_id': task.task_id,
                    'feedback_id': task.feedback_id,
                    'action': task.action.value,
                    'plan': task.plan.value,
                    'title': task.title,
                    'description': task.description,
                    'estimated_effort': task.estimated_effort,
                    'priority_score': task.priority_score,
                    'dependencies': task.dependencies,
                    'assignee': task.assignee,
                    'milestone': task.milestone,
                    'created_at': task.created_at.isoformat(),
                    'updated_at': task.updated_at.isoformat(),
                    'completed': task.completed,
                    'implementation_notes': task.implementation_notes,
                    'related_files': task.related_files,
                    'test_requirements': task.test_requirements
                }
                tasks_data.append(task_data)
            
            with open(tasks_file, 'w') as f:
                json.dump(tasks_data, f, indent=2)
        except Exception as e:
            print(f"Error saving integration tasks: {e}")
        
        # Save insights
        insights_file = storage_path / "community_insights.json"
        try:
            insights_data = []
            for insight in self.community_insights:
                insight_data = {
                    'insight_type': insight.insight_type,
                    'description': insight.description,
                    'confidence': insight.confidence,
                    'supporting_feedback_count': insight.supporting_feedback_count,
                    'suggested_actions': insight.suggested_actions,
                    'timeline_recommendation': insight.timeline_recommendation.value,
                    'business_value': insight.business_value
                }
                insights_data.append(insight_data)
            
            with open(insights_file, 'w') as f:
                json.dump(insights_data, f, indent=2)
        except Exception as e:
            print(f"Error saving community insights: {e}")


# Convenience functions for CLI integration
async def generate_community_roadmap(github_repo: Optional[str] = None) -> Dict[str, Any]:
    """Generate development roadmap based on community feedback"""
    manager = CommunityFeedbackManager(github_repo=github_repo)
    await manager.collect_all_feedback(90)  # Collect 3 months of feedback
    
    engine = FeedbackIntegrationEngine(manager)
    insights = engine.analyze_feedback_patterns(90)
    tasks = engine.generate_integration_tasks(insights)
    roadmap = engine.create_development_roadmap(4)
    
    return roadmap


def get_community_insights(github_repo: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get community insights for development planning"""
    manager = CommunityFeedbackManager(github_repo=github_repo)
    engine = FeedbackIntegrationEngine(manager)
    
    insights = engine.analyze_feedback_patterns(90)
    
    return [
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


def assess_release_impact(task_ids: List[str]) -> Dict[str, Any]:
    """Assess the impact of planned release tasks"""
    manager = CommunityFeedbackManager()
    engine = FeedbackIntegrationEngine(manager)
    
    impact = engine.assess_release_impact(task_ids)
    
    return {
        'user_satisfaction_improvement': impact.user_satisfaction_improvement,
        'feature_adoption_potential': impact.feature_adoption_potential,
        'technical_debt_reduction': impact.technical_debt_reduction,
        'maintenance_overhead': impact.maintenance_overhead,
        'breaking_changes': impact.breaking_changes,
        'documentation_updates_required': impact.documentation_updates_required,
        'test_coverage_impact': impact.test_coverage_impact
    }