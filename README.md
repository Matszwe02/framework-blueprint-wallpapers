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

### Idle time and still images

The animation stands still in three places: the closed laptop, the opened laptop and the exploded view with labels. By default each holds for the standard time. Add extra seconds to any of them (the video gets longer; the loop stays seamless):

```
python run.py --laptop fw13 --idle-closed 2 --idle-open 1 --idle-exploded 5
```

To get only images, with no video, use `--stills`. It writes three PNGs (closed, opened, exploded) to `out/` and ignores the frame rate and idle options:

```
python run.py --laptop fw13 --stills --width 3840 --yes
```

The interactive mode asks for all of this too.

A full 1080p render takes roughly 35-45 minutes per laptop on a CPU (about 4 s per frame, 540 frames). Frames are cached in `render/`, so a stopped run resumes where it left off. For a quick preview, use `--width 854`.

## Automatic releases

A GitHub Action ([.github/workflows/wallpapers.yml](.github/workflows/wallpapers.yml)) renders every laptop on each push (16:9 and 3:2: a 1920 px, 30 fps video plus three 4K stills) and uploads the files to the `wallpapers` release, replacing the previous ones. Rendering takes about an hour per laptop and aspect ratio; the eight jobs run in parallel.

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

## Licensing

- Code: MIT ([LICENSE](LICENSE)).
- Framework's CAD, and the models, videos and images made from it: CC BY 4.0, credited to Framework Computer Inc with the changes listed in [NOTICE.md](NOTICE.md). Every video and still carries the source and licence in its footer.
- Fonts: SIL Open Font License, see `fonts/`.
- "Framework" and the gear logo are trademarks of Framework Computer Inc. This is an unofficial project, and the footer of every video and image says so.
