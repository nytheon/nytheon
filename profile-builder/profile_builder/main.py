"""Command-line interface for the profile builder.

Examples
--------
Fetch live data and generate everything into the repository root::

    GITHUB_TOKEN=ghp_xxx python -m profile_builder --root ..

Regenerate from a cached snapshot without touching the network::

    python -m profile_builder --root .. --use-cache

Only refresh the banner (no network required)::

    python -m profile_builder --root .. --banner-only --use-cache
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

from .config import ProfileConfig
from .github_api import DEFAULT_CACHE_TTL_SECONDS, GitHubApi, token_from_env
from .models import LiveData
from .svg_assets import thousands
from . import __version__

CACHE_FILENAME = ".profile_cache.json"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="profile_builder",
        description="Generate a real-time GitHub profile README and assets.",
    )
    parser.add_argument("--root", default=".", help="Repository root to write files into.")
    parser.add_argument(
        "--username",
        default=os.environ.get("PROFILE_USERNAME", "nytheon"),
        help="GitHub username to build the profile for.",
    )
    parser.add_argument("--cache", default=CACHE_FILENAME, help="Path to the data cache file.")
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Read live data from the cache instead of the network.",
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=DEFAULT_CACHE_TTL_SECONDS,
        help="Cache freshness window in seconds.",
    )
    parser.add_argument(
        "--banner-only",
        action="store_true",
        help="Only regenerate the hero banner (no README).",
    )
    parser.add_argument(
        "--readme-only",
        action="store_true",
        help="Only regenerate the README (no banner).",
    )
    parser.add_argument(
        "--no-workflow",
        action="store_true",
        help="Do not (re)write the GitHub Actions workflow file.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _load_live_data(args: argparse.Namespace, cache_path: str) -> LiveData:
    """Load or fetch the LiveData bundle according to CLI flags."""
    if args.use_cache:
        with open(cache_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return LiveData.from_dict(payload)

    token = token_from_env()
    api = GitHubApi(token, args.username)
    cached = api.load_cache(cache_path, ttl=args.cache_ttl) if os.path.exists(cache_path) else None
    if cached is not None:
        print(f"[info] using cached data ({cached.fetched_at})")
        return cached
    data = api.assemble()
    api.save_cache(data, cache_path)
    return data


def _print_summary(data: LiveData) -> None:
    """Print a compact overview of the fetched live data."""
    stats = data.stats
    langs = data.top_languages(limit=6)
    print("-" * 58)
    print(f"  followers .......... {thousands(stats.followers)}")
    print(f"  public repos ....... {thousands(stats.public_repos)}")
    print(f"  total stars ........ {thousands(stats.total_stars)}")
    print(f"  contributions ...... {thousands(data.contributions)}")
    print(f"  language bytes ..... {thousands(data.total_language_bytes)}")
    if langs:
        top = ", ".join(f"{name} ({pct:.0f}%)" for name, pct in langs)
        print(f"  top languages ...... {top}")
    print("-" * 58)


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point; returns a process exit code."""
    args = _build_parser().parse_args(argv)
    cfg = ProfileConfig(username=args.username)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"[error] root directory does not exist: {root}", file=sys.stderr)
        return 1

    cache_path = os.path.join(root, args.cache)

    try:
        data = _load_live_data(args, cache_path)
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"[error] could not obtain live data: {exc}", file=sys.stderr)
        return 2

    _print_summary(data)

    from . import readme_builder
    from . import workflow

    if not args.readme_only:
        written = readme_builder.write_assets(cfg, data, root)
        for path in written:
            print(f"[wrote] {os.path.relpath(path, root)}")

    if not args.banner_only:
        content = readme_builder.write_readme(cfg, data, root)
        print(f"[wrote] README.md ({len(content.splitlines())} lines)")

    if not args.no_workflow and not args.banner_only and not args.readme_only:
        path = workflow.write_workflow(cfg, root)
        print(f"[wrote] {os.path.relpath(path, root)}")

    print("[done] profile is up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
