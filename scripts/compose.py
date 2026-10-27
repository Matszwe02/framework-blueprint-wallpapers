"""Composite blueprint frames: bg + glow pass + line pass + 2D overlay (dimensions, callouts, title) -> final PNG.
usage: compose.py RENDERDIR OUTDIR FRAME [FRAME...]"""
import sys, json, math, numpy as np, skia
from PIL import Image
from scipy.ndimage import gaussian_filter
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import fwconfig as C, laptops
REPO, LDIR = laptops.REPO, C.LDIR
L = C.L

W, H = C.RES; S = W / 1280.0          # layout unit: 1280-px-wide design grid, so any width / aspect ratio keeps the same proportions
rd, od, frames = sys.argv[1], sys.argv[2], [int(a) for a in sys.argv[3:]]
G = json.load(open(os.path.join(LDIR, "cad", "groups.json"))); GR = G["groups"]
FD = os.path.join(REPO, "fonts") + os.sep
def font(f, size): return skia.Font(skia.Typeface.MakeFromFile(FD + f), size * S)
F_TITLE, F_H, F_L, F_S, F_M = font("Rajdhani-Bold.ttf", 34), font("Rajdhani-Bold.ttf", 13.5), font("Rajdhani-Medium.ttf", 11), font("ShareTechMono-Regular.ttf", 9.2), font("ShareTechMono-Regular.ttf", 12)
F_BIG = font("Rajdhani-Bold.ttf", 66)

WHITE = (235, 244, 255); DIM = (150, 175, 230); ACC = (140, 215, 255)

# -------------------------------------------------------------------------------- static background (gradient + grid)
def make_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); u = (xx - W / 2) / (W / 2); v = (yy - H * 0.48) / (H / 2)
    r2 = (u * 0.75) ** 2 + v ** 2
    c0 = np.array([0.055, 0.115, 0.42]); c1 = np.array([0.020, 0.032, 0.20])
    bg = c1 + (c0 - c1) * np.exp(-r2 * 1.6)[..., None]
    gm, gM = 24 * S, 120 * S
    def lines(step, w): 
        a = np.minimum(np.abs(((xx - W / 2) + step / 2) % step - step / 2), 1e9); b = np.abs(((yy - H / 2) + step / 2) % step - step / 2)
        return np.clip(1.0 - np.minimum(a, b) / w, 0, 1)
    g = 0.10 * lines(gm, 0.9) + 0.16 * lines(gM, 1.1)
    bg = bg + g[..., None] * np.array([0.35, 0.55, 1.0]) * (0.35 + 0.65 * np.exp(-r2 * 0.6))[..., None]
    return bg.astype(np.float32)
BG = make_bg()

# -------------------------------------------------------------------------------- projection
SHIFT = 0.0
def project(cam, ortho, P):
    V = np.linalg.inv(np.array(cam)); Q = np.c_[np.atleast_2d(P), np.ones(len(np.atleast_2d(P)))] @ V.T
    k = W / ortho
    return np.c_[W / 2 + (Q[:, 0] - SHIFT * ortho) * k, H / 2 - Q[:, 1] * k]

# -------------------------------------------------------------------------------- canvas helpers
def paint(col, a=1.0, w=1.5, style=skia.Paint.kStroke_Style):
    p = skia.Paint(AntiAlias=True, Style=style, StrokeWidth=w * S, Color=skia.Color(*col, int(255 * max(0, min(1, a))))); p.setStrokeCap(skia.Paint.kRound_Cap); return p
def text(cv, s, x, y, f, col, a=1.0, align="l", track=0.0):
    if track:
        w = sum(f.measureText(c) + track * S for c in s) - track * S
        x0 = x - (w if align == "r" else w / 2 if align == "c" else 0)
        for c in s: cv.drawString(c, x0, y, f, paint(col, a, style=skia.Paint.kFill_Style)); x0 += f.measureText(c) + track * S
        return
    w = f.measureText(s); x0 = x - (w if align == "r" else w / 2 if align == "c" else 0)
    cv.drawString(s, x0, y, f, paint(col, a, style=skia.Paint.kFill_Style))
def tw(s, f, track=0.0): return sum(f.measureText(c) + track * S for c in s) - track * S if track else f.measureText(s)
def line(cv, a, b, col=WHITE, al=1.0, w=1.3): cv.drawLine(a[0], a[1], b[0], b[1], paint(col, al, w))
def poly(cv, pts, col=WHITE, al=1.0, w=1.3, prog=1.0):
    pts = np.array(pts, float); seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); tot = seg.sum(); lim = tot * prog; acc = 0; path = skia.Path(); path.moveTo(*pts[0])
    for i, L in enumerate(seg):
        if acc + L <= lim: path.lineTo(*pts[i + 1]); acc += L
        else: t = (lim - acc) / L; path.lineTo(*(pts[i] + (pts[i + 1] - pts[i]) * t)); break
    cv.drawPath(path, paint(col, al, w))
def ss(x): return C.ss(x)

# -------------------------------------------------------------------------------- dimensions (3D -> screen)
cad_lo = np.min([g["lo"] for g in GR.values()], axis=0); cad_hi = np.max([g["hi"] for g in GR.values()], axis=0)
XW, XE = cad_lo[0], cad_hi[0]; Z0_, DEPTH = cad_lo[2], cad_hi[2]       # overall envelope of the assembled laptop (CAD x = width, z = depth, y = thickness)
WIDTH = XE - XW; DEPTH_LEN = DEPTH - Z0_; THICK = cad_hi[1] - cad_lo[1]; YB = cad_lo[1]
def bl(x, y, z): return np.array(C.cad2bl((x, y, z)), float)
def dimension(cv, cam, ortho, A, B, off_dir, off, label, al, ext=10.0):
    if al <= 0.01: return
    a2, b2 = A + off_dir * off, B + off_dir * off
    pa, pb, pA, pB = [project(cam, ortho, p)[0] for p in (a2, b2, A + off_dir * 5, B + off_dir * 5)]
    for p0, p1 in ((pA, project(cam, ortho, a2 + off_dir * ext)[0]), (pB, project(cam, ortho, b2 + off_dir * ext)[0])): line(cv, p0, p1, DIM, al * 0.8, 1.0)
    line(cv, pa, pb, WHITE, al, 1.2)
    d = (pb - pa) / (np.linalg.norm(pb - pa) + 1e-9); n = np.array([-d[1], d[0]])
    for p, sgn in ((pa, 1), (pb, -1)):                           # arrow heads
        for k in (-1, 1): line(cv, p, p + (d * sgn * 11 + n * k * 3.8) * S, WHITE, al, 1.2)
    ang = math.degrees(math.atan2(d[1], d[0]))
    if ang > 90: ang -= 180
    if ang <= -90: ang += 180
    mid = (pa + pb) / 2; cv.save(); cv.translate(*mid); cv.rotate(ang)
    wlab = tw(label, F_M); cv.drawRect(skia.Rect(-wlab / 2 - 8 * S, -9 * S, wlab / 2 + 8 * S, 9 * S), paint((8, 20, 80), al * 0.9, style=skia.Paint.kFill_Style))
    text(cv, label, 0, 4.2 * S, F_M, WHITE, al, "c"); cv.restore()

# -------------------------------------------------------------------------------- callouts
LEFT, RIGHT = L.LEFT, L.RIGHT
import random
_rng = random.Random(11); JIT_IN = {g: _rng.uniform(0.0, 1.1) for g in C.GROUP_IDS}; JIT_OUT = {g: _rng.uniform(0.0, 0.3) for g in C.GROUP_IDS}
def info_lines(gid):
    """-> None (title only) or (part id, detail line). Defaults: first part name + measured size / part count; laptop.py LABEL_TEXT overrides."""
    g = GR[gid]; d = np.array(g["hi"]) - np.array(g["lo"]); ov = L.LABEL_TEXT.get(gid, {})
    if ov is None: return None
    auto = f"{d[0]:.1f} x {d[2]:.1f} x {d[1]:.1f} MM  /  {g['n']} PART{'S' if g['n'] > 1 else ''}"
    return ov.get("id", list(g["parts"])[0]), ov.get("detail", "{auto}").replace("{auto}", auto)

def relax(ys, gap):
    ys = list(ys)
    for _ in range(60):
        for i in range(1, len(ys)):
            if ys[i] - ys[i - 1] < gap: m = (ys[i] + ys[i - 1]) / 2; ys[i - 1], ys[i] = m - gap / 2, m + gap / 2
    return ys

HOLD_Y = G["hold_y"]
def slots(side, ids):
    """Fixed label slots: order = screen-y of each anchor at mid-hold, y evenly spread -> labels never swap while the camera moves."""
    order = sorted(ids, key=lambda g: HOLD_Y[g][side]); lo, hi = 132 * S, H - 100 * S
    return {g: lo + (hi - lo) * i / max(1, len(order) - 1) for i, g in enumerate(order)}
SLOTS = {"L": slots("L", LEFT), "R": slots("R", RIGHT)}

def callouts(cv, cam, ortho, mats, t):
    reveal0 = C.T_EXPLODE - 0.35
    if t < reveal0 or t > C.T_HOLD: return
    for side, ids in (("L", LEFT), ("R", RIGHT)):
        for gid in ids:
            ly = SLOTS[side][gid]
            M = np.array(mats[gid]); anc = np.array(GR[gid]["anchorL" if side == "L" else "anchorR"]); p = project(cam, ortho, (M @ np.r_[anc, 1.0])[:3])[0]
            prog = ss((t - reveal0 - JIT_IN[gid]) / 0.5) * (1 - ss((t - (C.T_HOLD - 0.9 + JIT_OUT[gid])) / 0.35))
            if prog <= 0.001: continue
            x0 = 64 * S if side == "L" else W - 64 * S; ttl, sub = GR[gid]["label"], info_lines(gid)
            wmax = (tw(ttl, F_H, 1.2) if sub is None else max(tw(ttl, F_H, 1.2), tw(sub[0], F_L), tw(sub[1], F_S))) + 6 * S
            xe = x0 + wmax if side == "L" else x0 - wmax; yb = ly + (29 if sub else 10) * S
            elbow = (xe + (26 * S if side == "L" else -26 * S), yb)
            poly(cv, [(x0, yb), elbow, tuple(p)], WHITE, 0.9 * min(1, prog * 1.6), 1.1, prog)
            if prog > 0.8: cv.drawCircle(p[0], p[1], 4.2 * S, paint(WHITE, 1, 1.3)); cv.drawCircle(p[0], p[1], 1.6 * S, paint(WHITE, 1, style=skia.Paint.kFill_Style))
            al = min(1, prog * 2.2); al_ = "l" if side == "L" else "r"
            text(cv, ttl, x0, ly - 6 * S, F_H, WHITE, al, al_, 1.2)
            if sub: text(cv, sub[0], x0, ly + 8 * S, F_L, ACC, al * 0.95, al_); text(cv, sub[1], x0, ly + 22 * S, F_S, DIM, al * 0.9, al_)

# -------------------------------------------------------------------------------- HUD / titles
LOGO = json.load(open(os.path.join(LDIR, "cad", "logo_loops.json")))      # solid gear: outer boundary + inner circle (even-odd), from this laptop's lid logo part in the official CAD
def gear(cv, cx, cy, size):
    k = size / 45.0; path = skia.Path(); path.setFillType(skia.PathFillType.kEvenOdd)
    for loop in LOGO:
        path.moveTo(cx + loop[0][0] * k, cy + loop[0][1] * k)
        for x, y in loop[1:]: path.lineTo(cx + x * k, cy + y * k)
        path.close()
    cv.drawPath(path, paint(ACC, 0.30, 6.0, skia.Paint.kStroke_Style)); cv.drawPath(path, paint(WHITE, 1.0, style=skia.Paint.kFill_Style))

def hud(cv, t):
    e = C.explode_mean(t); o = C.lid_open(t)
    gear(cv, 90 * S, 70 * S, 52 * S)
    TX = 134 * S
    text(cv, "FRAMEWORK", TX, 70 * S, F_TITLE, WHITE, 1, "l", 5.5)
    text(cv, f"{L.TITLE}  //  EXPLODED ASSEMBLY", TX + 2 * S, 92 * S, F_L, DIM, 1, "l", 2.6)
    cv.drawRect(skia.Rect(TX, 104 * S, TX + 52 * S, 105.6 * S), paint(ACC, 1, style=skia.Paint.kFill_Style))
    text(cv, L.WATERMARK, W - 62 * S, H - 52 * S, F_BIG, (150, 175, 235), 0.12, "r", 6)
    text(cv, L.SOURCE_LINE, 64 * S, H - 40 * S, F_S, DIM, 0.75, "l", 0.8)
    text(cv, L.NOTE_LINE.format(used=G["used"], dropped=G["dropped"]), 64 * S, H - 24 * S, F_S, DIM, 0.55, "l", 0.8)
    # state scrub bar
    bx0, bx1, by = 640 * S, 640 * S + 300 * S, 62 * S
    line(cv, (bx0, by), (bx1, by), DIM, 0.6, 1.0)
    for k in range(0, 31):
        x = bx0 + (bx1 - bx0) * k / 30; line(cv, (x, by), (x, by - (7 if k % 5 == 0 else 3.5) * S), DIM, 0.6, 1.0)
    px = bx0 + (bx1 - bx0) * e; cv.drawRect(skia.Rect(bx0, by - 1.4 * S, px, by + 1.4 * S), paint(ACC, 1, style=skia.Paint.kFill_Style))
    path = skia.Path(); path.moveTo(px, by + 3 * S); path.lineTo(px - 5 * S, by + 11 * S); path.lineTo(px + 5 * S, by + 11 * S); path.close(); cv.drawPath(path, paint(WHITE, 1, style=skia.Paint.kFill_Style))
    text(cv, "ASSEMBLED", bx0, by + 26 * S, F_S, WHITE if e < 0.5 else DIM, 1, "l", 1.5); text(cv, "EXPLODED", bx1, by + 26 * S, F_S, WHITE if e >= 0.5 else DIM, 1, "r", 1.5)
    text(cv, f"{e * 100:03.0f}%", (bx0 + bx1) / 2, by + 26 * S, F_S, ACC, 1, "c", 1.5)
    # corner registration marks
    for (cx, cy, sx, sy) in ((30, 30, 1, 1), (W / S - 30, 30, -1, 1), (30, H / S - 30, 1, -1), (W / S - 30, H / S - 30, -1, -1)):
        poly(cv, [(cx * S + sx * 18 * S, cy * S), (cx * S, cy * S), (cx * S, cy * S + sy * 18 * S)], DIM, 0.7, 1.2)

# -------------------------------------------------------------------------------- main
for f in frames:
    t = (f - 1) / C.FPS; d = json.load(open(f"{rd}/f{f:04d}.json")); cam, ortho, mats = d["cam"], d["ortho"], d["groups"]; SHIFT = d.get("shift", 0.0)
    A = np.asarray(Image.open(f"{rd}/a/f{f:04d}.png").convert("RGBA"), np.float32) / 255
    B = np.asarray(Image.open(f"{rd}/b/f{f:04d}.png").convert("RGBA"), np.float32) / 255
    glow = gaussian_filter(A[..., :3] * A[..., 3:], sigma=(4 * S, 4 * S, 0)) * 0.55 + gaussian_filter(A[..., :3] * A[..., 3:], sigma=(1.2 * S, 1.2 * S, 0)) * 0.25
    img = BG + B[..., :3] * B[..., 3:] * 0.32 + glow * np.array([0.55, 0.8, 1.0])
    img = img * (1 - A[..., 3:]) + A[..., :3] * A[..., 3:]
    surf = skia.Surface(W, H); cv = surf.getCanvas(); cv.clear(skia.Color(0, 0, 0, 0))
    hud(cv, t)
    e = C.explode_mean(t); o = C.lid_open(t)
    a_wd = (1 - ss(e / 0.05)) * (1 - (ss(C.flip_angle(t) / C.FLIP['angle'] / 0.12) if C.FLIP else 0)); a_h = (1 - ss(o / 0.04)) * a_wd * (1 if o < 0.04 else 0)
    z0 = YB
    dimension(cv, cam, ortho, bl(XW, z0, DEPTH), bl(XE, z0, DEPTH), bl(0, 0, 1), 26, f"{WIDTH:.1f} MM", a_wd * 0.95)
    dimension(cv, cam, ortho, bl(XE, z0, DEPTH), bl(XE, z0, Z0_), bl(1, 0, 0), 26, f"{DEPTH_LEN:.1f} MM", a_wd * 0.95)
    dimension(cv, cam, ortho, bl(XW, z0, DEPTH), bl(XW, z0 + THICK, DEPTH), bl(-1, 0, 0), 26, f"{THICK:.1f} MM", a_h * 0.95)
    callouts(cv, cam, ortho, mats, t)
    ov = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType).astype(np.float32) / 255
    ov_a = ov[..., 3:]; ov_rgb = ov[..., :3]
    ov_rgb = ov_rgb  # skia N32 premul (BGRA/RGBA depends)
    out = img * (1 - ov_a) + ov_rgb * 1.0
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(f"{od}/c{f:04d}.png")
