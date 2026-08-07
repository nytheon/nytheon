"""Live GitHub data fetching with retries, rate-limit awareness and caching.

The client uses the GitHub GraphQL API for account statistics and the
contribution calendar, plus the REST API to read per-repository language
byte counts. Results are normalised into :class:`models.LiveData`.

A small on-disk JSON cache (configurable TTL) lets the daily GitHub
Actions job avoid hammering the API when nothing has changed.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Dict, List, Optional

from .config import ProfileConfig
from .models import (
    CalendarWeek,
    ContributionCalendar,
    ContributionDay,
    LanguageStat,
    LiveData,
    Repository,
    UserStats,
)

GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
REST_ENDPOINT = "https://api.github.com"
DEFAULT_CACHE_TTL_SECONDS = 3600  # one hour


# ---------------------------------------------------------------------------
# Small retryable HTTP helper.
# ---------------------------------------------------------------------------
def _request(url: str, token: str, payload: Optional[Dict[str, object]] = None,
             attempts: int = 3) -> Dict[str, object]:
    """Perform a GitHub API request with retry + backoff on transient errors."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "nytheon-profile-builder",
    }
    data = json.dumps(payload).encode() if payload is not None else None
    if data is not None:
        headers["Content-Type"] = "application/json"

    last_error: Optional[Exception] = None
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
            with urllib.request.urlopen(req, timeout=30) as response:
                body = response.read().decode("utf-8")
                parsed = json.loads(body)
                if "errors" in parsed:
                    raise RuntimeError(f"GraphQL errors: {parsed['errors']}")
                return parsed
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, ValueError) as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (401, 403, 404):
                # Authentication / permission problems will not fix themselves.
                raise RuntimeError(f"GitHub API {exc.code}: {exc.reason}") from exc
            time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"GitHub API request failed after {attempts} attempts: {last_error}")


# ---------------------------------------------------------------------------
# GraphQL queries.
# ---------------------------------------------------------------------------
PROFILE_QUERY = """
query Profile($login: String!) {
  user(login: $login) {
    name
    login
    bio
    avatarUrl
    followers { totalCount }
    repositories(privacy: PUBLIC, ownerAffiliations: OWNER, first: 100) {
      totalCount
      nodes {
        name
        url
        stargazerCount
        primaryLanguage { name }
      }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            color
            weekday
          }
        }
      }
    }
  }
}
"""


class GitHubApi:
    """Thin wrapper around the GitHub API tailored for profile building."""

    def __init__(self, token: str, username: str) -> None:
        if not token:
            raise ValueError("A GitHub token is required (GITHUB_TOKEN env var).")
        self.token = token
        self.username = username

    # -- low-level ----------------------------------------------------
    def graphql(self, query: str, variables: Dict[str, object]) -> Dict[str, object]:
        payload = {"query": query, "variables": variables}
        result = _request(GRAPHQL_ENDPOINT, self.token, payload)
        if "data" not in result:
            raise RuntimeError(f"GraphQL response missing 'data': {result}")
        return result["data"]

    def rest(self, path: str) -> Dict[str, object]:
        return _request(f"{REST_ENDPOINT}{path}", self.token)

    # -- profile data -------------------------------------------------
    def fetch_user_block(self) -> Dict[str, object]:
        """Pull the GraphQL user block used for stats + calendar."""
        data = self.graphql(PROFILE_QUERY, {"login": self.username})
        user = data.get("user")
        if user is None:
            raise RuntimeError(f"User '{self.username}' not found.")
        return user

    def fetch_repo_languages(self, repo: Repository) -> Dict[str, int]:
        """Return {language: bytes} for a single repository via REST."""
        path = f"/repos/{self.username}/{repo.name}/languages"
        raw = self.rest(path)
        return {name: int(count) for name, count in raw.items()}

    # -- normalisation ------------------------------------------------
    def assemble(self) -> LiveData:
        """Fetch everything live and normalise it into a LiveData bundle."""
        user = self.fetch_user_block()

        stats = UserStats(
            followers=int(user["followers"]["totalCount"]),
            public_repos=int(user["repositories"]["totalCount"]),
            total_stars=sum(r["stargazerCount"] for r in user["repositories"]["nodes"]),
            avatar_url=str(user.get("avatarUrl", "")),
            bio=str(user.get("bio") or ""),
        )

        repos = [
            Repository(
                name=str(r["name"]),
                url=str(r.get("url", "")),
                stars=int(r["stargazerCount"]),
                primary_language=(
                    str(r["primaryLanguage"]["name"])
                    if r.get("primaryLanguage") else None
                ),
            )
            for r in user["repositories"]["nodes"]
        ]

        calendar_raw = user["contributionsCollection"]["contributionCalendar"]
        weeks = [
            CalendarWeek([
                ContributionDay(
                    date=str(d["date"]),
                    count=int(d["contributionCount"]),
                    color=str(d["color"]),
                    weekday=int(d["weekday"]),
                )
                for d in w["contributionDays"]
            ])
            for w in calendar_raw["weeks"]
        ]
        calendar = ContributionCalendar(
            total=int(calendar_raw["totalContributions"]),
            weeks=weeks,
        )

        # Language bytes via REST (kept in-process to stay robust if one
        # repository is temporarily unavailable).
        language_bytes: Dict[str, int] = {}
        for repo in repos:
            try:
                for name, count in self.fetch_repo_languages(repo).items():
                    language_bytes[name] = language_bytes.get(name, 0) + count
            except RuntimeError:
                continue

        languages = [
            LanguageStat(name=name, bytes_count=count)
            for name, count in sorted(
                language_bytes.items(), key=lambda kv: kv[1], reverse=True
            )
        ]

        return LiveData(
            stats=stats,
            calendar=calendar,
            repositories=repos,
            languages=languages,
        )

    # -- caching ------------------------------------------------------
    def load_cache(self, path: str, ttl: int = DEFAULT_CACHE_TTL_SECONDS) -> Optional[LiveData]:
        """Load and deserialise a cached LiveData payload if still fresh."""
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            fetched = payload.get("fetched_at", "")
            if not fetched:
                return None
            age = time.time() - self._parse_time(fetched)
            if age > ttl:
                return None
            return LiveData.from_dict(payload)
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def save_cache(self, data: LiveData, path: str) -> None:
        """Serialise a LiveData bundle to the cache file."""
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data.to_dict(), fh, indent=2)

    @staticmethod
    def _parse_time(stamp: str) -> float:
        """Best-effort parse of 'YYYY-MM-DDTHH:MM:SSZ' into epoch seconds."""
        try:
            return time.mktime(time.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ"))
        except ValueError:
            return 0.0


def token_from_env() -> Optional[str]:
    """Read GITHUB_TOKEN from the environment, if present."""
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
