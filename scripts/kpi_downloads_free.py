#!/usr/bin/env python3
"""
Free KPI Downloads Tracking Script
Monitors PyPI, Docker Hub, and GitHub downloads
Saves data to downloads.json in the repo (no external dependencies)
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FreeKPITracker:
    def __init__(self):
        self.github_repo = "siwenwang0803/PromptStrike"
        self.pypi_package = "promptstrike"
        self.docker_image = "promptstrike/cli"
        self.github_token = os.getenv("GITHUB_TOKEN")
        
        if not self.github_token:
            logger.warning("GITHUB_TOKEN not set - GitHub API rate limits may apply")
    
    def get_pypi_downloads(self) -> Dict[str, Any]:
        """Fetch PyPI download statistics"""
        try:
            # PyPI stats API (free, no auth required)
            url = f"https://pypistats.org/api/packages/{self.pypi_package}/recent"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 404:
                logger.info("Package not found on PyPI yet")
                return {
                    "total_downloads": 0,
                    "daily_downloads": 0,
                    "weekly_downloads": 0,
                    "monthly_downloads": 0,
                    "source": "PyPI",
                    "status": "not_found"
                }
            
            response.raise_for_status()
            data = response.json()
            
            return {
                "total_downloads": data.get("data", {}).get("last_month", 0),
                "daily_downloads": data.get("data", {}).get("last_day", 0),
                "weekly_downloads": data.get("data", {}).get("last_week", 0),
                "monthly_downloads": data.get("data", {}).get("last_month", 0),
                "source": "PyPI",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error fetching PyPI stats: {e}")
            return {
                "total_downloads": 0,
                "daily_downloads": 0,
                "weekly_downloads": 0,
                "monthly_downloads": 0,
                "source": "PyPI",
                "status": "error",
                "error": str(e)
            }
    
    def get_docker_pulls(self) -> Dict[str, Any]:
        """Fetch Docker Hub pull statistics"""
        try:
            # Docker Hub API (free, no auth required)
            url = f"https://hub.docker.com/v2/repositories/{self.docker_image}/"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 404:
                logger.info("Docker image not found on Docker Hub yet")
                return {
                    "total_pulls": 0,
                    "stars": 0,
                    "source": "Docker Hub",
                    "status": "not_found"
                }
            
            response.raise_for_status()
            data = response.json()
            
            return {
                "total_pulls": data.get("pull_count", 0),
                "stars": data.get("star_count", 0),
                "source": "Docker Hub",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error fetching Docker Hub stats: {e}")
            return {
                "total_pulls": 0,
                "stars": 0,
                "source": "Docker Hub",
                "status": "error",
                "error": str(e)
            }
    
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
            
            # Release downloads
            releases_url = f"https://api.github.com/repos/{self.github_repo}/releases"
            releases_response = requests.get(releases_url, headers=headers, timeout=30)
            releases_response.raise_for_status()
            releases_data = releases_response.json()
            
            total_release_downloads = 0
            latest_release = None
            
            for release in releases_data:
                if not latest_release:
                    latest_release = release.get("tag_name", "none")
                for asset in release.get("assets", []):
                    total_release_downloads += asset.get("download_count", 0)
            
            return {
                "stars": repo_data.get("stargazers_count", 0),
                "forks": repo_data.get("forks_count", 0),
                "watchers": repo_data.get("subscribers_count", 0),
                "open_issues": repo_data.get("open_issues_count", 0),
                "release_downloads": total_release_downloads,
                "latest_release": latest_release,
                "source": "GitHub",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error fetching GitHub stats: {e}")
            return {
                "stars": 0,
                "forks": 0,
                "watchers": 0,
                "open_issues": 0,
                "release_downloads": 0,
                "latest_release": "none",
                "source": "GitHub",
                "status": "error",
                "error": str(e)
            }
    
    def load_historical_data(self, filepath: str = "downloads.json") -> List[Dict[str, Any]]:
        """Load historical KPI data from JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return data.get("history", [])
        except FileNotFoundError:
            logger.info("No historical data found, starting fresh")
            return []
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return []
    
    def save_data(self, kpi_data: Dict[str, Any], filepath: str = "downloads.json") -> None:
        """Save KPI data to JSON file"""
        # Load existing history
        history = self.load_historical_data(filepath)
        
        # Add current data point
        history.append(kpi_data)
        
        # Keep only last 90 days of data (4 entries per day = 360 entries)
        if len(history) > 360:
            history = history[-360:]
        
        # Calculate sprint metrics
        total_downloads = (
            kpi_data["pypi"]["total_downloads"] + 
            kpi_data["docker"]["total_pulls"] + 
            kpi_data["github"]["release_downloads"]
        )
        
        # Prepare output data
        output = {
            "last_updated": kpi_data["timestamp"],
            "sprint": "S-1",
            "current_metrics": {
                "total_downloads": total_downloads,
                "pypi_downloads": kpi_data["pypi"]["total_downloads"],
                "docker_pulls": kpi_data["docker"]["total_pulls"],
                "github_release_downloads": kpi_data["github"]["release_downloads"],
                "github_stars": kpi_data["github"]["stars"],
                "github_issues": kpi_data["github"]["open_issues"],
                "latest_release": kpi_data["github"]["latest_release"]
            },
            "sprint_targets": {
                "downloads_target": 500,
                "downloads_progress": min(100, (total_downloads / 500) * 100),
                "issues_target": 5,
                "issues_progress": min(100, (kpi_data["github"]["open_issues"] / 5) * 100)
            },
            "status": {
                "downloads": "✅ ACHIEVED" if total_downloads >= 500 else f"⏳ IN PROGRESS ({total_downloads}/500)",
                "issues": "✅ ACHIEVED" if kpi_data["github"]["open_issues"] >= 5 else f"⏳ IN PROGRESS ({kpi_data['github']['open_issues']}/5)"
            },
            "history": history
        }
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"KPI data saved to {filepath}")
    
    def generate_badge_data(self, kpi_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate data for GitHub badges"""
        total_downloads = (
            kpi_data["pypi"]["total_downloads"] + 
            kpi_data["docker"]["total_pulls"] + 
            kpi_data["github"]["release_downloads"]
        )
        
        return {
            "downloads": f"{total_downloads:,}",
            "pypi": f"{kpi_data['pypi']['total_downloads']:,}",
            "docker": f"{kpi_data['docker']['total_pulls']:,}",
            "stars": f"{kpi_data['github']['stars']:,}",
            "issues": f"{kpi_data['github']['open_issues']:,}"
        }
    
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
        
        # Save to JSON file
        self.save_data(kpi_data)
        
        # Generate badge data
        badges = self.generate_badge_data(kpi_data)
        
        # Save badge data separately for easy access
        with open("badges.json", 'w') as f:
            json.dump(badges, f, indent=2)
        
        # Log summary
        total_downloads = (
            kpi_data["pypi"]["total_downloads"] + 
            kpi_data["docker"]["total_pulls"] + 
            kpi_data["github"]["release_downloads"]
        )
        
        logger.info(f"""
📊 KPI Summary for Sprint S-1:
- Total Downloads: {total_downloads:,} / 500 target
- GitHub Issues: {kpi_data['github']['open_issues']} / 5 target
- GitHub Stars: {kpi_data['github']['stars']}
- Latest Release: {kpi_data['github']['latest_release']}
        """)
        
        return kpi_data

def main():
    """CLI entry point"""
    tracker = FreeKPITracker()
    kpi_data = tracker.run()
    
    # Check if targets are met
    total_downloads = (
        kpi_data["pypi"]["total_downloads"] + 
        kpi_data["docker"]["total_pulls"] + 
        kpi_data["github"]["release_downloads"]
    )
    
    if total_downloads >= 500 and kpi_data["github"]["open_issues"] >= 5:
        logger.info("🎉 Sprint S-1 gate review metrics achieved!")
        exit(0)
    else:
        logger.info("⏳ Sprint S-1 targets in progress...")
        exit(0)

if __name__ == "__main__":
    main()