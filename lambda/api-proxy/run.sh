#!/bin/sh
set -eu
exec python -m uvicorn stream_app:app --host 0.0.0.0 --port "${PORT:-8080}"
