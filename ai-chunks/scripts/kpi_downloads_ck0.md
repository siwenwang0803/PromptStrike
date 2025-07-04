<!-- source: scripts/kpi_downloads.py idx:0 lines:264 -->

```py
#!/usr/bin/env python3
"""
KPI Downloads Tracking Script
Monitors PyPI, Docker Hub, and GitHub downloads for PromptStrike CLI
Sends data to Notion dashboard for Sprint S-1 gate review
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KPITracker:
    def __init__(self):
        self.github_repo = "siwenwang0803/PromptStrike"
        self.pypi_package = "promptstrike"
        self.docker_image = "promptstrike/cli"
        
        # Environment variables for API keys
        self.notion_token = os.getenv("NOTION_TOKEN")
        self.notion_database_id = os.getenv("NOTION_DATABASE_ID")
        self.github_token = os.getenv("GITHUB_TOKEN")
        
        if not self.notion_token:
            logger.warning("NOTION_TOKEN not set - will log to console only")
        if not self.github_token:
            logger.warning("GITHUB_TOKEN not set - GitHub API rate limits may apply")
    
    def get_pypi_downloads(self) -> Dict[str, Any]:
        """Fetch PyPI download statistics"""
        try:
            # PyPI download stats API
            url = f"https://pypistats.org/api/packages/{self.pypi_package}/recent"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return {
                "total_downloads": data.get("data", {}).get("last_month", 0),
                "daily_downloads": data.get("data", {}).get("last_day", 0),
                "source": "PyPI",
                "package": self.pypi_package
            }
        except Exception as e:
            logger.error(f"Error fetching PyPI stats: {e}")
            return {"total_downloads": 0, "daily_downloads": 0, "source": "PyPI", "error": str(e)}
    
    def get_docker_pulls(self) -> Dict[str, Any]:
        """Fetch Docker Hub pull statistics"""
        try:
            # Docker Hub API
            url = f"https://hub.docker.com/v2/repositories/{self.docker_image}/"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return {
                "total_pulls": data.get("pull_count", 0),
                "stars": data.get("star_count", 0),
                "source": "Docker Hub",
                "image": self.docker_image
            }
        except Exception as e:
            logger.error(f"Error fetching Docker Hub stats: {e}")
            return {"total_pulls": 0, "stars": 0, "source": "Docker Hub", "error": str(e)}
    
    def get_github_stats(self) -> Dict[str, Any]:
        """Fetch GitHub repository statistics"""
        try:
            headers = {}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
            
            # Repository stats
            url = f"https://api.github.com/repos/{self.github_repo}"
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            repo_data = response.json()
            
            # Release download stats
            releases_url = f"https://api.github.com/repos/{self.github_repo}/releases"
            releases_response = requests.get(releases_url, headers=headers, timeout=30)
            releases_response.raise_for_status()
            
            releases_data = releases_response.json()
            total_release_downloads = 0
            
            for release in releases_data:
                for asset in release.get("assets", []):
                    total_release_downloads += asset.get("download_count", 0)
            
            # Issues stats
            issues_url = f"https://api.github.com/repos/{self.github_repo}/issues"
            issues_response = requests.get(issues_url, headers=headers, timeout=30)
            issues_response.raise_for_status()
            
            issues_data = issues_response.json()
            open_issues = len([issue for issue in issues_data if issue.get("state") == "open"])
            
            return {
                "stars": repo_data.get("stargazers_count", 0),
                "forks": repo_data.get("forks_count", 0),
                "watchers": repo_data.get("subscribers_count", 0),
                "open_issues": open_issues,
                "total_issues": repo_data.get("open_issues_count", 0),
                "release_downloads": total_release_downloads,
                "source": "GitHub",
                "repo": self.github_repo
            }
        except Exception as e:
            logger.error(f"Error fetching GitHub stats: {e}")
            return {"stars": 0, "forks": 0, "watchers": 0, "open_issues": 0, "release_downloads": 0, "source": "GitHub", "error": str(e)}
    
    def send_to_notion(self, kpi_data: Dict[str, Any]) -> bool:
        """Send KPI data to Notion dashboard"""
        if not self.notion_token or not self.notion_database_id:
            logger.warning("Notion integration not configured - skipping")
            return False
        
        try:
            url = "https://api.notion.com/v1/pages"
            headers = {
                "Authorization": f"Bearer {self.notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            # Create Notion page with KPI data
            notion_data = {
                "parent": {"database_id": self.notion_database_id},
                "properties": {
                    "Date": {
                        "date": {"start": datetime.now().isoformat()}
                    },
                    "Sprint": {
                        "select": {"name": "S-1"}
                    },
                    "PyPI Downloads": {
                        "number": kpi_data["pypi"]["total_downloads"]
                    },
                    "Docker Pulls": {
                        "number": kpi_data["docker"]["total_pulls"]
                    },
                    "GitHub Stars": {
                        "number": kpi_data["github"]["stars"]
                    },
                    "GitHub Issues": {
                        "number": kpi_data["github"]["open_issues"]
                    },
                    "Release Downloads": {
                        "number": kpi_data["github"]["release_downloads"]
                    },
                    "Status": {
                        "select": {"name": "Active"}
                    }
                }
            }
            
            response = requests.post(url, headers=headers, json=notion_data, timeout=30)
            response.raise_for_status()
            
            logger.info("Successfully sent KPI data to Notion")
            return True
            
        except Exception as e:
            logger.error(f"Error sending to Notion: {e}")
            return False
    
    def generate_report(self, kpi_data: Dict[str, Any]) -> str:
        """Generate a formatted KPI report"""
        report = f"""
📊 PromptStrike KPI Report - Sprint S-1
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🐍 PyPI Package ({self.pypi_package})
  Total Downloads: {kpi_data['pypi']['total_downloads']:,}
  Daily Downloads: {kpi_data['pypi']['daily_downloads']:,}

🐳 Docker Hub ({self.docker_image})
  Total Pulls: {kpi_data['docker']['total_pulls']:,}
  Stars: {kpi_data['docker']['stars']:,}

📂 GitHub Repository ({self.github_repo})
  Stars: {kpi_data['github']['stars']:,}
  Forks: {kpi_data['github']['forks']:,}
  Watchers: {kpi_data['github']['watchers']:,}
  Open Issues: {kpi_data['github']['open_issues']:,}
  Release Downloads: {kpi_data['github']['release_downloads']:,}

🎯 Sprint S-1 Gate Review Metrics
  Target: 500 downloads → Current: {kpi_data['pypi']['total_downloads'] + kpi_data['docker']['total_pulls'] + kpi_data['github']['release_downloads']:,}
  Target: 5 GitHub issues → Current: {kpi_data['github']['open_issues']:,}
  Status: {"✅ ON TRACK" if kpi_data['pypi']['total_downloads'] + kpi_data['docker']['total_pulls'] >= 500 else "⚠️ NEEDS ATTENTION"}

---
Reference: cid-roadmap-v1 Sprint S-1
        """
        return report.strip()
    
    def run(self) -> Dict[str, Any]:
        """Main execution function"""
        logger.info("Starting KPI tracking for PromptStrike CLI")
        
        # Collect all KPI data
        kpi_data = {
            "timestamp": datetime.now().isoformat(),
            "sprint": "S-1",
            "pypi": self.get_pypi_downloads(),
            "docker": self.get_docker_pulls(),
            "github": self.get_github_stats()
        }
        
        # Generate report
        report = self.generate_report(kpi_data)
        logger.info(f"KPI Report:\\n{report}")
        
        # Send to Notion if configured
        if self.send_to_notion(kpi_data):
            logger.info("KPI data sent to Notion dashboard")
        
        # Save to local file
        output_file = f"kpi_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(kpi_data, f, indent=2)
        
        logger.info(f"KPI data saved to {output_file}")
        
        return kpi_data

def main():
    """CLI entry point"""
    tracker = KPITracker()
    kpi_data = tracker.run()
    
    # Calculate combined downloads for gate review
    total_downloads = (
        kpi_data["pypi"]["total_downloads"] + 
        kpi_data["docker"]["total_pulls"] + 
        kpi_data["github"]["release_downloads"]
    )
    
    # Exit with appropriate code for automation
    if total_downloads >= 500 and kpi_data["github"]["open_issues"] >= 5:
        logger.info("🎉 Sprint S-1 gate review metrics achieved!")
        exit(0)
    elif total_downloads >= 500:
        logger.warning("⚠️ Download target met, but need more GitHub issues")
        exit(1)
    elif kpi_data["github"]["open_issues"] >= 5:
        logger.warning("⚠️ GitHub issues target met, but need more downloads")
        exit(1)
    else:
        logger.warning("⚠️ Both targets need attention")
        exit(2)

if __name__ == "__main__":
    main()
```