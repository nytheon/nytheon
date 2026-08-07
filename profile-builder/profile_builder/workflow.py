"""GitHub Actions workflow generation.

Produces a valid ``.github/workflows/profile.yml`` that:

- runs every day on a schedule, on every push, and on demand;
- checks out the repository with the bot's credentials;
- installs nothing extra (the tool is standard-library only);
- runs the test suite to prove the generator is healthy;
- regenerates the README + banner from live GitHub data;
- commits and pushes any changes.

This is what makes the profile genuinely *real-time*: the numbers baked
into the banner and the layout of the README are refreshed daily by the
service itself, no manual re-runs required.
"""

from __future__ import annotations

import os
from typing import List

from .config import ProfileConfig

WORKFLOW_REL_PATH = os.path.join(".github", "workflows", "profile.yml")

CRON_DEFAULT = "0 2 * * *"


def _quote(value: str) -> str:
    return value.replace("'", "'\\''")


def build_workflow(cfg: ProfileConfig, cron: str = CRON_DEFAULT) -> str:
    """Return the YAML content for the auto-refresh workflow."""
    lines: List[str] = [
        "name: refresh profile",
        "",
        "on:",
        "  schedule:",
        f"    - cron: {_quote(cron)}",
        "  push:",
        "    branches: [ main ]",
        "  workflow_dispatch:",
        "",
        "permissions:",
        "  contents: write",
        "",
        "concurrency:",
        "  group: profile-refresh",
        "  cancel-in-progress: true",
        "",
        "jobs:",
        "  build:",
        "    runs-on: ubuntu-latest",
        "    steps:",
        "      - name: Checkout",
        "        uses: actions/checkout@v4",
        "        with:",
        "          ref: main",
        "      - name: Set up Python",
        "        uses: actions/setup-python@v5",
        "        with:",
        "          python-version: '3.12'",
        "      - name: Run tests",
        "        working-directory: profile-builder",
        "        run: python -m unittest discover -s tests -v",
        "      - name: Generate profile",
        "        working-directory: profile-builder",
        "        env:",
        "          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}",
        "          PROFILE_USERNAME: ${{ github.repository_owner }}",
        "        run: python -m profile_builder --root ..",
        "      - name: Commit and push",
        "        env:",
        f"          BOT_NAME: {_quote(cfg.display_name)}",
        f"          BOT_EMAIL: {_quote(cfg.email)}",
        "        run: |",
        '          git config user.name "$BOT_NAME"',
        '          git config user.email "$BOT_EMAIL"',
        "          git add -A",
        "          git diff --cached --quiet || git commit -m \"chore: refresh profile [skip ci]\"",
        "          git push",
        "",
    ]
    return "\n".join(lines)


def write_workflow(cfg: ProfileConfig, root: str,
                   cron: str = CRON_DEFAULT) -> str:
    """Write the workflow YAML file, returning its absolute path."""
    path = os.path.join(root, WORKFLOW_REL_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(build_workflow(cfg, cron=cron))
    return path
