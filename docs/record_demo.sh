#!/usr/bin/env bash
# Record docs/demo.gif and docs/demo-poster.png from a clean wheel.
#
# The recording must show what a reader gets from `pip install memory-arena`,
# so it runs against a throwaway virtual environment that holds only the built
# wheel. No provider key and no container are set, which is the claim the last
# frame makes. Run it from the repository root:
#
#     ./docs/record_demo.sh
#
# Needs: vhs, ffmpeg, gifsicle, and the project virtual environment at .venv
# for Playwright.

set -euo pipefail

cd "$(dirname "$0")/.."
REPO="$PWD"
# A git worktree has no .venv of its own. Take an explicit interpreter first,
# then this checkout's, then python3.
PYTHON="${MEMORY_ARENA_PYTHON:-$REPO/.venv/bin/python}"
[ -x "$PYTHON" ] || PYTHON="$(command -v python3)"
GIF="docs/demo.gif"
POSTER="docs/demo-poster.png"

for tool in vhs ffmpeg gifsicle; do
  command -v "$tool" >/dev/null || { echo "missing $tool" >&2; exit 1; }
done

WORKDIR=$(mktemp -d /tmp/memory-arena-demo-XXXXXX)
trap 'kill "${SERVER_PID:-}" 2>/dev/null || true; rm -rf "$WORKDIR"' EXIT
mkdir -p "$WORKDIR/stage"

echo "[build] wheel"
rm -rf dist
"$PYTHON" -m build >/dev/null
WHEEL=$(ls dist/memory_arena-*-py3-none-any.whl)

echo "[venv] install $WHEEL"
python3 -m venv "$WORKDIR/venv"
"$WORKDIR/venv/bin/pip" -q install "$REPO/$WHEEL"
VENV_BIN="$WORKDIR/venv/bin"

echo "[terminal] vhs"
sed -e "s|__VENV_BIN__|$VENV_BIN|g" -e "s|__WORKDIR__|$WORKDIR|g" \
  docs/demo.tape > "$WORKDIR/demo.tape"
( cd "$WORKDIR" && vhs "$WORKDIR/demo.tape" >/dev/null )

echo "[server] start the same wheel for the browser beats"
(
  cd "$WORKDIR/stage"
  env -u ANTHROPIC_API_KEY -u OPENAI_API_KEY -u MEM_ARENA_RESULTS_PATH \
      -u MEM_ARENA_DATASETS_PATH BROWSER=true \
      "$VENV_BIN/memory-arena" demo --port 8823 > "$WORKDIR/server.log" 2>&1 &
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

echo "[browser] playwright"
"$PYTHON" scripts/record_browser_demo.py --base "http://127.0.0.1:$PORT" --out "$WORKDIR/rec"
kill "$SERVER_PID" 2>/dev/null || true

echo "[compose] terminal + browser at 960x540, 10 fps"
FILTER="scale=960:540:force_original_aspect_ratio=decrease,pad=960:540:(ow-iw)/2:(oh-ih)/2:color=0x1c1f24,fps=10,setsar=1"
ffmpeg -y -loglevel error -i "$WORKDIR/terminal.mp4" -vf "$FILTER" -an "$WORKDIR/a.mp4"
ffmpeg -y -loglevel error -i "$WORKDIR/rec/browser.webm" -vf "$FILTER" -an "$WORKDIR/b.mp4"
# Concat by filter, not by stream copy. The two sources come from different
# encoders, and a copied concat produces a stream that palettegen rejects.
ffmpeg -y -loglevel error -i "$WORKDIR/a.mp4" -i "$WORKDIR/b.mp4" \
  -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0[v]" -map "[v]" \
  -pix_fmt yuv420p -r 10 "$WORKDIR/full.mp4"

echo "[gif] palette pass"
ffmpeg -y -loglevel error -i "$WORKDIR/full.mp4" \
  -vf "fps=10,palettegen=max_colors=128" "$WORKDIR/palette.png"
ffmpeg -y -loglevel error -i "$WORKDIR/full.mp4" -i "$WORKDIR/palette.png" \
  -filter_complex "[0:v]fps=10[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3" \
  "$WORKDIR/raw.gif"
gifsicle -O3 --lossy=70 --colors 128 "$WORKDIR/raw.gif" -o "$GIF"

echo "[poster] first browser frame"
ffmpeg -y -loglevel error -ss 0.5 -i "$WORKDIR/b.mp4" -frames:v 1 "$POSTER"

DURATION=$("$PYTHON" -c "
import subprocess,sys
out=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0','$WORKDIR/full.mp4'],capture_output=True,text=True).stdout.strip()
print(out)")
echo
echo "GIF:      $GIF  ($(du -h "$GIF" | cut -f1), ${DURATION}s)"
echo "Poster:   $POSTER"
