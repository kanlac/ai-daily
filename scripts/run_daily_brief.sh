#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DATE_ARG="${1:-$(date +%F)}"
LOOPS="${DAILY_BRIEF_LOOPS:-7}"

if command -v uv >/dev/null 2>&1; then
  exec uv run python -m daily_brief.cli run --config configs/daily-brief.yaml --date "$DATE_ARG" --loops "$LOOPS"
fi

exec python3 -m daily_brief.cli run --config configs/daily-brief.yaml --date "$DATE_ARG" --loops "$LOOPS"
