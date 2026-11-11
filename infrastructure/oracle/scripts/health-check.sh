#!/usr/bin/env bash
set -euo pipefail
curl --fail --silent --show-error http://127.0.0.1:8000/health || exit 1
curl --fail --silent --show-error http://127.0.0.1:3000/ || exit 1
echo "Local frontend/backend checks passed."
