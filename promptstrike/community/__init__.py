"""
Community Feedback Integration

This module provides comprehensive community feedback collection, analysis,
and integration capabilities for PromptStrike. It enables data-driven
development decisions based on user feedback from multiple sources.

Key Features:
- Multi-source feedback collection (GitHub, telemetry, surveys)
- Automated pattern analysis and insight generation
- Priority-based development roadmap planning
- Integration task generation and tracking
- Community-driven release planning

Usage:
    # Collect feedback from all sources
    from promptstrike.community import collect_community_feedback
    new_count, analytics = await collect_community_feedback(days_back=30)
    
    # Get prioritized feedback for development
    from promptstrike.community import get_feedback_priorities
    priorities = get_feedback_priorities(limit=10)
    
    # Generate community-driven roadmap
    from promptstrike.community import generate_community_roadmap
    roadmap = await generate_community_roadmap()
    
    # Update feedback implementation status
    from promptstrike.community import update_feedback_implementation
    success = update_feedback_implementation("fb_12345", implemented=True)

Classes:
    FeedbackType: Enumeration of feedback types
    FeedbackPriority: Priority levels for feedback
    FeedbackStatus: Processing status of feedback
    FeedbackItem: Individual feedback item data structure
    FeedbackAnalytics: Analytics data structure
    CommunityFeedbackManager: Main feedback management class
    FeedbackIntegrationEngine: Integration and planning engine
    
CLI Integration:
    The community module integrates with PromptStrike CLI via the 'community' command group:
    
    promptstrike community collect --days 30 --repo anthropics/promptstrike
    promptstrike community analyze --days 90 --insights
    promptstrike community priorities --limit 20 --status new
    promptstrike community roadmap --quarters 4 --format tree
    promptstrike community update fb_12345 --status implemented --notes "Fixed in v1.2.0"
    promptstrike community stats --days 30 --export stats.json
"""

from .feedback_collector import (
    FeedbackType,
    FeedbackPriority, 
    FeedbackStatus,
    FeedbackItem,
    FeedbackAnalytics,
    CommunityFeedbackManager,
    GitHubFeedbackCollector,
    TelemetryFeedbackCollector,
    collect_community_feedback,
    get_feedback_priorities,
    update_feedback_implementation
)

from .integration_engine import (
    IntegrationAction,
    IntegrationPlan,
    IntegrationTask,
    ReleaseImpact,
    CommunityInsight,
    FeedbackIntegrationEngine,
    generate_community_roadmap,
    get_community_insights,
    assess_release_impact
)

from .cli_integration import (
    community_app,
    create_community_cli
)

__all__ = [
    # Enums
    'FeedbackType',
    'FeedbackPriority',
    'FeedbackStatus', 
    'IntegrationAction',
    'IntegrationPlan',
    
    # Data structures
    'FeedbackItem',
    'FeedbackAnalytics',
    'IntegrationTask',
    'ReleaseImpact',
    'CommunityInsight',
    
    # Core classes
    'CommunityFeedbackManager',
    'GitHubFeedbackCollector',
    'TelemetryFeedbackCollector',
    'FeedbackIntegrationEngine',
    
    # Convenience functions
    'collect_community_feedback',
    'get_feedback_priorities',
    'update_feedback_implementation',
    'generate_community_roadmap',
    'get_community_insights',
    'assess_release_impact',
    
    # CLI integration
    'community_app',
    'create_community_cli'
]

# Module metadata
__version__ = "1.0.0"
__author__ = "PromptStrike Community Team"
__description__ = "Community feedback integration for PromptStrike"

def get_module_info() -> dict:
    """Get module information and capabilities"""
    return {
        "name": "promptstrike.community",
        "version": __version__,
        "description": __description__,
        "features": [
            "GitHub issues collection",
            "Telemetry-based feedback analysis", 
            "Pattern recognition and insights",
            "Priority-based development planning",
            "Community-driven roadmaps",
            "Implementation tracking",
            "CLI integration"
        ],
        "dependencies": {
            "required": ["typer", "rich"],
            "optional": ["aiohttp", "PyGithub"]
        },
        "cli_commands": [
            "community collect",
            "community analyze", 
            "community priorities",
            "community roadmap",
            "community update",
            "community stats"
        ]
    }