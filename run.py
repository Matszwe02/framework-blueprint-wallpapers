#!/usr/bin/env python3
"""Framework laptop blueprint exploded-view video - interactive renderer.

    python run.py                      # asks for the laptop model, pixel width, aspect ratio and frame rate
    python run.py --laptop fw16 --width 1920 --aspect 16:9 --fps 30 --yes      # same, no questions
    python run.py --laptop fw16 --idle-closed 2 --idle-open 1 --idle-exploded 4 ...   # hold the still poses longer (seconds added to the 18 s)
    python run.py --laptop fw16 --stills --width 3840 --yes                    # 3 PNGs (closed, open, exploded), no video

Pipeline: Blender/Cycles (two passes per frame) -> 2D overlay composite -> ffmpeg.
Needs Blender 4.x, ffmpeg on PATH and `pip install -r requirements.txt`.
Frames are kept in render/<laptop>_<W>x<H>_<fps>_<scene id>/, so an interrupted run resumes where it stopped but frames from an older build are never reused.
"""
import argparse, glob, hashlib, os, shutil, subprocess, sys
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "scripts")); import laptops
ASPECTS = {"16:9": (16, 9), "3:2": (3, 2)}
DURATION = 18.0                                                  # base animation; the idle options add to it
STILL_FPS = 30                                                   # --stills renders three frames of the 30 fps timeline
COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
def c(code, s): return f"\033[{code}m{s}\033[0m" if COLOR else s
def bold(s): return c("1", s)
def cyan(s): return c("36", s)
def dim(s): return c("2", s)

def ask(prompt, default, parse):
    while True:
        raw = input(f"  {cyan('>')} {prompt} {dim(f'[{default}]')} ").strip()
        if not raw: raw = str(default)
        try: return parse(raw)
        except ValueError as e: print(c("31", f"    {e}"))

def parse_width(s):
    w = int(s)
    if not 320 <= w <= 8192: raise ValueError("width must be between 320 and 8192 px")
    return w - (w % 2)                                           # h264 needs even dimensions

def parse_aspect(s):
    s = s.strip().lower().replace("/", ":").replace("x", ":")
    s = {"1": "16:9", "2": "3:2", "standard": "16:9", "16:9": "16:9", "3:2": "3:2"}.get(s)
    if s is None: raise ValueError("choose 1 (16:9) or 2 (3:2)")
    return s

def parse_fps(s):
    f = int(float(s.lower().replace("hz", "").replace("fps", "")))
    if not 1 <= f <= 240: raise ValueError("frame rate must be between 1 and 240")
    return f

def parse_idle(s):
    v = float(s.lower().replace("seconds", "").replace("sec", "").replace("s", "").strip() or 0)
    if not 0 <= v <= 600: raise ValueError("idle time must be between 0 and 600 seconds")
    return v

def parse_output(s):
    s = s.strip().lower()
    s = {"1": "video", "video": "video", "2": "images", "images": "images", "image": "images", "stills": "images", "3": "images"}.get(s)
    if s is None: raise ValueError("choose 1 (video) or 2 (3 images)")
    return s

HUES = {"blue": 0, "purple": 40, "violet": 40, "magenta": 80, "pink": 100, "red": 135, "orange": 170, "yellow": 195, "green": 270, "teal": 320, "cyan": 345}   # name -> hue shift in degrees from the original blue

def parse_hue(s):
    s = s.strip().lower()
    if s in HUES: return float(HUES[s])
    try: return float(s.replace("deg", "").replace("°", "")) % 360
    except ValueError: raise ValueError("hue: a colour name (" + ", ".join(HUES) + ") or a shift in degrees")

def parse_sat(s):
    v = float(s.strip().rstrip("%")) / (100 if s.strip().endswith("%") else 1)
    if not 0 <= v <= 3: raise ValueError("saturation must be between 0 (grey) and 3; 1 = original")
    return v

def size_for(width, aspect):
    a, b = ASPECTS[aspect]; h = round(width * b / a); return width, h - (h % 2)

def scene_id(ldir):
    """Short fingerprint of the scene (laptop's scene.blend + laptop.py + groups + the shared scripts). Frame folders are keyed on it, so frames rendered from an older build are never reused."""
    h = hashlib.sha1()
    for f in (f"{ldir}/scene.blend", f"{ldir}/laptop.py", f"{ldir}/cad/groups.json", f"{ldir}/cad/logo_loops.json",
              f"{ROOT}/scripts/fwconfig.py", f"{ROOT}/scripts/compose.py", f"{ROOT}/scripts/render_frames.py", f"{ROOT}/scripts/laptops.py"):
        with open(f, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()[:8]

def pick_laptop(arg, interactive):
    avail = laptops.available()
    if not avail: sys.exit("no laptop directories (*_blueprint_renderer) found next to run.py")
    info = {}
    for slug in avail:
        m = laptops.load_module(laptops.resolve(slug)[1]); info[slug] = m.TITLE
    if arg: return laptops.resolve(arg)
    if not interactive: return laptops.resolve(avail[0])
    print(bold("  0/3  Laptop model"))
    for i, slug in enumerate(avail, 1): print(f"       {i}) Framework {info[slug].title():<18} ({slug})")
    def parse(v):
        v = v.strip().lower()
        if v.isdigit() and 1 <= int(v) <= len(avail): return avail[int(v) - 1]
        if v in avail: return v
        raise ValueError(f"choose 1-{len(avail)}")
    return laptops.resolve(ask("choose", 1, parse))

def find_blender():
    cands = [shutil.which("blender")]
    cands += glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe")
    cands += ["/Applications/Blender.app/Contents/MacOS/Blender", "/usr/bin/blender", "/snap/bin/blender"]
    return next((p for p in cands if p and os.path.exists(p)), None)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--laptop", help="laptop slug, e.g. fw16 (default: ask)"); ap.add_argument("--width", type=parse_width); ap.add_argument("--aspect", type=parse_aspect); ap.add_argument("--fps", type=parse_fps)
    ap.add_argument("--idle-closed", type=parse_idle, metavar="SEC", help="extra seconds to hold the closed laptop (default 0)")
    ap.add_argument("--idle-open", type=parse_idle, metavar="SEC", help="extra seconds to hold the opened laptop (default 0)")
    ap.add_argument("--idle-exploded", type=parse_idle, metavar="SEC", help="extra seconds to hold the exploded view with labels (default 0)")
    ap.add_argument("--hue", type=parse_hue, help="colour: a name (" + ", ".join(HUES) + ") or degrees to rotate the hue from the original blue (default 0)")
    ap.add_argument("--saturation", type=parse_sat, help="colour saturation, 1 = original, 0 = grey, up to 3 (default 1)")
    ap.add_argument("--stills", action="store_true", help="export 3 images (closed, open, exploded) instead of a video; no frame rate or idle time")
    ap.add_argument("--blender"); ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4, help="parallel overlay-composite processes")
    ap.add_argument("--only", help="render only these output frame numbers, e.g. 1,271 (smoke test)")
    ap.add_argument("--yes", action="store_true", help="skip the confirmation question")
    a = ap.parse_args()

    print()
    print(bold("  FRAMEWORK LAPTOPS  -  blueprint exploded view"))
    print(dim("  official CAD, rendered in Blender - 18 s seamless loop\n"))
    interactive = sys.stdin.isatty() and not (a.laptop and a.width and a.aspect and (a.fps or a.stills))
    slug, ldir = pick_laptop(a.laptop, interactive); L = laptops.load_module(ldir)
    if interactive:
        print()
        print(bold("  1/6  Pixel width"))
        a.width = a.width or ask("width in px (e.g. 1280, 1920, 2560, 3840)", 1920, parse_width)
        print(bold("\n  2/6  Aspect ratio"))
        print("       1) 16:9   standard widescreen\n       2) 3:2    taller frame")
        a.aspect = a.aspect or ask("choose", 1, parse_aspect)
        print(bold("\n  3/6  Colour"))
        print(dim("       hue: " + ", ".join(HUES) + ", or degrees; saturation 1 = original"))
        a.hue = a.hue if a.hue is not None else ask("hue", "blue", parse_hue)
        a.saturation = a.saturation if a.saturation is not None else ask("saturation", 1, parse_sat)
        print(bold("\n  4/6  Output"))
        print("       1) video     18 s seamless loop (mp4)\n       2) 3 images  closed, opened and exploded (png), no video")
        a.stills = a.stills or ask("choose", 1, parse_output) == "images"
        if not a.stills:
            print(bold("\n  5/6  Frame rate"))
            a.fps = a.fps or ask("frames per second (Hz)", 30, parse_fps)
            print(bold("\n  6/6  Idle time"))
            print(dim("       the animation stands still in three places; add extra seconds to each (0 = standard timing)"))
            if a.idle_closed is None: a.idle_closed = ask("extra seconds, closed laptop", 0, parse_idle)
            if a.idle_open is None: a.idle_open = ask("extra seconds, opened laptop", 0, parse_idle)
            if a.idle_exploded is None: a.idle_exploded = ask("extra seconds, exploded with labels", 0, parse_idle)
    a.width, a.aspect = a.width or 1920, a.aspect or "16:9"; hue, sat = a.hue or 0.0, 1.0 if a.saturation is None else a.saturation
    graded = hue % 360 != 0 or sat != 1.0; ctag = f"_h{hue:g}_s{sat:g}" if graded else ""     # colour only affects the composite, so Blender frames are shared between colours
    if a.stills: a.fps, idle = STILL_FPS, (0.0, 0.0, 0.0)             # stills use the standard timeline
    else: a.fps = a.fps or 30; idle = tuple(v or 0.0 for v in (a.idle_closed, a.idle_open, a.idle_exploded))
    W, H = size_for(a.width, a.aspect); duration = DURATION + sum(idle); nframes = round(duration * a.fps)
    if a.stills: only = still_frames(L, a.fps)                         # middle of each hold: closed, open, exploded (labels fully shown)
    else: only = [int(x) for x in a.only.split(",")] if a.only else list(range(1, nframes + 1))

    blender = a.blender or find_blender()
    if not blender and interactive: blender = ask("path to the Blender executable", "", lambda s: s if os.path.exists(s) else (_ for _ in ()).throw(ValueError("file not found")))
    if not blender: sys.exit("Blender not found - pass --blender <path>")
    if not shutil.which("ffmpeg"): sys.exit("ffmpeg not found on PATH")

    print(f"\n  {bold('Laptop')}   Framework {L.TITLE.title()}")
    if a.stills: print(f"  {bold('Output')}   {W} x {H}  ({a.aspect})  -  3 images (closed, opened, exploded)")
    else:
        print(f"  {bold('Output')}   {W} x {H}  ({a.aspect})  @ {a.fps} fps  -  {nframes} frames, {duration:g} s")
        if any(idle): print(f"  {bold('Idle')}     +{idle[0]:g} s closed, +{idle[1]:g} s opened, +{idle[2]:g} s exploded")
    print(f"  {bold('Blender')}  {blender}")
    ensure_scene(slug, ldir, blender)
    sid = scene_id(ldir); print(f"  {bold('Scene')}    {sid}  (frames are cached per scene build; older builds' frames are ignored)")
    if interactive and not a.yes and input(f"\n  {cyan('>')} start render? {dim('[Y/n]')} ").strip().lower() in ("n", "no"): sys.exit("aborted")
    print()

    env = dict(os.environ, FW_LAPTOP=slug, FW_RES=f"{W}x{H}", FW_FPS=str(a.fps), FW_IDLE=",".join(f"{v:g}" for v in idle), FW_HUE=f"{hue:g}", FW_SAT=f"{sat:g}")
    tag = f"{slug}_{W}x{H}_{a.fps}_{sid}" + ("_idle" + "-".join(f"{v:g}" for v in idle) if any(idle) else "")
    rd, cd = os.path.join(ROOT, "render", tag), os.path.join(ROOT, "render", "comp_" + tag + ctag)       # the tag includes the idle times: they shift what each frame number shows
    os.makedirs(rd, exist_ok=True); os.makedirs(cd, exist_ok=True)
    todo = [f for f in only if not os.path.exists(os.path.join(rd, f"f{f:04d}.json"))]
    print(f"  {len(todo)} of {len(only)} frames to render" + (" (rest found from a previous run)" if len(todo) < len(only) else ""))
    blend = os.path.join(ldir, "scene.blend")
    while todo:
        err = run_blender([blender, "-b", blend, "--python", os.path.join(ROOT, "scripts", "render_frames.py"), "--", rd, *map(str, todo)], env, len(todo))
        left = [f for f in todo if not os.path.exists(os.path.join(rd, f"f{f:04d}.json"))]
        if not err: break
        if len(left) >= len(todo): sys.exit(err)                    # crashed without finishing a single frame: not a random crash, give up
        print(c("33", f"  Blender crashed after {len(todo) - len(left)} frames, restarting it for the remaining {len(left)} ...")); todo = left   # (finished frames are kept)
    print("  compositing overlay ...")
    jobs = max(1, min(a.jobs, len(only))); chunks = [only[i::jobs] for i in range(jobs)]
    with ProcessPoolExecutor(jobs) as ex:
        list(ex.map(lambda_compose, [(rd, cd, ch, env) for ch in chunks]))
    out = os.path.join(ROOT, "out"); os.makedirs(out, exist_ok=True); mp4 = os.path.join(out, f"{slug}_blueprint_{W}x{H}_{a.fps}{ctag}.mp4")
    if a.stills:
        names = ("closed", "open", "exploded")
        for n, f in zip(names, only): shutil.copy(os.path.join(cd, f"c{f:04d}.png"), os.path.join(out, f"{slug}_blueprint_{W}x{H}_{n}{ctag}.png"))
        print(f"\n  {bold('done')} -> {out}{os.sep}{slug}_blueprint_{W}x{H}_{{{','.join(names)}}}{ctag}.png\n"); return
    if a.only: print("  --only given: skipping video encode, composites are in", cd); return
    print("  encoding ...")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(a.fps), "-i", os.path.join(cd, "c%04d.png"), "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4], check=True)
    print(f"\n  {bold('done')} -> {mp4}\n")

def still_frames(L, fps):
    """Output frame numbers in the middle of the closed, open and exploded holds (standard timing; same constants as scripts/fwconfig.py)."""
    T = dict(T_OPEN0=1.5, T_OPEN1=3.2, T_DIMS=4.8, T_EXPLODE=7.6, T_HOLD=11.6); T.update(getattr(L, "TIMING", {}))
    return [round(m * fps) + 1 for m in (T["T_OPEN0"] / 2, (T["T_OPEN1"] + T["T_DIMS"]) / 2, (T["T_EXPLODE"] + T["T_HOLD"]) / 2)]

def ensure_scene(slug, ldir, blender):
    """The scene (<laptop dir>/scene.blend) is shipped; if it is missing, bake it from the laptop's cad/ data."""
    if os.path.exists(os.path.join(ldir, "scene.blend")): return
    print("  scene.blend missing - baking it from the cad/ data ...")
    r = subprocess.run([blender, "-b", "--python", os.path.join(ROOT, "scripts", "build_scene.py")], cwd=ROOT, env=dict(os.environ, FW_LAPTOP=slug), capture_output=True, text=True)
    if r.returncode or not os.path.exists(os.path.join(ldir, "scene.blend")): sys.exit("scene bake failed:\n" + r.stdout[-1500:] + r.stderr[-1500:])

def run_blender(cmd, env, total):
    """Run Blender quietly; show 'frame n / total' (a frame is done when its glow pass 'b/fNNNN.png' is saved)."""
    p = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1); done = 0; tail = []
    for line in p.stdout:
        tail = (tail + [line.rstrip()])[-25:]
        if line.startswith("Saved:") and (os.sep + "b" + os.sep) in line:
            done += 1; print(f"\r  rendering  {done} / {total}", end="", flush=True)
    p.wait(); print()
    if p.returncode:                                              # -> error text (None = ok)
        crash = next((l.split("Writing:", 1)[1].strip() for l in reversed(tail) if l.startswith("Writing:") and l.rstrip().endswith(".crash.txt")), None)
        info = ""
        if crash and os.path.exists(crash):                       # Blender's own crash report (stack trace) - the useful part when it dies in a CI container
            with open(crash, errors="replace") as fh: info = f"\n--- {crash} ---\n" + "".join(fh.readlines()[:60])
        return f"Blender failed (exit code {p.returncode}):\n" + "\n".join(tail) + info

def lambda_compose(job):
    rd, cd, chunk, env = job
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "compose.py"), rd, cd, *map(str, chunk)], env=env, check=True)

if __name__ == "__main__":
    main()
