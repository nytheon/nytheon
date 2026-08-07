"""Data models for everything the profile builder works with.

Every object fetched from the GitHub API is normalised into one of these
dataclasses so the rendering layer (SVG + README) only ever deals with
plain, well-formed Python objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def now_iso() -> str:
    """Current UTC timestamp used for cache invalidation and labels."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Repository:
    """A single public repository owned by the user."""

    name: str
    stars: int
    primary_language: Optional[str]
    url: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "stars": self.stars,
            "primary_language": self.primary_language,
            "url": self.url,
        }


@dataclass
class LanguageStat:
    """Aggregated byte count for one programming language."""

    name: str
    bytes_count: int

    def percent_of(self, total: int) -> float:
        """Share (0-100) of this language relative to a total byte count."""
        if total <= 0:
            return 0.0
        return round(self.bytes_count / total * 100.0, 1)


@dataclass
class ContributionDay:
    """One day of the contribution calendar."""

    date: str
    count: int
    color: str
    weekday: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "date": self.date,
            "count": self.count,
            "color": self.color,
            "weekday": self.weekday,
        }


@dataclass
class CalendarWeek:
    """A week (seven days) of the contribution calendar."""

    days: List[ContributionDay]

    @property
    def total(self) -> int:
        return sum(d.count for d in self.days)

    def to_dict(self) -> Dict[str, object]:
        return {"days": [d.to_dict() for d in self.days]}


@dataclass
class ContributionCalendar:
    """Full contribution calendar with helper statistics."""

    total: int
    weeks: List[CalendarWeek]

    @property
    def week_count(self) -> int:
        return len(self.weeks)

    @property
    def active_days(self) -> int:
        return sum(1 for w in self.weeks for d in w.days if d.count > 0)

    @property
    def max_day(self) -> int:
        return max((d.count for w in self.weeks for d in w.days), default=0)

    @property
    def last_updated(self) -> str:
        all_days = [d for w in self.weeks for d in w.days]
        if not all_days:
            return "never"
        return max(d.date for d in all_days)

    def monthly_labels(self) -> List[str]:
        """Approximate month labels across the calendar's weeks."""
        labels: List[str] = []
        previous: Optional[str] = None
        for w in self.weeks:
            if not w.days:
                continue
            month = w.days[0].date[:7]  # YYYY-MM
            if month != previous:
                labels.append(month)
                previous = month
        return labels

    def to_dict(self) -> Dict[str, object]:
        return {
            "total": self.total,
            "weeks": [w.to_dict() for w in self.weeks],
        }


@dataclass
class UserStats:
    """High-level account statistics."""

    followers: int
    public_repos: int
    total_stars: int
    avatar_url: str = ""
    bio: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "followers": self.followers,
            "public_repos": self.public_repos,
            "total_stars": self.total_stars,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
        }


@dataclass
class LiveData:
    """Everything fetched from GitHub, bundled for the renderers."""

    stats: UserStats
    calendar: ContributionCalendar
    repositories: List[Repository]
    languages: List[LanguageStat] = field(default_factory=list)
    fetched_at: str = field(default_factory=now_iso)

    # ------------------------------------------------------------------
    @property
    def contributions(self) -> int:
        return self.calendar.total

    @property
    def total_language_bytes(self) -> int:
        return sum(l.bytes_count for l in self.languages)

    def top_languages(self, limit: int = 6) -> List[Tuple[LanguageStat, float]]:
        """Return (language, percent) pairs, best first, capped by limit."""
        total = self.total_language_bytes
        ranked = sorted(self.languages, key=lambda l: l.bytes_count, reverse=True)
        return [(l, l.percent_of(total)) for l in ranked[:limit]]

    def language_dict(self) -> Dict[str, int]:
        return {l.name: l.bytes_count for l in self.languages}

    def to_dict(self) -> Dict[str, object]:
        return {
            "stats": self.stats.to_dict(),
            "calendar": self.calendar.to_dict(),
            "repositories": [r.to_dict() for r in self.repositories],
            "languages": self.language_dict(),
            "fetched_at": self.fetched_at,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "LiveData":
        """Rebuild a LiveData instance from a previously serialised dict."""
        stats_raw = payload["stats"]
        stats = UserStats(
            followers=int(stats_raw["followers"]),
            public_repos=int(stats_raw["public_repos"]),
            total_stars=int(stats_raw["total_stars"]),
            avatar_url=str(stats_raw.get("avatar_url", "")),
            bio=str(stats_raw.get("bio", "")),
        )
        cal_raw = payload["calendar"]
        weeks = [
            CalendarWeek([
                ContributionDay(
                    date=str(d["date"]),
                    count=int(d["count"]),
                    color=str(d["color"]),
                    weekday=int(d["weekday"]),
                )
                for d in w["days"]
            ])
            for w in cal_raw["weeks"]
        ]
        calendar = ContributionCalendar(total=int(cal_raw["total"]), weeks=weeks)
        repos = [
            Repository(
                name=str(r["name"]),
                stars=int(r["stars"]),
                primary_language=(
                    str(r["primary_language"]) if r.get("primary_language") else None
                ),
                url=str(r.get("url", "")),
            )
            for r in payload["repositories"]
        ]
        languages = [
            LanguageStat(name=str(name), bytes_count=int(count))
            for name, count in payload.get("languages", {}).items()
        ]
        return cls(
            stats=stats,
            calendar=calendar,
            repositories=repos,
            languages=languages,
            fetched_at=str(payload.get("fetched_at", "")),
        )
