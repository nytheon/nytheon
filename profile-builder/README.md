# nytheon-profile-builder

Real-time GitHub profile generator — dependency-free (standard library only).

## What it does

- Fetches live account stats, contribution calendar and per-language byte
  counts from the GitHub GraphQL + REST APIs.
- Renders an animated, data-driven hero banner as local SVG branding.
- Builds `README.md` from live services that stay up (`skillicons.dev` real
  language logos, `streak-stats`, `github-readme-activity-graph`,
  `img.shields.io`) and from local assets baked from live data every day
  (`assets/stats.svg`, `assets/langs.svg`) so the stats/top-languages cards
  always load — the public `github-readme-stats` service is frequently
  suspended and is not used.
- Ships a GitHub Actions workflow (`.github/workflows/profile.yml`) that
  re-runs the generator every day and commits the refreshed profile.

## Usage

```bash
GITHUB_TOKEN=ghp_xxx python -m profile_builder --root ..
```

Regenerate from cache (offline):

```bash
python -m profile_builder --root .. --use-cache
```

Refresh only the banner:

```bash
python -m profile_builder --root .. --banner-only --use-cache
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Layout

```
profile_builder/
  config.py        profile configuration + brand palette
  models.py        data models (LiveData, stats, calendar, languages)
  github_api.py    GitHub API client (GraphQL + REST, retries, caching)
  svg_assets.py    hero banner / stat card / language bar generators
  readme_builder.py  README assembly from live service URLs
  workflow.py      GitHub Actions workflow generator
  main.py          CLI entry point
tests/             unit tests for the pure helpers
```
