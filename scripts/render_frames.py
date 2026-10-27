# blender -b <laptop dir>/scene.blend --python scripts/render_frames.py -- OUTDIR FRAME [FRAME...]   (1-based output frames)
# env: FW_SAMPLES (Cycles samples), FW_FPS (output frame rate, default 30), FW_RES = WIDTHxHEIGHT (default: what the .blend says)
# pass A (lines, fill = holdout) -> OUTDIR/a/fNNNN.png ; pass B (glowing fill) -> OUTDIR/b/fNNNN.png ; matrices -> OUTDIR/fNNNN.json
import bpy, sys, json, os, math
argv = sys.argv[sys.argv.index("--") + 1:]; out = argv[0]; frames = [int(a) for a in argv[1:]]
sc = bpy.context.scene
fps = float(os.environ.get("FW_FPS", sc.render.fps)); baked = sc.render.fps          # the animation is keyed per 1/baked s; other rates sample it between keys
if os.environ.get("FW_RES"): sc.render.resolution_x, sc.render.resolution_y = (int(v) for v in os.environ["FW_RES"].split("x"))
if os.environ.get("FW_SAMPLES"): sc.cycles.samples = int(os.environ["FW_SAMPLES"])
sc.camera.data.sensor_fit = "HORIZONTAL"                     # ortho width is the horizontal extent for every aspect ratio
for sub in "ab": os.makedirs(f"{out}/{sub}", exist_ok=True)
def setpass(v):
    for m in ("FILL", "LINE"): bpy.data.materials[m].node_tree.nodes["PASS"].outputs[0].default_value = v
for f in frames:
    bf = (f - 1) / fps * baked + 1; fi = math.floor(bf); sc.frame_set(fi, subframe=bf - fi)
    for sub, v in (("a", 1.0), ("b", 0.0)):
        setpass(v); sc.render.filepath = f"{out}/{sub}/f{f:04d}.png"; bpy.ops.render.render(write_still=True)
    cam = sc.camera
    d = {"cam": [list(r) for r in cam.matrix_world], "ortho": cam.data.ortho_scale, "shift": cam.data.shift_x,
         "groups": {o.name[2:]: [list(r) for r in o.matrix_world] for o in bpy.data.objects if o.name.startswith("G_")}}
    json.dump(d, open(f"{out}/f{f:04d}.json", "w"))
