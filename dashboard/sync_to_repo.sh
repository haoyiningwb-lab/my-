#!/usr/bin/env bash
set -euo pipefail

WORKDIR="/Users/haoyining/.openclaw/workspace/dashboard"
REPO_DIR="${1:-$WORKDIR}"
BRANCH="${2:-main}"
COMMIT_MSG="dashboard data sync: $(date '+%Y-%m-%d %H:%M:%S')"

cd "$WORKDIR"
python3 export_bi_data.py
python3 export_duckdb.py
python3 export_sqlite.py

cd "$REPO_DIR"
git add dashboard/exports dashboard/app_cloud.py dashboard/requirements.txt || true
git commit -m "$COMMIT_MSG" || true
git push origin "$BRANCH"

echo "Done: data exported and pushed to $BRANCH"
