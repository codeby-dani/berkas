#!/usr/bin/env bash
# Deploy the ADK agent to Cloud Run.
# Note: brew's python@3.14 has a broken _sqlite3, so gcloud is pinned to a working 3.13.
set -euo pipefail

export PATH="$HOME/.local/bin:/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
export CLOUDSDK_PYTHON="/Users/danimuhammad/.local/share/uv/python/cpython-3.13-macos-aarch64-none/bin/python3"

PROJECT="project-336ac302-a8b2-4026-98e"
REGION="us-central1"          # Cloud Run region. The *model* location is "global" (see agent/.env).
SERVICE="${1:-agentic-skeleton}"

cd "$(dirname "$0")"

uv run adk deploy cloud_run \
  --project="$PROJECT" \
  --region="$REGION" \
  --service_name="$SERVICE" \
  --with_ui \
  --trace_to_cloud \
  agent \
  -- --allow-unauthenticated --min-instances=0 --max-instances=3
