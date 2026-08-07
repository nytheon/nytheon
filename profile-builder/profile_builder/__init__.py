"""nytheon-profile-builder.

A dependency-free toolkit that generates a real-time GitHub profile:

- fetches live account statistics, the contribution calendar and language
  byte-counts from the GitHub API (GraphQL + REST);
- renders an animated, data-driven hero banner as local SVG branding;
- assembles README.md from live services (github-readme-stats,
  skillicons, streak-stats, activity-graph, shields.io) so every number
  stays current without re-running anything;
- ships a GitHub Actions workflow that refreshes the profile every day.

The project is standard-library only and ships with a unit test suite.
"""

__version__ = "1.0.0"

from .config import ProfileConfig
from .github_api import GitHubApi, token_from_env
from .models import LiveData

__all__ = [
    "ProfileConfig",
    "GitHubApi",
    "LiveData",
    "token_from_env",
    "__version__",
]
