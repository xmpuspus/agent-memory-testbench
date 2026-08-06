#!/usr/bin/env bash
# Re-capture the README screenshots from a clean wheel.
#
# The pictures must show what `pip install memory-arena` gives a reader, so this
# builds the wheel, installs it into a throwaway virtual environment, serves the
# bundled historical snapshot with no provider key and no container, and shoots
# every README image against that server.
#
#     ./docs/recapture.sh
#
# Re-record the GIF with ./docs/record_demo.sh.

set -euo pipefail

cd "$(dirname "$0")/.."
REPO="$PWD"
PYTHON="${MEMORY_ARENA_PYTHON:-$REPO/.venv/bin/python}"
[ -x "$PYTHON" ] || PYTHON="$(command -v python3)"

WORKDIR=$(mktemp -d /tmp/memory-arena-shots-XXXXXX)
trap 'kill "${SERVER_PID:-}" 2>/dev/null || true; rm -rf "$WORKDIR"' EXIT
mkdir -p "$WORKDIR/stage"

echo "[build] wheel"
rm -rf dist
"$PYTHON" -m build >/dev/null
WHEEL=$(ls dist/memory_arena-*-py3-none-any.whl)

echo "[venv] install $WHEEL"
python3 -m venv "$WORKDIR/venv"
"$WORKDIR/venv/bin/pip" -q install "$REPO/$WHEEL"

echo "[server] start"
(
  cd "$WORKDIR/stage"
  env -u ANTHROPIC_API_KEY -u OPENAI_API_KEY -u MEM_ARENA_RESULTS_PATH \
      -u MEM_ARENA_DATASETS_PATH BROWSER=true \
      "$WORKDIR/venv/bin/memory-arena" demo --port 8824 > "$WORKDIR/server.log" 2>&1 &
  echo $! > "$WORKDIR/server.pid"
)
SERVER_PID=$(cat "$WORKDIR/server.pid")
PORT=""
for _ in $(seq 1 40); do
  PORT=$(grep -o "127.0.0.1:[0-9]*" "$WORKDIR/server.log" | head -1 | cut -d: -f2 || true)
  [ -n "$PORT" ] && curl -sf "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1 && break
  sleep 1
done
[ -n "$PORT" ] || { echo "server never came up" >&2; cat "$WORKDIR/server.log" >&2; exit 1; }
echo "[server] port $PORT"

echo "[shots]"
"$PYTHON" scripts/capture_screenshots.py --base "http://127.0.0.1:$PORT" --out docs
echo "[done] read every regenerated PNG back before committing it."
