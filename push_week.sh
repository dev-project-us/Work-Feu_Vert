#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# push_week.sh — Weekly CSV push wrapper (Linux / Mac / WSL)
#
# Usage:
#   ./push_week.sh              ← reads from inbox/ by default
#   ./push_week.sh /path/to/exports
#   ./push_week.sh --dry-run    ← preview without committing
#
# Make executable (one-time):
#   chmod +x push_week.sh
# ──────────────────────────────────────────────────────────────────────────────

set -e   # stop on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Use the Python in the virtual env if it exists, else system Python
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
else
    PYTHON="python3"
fi

exec "$PYTHON" scripts/push_week.py "$@"
