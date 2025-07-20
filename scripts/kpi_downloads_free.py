#!/usr/bin/env python3
"""
KPI Monitoring Script for Free Tier Downloads
Tracks GitHub downloads, stars, and issues for Sprint S-3 metrics
"""

import json
import os
import requests
from datetime import datetime, timezone

def get_github_metrics():
    """Get metrics from GitHub API"""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("Warning: No GITHUB_TOKEN found, using public API (rate limited)")
    
    headers = {}
    if token:
        headers['Authorization'] = f'token {token}'
        headers['Accept'] = 'application/vnd.github.v3+json'
    
    repo_owner = 'siwenwang0803'
    repo_name = 'RedForge'
    
    try:
        # Get repository stats
        repo_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}'
        repo_response = requests.get(repo_url, headers=headers)
        repo_data = repo_response.json()
        
        # Get releases for download counts
        releases_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/releases'
        releases_response = requests.get(releases_url, headers=headers)
        releases_data = releases_response.json()
        
        # Get issues count
        issues_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues'
        issues_response = requests.get(issues_url, headers=headers)
        issues_data = issues_response.json()
        
        # Calculate total downloads from releases
        total_downloads = 0
        for release in releases_data:
            for asset in release.get('assets', []):
                total_downloads += asset.get('download_count', 0)
        
        # Get stars and open issues
        stars = repo_data.get('stargazers_count', 0)
        open_issues = len([issue for issue in issues_data if 'pull_request' not in issue])
        
        return {
            'downloads': total_downloads,
            'stars': stars,
            'issues': open_issues,
            'forks': repo_data.get('forks_count', 0),
            'watchers': repo_data.get('watchers_count', 0)
        }
        
    except Exception as e:
        print(f"Error fetching GitHub metrics: {e}")
        return {
            'downloads': 0,
            'stars': 0,
            'issues': 0,
            'forks': 0,
            'watchers': 0
        }

def generate_kpi_data():
    """Generate KPI data for Sprint S-3"""
    metrics = get_github_metrics()
    
    # Sprint S-3 targets (Product Hunt launch preparation)
    targets = {
        'downloads': 500,
        'issues': 5,
        'stars': 50,
        'community_engagement': 10
    }
    
    # Calculate progress
    downloads_progress = min(100, (metrics['downloads'] / targets['downloads']) * 100)
    issues_progress = min(100, (metrics['issues'] / targets['issues']) * 100)
    stars_progress = min(100, (metrics['stars'] / targets['stars']) * 100)
    
    kpi_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'sprint': 'S-3',
        'current_metrics': metrics,
        'sprint_targets': targets,
        'progress': {
            'downloads': round(downloads_progress, 1),
            'issues': round(issues_progress, 1),
            'stars': round(stars_progress, 1)
        },
        'status': {
            'downloads': f"{'✅' if metrics['downloads'] >= targets['downloads'] else '🔄'} Downloads: {metrics['downloads']}/{targets['downloads']} ({downloads_progress:.1f}%)",
            'issues': f"{'✅' if metrics['issues'] >= targets['issues'] else '🔄'} Issues: {metrics['issues']}/{targets['issues']} ({issues_progress:.1f}%)",
            'stars': f"{'✅' if metrics['stars'] >= targets['stars'] else '🔄'} Stars: {metrics['stars']}/{targets['stars']} ({stars_progress:.1f}%)"
        },
        'next_milestone': 'Product Hunt Launch',
        'gate_review_ready': all([
            metrics['downloads'] >= targets['downloads'],
            metrics['issues'] >= targets['issues']
        ])
    }
    
    return kpi_data

def generate_badges_data():
    """Generate data for shields.io badges"""
    metrics = get_github_metrics()
    
    return {
        'downloads': str(metrics['downloads']),
        'stars': str(metrics['stars']),
        'issues': str(metrics['issues']),
        'status': 'stable' if metrics['downloads'] >= 500 else 'beta'
    }

def main():
    """Main execution"""
    print("🔥 RedForge KPI Monitoring - Sprint S-3")
    print("=" * 50)
    
    # Generate KPI data
    kpi_data = generate_kpi_data()
    badges_data = generate_badges_data()
    
    # Save to files
    with open('downloads.json', 'w') as f:
        json.dump(kpi_data, f, indent=2)
    
    with open('badges.json', 'w') as f:
        json.dump(badges_data, f, indent=2)
    
    # Print summary
    print(f"📊 Current Metrics:")
    print(f"   Downloads: {kpi_data['current_metrics']['downloads']}")
    print(f"   Stars: {kpi_data['current_metrics']['stars']}")
    print(f"   Issues: {kpi_data['current_metrics']['issues']}")
    print()
    print(f"🎯 Sprint S-3 Progress:")
    print(f"   Downloads: {kpi_data['progress']['downloads']}%")
    print(f"   Issues: {kpi_data['progress']['issues']}%")
    print(f"   Stars: {kpi_data['progress']['stars']}%")
    print()
    print(f"🚀 Gate Review Ready: {'Yes' if kpi_data['gate_review_ready'] else 'No'}")
    
    if kpi_data['gate_review_ready']:
        print("✅ Ready for Product Hunt launch!")
    else:
        print("🔄 Continue building toward targets...")

if __name__ == '__main__':
    main()