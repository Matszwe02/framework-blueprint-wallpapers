"""Shared timeline / camera / explode logic. Everything laptop-specific comes from <laptop dir>/laptop.py (chosen with FW_LAPTOP). Pure python (runs inside Blender too)."""
import math, re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import laptops
SLUG, LDIR = laptops.current()                  # e.g. ("fw16", "<repo>/fw16_blueprint_renderer")
if LDIR not in sys.path: sys.path.insert(0, LDIR)
import laptop as L

# output settings come from the environment (run.py / the dev scripts set them); defaults = 1080p30, 24 samples
FPS = int(os.environ.get("FW_FPS", 30))
RES = tuple(int(v) for v in os.environ.get("FW_RES", "1920x1080").split("x"))
SAMPLES = int(os.environ.get("FW_SAMPLES", 24))
BAKED_FPS = 30                          # the .blend animation is keyed once per 1/30 s; any output fps is sampled from it (render_frames.py)
BASE_DURATION = 18.0                    # length of the baked animation
BAKED_NFRAMES = int(BAKED_FPS * BASE_DURATION)
# optional extra idle time [s] in the three still holds (closed, open, exploded), "FW_IDLE=closed,open,exploded"; the video gets that much longer
IDLE = tuple(max(0.0, float(v)) for v in (os.environ.get("FW_IDLE") or "0,0,0").split(","))
SPEED = min(4.0, max(0.25, float(os.environ.get("FW_SPEED") or 1.0)))              # laptop transition speed (1 = original); the base animation takes 18 / SPEED seconds
LABEL_SPEED = min(4.0, max(0.25, float(os.environ.get("FW_LABEL_SPEED") or 1.0)))  # label fade speed (1 = original)
IDLE_HOLDS = (IDLE[0], IDLE[1], IDLE[2], IDLE[1])      # per hold in timeline order: closed, open, exploded, open again (after collapsing; shares the 'open' idle time)
DURATION = BASE_DURATION / SPEED + sum(IDLE_HOLDS)
NFRAMES = int(round(FPS * DURATION))
LID_ANGLE = getattr(L, "LID_ANGLE", 105.0)     # deg, presentational hero pose
HINGE_CAD = L.HINGE_CAD                        # hinge pin axis (CAD Y, Z), read from the hinge parts' cylindrical faces
HINGE2_CAD = getattr(L, "HINGE2_CAD", None)    # optional second pivot for a lid that folds on past 180 deg (360-degree convertibles): the lid ends up under the base

# CAD (x, y=thickness, z=depth) -> Blender (x, -z, y)
def cad2bl(p): return (p[0], -p[2], p[1])

DROP = re.compile(L.DROP)
GROUPS = L.GROUPS                       # (id, label, "lid"|"base", explode offset [mm] along the lid/base normal, name regex)
GROUP_IDS = [g[0] for g in GROUPS]
GROUP = {g[0]: g for g in GROUPS}
GROUP_SLIDE = getattr(L, "GROUP_SLIDE", {})    # {gid: (dx_cad, dz_cad, trigger_gid)} sideways/backwards slide once the trigger group has dropped
MAXOFF = max(abs(g[3]) for g in GROUPS)

def classify(name, path):
    if DROP.match(name): return None
    for gid, _, _, _, pat in GROUPS:
        if re.match(pat, name):
            for src_gid, sub, dst in getattr(L, "PATH_RULES", []):
                if gid == src_gid and sub in path: return dst
            return gid
    raise ValueError("unclassified part: " + name)

# ---------------------------------------------------------------- timeline (seconds)
T_OPEN0, T_OPEN1, T_DIMS, T_EXPLODE, T_HOLD, T_COLLAPSE, T_CLOSE0, T_CLOSE1 = 1.5, 3.2, 4.8, 7.6, 11.6, 14.2, 15.4, 17.0   # holds: [0,1.5] closed, [3.2,4.8] open, [7.6,11.6] exploded

for _k, _v in getattr(L, "TIMING", {}).items(): globals()[_k] = _v        # optional per-laptop retiming of the T_* constants above (e.g. a slower lid motion)

def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * x * (x * (x * 6 - 15) + 10)

def hold_mids():                         # base-timeline middle of each still hold: closed, open, exploded (labels are fully shown at the exploded one), open again after collapsing
    return (T_OPEN0 / 2, (T_OPEN1 + T_DIMS) / 2, (T_EXPLODE + T_HOLD) / 2, (T_COLLAPSE + T_CLOSE0) / 2)

def warp(t):
    """Output time -> baked-animation time (SPEED scales the whole animation). The extra idle seconds (IDLE) are inserted by freezing the animation at the middle of each hold."""
    shift = 0.0
    for m, x in zip(hold_mids(), IDLE_HOLDS):
        ms = m / SPEED                   # hold middle in output time (before the idle seconds already inserted)
        if t < ms + shift: break
        if t < ms + shift + x: return m
        shift += x
    return (t - shift) * SPEED

def lid_open(t):                         # 0 = closed, 1 = open hero pose; loop starts and ends closed
    if t < T_OPEN0: return 0.0
    if t < T_OPEN1: return ss((t - T_OPEN0) / (T_OPEN1 - T_OPEN0))
    if t < T_CLOSE0: return 1.0
    if t < T_CLOSE1: return 1 - ss((t - T_CLOSE0) / (T_CLOSE1 - T_CLOSE0))
    return 0.0

# optional rotation of the whole base (everything not on the lid) about a CAD point, for convertibles. Two modes:
#   follow_lid=True : the base turns by angle * lid_open(t) in the OPPOSITE sense to the lid, in the same single motion (no separate stage)
#   otherwise       : a separate turn-over stage ins -> out
FLIP = getattr(L, "FLIP", None)           # dict(center=(cad_x, cad_y, cad_z), angle=180, axis='width'|'depth', follow_lid=bool, ins=(t0, t1), out=(t0, t1))
def flip_angle(t):
    if not FLIP: return 0.0
    if FLIP.get("follow_lid"): return FLIP["angle"] * lid_open(t)
    i0, i1 = FLIP["ins"]; o0, o1 = FLIP["out"]
    return FLIP["angle"] * (ss((t - i0) / (i1 - i0)) - ss((t - o0) / (o1 - o0)))

def lid_angles(t):
    """(lid angle about HINGE_CAD, link angle about HINGE2_CAD) in degrees. A dual-axis (360-degree) hinge turns the link by half the lid's total rotation
    about the base pivot while the lid turns the other half about the link's far end."""
    a = LID_ANGLE * lid_open(t)
    return (a / 2, a / 2) if HINGE2_CAD else (a, 0.0)

STAG = 0.45
def explode(gid, t):                     # 0..1 per group; outer layers lead out and trail back so layers never pass through each other
    k = abs(GROUP[gid][3]) / MAXOFF
    if t < T_HOLD: return ss((t - T_DIMS - STAG * (1 - k)) / (T_EXPLODE - T_DIMS - STAG))
    return 1 - ss((t - T_HOLD - STAG * k) / (T_COLLAPSE - T_HOLD - STAG))

def explode_mean(t): return sum(explode(g, t) for g in GROUP_IDS) / len(GROUP_IDS)

def group_slide(gid, t):                 # (dx_cad, dz_cad): cards slide out after the D-cover has dropped, before it rises
    if gid not in GROUP_SLIDE: return 0.0, 0.0
    dx, dz, trig = GROUP_SLIDE[gid]; k = ss((explode(trig, t) - 0.6) / 0.4)
    return dx * k, dz * k

def lerp(a, b, k): return a + (b - a) * k

# camera waypoints: (azimuth deg, elevation deg, ortho width mm, target (Blender xyz), horizontal shift)
P_CLOSED, P_OPEN, P_EXPLODED = L.POSES["closed"], L.POSES["open"], L.POSES["exploded"]
P_VIA = L.POSES.get("via")             # optional framing the camera passes through (smoothly) halfway through the lid opening / closing, e.g. when the lid is vertical and tall
CAM_MOVES = [(T_OPEN0, T_OPEN1, P_CLOSED, P_OPEN, P_VIA), (T_DIMS, T_EXPLODE, P_OPEN, P_EXPLODED, None),
             (T_HOLD, T_COLLAPSE, P_EXPLODED, P_OPEN, None), (T_CLOSE0, T_CLOSE1, P_OPEN, P_CLOSED, P_VIA)]
def _flat(p): return [p[0], p[1], p[2], p[3][0], p[3][1], p[3][2], p[4]]
def _blend(a, b, via, k):
    fa, fb = _flat(a), _flat(b)
    if via is None: v = [lerp(x, y, k) for x, y in zip(fa, fb)]
    else:                                  # quadratic Bezier a -> b whose midpoint (k = 0.5) is exactly `via`
        fv = _flat(via); ctrl = [2 * m - 0.5 * (x + y) for m, x, y in zip(fv, fa, fb)]
        v = [(1 - k) ** 2 * x + 2 * (1 - k) * k * c + k * k * y for x, c, y in zip(fa, ctrl, fb)]
    return (v[0], v[1], v[2], (v[3], v[4], v[5]), v[6])
def camera(t):
    """-> (azimuth, elevation, ortho width, target, shift_x). Static during the three holds, moves only with the action; periodic."""
    pose = P_CLOSED
    for t0, t1, a, b, via in CAM_MOVES:
        if t >= t1: pose = b
        elif t > t0: pose = _blend(a, b, via, ss((t - t0) / (t1 - t0))); break
    return pose[0], pose[1], pose[2], pose[3], pose[4]
