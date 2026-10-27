"""Mainboard top-view outline polygon from Framework's 2D drawing (sheet 2, 'OUTLINE / TOP VIEW')."""
import ezdxf, math, json, os, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # this laptop's directory
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union, polygonize
d = ezdxf.readfile(f"{ROOT}/cad/mb2.dxf"); m = d.modelspace()
X0, X1, Y0, Y1 = 40, 292, 100, 300             # top-view region of sheet 2 (mm on the A2 sheet)
segs = []
def inb(p): return X0 <= p[0] <= X1 and Y0 <= p[1] <= Y1
def arc_pts(e):
    c = e.dxf.center; r = e.dxf.radius; a0, a1 = math.radians(e.dxf.start_angle), math.radians(e.dxf.end_angle)
    if a1 < a0: a1 += 2 * math.pi
    n = max(6, int((a1 - a0) / 0.1)); return [(c.x + r * math.cos(a0 + (a1 - a0) * i / n), c.y + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
for e in m:
    t = e.dxftype(); pts = None
    if t == "LINE": pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
    elif t == "ARC": pts = arc_pts(e)
    elif t == "LWPOLYLINE": pts = [(p[0], p[1]) for p in e.get_points()] + ([(e.get_points()[0][0], e.get_points()[0][1])] if e.closed else [])
    if pts and all(inb(p) for p in pts) and len(pts) >= 2: segs.append(LineString(pts))
print("segments", len(segs))
U = unary_union(segs).buffer(1.2).buffer(-0.6); polys = sorted(U.geoms if hasattr(U, "geoms") else [U], key=lambda p: -p.area); polys = [Polygon(p.exterior) for p in polys]
for p in polys[:6]: print(round(p.area, 1), [round(v, 1) for v in p.bounds])
json.dump([list(map(list, p.exterior.coords)) for p in polys[:3]], open(f"{ROOT}/cad/mb_polys.json", "w"))
