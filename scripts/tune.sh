#!/bin/bash
# quick stills + contact sheet while tuning a laptop:  scripts/tune.sh <laptop> "frame frame ..." [sheet name]     (default 854x480; FW_RES=1280x720 for bigger)
# -> render/<slug>_tune/comp/cNNNN.png and render/<slug>_tune/<name>.png. Output frame n is at t = (n-1)/30 s.
set -e; cd "$(dirname "$0")/.."; PY=${PYTHON:-$([ -x venv/bin/python ] && echo venv/bin/python || echo python3)}; BLENDER=${BLENDER:-blender}
export FW_LAPTOP=${1:?usage: scripts/tune.sh <laptop> "frames" [name]}
SLUG=$($PY -c "import sys; sys.path.insert(0,'scripts'); import laptops; print(laptops.current()[0])")
export FW_RES=${FW_RES:-854x480} FW_FPS=30 FW_SAMPLES=${FW_SAMPLES:-12} FW_SCENE_OUT=render/${SLUG}_tune/scene.blend
D=render/${SLUG}_tune; rm -rf $D; mkdir -p $D/comp
$BLENDER -b --python scripts/build_scene.py 2>&1 | grep -E "instances|rror|Trace|unclass" || true
$BLENDER -b $FW_SCENE_OUT --python scripts/render_frames.py -- $D $2 2>&1 | grep -E "rror" || true
$PY scripts/compose.py $D $D/comp $2 2>&1 | grep -v Fontconfig || true
$PY - "$D" "$2" "${3:-tune}" <<'EOF2'
import sys; from PIL import Image
d=sys.argv[1]; fs=[int(x) for x in sys.argv[2].split()]; ims=[Image.open(f"{d}/comp/c{f:04d}.png") for f in fs]; w,h=ims[0].size
cols=min(4,len(fs)); rows=(len(fs)+cols-1)//cols; sh=Image.new("RGB",(w*cols,h*rows))
for i,im in enumerate(ims): sh.paste(im,((i%cols)*w,(i//cols)*h))
sh.resize((1900,int(1900*h*rows/(w*cols)))).save(f"{d}/{sys.argv[3]}.png"); print("sheet:", f"{d}/{sys.argv[3]}.png")
EOF2
