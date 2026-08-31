#!/usr/bin/env bash
# One-time IAM fix for a fresh GCP project.
#
# New projects no longer grant Editor to the default compute service account, and
# Cloud Build runs as that account. Without these two roles:
#   - the build fails with "does not have storage.objects.get access" (it cannot read
#     the source zip it just uploaded)
#   - the deployed service gets 403s from Vertex AI at runtime
set -euo pipefail

export PATH="$HOME/.local/bin:/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
export CLOUDSDK_PYTHON="/Users/danimuhammad/.local/share/uv/python/cpython-3.13-macos-aarch64-none/bin/python3"

PROJECT="project-336ac302-a8b2-4026-98e"
SA="647274440523-compute@developer.gserviceaccount.com"

for ROLE in roles/cloudbuild.builds.builder roles/aiplatform.user; do
  echo "==> granting $ROLE to $SA"
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="serviceAccount:$SA" \
    --role="$ROLE" \
    --condition=None \
    --quiet >/dev/null
done

echo
echo "Roles now held by the compute service account:"
gcloud projects get-iam-policy "$PROJECT" \
  --flatten="bindings[].members" \
  --filter="bindings.members:${SA}" \
  --format="value(bindings.role)" | sort
