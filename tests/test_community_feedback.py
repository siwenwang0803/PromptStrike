"""
Test suite for community feedback integration system
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import shutil

from promptstrike.community.feedback_collector import (
    FeedbackType,
    FeedbackPriority,
    FeedbackStatus,
    FeedbackItem,
    CommunityFeedbackManager,
    GitHubFeedbackCollector,
    TelemetryFeedbackCollector
)
from promptstrike.community.integration_engine import (
    FeedbackIntegrationEngine,
    IntegrationAction,
    IntegrationPlan,
    IntegrationTask,
    CommunityInsight
)


@pytest.fixture
def temp_storage():
    """Create temporary storage directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_feedback_items():
    """Create sample feedback items for testing"""
    return [
        FeedbackItem(
            feedback_id="gh_123",
            feedback_type=FeedbackType.BUG_REPORT,
            title="CLI crashes with invalid config",
            description="The CLI crashes when config file has invalid YAML syntax",
            priority=FeedbackPriority.HIGH,
            status=FeedbackStatus.NEW,
            source="github",
            source_id="123",
            user_id="user123",
            votes=5,
            tags=["cli", "config", "bug"],
            created_at=datetime.now() - timedelta(days=2)
        ),
        FeedbackItem(
            feedback_id="gh_124",
            feedback_type=FeedbackType.FEATURE_REQUEST,
            title="Add support for custom attack patterns",
            description="Users want to create their own attack patterns for specific use cases",
            priority=FeedbackPriority.MEDIUM,
            status=FeedbackStatus.TRIAGED,
            source="github",
            source_id="124",
            user_id="user456",
            votes=12,
            tags=["feature", "attack-patterns", "customization"],
            created_at=datetime.now() - timedelta(days=5)
        ),
        FeedbackItem(
            feedback_id="tel_perf_001",
            feedback_type=FeedbackType.PERFORMANCE_ISSUE,
            title="Slow scan performance",
            description="Scan operations are taking longer than expected",
            priority=FeedbackPriority.MEDIUM,
            status=FeedbackStatus.NEW,
            source="telemetry",
            votes=0,
            tags=["performance", "scan"],
            created_at=datetime.now() - timedelta(days=1),
            metadata={
                "operation": "scan",
                "average_duration_ms": 8500,
                "slow_instances": 15
            }
        )
    ]


@pytest.fixture
def feedback_manager(temp_storage, sample_feedback_items):
    """Create feedback manager with sample data"""
    manager = CommunityFeedbackManager(storage_path=temp_storage)
    manager.feedback_items = sample_feedback_items.copy()
    return manager


class TestFeedbackItem:
    """Test FeedbackItem data structure"""
    
    def test_feedback_item_creation(self):
        """Test creating feedback item"""
        item = FeedbackItem(
            feedback_id="test_001",
            feedback_type=FeedbackType.BUG_REPORT,
            title="Test bug",
            description="Test description",
            priority=FeedbackPriority.HIGH,
            status=FeedbackStatus.NEW,
            source="test"
        )
        
        assert item.feedback_id == "test_001"
        assert item.feedback_type == FeedbackType.BUG_REPORT
        assert item.priority == FeedbackPriority.HIGH
        assert item.status == FeedbackStatus.NEW
        assert item.votes == 0
        assert len(item.tags) == 0
        assert isinstance(item.created_at, datetime)
    
    def test_feedback_item_with_metadata(self):
        """Test feedback item with metadata"""
        metadata = {"test_key": "test_value", "count": 42}
        item = FeedbackItem(
            feedback_id="test_002",
            feedback_type=FeedbackType.FEATURE_REQUEST,
            title="Test feature",
            description="Test description",
            priority=FeedbackPriority.LOW,
            status=FeedbackStatus.NEW,
            source="test",
            metadata=metadata
        )
        
        assert item.metadata == metadata
        assert item.metadata["test_key"] == "test_value"
        assert item.metadata["count"] == 42


class TestGitHubFeedbackCollector:
    """Test GitHub feedback collection"""
    
    def test_collector_initialization(self):
        """Test GitHub collector initialization"""
        collector = GitHubFeedbackCollector("test/repo")
        assert collector.repo_name == "test/repo"
        assert collector.github_client is None  # No token provided
    
    def test_classify_issue_type_bug(self):
        """Test issue type classification for bugs"""
        collector = GitHubFeedbackCollector("test/repo")
        
        mock_label = Mock()
        mock_label.name = "bug"
        mock_issue = Mock()
        mock_issue.labels = [mock_label]
        mock_issue.title = "CLI crashes"
        
        issue_type = collector._classify_issue_type(mock_issue)
        assert issue_type == FeedbackType.BUG_REPORT
    
    def test_classify_issue_type_feature(self):
        """Test issue type classification for features"""
        collector = GitHubFeedbackCollector("test/repo")
        
        mock_label = Mock()
        mock_label.name = "enhancement"
        mock_issue = Mock()
        mock_issue.labels = [mock_label]
        mock_issue.title = "Add new feature"
        
        issue_type = collector._classify_issue_type(mock_issue)
        assert issue_type == FeedbackType.FEATURE_REQUEST
    
    def test_determine_priority_critical(self):
        """Test priority determination for critical issues"""
        collector = GitHubFeedbackCollector("test/repo")
        
        mock_label = Mock()
        mock_label.name = "critical"
        mock_issue = Mock()
        mock_issue.labels = [mock_label]
        
        priority = collector._determine_priority(mock_issue)
        assert priority == FeedbackPriority.CRITICAL
    
    def test_map_issue_status_closed(self):
        """Test status mapping for closed issues"""
        collector = GitHubFeedbackCollector("test/repo")
        
        mock_issue = Mock()
        mock_issue.state = "closed"
        mock_issue.labels = []
        
        status = collector._map_issue_status(mock_issue)
        assert status == FeedbackStatus.IMPLEMENTED


class TestTelemetryFeedbackCollector:
    """Test telemetry feedback collection"""
    
    def test_collector_initialization(self, temp_storage):
        """Test telemetry collector initialization"""
        collector = TelemetryFeedbackCollector(temp_storage)
        assert collector.data_path == Path(temp_storage).expanduser()
        assert collector.data_path.exists()
    
    def test_analyze_error_patterns(self, temp_storage):
        """Test error pattern analysis"""
        collector = TelemetryFeedbackCollector(temp_storage)
        
        # Create mock error data
        error_data = [
            {
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "error_type": "config_error",
                "message": "Invalid YAML syntax"
            },
            {
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "error_type": "config_error", 
                "message": "Missing required field"
            },
            {
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
                "error_type": "config_error",
                "message": "File not found"
            },
            {
                "timestamp": (datetime.now() - timedelta(days=4)).isoformat(),
                "error_type": "config_error",
                "message": "Permission denied"
            },
            {
                "timestamp": (datetime.now() - timedelta(days=5)).isoformat(),
                "error_type": "config_error",
                "message": "Invalid format"
            }
        ]
        
        # Write error data to file
        error_file = collector.data_path / "errors.json"
        with open(error_file, 'w') as f:
            json.dump(error_data, f)
        
        # Analyze patterns
        feedback = collector._analyze_error_patterns(30)
        
        assert len(feedback) == 1
        assert feedback[0].feedback_type == FeedbackType.BUG_REPORT
        assert "config_error" in feedback[0].title
        assert feedback[0].metadata["error_count"] == 5
    
    def test_analyze_performance_patterns(self, temp_storage):
        """Test performance pattern analysis"""
        collector = TelemetryFeedbackCollector(temp_storage)
        
        # Create mock performance data
        perf_data = [
            {
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "operation": "scan",
                "duration_ms": 6000
            },
            {
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "operation": "scan",
                "duration_ms": 7500
            },
            {
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
                "operation": "scan", 
                "duration_ms": 8200
            }
        ]
        
        # Write performance data to file
        perf_file = collector.data_path / "performance.json"
        with open(perf_file, 'w') as f:
            json.dump(perf_data, f)
        
        # Analyze patterns
        feedback = collector._analyze_performance_patterns(30)
        
        assert len(feedback) == 1
        assert feedback[0].feedback_type == FeedbackType.PERFORMANCE_ISSUE
        assert "scan" in feedback[0].title
        assert feedback[0].metadata["slow_instances"] == 3


class TestCommunityFeedbackManager:
    """Test community feedback manager"""
    
    def test_manager_initialization(self, temp_storage):
        """Test manager initialization"""
        manager = CommunityFeedbackManager(storage_path=temp_storage)
        assert manager.storage_path == Path(temp_storage).expanduser()
        assert len(manager.feedback_items) == 0
    
    def test_analyze_feedback_trends(self, feedback_manager):
        """Test feedback trend analysis"""
        analytics = feedback_manager.analyze_feedback_trends(30)
        
        assert analytics.total_feedback == 3
        assert analytics.feedback_by_type[FeedbackType.BUG_REPORT.value] == 1
        assert analytics.feedback_by_type[FeedbackType.FEATURE_REQUEST.value] == 1
        assert analytics.feedback_by_type[FeedbackType.PERFORMANCE_ISSUE.value] == 1
        
        assert analytics.feedback_by_priority[FeedbackPriority.HIGH.value] == 1
        assert analytics.feedback_by_priority[FeedbackPriority.MEDIUM.value] == 2
        
        assert analytics.feedback_by_status[FeedbackStatus.NEW.value] == 2
        assert analytics.feedback_by_status[FeedbackStatus.TRIAGED.value] == 1
    
    def test_get_prioritized_feedback(self, feedback_manager):
        """Test prioritized feedback retrieval"""
        priorities = feedback_manager.get_prioritized_feedback(10)
        
        assert len(priorities) == 3
        # Should be sorted by priority score (high priority bug should be first)
        assert priorities[0].feedback_type == FeedbackType.BUG_REPORT
        assert priorities[0].priority == FeedbackPriority.HIGH
    
    def test_update_feedback_status(self, feedback_manager):
        """Test feedback status updates"""
        success = feedback_manager.update_feedback_status(
            "gh_123", 
            FeedbackStatus.IMPLEMENTED,
            "Fixed in v1.2.0"
        )
        
        assert success
        
        # Find the updated item
        updated_item = None
        for item in feedback_manager.feedback_items:
            if item.feedback_id == "gh_123":
                updated_item = item
                break
        
        assert updated_item is not None
        assert updated_item.status == FeedbackStatus.IMPLEMENTED
        assert updated_item.implementation_notes == "Fixed in v1.2.0"
    
    def test_merge_feedback_new_items(self, feedback_manager):
        """Test merging new feedback items"""
        new_feedback = [
            FeedbackItem(
                feedback_id="new_001",
                feedback_type=FeedbackType.DOCUMENTATION,
                title="Missing API docs",
                description="API documentation is incomplete",
                priority=FeedbackPriority.LOW,
                status=FeedbackStatus.NEW,
                source="survey"
            )
        ]
        
        original_count = len(feedback_manager.feedback_items)
        new_count = feedback_manager._merge_feedback(new_feedback)
        
        assert new_count == 1
        assert len(feedback_manager.feedback_items) == original_count + 1
    
    def test_merge_feedback_duplicate_items(self, feedback_manager):
        """Test merging duplicate feedback items"""
        # Try to add an item with existing ID
        duplicate_feedback = [
            FeedbackItem(
                feedback_id="gh_123",  # Same as existing item
                feedback_type=FeedbackType.BUG_REPORT,
                title="Updated title",
                description="Updated description",
                priority=FeedbackPriority.CRITICAL,
                status=FeedbackStatus.IN_PROGRESS,
                source="github",
                updated_at=datetime.now()  # More recent
            )
        ]
        
        original_count = len(feedback_manager.feedback_items)
        new_count = feedback_manager._merge_feedback(duplicate_feedback)
        
        assert new_count == 0  # No new items added
        assert len(feedback_manager.feedback_items) == original_count
        
        # Check that existing item was updated
        updated_item = None
        for item in feedback_manager.feedback_items:
            if item.feedback_id == "gh_123":
                updated_item = item
                break
        
        assert updated_item.title == "Updated title"


class TestFeedbackIntegrationEngine:
    """Test feedback integration engine"""
    
    def test_engine_initialization(self, feedback_manager):
        """Test integration engine initialization"""
        engine = FeedbackIntegrationEngine(feedback_manager, load_existing=False)
        assert engine.feedback_manager == feedback_manager
        assert len(engine.integration_tasks) == 0
        assert len(engine.community_insights) == 0
    
    def test_analyze_bug_patterns(self, feedback_manager):
        """Test bug pattern analysis"""
        engine = FeedbackIntegrationEngine(feedback_manager, load_existing=False)
        insights = engine._analyze_bug_patterns(feedback_manager.feedback_items)
        
        # Our sample data has 1 bug report, need to add more for pattern detection
        bug_feedback = feedback_manager.feedback_items[0]  # The first one is a bug report
        
        # Add more bug reports with similar keywords to trigger pattern detection
        additional_bugs = []
        for i in range(2, 5):
            bug_copy = FeedbackItem(
                feedback_id=f"gh_{120+i}",
                feedback_type=FeedbackType.BUG_REPORT,
                title=f"CLI crashes with config issue {i}",
                description="The CLI crashes when config file has invalid syntax",
                priority=FeedbackPriority.HIGH,
                status=FeedbackStatus.NEW,
                source="github",
                source_id=str(120+i),
                user_id=f"user{120+i}",
                votes=3,
                tags=["cli", "config", "bug"],
                created_at=datetime.now() - timedelta(days=i)
            )
            additional_bugs.append(bug_copy)
        
        all_bugs = [bug_feedback] + additional_bugs
        insights = engine._analyze_bug_patterns(all_bugs)
        
        assert len(insights) > 0
        bug_insight = insights[0]
        assert bug_insight.insight_type == "recurring_bug"
        assert bug_insight.confidence > 0
        assert len(bug_insight.suggested_actions) > 0
    
    def test_analyze_feature_clusters(self, feedback_manager):
        """Test feature request clustering"""
        engine = FeedbackIntegrationEngine(feedback_manager, load_existing=False)
        
        # Get feature requests from sample data
        feature_requests = [f for f in feedback_manager.feedback_items if f.feedback_type == FeedbackType.FEATURE_REQUEST]
        
        # Add another feature request to create a cluster
        additional_feature = FeedbackItem(
            feedback_id="gh_200",
            feedback_type=FeedbackType.FEATURE_REQUEST,
            title="Custom attack patterns for specific domains",
            description="Users want to create domain-specific attack patterns",
            priority=FeedbackPriority.MEDIUM,
            status=FeedbackStatus.NEW,
            source="github",
            source_id="200",
            user_id="user200",
            votes=8,
            tags=["feature", "attack-patterns", "customization"],
            created_at=datetime.now() - timedelta(days=3)
        )
        
        all_features = feature_requests + [additional_feature]
        insights = engine._analyze_feature_clusters(all_features)
        
        # Should find at least one insight for feature requests
        assert len(insights) > 0
        feature_insight = insights[0]
        assert feature_insight.insight_type == "feature_demand"
        assert feature_insight.confidence > 0
    
    def test_generate_integration_tasks(self, feedback_manager):
        """Test integration task generation"""
        engine = FeedbackIntegrationEngine(feedback_manager, load_existing=False)
        
        # Create some insights manually for testing
        insights = [
            CommunityInsight(
                insight_type="recurring_bug",
                description="Test bug pattern",
                confidence=0.8,
                supporting_feedback_count=3,
                suggested_actions=["Fix bug", "Add tests"],
                timeline_recommendation=IntegrationPlan.SHORT_TERM,
                business_value="High"
            )
        ]
        
        # Generate tasks
        tasks = engine.generate_integration_tasks(insights)
        
        assert len(tasks) > 0
        
        # Check task structure
        task = tasks[0]
        assert isinstance(task.task_id, str)
        assert isinstance(task.action, IntegrationAction)
        assert isinstance(task.plan, IntegrationPlan)
        assert task.estimated_effort > 0
        assert task.priority_score > 0
    
    def test_create_development_roadmap(self, feedback_manager):
        """Test development roadmap creation"""
        engine = FeedbackIntegrationEngine(feedback_manager, load_existing=False)
        
        # Add a test task to the engine
        test_task = IntegrationTask(
            task_id="test_001",
            feedback_id="gh_123",
            action=IntegrationAction.FIX_BUG,
            plan=IntegrationPlan.SHORT_TERM,
            title="Test task",
            description="Test description",
            estimated_effort=8,
            priority_score=75.0
        )
        engine.integration_tasks.append(test_task)
        
        # Create roadmap
        roadmap = engine.create_development_roadmap(4)
        
        assert "quarters" in roadmap
        assert "community_metrics" in roadmap
        assert len(roadmap["quarters"]) == 4
        
        # Check community metrics
        metrics = roadmap["community_metrics"]
        assert "total_feedback" in metrics
        assert "implementation_rate" in metrics
        assert "trending_topics" in metrics
    
    def test_assess_release_impact(self, feedback_manager):
        """Test release impact assessment"""
        engine = FeedbackIntegrationEngine(feedback_manager, load_existing=False)
        
        # Create a mock task
        task = IntegrationTask(
            task_id="test_task_001",
            feedback_id="gh_123",
            action=IntegrationAction.FIX_BUG,
            plan=IntegrationPlan.SHORT_TERM,
            title="Fix critical bug",
            description="Fix the config parsing bug",
            estimated_effort=16,
            priority_score=85.0
        )
        engine.integration_tasks.append(task)
        
        # Assess impact
        impact = engine.assess_release_impact(["test_task_001"])
        
        assert impact.user_satisfaction_improvement >= 0
        assert impact.technical_debt_reduction >= 0
        assert isinstance(impact.breaking_changes, bool)
        assert impact.documentation_updates_required >= 0


class TestIntegrationTaskCreation:
    """Test integration task creation and management"""
    
    def test_create_task_from_bug_feedback(self, feedback_manager):
        """Test creating task from bug report feedback"""
        engine = FeedbackIntegrationEngine(feedback_manager, load_existing=False)
        
        # Get the bug report from sample data
        bug_feedback = None
        for item in feedback_manager.feedback_items:
            if item.feedback_type == FeedbackType.BUG_REPORT:
                bug_feedback = item
                break
        
        assert bug_feedback is not None
        
        task = engine._create_task_from_feedback(bug_feedback)
        
        assert task.action == IntegrationAction.FIX_BUG
        assert task.feedback_id == bug_feedback.feedback_id
        assert task.title == bug_feedback.title
        assert task.estimated_effort > 0
        assert task.priority_score > 0
    
    def test_create_task_from_feature_feedback(self, feedback_manager):
        """Test creating task from feature request feedback"""
        engine = FeedbackIntegrationEngine(feedback_manager, load_existing=False)
        
        # Get the feature request from sample data
        feature_feedback = None
        for item in feedback_manager.feedback_items:
            if item.feedback_type == FeedbackType.FEATURE_REQUEST:
                feature_feedback = item
                break
        
        assert feature_feedback is not None
        
        task = engine._create_task_from_feedback(feature_feedback)
        
        assert task.action == IntegrationAction.SCHEDULE_DEVELOPMENT
        assert task.feedback_id == feature_feedback.feedback_id
        assert task.title == feature_feedback.title
    
    def test_task_priority_calculation(self, feedback_manager):
        """Test task priority score calculation"""
        engine = FeedbackIntegrationEngine(feedback_manager, load_existing=False)
        
        # Create high priority feedback
        high_priority_feedback = FeedbackItem(
            feedback_id="test_high",
            feedback_type=FeedbackType.BUG_REPORT,
            title="Critical security issue",
            description="Security vulnerability found",
            priority=FeedbackPriority.CRITICAL,
            status=FeedbackStatus.NEW,
            source="github",
            votes=25,
            created_at=datetime.now() - timedelta(days=1)  # Recent
        )
        
        # Create low priority feedback  
        low_priority_feedback = FeedbackItem(
            feedback_id="test_low",
            feedback_type=FeedbackType.GENERAL_FEEDBACK,  # Use existing enum value
            title="Minor UI improvement",
            description="Small UI enhancement",
            priority=FeedbackPriority.LOW,
            status=FeedbackStatus.NEW,
            source="survey",
            votes=2,
            created_at=datetime.now() - timedelta(days=60)  # Old
        )
        
        high_score = engine._calculate_feedback_priority_score(high_priority_feedback)
        low_score = engine._calculate_feedback_priority_score(low_priority_feedback)
        
        assert high_score > low_score
        assert high_score > 100  # Should get high score due to critical priority and votes


class TestCommunityInsightGeneration:
    """Test community insight generation"""
    
    def test_insight_creation(self):
        """Test creating community insight"""
        insight = CommunityInsight(
            insight_type="test_insight",
            description="Test insight description",
            confidence=0.85,
            supporting_feedback_count=10,
            suggested_actions=["Action 1", "Action 2"],
            timeline_recommendation=IntegrationPlan.SHORT_TERM,
            business_value="High"
        )
        
        assert insight.insight_type == "test_insight"
        assert insight.confidence == 0.85
        assert insight.supporting_feedback_count == 10
        assert len(insight.suggested_actions) == 2
        assert insight.timeline_recommendation == IntegrationPlan.SHORT_TERM
        assert insight.business_value == "High"
    
    def test_keyword_extraction(self, feedback_manager):
        """Test keyword extraction from feedback text"""
        engine = FeedbackIntegrationEngine(feedback_manager, load_existing=False)
        
        text = "The CLI crashes when config file has invalid YAML syntax and missing fields"
        keywords = engine._extract_keywords(text)
        
        assert "cli" in keywords
        assert "crashes" in keywords
        assert "config" in keywords
        assert "file" in keywords
        assert "yaml" in keywords
        assert "syntax" in keywords
        
        # Common words should be filtered out
        assert "the" not in keywords
        assert "when" not in keywords
        assert "has" not in keywords


@pytest.mark.asyncio
class TestAsyncFeedbackCollection:
    """Test async feedback collection operations"""
    
    async def test_collect_all_feedback(self, temp_storage):
        """Test collecting feedback from all sources"""
        manager = CommunityFeedbackManager(storage_path=temp_storage)
        
        # Mock the GitHub collector to avoid API calls
        with patch.object(manager, 'github_collector') as mock_github:
            mock_github.collect_issues = AsyncMock(return_value=[])
            
            new_count = await manager.collect_all_feedback(30)
            
            # Should return 0 since we mocked empty results
            assert new_count >= 0


class TestCommunityConvenienceFunctions:
    """Test convenience functions for CLI integration"""
    
    @pytest.mark.asyncio
    async def test_collect_community_feedback_function(self, temp_storage):
        """Test collect_community_feedback convenience function"""
        from promptstrike.community.feedback_collector import collect_community_feedback
        
        with patch('promptstrike.community.feedback_collector.CommunityFeedbackManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager.collect_all_feedback = AsyncMock(return_value=5)
            mock_manager.analyze_feedback_trends = Mock(return_value=Mock(
                total_feedback=10,
                implementation_rate=75.0,
                trending_topics=["cli", "config"]
            ))
            mock_manager_class.return_value = mock_manager
            
            new_count, analytics = await collect_community_feedback(30)
            
            assert new_count == 5
            assert analytics.total_feedback == 10
            assert analytics.implementation_rate == 75.0
    
    def test_get_feedback_priorities_function(self):
        """Test get_feedback_priorities convenience function"""
        from promptstrike.community.feedback_collector import get_feedback_priorities
        
        with patch('promptstrike.community.feedback_collector.CommunityFeedbackManager') as mock_manager_class:
            mock_feedback = Mock()
            mock_feedback.feedback_id = "test_001"
            mock_feedback.feedback_type = Mock(value="bug_report")
            mock_feedback.title = "Test bug"
            mock_feedback.priority = Mock(value="high")
            mock_feedback.status = Mock(value="new")
            mock_feedback.votes = 5
            mock_feedback.created_at = datetime.now()
            mock_feedback.source = "github"
            
            mock_manager = Mock()
            mock_manager.get_prioritized_feedback = Mock(return_value=[mock_feedback])
            mock_manager_class.return_value = mock_manager
            
            priorities = get_feedback_priorities(10)
            
            assert len(priorities) == 1
            assert priorities[0]['id'] == "test_001"
            assert priorities[0]['type'] == "bug_report"
            assert priorities[0]['title'] == "Test bug"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])