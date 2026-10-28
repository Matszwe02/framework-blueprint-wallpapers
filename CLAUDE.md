# Framework Blueprint Wallpapers

Renders a stylised, seamlessly looping 18 s exploded-view video of a Framework laptop from **Framework's official CAD** (github.com/FrameworkComputer, CC BY 4.0). The laptop starts closed, opens, explodes into labelled layers, re-assembles and closes. Look: navy blueprint grid, glassy translucent fill with a rim glow, hidden-line white CAD edges, dimension lines, callout labels, a scrub bar and the Framework gear logo.

Laptops: **Framework 13 Pro** (`fw13pro`), **13** (`fw13`), **12** (`fw12`, 360° convertible), **16** (`fw16`, Graphics Module). All videos must look identical apart from the laptop model and per-laptop tuning.

## Layout

```
CLAUDE.md
run.py                       interactive renderer (asks laptop, pixel width, 16:9 or 3:2, fps) — also the CLI
requirements.txt             runtime deps (numpy pillow scipy skia-python)
requirements-dev.txt         + CAD/authoring deps (cadquery trimesh rtree shapely ezdxf mapbox-earcut matplotlib)
fonts/                       Rajdhani, Share Tech Mono
scripts/                     ALL shared code (there is one copy; laptops never carry code of their own except tools/)
fwXX_blueprint_renderer/     one per laptop (fw13pro, fw13, fw12, fw16):
    laptop.py                the laptop's whole configuration (see schema below)
    scene.blend              the baked Blender scene (animation keyed at 30 fps)
    cad/                     derived meshes (*.npz/*.json/*_edges.npz), groups.json, logo_loops.json; downloaded source CAD (git-ignored)
    tools/                   optional laptop-specific generators (mainboard placement, keycaps, battery estimate)
```

Generated and git-ignored: `render/` (frames; `run.py` deletes them when a render finishes), `out/` (videos), `venv/`. Source CAD (`cad/*.stp|*.dxf|*.zip`) is git-ignored and re-downloadable.

## Golden rules (user preferences — follow them)

1. **Previews are 480p (854x480) @ 30 fps** until the user explicitly confirms a final render. 1080p is slow on a CPU (~4 s/frame, 540 frames, ~35-45 min per laptop). Never start a 1080p render unprompted. Default final = 1920x1080 @ 30 fps.
2. **No process/provenance wording on screen.** The footer is the source line + `"{used} PARTS"` (bottom right: the repo URL, `REPO` in `compose.py`); labels must not say "estimate", "reconstructed", "from X CAD", etc. The one required exception is the licensing/trademark disclaimer the footer carries in every video and still (`DISCLAIMER` in `compose.py`, next to the source + CC BY text; see `NOTICE.md`) - keep it. Put caveats in `NOTICE.md`/`README.md` and tell the user in your reply.
3. **Calm motion:** three fully still holds (closed, lid open, exploded); the camera moves only with the action. Labels sit in **fixed slots** (never swap places while the camera moves) and fade in at slightly randomised times.
4. **One shared codebase.** Laptops differ only through `fwXX_blueprint_renderer/`; never copy code into a laptop dir (except its own `tools/`). The CLI must stay **CPU-only** (no GPU code).
5. Verify visually: render stills and look at them before claiming something works. Report limitations honestly (inferred placements, estimates).
6. Frame n of a video is at t = (n-1)/fps seconds (the user refers to problems by frame number, e.g. "frame 217").

## Running

```
python run.py                                                    # TUI: laptop -> width -> aspect -> colour -> output -> fps -> speed -> idle -> confirm
python run.py --laptop fw16 --width 1920 --aspect 3:2 --fps 60 --yes
python run.py --laptop fw12 --only 1,271 --yes                   # render just those frames, no video (smoke test)
```
`--speed X` / `--label-speed X` (0.25-4, 1 = original) scale the laptop transition / the label fades (`fwconfig.SPEED`, `LABEL_SPEED`; base animation takes 18/X s; the frame cache and `comp_*` folder names get `_speed<X>` / `_label<X>` suffixes).

Idle time: `--idle-closed S --idle-open S --idle-exploded S` add extra seconds to the three still holds (default 0; the open idle is applied twice, before and after the explode, so video = 18 s / speed + closed + 2 x open + exploded). `--stills` renders only 3 images (closed, open, exploded; standard timing, 30 fps timeline) to `out/<slug>_blueprint_<W>x<H>_{closed,open,exploded}.png`, no video. Mechanism: `run.py` passes `FW_IDLE="c,o,e"`; `fwconfig.warp(t)` maps output time to the baked 18 s timeline by freezing it at the middle of each hold (`hold_mids()`; labels are fully shown at the exploded one), and `render_frames.py`/`compose.py` both sample through `warp`. `scene.blend` is unaffected (always the base 18 s, `BASE_DURATION`). The frame cache folder gets an `_idle<c>-<o>-<e>` suffix, since idle time changes what a frame number shows.

Colour: `--hue NAME|DEG` (blue, purple/violet, magenta, pink, red, orange, yellow, green, teal, cyan, or degrees rotated from the original blue; default 0) and `--saturation X` (1 = original, 0 = grey, max 3). `run.py` passes `FW_HUE`/`FW_SAT`; `compose.py` applies `grade()` (YIQ hue rotation + chroma scale) to the finished composite, so Blender frames are shared between colours (only the `comp_*` folder, which gets an `_h<deg>_s<sat>` suffix, and the output name differ). Defaults leave the output byte-identical.

`run.py` restarts Blender (keeping finished frames) when it crashes mid-render, giving up only if a run finishes no frame, and prints Blender's crash report on failure. Needs Blender 4.x (auto-detected or `--blender PATH`; developed on 4.0.2), ffmpeg on PATH, `pip install -r requirements.txt`. Frames are cached in `render/<slug>_<W>x<H>_<fps>_<scene id>/`: a stopped run resumes, and frames from an older build (different scene id) are never reused. If a laptop's `scene.blend` is missing, `run.py` bakes it from `cad/`. Output: `out/<slug>_blueprint_<W>x<H>_<fps>.mp4`. `run.py` renders from the tracked `scene.blend`, whose edge-line ribbons are baked for 1920 px width.

Dev scripts (all take the laptop slug; honour `PYTHON=` and `BLENDER=` env overrides, otherwise use `venv/bin/python` if present, else `python3`):
- `scripts/tune.sh <laptop> "110 271" [name]` — stills at 854x480 (`FW_RES=1280x720` for bigger) + a contact sheet at `render/<slug>_tune/<name>.png`. Use it for every visual check.
- `scripts/preview.sh <laptop> [frames...]` — bakes a scene for 854 px (so line weight matches) and renders the 480p30 preview video to `out/<slug>_blueprint_preview.mp4` (~6-10 min). Run it detached (`nohup`) and wait; don't poll.
- `scripts/fetch_cad.py <laptop>` downloads the official source CAD (`CAD_FILES` in `laptop.py`); `scripts/rebuild_cad.py <laptop> [--no-scene]` runs the laptop's `REBUILD` recipe (STEP -> npz meshes -> feature edges -> tools -> logo) and bakes `scene.blend`. Needs `requirements-dev.txt` (`python3 -m venv venv && venv/bin/pip install -r requirements-dev.txt`).
- Manual scene bake: `FW_LAPTOP=fw16 blender -b --python scripts/build_scene.py` (run from the repo root). Inspect CAD with `scripts/tree.py`, `scripts/inspect_parts.py`, `scripts/hinge_axis.py` (finds hinge pivots from cylinder faces).

Environment variables read by the scripts: `FW_LAPTOP` (slug or dir name; required by every script except `run.py`/`fetch_cad.py`/`rebuild_cad.py`, which take it as an argument), `FW_RES` (`WxH`, default 1920x1080), `FW_FPS` (default 30), `FW_IDLE` (`closed,open,exploded` extra hold seconds, default `0,0,0`), `FW_SPEED` / `FW_LABEL_SPEED` (laptop / label animation speed, 1 = original, 0.25-4), `FW_HUE` / `FW_SAT` (colour grade), `FW_SAMPLES` (Cycles samples, default 24), `FW_SHRINK` (fill inset, default 0.03 mm), `FW_SCENE_OUT` (where `build_scene.py` writes the .blend; default `<laptop dir>/scene.blend`).

## Pipeline and architecture

```
source CAD --export_parts.py--> cad/<src>.npz+json (tessellated meshes + instance matrices)
           --extract_edges.py-> cad/<src>_edges.npz (creases >38°, boundaries)       --logo_path.py--> cad/logo_loops.json
laptop.py + cad/* --build_scene.py (Blender)--> scene.blend + cad/groups.json
scene.blend --render_frames.py (Blender, 2 Cycles passes/frame)--> render/.../a|b/fNNNN.png + fNNNN.json
render/... --compose.py (Skia overlay)--> cNNNN.png --ffmpeg--> mp4
```

- **Two passes per frame:** `a` = hidden-line edge pass (the fill is a holdout, edges are thin emissive ribbons built in `build_scene.py`), `b` = glowing facing-ratio fill. `compose.py` composites BG grid + glow + both passes + the 2D overlay (dimensions, callouts, title, scrub bar, footer). The fill is sunk `FW_SHRINK` mm under the ribbons to avoid z-fighting.
- **Timeline is sampled, not authored:** `scripts/fwconfig.py` defines timeline/camera/explode (pure python, shared by Blender and compose). `build_scene.py` bakes keys at 30 fps; `render_frames.py` samples any output fps between them. Constants `T_OPEN0,T_OPEN1,T_DIMS,T_EXPLODE,T_HOLD,T_COLLAPSE,T_CLOSE0,T_CLOSE1 = 1.5,3.2,4.8,7.6,11.6,14.2,15.4,17.0` (holds: closed 0-1.5, open 3.2-4.8, exploded 7.6-11.6); `laptop.TIMING` can retime them. Explode is staggered so outer layers lead out and trail back (layers never pass through each other). Camera = `POSES` waypoints (`closed`/`open`/`exploded`, optional `via`) with smootherstep blends.
- **Coordinates:** CAD frame x = width, y = thickness (keyboard deck ≈ 0, D-cover negative, lid positive when closed), z = depth (z = 0 at the hinge/back edge, front at +z). Blender = `(x, -z, y)` (`fwconfig.cad2bl`). Lid hinges about `HINGE_CAD = (cad_y, cad_z)`; explode offsets act along the lid/base normal.
- **Labels:** fixed slots per side (`LEFT`/`RIGHT` in `laptop.py`), ordered by each anchor's screen-y at mid-hold (`hold_y` in `groups.json`). Titles come from the `GROUPS` labels, id/detail lines from `LABEL_TEXT`. **Group labels are baked into `cad/groups.json` at scene-build time — after editing `GROUPS` labels, re-bake the scene**, otherwise the old text stays on screen. Dimension lines fade out when the explode starts. Output width only sets the layout scale (`S = W/1280`), so any width/aspect keeps the proportions; 3:2 just adds vertical space.
- `scripts/laptops.py` finds the `*_blueprint_renderer` dirs and resolves `FW_LAPTOP`; `fwconfig.py` imports the chosen `laptop.py`.

## `laptop.py` schema

`SLUG, TITLE, WATERMARK, SOURCE_LINE, NOTE_LINE` (footer; keep `"{used} PARTS"`); `SOURCES` (key -> mesh base name in `cad/`); `USE_ALL` (source keys whose every instance is used); `FORCE_GROUP` (source key -> group, bypassing regexes); `LOGO_SOURCE/LOGO_PART`; `HINGE_CAD`, `LID_ANGLE` (default 105); `extra_instances(SRC)` (synthesised instances, e.g. extra cards); `DROP` (regex of duplicate/variant parts); `PATH_RULES`; `GROUPS` (id, label, `"lid"|"base"|"link"`, explode offset mm, name regex — **every instance must match a group or `DROP`, else `ValueError: unclassified part`**); `GROUP_SLIDE` (`gid: (dx_cad, dz_cad, trigger_gid)`, e.g. cards slide out after the D-cover has dropped); optional `INTERNAL` (groups hidden until they have moved apart because they show through key gaps), `HINGE2_CAD`, `FLIP`, `TIMING`; `POSES`; `LEFT/RIGHT`; `LABEL_TEXT`; `SOURCES_MD` (source list text; no longer used by any script since `package.py` was removed); `CAD_FILES` and `REBUILD` (fetch/rebuild recipes).

## Per-laptop facts and caveats

**13 Pro** (`fw13pro`): its CAD is exterior-only (no cards, battery, mainboard). Cards = Laptop 13 USB-C card model in all four slots (`extra_instances`; left side rotated 180°; slide ±60 mm). Battery = official Laptop 13 battery STEP (same chassis coordinates). **Mainboard = the community 3D model 'Framework Mainboard v2' by ManelTo (Printables, CC BY 4.0; not Framework's CAD)** (`cad/mainboard.step`, committed because it is not on Framework's GitHub and `fetch_cad.py` cannot download it; `tools/mb_mesh.py` tessellates it, re-orients it and places it: X centred, z-centre 63.4 between the card brackets, y -7.2 on the card bodies); **placement is inferred**. Mainboard has no label. Logo from the lid logo part `POC_P_13_LOGO_1`.

**13** (`fw13`): Laptop 13 system CAD (shell, bezel, keyboard, hinge frame, four cards USB-C/SD/USB-A/HDMI — two per side, slide ±60 mm). Same battery and mainboard as the 13 Pro.

**12** (`fw12`): system, battery and mainboard STEPs are official 3D and share the chassis frame. Dual-axis hinge modelled as two pivots (lid `HINGE_CAD=(3.1,3.55)`, base `HINGE2_CAD=(-7.2,3.55)`, read from the hinge covers' cylinder faces): the hinge covers (group side `"link"`) turn **half** the lid angle about the base pivot while the lid turns the other half (`LID_ANGLE=360`). **One continuous opening** (user requirement): as the lid rotates up, the whole base rotates the opposite way about the hinge axis (`FLIP` with `follow_lid=True`), ending in tablet mode, screen up, seen from a higher camera; no separate flip stage. The lid layers fan upward in the explode. The CAD has **no keycaps** (the input cover is one solid with 76 empty openings): `tools/keys_from_openings.py` rasterises the cover, finds key-sized holes and extrudes inset rounded keycaps (group `KEYS`, source `keysparts`). `INTERNAL = [C_INNER, MAINBOARD, BATTERY]`.

**16** (`fw16`): the Graphics Module assembly `Framework_16_all_DIS_asm_0408.stp` (unzipped from `cad/system_gpu.zip`), the official 3D mainboard and hinge STEPs; pivot `HINGE_CAD=(1.0,4.1)`. Exporting the system STEP is slow (~2.5 min; keycap parts have ~340k triangles each; edge extraction is vectorised). `DROP` removes duplicate keyboard/numpad variants **and `EXPANSION_CARD_COV1`**, the six dummy slot-cover plates in the CAD (they previously showed up as "double brackets" beside the real cards). Cards: six Laptop 13 card models (USB-C/SD/USB-C right, USB-A/HDMI/USB-A left) at the mainboard's three receptacles per side (pitch 34.9 mm), sliding ±95 mm; the graphics module slides out of the rear. **Battery: Framework publishes no 16 battery CAD or dimensions (only 85 Wh, 4S1P).** `tools/battery_estimate.py` makes four cells (82 x 66 x 7.8 mm) sized to the free pocket in the D-cover (measured by ray-casting the official CAD) — an **estimate**; disclose it to the user, never on screen. The faint outlines at the left/right edges of the 16 keyboard are the blank side-spacer modules in the CAD (the keyboard is complete).

## CI (`.github/workflows/wallpapers.yml`)

On every push to master/main (and manually): a matrix job per laptop x aspect (8 jobs, the official Blender 4.0.2 tarball + apt ffmpeg, CPU; Ubuntu's apt blender crashes in libembree4 `rtcSetSharedGeometryBuffer`, so don't use it in CI) renders 1920 px @ 30 fps video, then `--stills` at 3840 px (4K; its own 3 frames, the video's cache is at a different size), and uploads `out/*`. A final job replaces the assets of the single `wallpapers` release (created on first run; stale assets deleted, same-named ones overwritten). A newer push cancels a running render. This is the explicit exception to golden rule 1: the user asked for 1080p30 on every commit. Not tested on GitHub yet (YAML only parsed locally).

## Licensing

Code is MIT (`LICENSE`). Framework's CAD (Laptop 13/12/16 repos; the 13 Pro files are in the 13 repo) is CC BY 4.0, so the derived `cad/` meshes, scenes, videos and stills need attribution, the licence link and a statement of changes - all in `NOTICE.md` (keep its table in step when `CAD_FILES` changes) and the footer `SOURCE_LINE` (the release has no notes). Framework's name and gear logo are trademarks the CAD licence does not cover, hence the on-screen "unofficial" disclaimer and `NOTICE.md`. Fonts are OFL; the licence texts sit in `fonts/`. Not legal advice - Framework's brand guidelines were not reviewed.

## Gotchas

- Never `pkill -f <pattern>` from a Bash call whose own command line contains that pattern — it kills your shell. Use `ps aux | grep … | awk '{print $2}' | xargs kill`.
- `python -I` removes the script directory from `sys.path`; the scripts insert their own paths, so call them as `python scripts/x.py` with the repo root as cwd.
- Blender scripts expect the repo root as cwd (`build_scene.py` imports `scripts/`).
- `fw16/scene.blend` is 99.9 MB — right under GitHub's 100 MB per-file limit; use Git LFS for the scenes if it grows.
- Source CAD URL pattern: `https://github.com/FrameworkComputer/<repo>/raw/main/<path>` (URL-encode spaces); the exact files are listed in each `laptop.py` `CAD_FILES`. Framework's Laptop 13 repo has no 3D mainboard (only 2D drawings) and no 3D battery for the 16.

## Status

Four laptops, all scenes baked; the 13 Pro has been rendered at 1080p30, the others only as 480p30 previews. Possible next steps if asked: 1080p30 finals for fw13/fw12/fw16, tighter framing for 3:2.
