#!/usr/bin/env bash
# Deploy Berkas to Cloud Run.
#
# Regenerates requirements.txt from the lockfile first. `uv add` updates
# pyproject.toml and uv.lock but not requirements.txt, and the container installs
# from requirements.txt -- so adding a dependency and deploying without this step
# ships an image missing it. That cost a 500 on every PDF upload, with the module
# importing fine locally the whole time.
#
# Also re-syncs the corpus, which is gitignored and therefore easy to forget.
set -euo pipefail

export PATH="$HOME/.local/bin:/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
export CLOUDSDK_PYTHON="/Users/danimuhammad/.local/share/uv/python/cpython-3.13-macos-aarch64-none/bin/python3"

PROJECT="project-336ac302-a8b2-4026-98e"
REGION="us-central1"

cd "$(dirname "$0")"

uv export --no-dev --no-emit-project --format requirements-txt -o requirements.txt
uv run python scripts/sync_corpus.py
uv run pytest -q

gcloud run deploy berkas \
  --source . --project="$PROJECT" --region="$REGION" \
  --allow-unauthenticated --min-instances=1 --max-instances=3 \
  --memory=2Gi --cpu=2 --timeout=900 \
  --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT="$PROJECT",GOOGLE_CLOUD_LOCATION=global,MODEL_ID=gemini-3.7-flash,BERKAS_GMAIL_TOKEN_SECRET=berkas-gmail-token,BERKAS_DEMO_RECIPIENT=dani.muhammad.k@gmail.com \
  --set-secrets=GOOGLE_API_KEY=berkas-gemini-key:latest
