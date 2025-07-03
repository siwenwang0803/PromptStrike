# 📊 KPI Dashboard - Sprint S-1

**Last Updated**: Auto-updates every 6 hours via GitHub Actions  
**Data Source**: [downloads.json](./downloads.json)

## 🎯 Sprint S-1 Gate Review Targets

| Metric | Target | Current | Progress | Status |
|--------|--------|---------|----------|--------|
| **Total Downloads** | 500 | Loading... | Loading... | ⏳ |
| **GitHub Issues** | 5 | Loading... | Loading... | ⏳ |

## 📈 Download Breakdown

- **PyPI Downloads**: Loading...
- **Docker Hub Pulls**: Loading...  
- **GitHub Release Downloads**: Loading...

## ⭐ Community Metrics

- **GitHub Stars**: Loading...
- **Forks**: Loading...
- **Watchers**: Loading...

## 📊 Historical Trend

View full metrics history in [downloads.json](./downloads.json)

## 🔄 How It Works

1. **GitHub Actions** runs every 6 hours (or manually triggered)
2. **Free APIs** used:
   - PyPI Stats API (no auth required)
   - Docker Hub API (public endpoint)
   - GitHub API (uses GITHUB_TOKEN)
3. **Data saved** to `downloads.json` in the repo
4. **No external services** - completely free and self-contained

## 🚀 Manual Update

To trigger a manual KPI update:

1. Go to [Actions](../../actions/workflows/kpi-free.yml)
2. Click "Run workflow"
3. Select branch and sprint
4. Click "Run workflow" button

## 📝 Data Structure

```json
{
  "last_updated": "2025-07-03T14:00:00Z",
  "sprint": "S-1",
  "current_metrics": {
    "total_downloads": 0,
    "pypi_downloads": 0,
    "docker_pulls": 0,
    "github_release_downloads": 0,
    "github_stars": 0,
    "github_issues": 0
  },
  "sprint_targets": {
    "downloads_target": 500,
    "downloads_progress": 0,
    "issues_target": 5,
    "issues_progress": 0
  },
  "status": {
    "downloads": "⏳ IN PROGRESS (0/500)",
    "issues": "⏳ IN PROGRESS (0/5)"
  },
  "history": []
}
```

## 🔗 Integration

### README Badges

Add these to your README.md:

```markdown
![Downloads](https://img.shields.io/badge/downloads-loading-blue)
![Stars](https://img.shields.io/github/stars/siwenwang0803/PromptStrike)
![Issues](https://img.shields.io/github/issues/siwenwang0803/PromptStrike)
```

### Programmatic Access

```python
import json
import requests

# Fetch latest KPI data
url = "https://raw.githubusercontent.com/siwenwang0803/PromptStrike/main/downloads.json"
response = requests.get(url)
kpi_data = response.json()

print(f"Total downloads: {kpi_data['current_metrics']['total_downloads']}")
print(f"Sprint progress: {kpi_data['sprint_targets']['downloads_progress']}%")
```

---

*This dashboard is automatically updated by the [KPI monitoring workflow](.github/workflows/kpi-free.yml)*