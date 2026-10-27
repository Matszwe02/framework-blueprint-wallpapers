# Framework Blueprint Wallpapers

Seamlessly looping, 18-second exploded-view "blueprint" videos of Framework laptops, rendered from [Framework's official CAD](https://github.com/FrameworkComputer) (CC BY 4.0). Use them as animated wallpapers.

Each video starts with the laptop closed. The lid opens, the machine explodes into labelled layers, re-assembles and closes. The look is a navy blueprint grid with a glassy translucent fill and rim glow, white hidden-line CAD edges, dimension lines, callout labels, a scrub bar and the Framework logo.

## Laptops

| Slug | Laptop |
|------|--------|
| `fw13pro` | Framework Laptop 13 Pro |
| `fw13` | Framework Laptop 13 |
| `fw12` | Framework Laptop 12 (360° convertible) |
| `fw16` | Framework Laptop 16 (with Graphics Module) |

## Requirements

- Python 3 with `pip install -r requirements.txt` (numpy, pillow, scipy, skia-python)
- [Blender](https://www.blender.org/) 4.x (auto-detected, or pass `--blender PATH`; developed on 4.0.2)
- `ffmpeg` on your `PATH`

Rendering is CPU-only.

## Usage

```
python run.py                                                    # interactive: laptop, width, aspect, fps
python run.py --laptop fw16 --width 1920 --aspect 3:2 --fps 60 --yes
python run.py --laptop fw12 --only 1,271 --yes                   # render only those frames (smoke test)
```

Supported aspect ratios are 16:9 and 3:2. The default is 1920x1080 at 30 fps. Videos are written to `out/<slug>_blueprint_<W>x<H>_<fps>.mp4`.

A full 1080p render takes roughly 35-45 minutes per laptop on a CPU (about 4 s per frame, 540 frames). Frames are cached in `render/`, so a stopped run resumes where it left off. For a quick preview, use `--width 854`.

## Repository layout

```
run.py                       renderer (interactive and CLI)
scripts/                     shared code: scene baking, frame rendering, compositing, packaging
fwXX_blueprint_renderer/     per-laptop config (laptop.py), baked scene.blend, derived CAD, optional tools/
fonts/                       Rajdhani, Share Tech Mono
```

All laptops share one codebase and differ only through their `fwXX_blueprint_renderer/` folder. See [CLAUDE.md](CLAUDE.md) for the pipeline, the `laptop.py` schema, development scripts and per-laptop caveats.

## Notes

- The 13 Pro CAD is exterior-only. Its cards, battery and mainboard are taken from the Laptop 13 CAD, and the mainboard is extruded from the official 2D outline, so its placement is inferred.
- Framework publishes no 3D battery model for the Laptop 16. Its battery is an estimate sized to the free pocket in the chassis.

## Credits

3D models come from Framework's official CAD repositories on GitHub, licensed CC BY 4.0. This is an unofficial fan project, not affiliated with or endorsed by Framework Computer Inc.
