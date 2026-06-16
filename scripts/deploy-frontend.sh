#!/usr/bin/env bash
# Build the Vite frontend and deploy to S3 + invalidate CloudFront.
#
# Prerequisites:
#   - terraform apply in terraform/frontend/ (one-time)
#   - AWS CLI v2, Terraform, pnpm install at repo root
#   - AWS credentials (AWS_PROFILE or default credential chain)
#   - Root .env with FRONTEND_S3_BUCKET, FRONTEND_CLOUDFRONT_DISTRIBUTION_ID
#
# Operator workflow:
#   1. cd terraform/frontend && terraform apply
#   2. Copy outputs into root .env (bucket, distribution id, VITE_API_BASE_URL)
#   3. pnpm deploy:frontend

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

for var in AWS_REGION FRONTEND_S3_BUCKET FRONTEND_CLOUDFRONT_DISTRIBUTION_ID; do
  if [[ -z "${!var:-}" ]]; then
    echo "Error: $var is not set (configure in .env)" >&2
    exit 1
  fi
done

export AWS_REGION
if [[ -n "${AWS_PROFILE:-}" ]]; then
  export AWS_PROFILE
fi

echo "Building frontend..."
VITE_API_BASE_URL="${VITE_API_BASE_URL:-}" pnpm --filter frontend build

DIST_DIR="$REPO_ROOT/frontend/dist"
if [[ ! -d "$DIST_DIR" ]]; then
  echo "Error: build output not found at $DIST_DIR" >&2
  exit 1
fi

echo "Syncing assets to s3://$FRONTEND_S3_BUCKET ..."
aws s3 sync "$DIST_DIR/" "s3://$FRONTEND_S3_BUCKET/" \
  --delete \
  --exclude "index.html" \
  --cache-control "public,max-age=31536000,immutable"

echo "Uploading index.html with no-cache..."
aws s3 cp "$DIST_DIR/index.html" "s3://$FRONTEND_S3_BUCKET/index.html" \
  --cache-control "no-cache,no-store,must-revalidate" \
  --content-type "text/html"

echo "Creating CloudFront invalidation..."
INVALIDATION_ID="$(aws cloudfront create-invalidation \
  --distribution-id "$FRONTEND_CLOUDFRONT_DISTRIBUTION_ID" \
  --paths "/*" \
  --query 'Invalidation.Id' \
  --output text)"

echo "Invalidation $INVALIDATION_ID created."

if [[ -n "${FRONTEND_URL:-}" ]]; then
  echo "Frontend URL: $FRONTEND_URL"
else
  echo "Tip: set FRONTEND_URL in .env (from terraform output frontend_url)."
fi

echo "Deploy complete."
