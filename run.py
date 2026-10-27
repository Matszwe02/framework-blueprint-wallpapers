#!/usr/bin/env python3
"""Framework laptop blueprint exploded-view video - interactive renderer.

    python run.py                      # asks for the laptop model, pixel width, aspect ratio and frame rate
    python run.py --laptop fw16 --width 1920 --aspect 16:9 --fps 30 --yes      # same, no questions

Pipeline: Blender/Cycles (two passes per frame) -> 2D overlay composite -> ffmpeg.
Needs Blender 4.x, ffmpeg on PATH and `pip install -r requirements.txt`.
Frames are kept in render/<laptop>_<W>x<H>_<fps>_<scene id>/, so an interrupted run resumes where it stopped but frames from an older build are never reused.
"""
import argparse, glob, hashlib, os, shutil, subprocess, sys
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "scripts")); import laptops
ASPECTS = {"16:9": (16, 9), "3:2": (3, 2)}
DURATION = 18.0
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
    ap.add_argument("--blender"); ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4, help="parallel overlay-composite processes")
    ap.add_argument("--only", help="render only these output frame numbers, e.g. 1,271 (smoke test)")
    ap.add_argument("--yes", action="store_true", help="skip the confirmation question")
    a = ap.parse_args()

    print()
    print(bold("  FRAMEWORK LAPTOPS  -  blueprint exploded view"))
    print(dim("  official CAD, rendered in Blender - 18 s seamless loop\n"))
    interactive = sys.stdin.isatty() and not (a.laptop and a.width and a.aspect and a.fps)
    slug, ldir = pick_laptop(a.laptop, interactive); L = laptops.load_module(ldir)
    if interactive:
        print()
        print(bold("  1/3  Pixel width"))
        a.width = a.width or ask("width in px (e.g. 1280, 1920, 2560, 3840)", 1920, parse_width)
        print(bold("\n  2/3  Aspect ratio"))
        print("       1) 16:9   standard widescreen\n       2) 3:2    taller frame")
        a.aspect = a.aspect or ask("choose", 1, parse_aspect)
        print(bold("\n  3/3  Frame rate"))
        a.fps = a.fps or ask("frames per second (Hz)", 30, parse_fps)
    a.width, a.aspect, a.fps = a.width or 1920, a.aspect or "16:9", a.fps or 30
    W, H = size_for(a.width, a.aspect); nframes = round(DURATION * a.fps)
    only = [int(x) for x in a.only.split(",")] if a.only else list(range(1, nframes + 1))

    blender = a.blender or find_blender()
    if not blender and interactive: blender = ask("path to the Blender executable", "", lambda s: s if os.path.exists(s) else (_ for _ in ()).throw(ValueError("file not found")))
    if not blender: sys.exit("Blender not found - pass --blender <path>")
    if not shutil.which("ffmpeg"): sys.exit("ffmpeg not found on PATH")

    print(f"\n  {bold('Laptop')}   Framework {L.TITLE.title()}")
    print(f"  {bold('Output')}   {W} x {H}  ({a.aspect})  @ {a.fps} fps  -  {nframes} frames, {nframes / a.fps:.0f} s")
    print(f"  {bold('Blender')}  {blender}")
    ensure_scene(slug, ldir, blender)
    sid = scene_id(ldir); print(f"  {bold('Scene')}    {sid}  (frames are cached per scene build; older builds' frames are ignored)")
    if interactive and not a.yes and input(f"\n  {cyan('>')} start render? {dim('[Y/n]')} ").strip().lower() in ("n", "no"): sys.exit("aborted")
    print()

    env = dict(os.environ, FW_LAPTOP=slug, FW_RES=f"{W}x{H}", FW_FPS=str(a.fps))
    tag = f"{slug}_{W}x{H}_{a.fps}_{sid}"; rd, cd = os.path.join(ROOT, "render", tag), os.path.join(ROOT, "render", "comp_" + tag)
    os.makedirs(rd, exist_ok=True); os.makedirs(cd, exist_ok=True)
    todo = [f for f in only if not os.path.exists(os.path.join(rd, f"f{f:04d}.json"))]
    print(f"  {len(todo)} of {len(only)} frames to render" + (" (rest found from a previous run)" if len(todo) < len(only) else ""))
    if todo:
        blend = os.path.join(ldir, "scene.blend")
        run_blender([blender, "-b", blend, "--python", os.path.join(ROOT, "scripts", "render_frames.py"), "--", rd, *map(str, todo)], env, len(todo))
    print("  compositing overlay ...")
    jobs = max(1, min(a.jobs, len(only))); chunks = [only[i::jobs] for i in range(jobs)]
    with ProcessPoolExecutor(jobs) as ex:
        list(ex.map(lambda_compose, [(rd, cd, ch, env) for ch in chunks]))
    out = os.path.join(ROOT, "out"); os.makedirs(out, exist_ok=True); mp4 = os.path.join(out, f"{slug}_blueprint_{W}x{H}_{a.fps}.mp4")
    if a.only: print("  --only given: skipping video encode, composites are in", cd); return
    print("  encoding ...")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(a.fps), "-i", os.path.join(cd, "c%04d.png"), "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4], check=True)
    print(f"\n  {bold('done')} -> {mp4}\n")

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
    if p.returncode: sys.exit("Blender failed:\n" + "\n".join(tail))

def lambda_compose(job):
    rd, cd, chunk, env = job
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "compose.py"), rd, cd, *map(str, chunk)], env=env, check=True)

if __name__ == "__main__":
    main()
