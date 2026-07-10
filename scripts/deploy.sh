#!/usr/bin/env bash
# =============================================================================
# deploy.sh - Deploy a published image tag using docker-compose.prod.yml
# =============================================================================
# Usage:
#   export DOCKERHUB_USERNAME=<dockerhub-username>
#   export APP_NAME=<repo-name>   # optional, defaults to current directory name
#   ./scripts/deploy.sh sha-<short-commit-hash>
#
# Example:
#   ./scripts/deploy.sh sha-a1b2c3d
# =============================================================================

set -euo pipefail

IMAGE_TAG="${1:-}"

if [ -z "$IMAGE_TAG" ]; then
    echo "Usage: ./scripts/deploy.sh sha-<short-commit-hash>"
    echo "Example: ./scripts/deploy.sh sha-a1b2c3d"
    exit 1
fi

if [ "$IMAGE_TAG" = "latest" ]; then
    echo "Refusing to deploy tag 'latest' - deployments must be pinned to a commit."
    echo "Usage: ./scripts/deploy.sh sha-<short-commit-hash>"
    exit 1
fi

export IMAGE_TAG
export APP_NAME="${APP_NAME:-$(basename "$PWD")}"

if [ -z "${DOCKERHUB_USERNAME:-}" ]; then
    echo "Missing DOCKERHUB_USERNAME"
    exit 1
fi

echo "Deploying ${APP_NAME} using image tag: ${IMAGE_TAG}"

docker compose -f docker-compose.prod.yml pull
# `--wait` blocks until every service reports healthy (or times out), so we
# fail the deploy fast instead of returning success on a stack that isn't
# actually ready to serve traffic.
docker compose -f docker-compose.prod.yml up -d --remove-orphans --wait --wait-timeout 90
docker compose -f docker-compose.prod.yml ps

