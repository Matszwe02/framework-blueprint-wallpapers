#!/bin/bash
# 480p30 preview video of one laptop:  scripts/preview.sh <laptop> [frames...]     (default: all 540 frames)  ->  out/<slug>_blueprint_preview.mp4
# Bakes a scene for 854 px width (so the edge lines keep their pixel weight), renders it into render/<slug>_preview/ and encodes. Needs the dev requirements + Blender + ffmpeg.
set -e; cd "$(dirname "$0")/.."; PY=${PYTHON:-$([ -x venv/bin/python ] && echo venv/bin/python || echo python3)}; BLENDER=${BLENDER:-blender}
export FW_LAPTOP=${1:?usage: scripts/preview.sh <laptop> [frames...]}; shift || true
SLUG=$($PY -c "import sys; sys.path.insert(0,'scripts'); import laptops; print(laptops.current()[0])")
export FW_RES=854x480 FW_FPS=30 FW_SAMPLES=12 FW_SCENE_OUT=render/${SLUG}_preview/scene.blend
FRAMES=${*:-$(seq 1 540)}
mkdir -p render/${SLUG}_preview out
$BLENDER -b --python scripts/build_scene.py > render/${SLUG}_preview/build.log 2>&1
$BLENDER -b $FW_SCENE_OUT --python scripts/render_frames.py -- render/${SLUG}_preview $FRAMES > render/${SLUG}_preview/render.log 2>&1
mkdir -p render/${SLUG}_preview/comp
echo $FRAMES | tr ' ' '\n' | xargs -P ${JOBS:-4} -n 21 $PY scripts/compose.py render/${SLUG}_preview render/${SLUG}_preview/comp 2>&1 | grep -v Fontconfig || true
if [ -z "$1" ] && [ "$FRAMES" = "$(seq 1 540)" ]; then
  ffmpeg -y -v error -framerate 30 -i render/${SLUG}_preview/comp/c%04d.png -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p -movflags +faststart out/${SLUG}_blueprint_preview.mp4 && echo "done -> out/${SLUG}_blueprint_preview.mp4"
else echo "composites in render/${SLUG}_preview/comp/"; fi
