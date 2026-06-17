#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${ROOT}/lambda/api-proxy"
OUT="${ROOT}/terraform/api/build"

if command -v uv >/dev/null 2>&1; then
  install_deps() {
    uv pip install \
      --python 3.12 \
      -r "$1" \
      -t "$2" \
      --quiet
  }
else
  install_deps() {
    python3 -m pip install \
      -r "$1" \
      -t "$2" \
      --quiet
  }
fi

rm -rf "${OUT}"
mkdir -p "${OUT}/auth" "${OUT}/stream"

install_deps "${SRC}/requirements-auth.txt" "${OUT}/auth"
cp "${SRC}/auth_handler.py" "${SRC}/common.py" "${SRC}/secrets_module.py" "${OUT}/auth/"

install_deps "${SRC}/requirements-stream.txt" "${OUT}/stream"
cp "${SRC}/stream_app.py" "${SRC}/common.py" "${SRC}/secrets_module.py" "${SRC}/run.sh" "${OUT}/stream/"
chmod +x "${OUT}/stream/run.sh"

echo "Built Lambda packages in ${OUT}"
