#!/usr/bin/env python3
"""Build dist/framework_blueprint_renderers.zip: the runnable CPU renderer (run.py asks laptop / width / aspect / fps) with the chosen laptops' scenes.
usage: package.py [laptop ...]      (default: all laptops).  Needs every selected laptop's scene.blend (bake with build_scene.py or rebuild_cad.py)."""
import os, sys, shutil, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import laptops
REPO = laptops.REPO; slugs = [laptops.resolve(a)[0] for a in sys.argv[1:]] or laptops.available()
RUNTIME = ["laptops.py", "fwconfig.py", "compose.py", "render_frames.py"]
pkg = os.path.join(REPO, "dist", "framework_blueprint_renderers"); shutil.rmtree(pkg, ignore_errors=True)
os.makedirs(os.path.join(pkg, "scripts")); shutil.copytree(os.path.join(REPO, "fonts"), os.path.join(pkg, "fonts"))
for f in RUNTIME: shutil.copy(os.path.join(REPO, "scripts", f), os.path.join(pkg, "scripts", f))
for f in ("run.py", "requirements.txt", "LICENSE", "NOTICE.md"): shutil.copy(os.path.join(REPO, f), os.path.join(pkg, f))
sources = []
for slug in slugs:
    _, ldir = laptops.resolve(slug); dst = os.path.join(pkg, os.path.basename(ldir)); os.makedirs(os.path.join(dst, "cad"))
    if not os.path.exists(os.path.join(ldir, "scene.blend")): sys.exit(f"{slug}: scene.blend missing - bake it first (FW_LAPTOP={slug} blender -b --python scripts/build_scene.py)")
    for f in ("scene.blend", "laptop.py"): shutil.copy(os.path.join(ldir, f), os.path.join(dst, f))
    for f in ("groups.json", "logo_loops.json"): shutil.copy(os.path.join(ldir, "cad", f), os.path.join(dst, "cad", f))
    m = laptops.load_module(ldir); sources.append(f"### Framework {m.TITLE.title()}\n{m.SOURCES_MD}\n")
open(os.path.join(pkg, "README.md"), "w").write(f"""# Framework laptops - blueprint exploded-view videos

Geometry is baked into each laptop's `scene.blend` (official Framework CAD, see Sources). Rendering is CPU Cycles in Blender.

## Run
    pip install -r requirements.txt      # numpy pillow scipy skia-python
    python run.py                        # interactive: laptop model, pixel width, aspect ratio (16:9 or 3:2), frame rate

Needs Blender 4.x (found automatically, or pass `--blender <path>`) and ffmpeg on PATH.

Questions asked: 0) laptop model  1) pixel width (320-8192, default 1920)  2) aspect ratio: 16:9 or 3:2  3) frame rate in Hz (default 30).
Height follows from width + aspect ratio (e.g. 1920 / 16:9 -> 1920x1080, 1920 / 3:2 -> 1920x1280).

Skip the questions:  `python run.py --laptop {slugs[0]} --width 1920 --aspect 3:2 --fps 60 --yes`
Idle time: the animation stands still three times (closed, opened, exploded with labels). Add extra seconds to any of them with `--idle-closed S`, `--idle-open S`, `--idle-exploded S` (default 0 = standard timing; the video gets that much longer). The interactive mode asks for them too.
Only images: `--stills` exports 3 PNGs (closed, opened, exploded) to `out/` and no video (no frame rate or idle questions).
Other flags: `--blender PATH`, `--jobs N` (parallel overlay compositing), `--only 1,271` (render just those frames, no video - quick test).

The animation is 18 s long by default and loops seamlessly (starts and ends closed): frames = 18 x fps. Any frame rate works (the animation keyed at 30 fps in the scene is sampled between keys).
Frames are kept in `render/<laptop>_<W>x<H>_<fps>_<scene id>/` (the scene id is printed at start): a stopped run resumes, but frames rendered from an older build are never reused.
Output: `out/<laptop>_blueprint_<W>x<H>_<fps>.mp4`, or with `--stills` `out/<laptop>_blueprint_<W>x<H>_{closed,open,exploded}.png`.

## Licensing
Unofficial fan project, not affiliated with or endorsed by Framework Computer Inc; "Framework" and the gear logo are its trademarks. Code: MIT (`LICENSE`). The CAD and everything rendered from it: CC BY 4.0, adapted from Framework's official CAD, changes listed in `NOTICE.md`. Fonts: SIL OFL (`fonts/`). The footer of every video and image carries the source, the licence and the disclaimer.

## Sources (Framework Computer, CC BY 4.0, github.com/FrameworkComputer)
""" + "\n".join(sources))
zp = os.path.join(REPO, "dist", "framework_blueprint_renderers.zip")
if os.path.exists(zp): os.remove(zp)
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for dp, _, fs in os.walk(pkg):
        for f in fs: z.write(os.path.join(dp, f), os.path.relpath(os.path.join(dp, f), os.path.join(REPO, "dist")))
print(zp, round(os.path.getsize(zp) / 1e6, 1), "MB  (laptops:", ", ".join(slugs) + ")")
