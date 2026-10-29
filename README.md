# Framework Blueprint Wallpapers

Seamlessly looping, 18-second exploded-view "blueprint" videos of Framework laptops, rendered from [Framework's official CAD](https://github.com/FrameworkComputer) (CC BY 4.0). Use them as animated wallpapers.

Each video starts with the laptop closed. The lid opens, the machine explodes into labelled layers, re-assembles and closes. The look is a navy blueprint grid with a glassy translucent fill and rim glow, white hidden-line CAD edges, dimension lines, callout labels, a scrub bar and the Framework logo.

## Examples

Exploded views, as published in the [`wallpapers` release](https://github.com/Matszwe02/framework-blueprint-wallpapers/releases/tag/wallpapers) (4K stills):

| | |
|---|---|
| <img src="https://github.com/Matszwe02/framework-blueprint-wallpapers/releases/download/wallpapers/fw13pro_blueprint_3840x2160_exploded.png" alt="Framework Laptop 13 Pro, exploded view"><br>Framework Laptop 13 Pro | <img src="https://github.com/Matszwe02/framework-blueprint-wallpapers/releases/download/wallpapers/fw13_blueprint_3840x2160_exploded.png" alt="Framework Laptop 13, exploded view"><br>Framework Laptop 13 |
| <img src="https://github.com/Matszwe02/framework-blueprint-wallpapers/releases/download/wallpapers/fw12_blueprint_3840x2160_exploded.png" alt="Framework Laptop 12, exploded view"><br>Framework Laptop 12 | <img src="https://github.com/Matszwe02/framework-blueprint-wallpapers/releases/download/wallpapers/fw16_blueprint_3840x2160_exploded.png" alt="Framework Laptop 16, exploded view"><br>Framework Laptop 16 |

Every laptop is also available as a looping 1920 px video (16:9 and 3:2) and as closed, open and exploded stills:

| Laptop | Video (16:9) | Video (3:2) |
|--------|--------------|-------------|
| 13 Pro | [mp4](https://github.com/Matszwe02/framework-blueprint-wallpapers/releases/download/wallpapers/fw13pro_blueprint_1920x1080_30.mp4) | [mp4](https://github.com/Matszwe02/framework-blueprint-wallpapers/releases/download/wallpapers/fw13pro_blueprint_1920x1280_30.mp4) |
| 13 | [mp4](https://github.com/Matszwe02/framework-blueprint-wallpapers/releases/download/wallpapers/fw13_blueprint_1920x1080_30.mp4) | [mp4](https://github.com/Matszwe02/framework-blueprint-wallpapers/releases/download/wallpapers/fw13_blueprint_1920x1280_30.mp4) |
| 12 | [mp4](https://github.com/Matszwe02/framework-blueprint-wallpapers/releases/download/wallpapers/fw12_blueprint_1920x1080_30.mp4) | [mp4](https://github.com/Matszwe02/framework-blueprint-wallpapers/releases/download/wallpapers/fw12_blueprint_1920x1280_30.mp4) |
| 16 | [mp4](https://github.com/Matszwe02/framework-blueprint-wallpapers/releases/download/wallpapers/fw16_blueprint_1920x1080_30.mp4) | [mp4](https://github.com/Matszwe02/framework-blueprint-wallpapers/releases/download/wallpapers/fw16_blueprint_1920x1280_30.mp4) |

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

The animation stands still in three places: the closed laptop, the opened laptop and the exploded view with labels. By default each holds for the standard time. Add extra seconds to any of them (the video gets longer; the loop stays seamless). The opened laptop is held twice, before and after the explode, and the open idle time applies to both:

```
python run.py --laptop fw13 --idle-closed 2 --idle-open 1 --idle-exploded 5
```

To get only images, with no video, use `--stills`. It writes three PNGs (closed, opened, exploded) to `out/` and ignores the frame rate and idle options:

```
python run.py --laptop fw13 --stills --width 3840 --yes
```

### Speed and colour

`--speed X` scales the laptop animation and `--label-speed X` the label fades (1 = original, 2 = twice as fast, range 0.25-4). `--hue` takes a name (blue, purple, violet, magenta, pink, red, orange, yellow, green, teal, cyan) or degrees from the original blue, and `--saturation` runs from 0 (grey) to 3 (1 = original):

```
python run.py --laptop fw12 --speed 1.5 --hue green --saturation 1.2
```

The interactive mode asks for the options above too.

A full 1080p render takes roughly 35-45 minutes per laptop on a CPU (about 4 s per frame, 540 frames). Frames are cached in `render/` while rendering, so a stopped run resumes where it left off; once the video (or stills) is written, the frames are deleted. For a quick preview, use `--width 854`.

## Automatic releases

A GitHub Action ([.github/workflows/wallpapers.yml](.github/workflows/wallpapers.yml)) renders every laptop on each push (16:9 and 3:2: a 1920 px, 30 fps video plus three 4K stills) and uploads the files to the `wallpapers` release, replacing the previous ones. Rendering takes about an hour per laptop and aspect ratio; the eight jobs run in parallel. The video is rendered at 1.5x laptop speed, 1x label speed and 2 s of extra idle time on each still hold (closed, open, exploded; the open hold counts twice), i.e. `--speed 1.5 --label-speed 1 --idle-closed 2 --idle-open 2 --idle-exploded 2`.

## Repository layout

```
run.py                       renderer (interactive and CLI)
scripts/                     shared code: scene baking, frame rendering, compositing, CAD tools
fwXX_blueprint_renderer/     per-laptop config (laptop.py), baked scene.blend, derived CAD, optional tools/
fonts/                       Rajdhani, Share Tech Mono
```

All laptops share one codebase and differ only through their `fwXX_blueprint_renderer/` folder. See [CLAUDE.md](CLAUDE.md) for the pipeline, the `laptop.py` schema, development scripts and per-laptop caveats.

## Notes

- The 13 Pro CAD is exterior-only. Its cards, battery and mainboard are taken from the Laptop 13 CAD, and the mainboard is the community 3D model 'Framework Mainboard v2' by ManelTo (CC BY 4.0), so its placement is inferred. The same board is used in the Laptop 13.
- Framework publishes no 3D battery model for the Laptop 16. Its battery is an estimate sized to the free pocket in the chassis.

## Licensing

- Code: MIT ([LICENSE](LICENSE)).
- Framework's CAD, and the models, videos and images made from it: CC BY 4.0, credited to Framework Computer Inc with the changes listed in [NOTICE.md](NOTICE.md). Every video and still carries the source, the licence and the repository URL in its footer.
- Fonts: SIL Open Font License, see `fonts/`.
- "Framework" and the gear logo are trademarks of Framework Computer Inc. This is an unofficial project, and the footer of every video and image says so.
