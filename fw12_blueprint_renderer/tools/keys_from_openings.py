"""Framework's Laptop 12 CAD has no keycap parts - the input cover (SF_360_ID_D_C_PART) is one solid with empty key openings.
Rebuild the keycaps from those official openings: rasterise the cover from above, take every through-hole of key size, inset it, round the corners, extrude."""
import json, os, numpy as np, trimesh
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from shapely.geometry import box
from shapely.ops import unary_union
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(f"{ROOT}/cad/system.json")); z = np.load(f"{ROOT}/cad/system.npz")
i = [i for i in d["instances"] if i["name"] == "SF_360_ID_D_C_PART"][0]; v = z[f"v{i['proto']}"]; f = z[f"f{i['proto']}"]; m = np.array(i["m"])
w = v @ m[:, :3].T + m[:, 3]
S, x0, x1, z0, z1 = 4.0, -146.0, 146.0, 0.0, 216.0
W, H = int((x1 - x0) * S), int((z1 - z0) * S); im = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(im)
P = np.c_[(w[:, 0] - x0) * S, (w[:, 2] - z0) * S]
for a, b, c in f: dr.polygon([tuple(P[a]), tuple(P[b]), tuple(P[c])], fill=255)
lab, n = ndi.label(np.array(im) == 0)
GAP, R = 0.45, 0.9                                     # key-to-opening clearance and corner radius (mm)
Y_BOT, Y_TOP = -1.4, 0.7                               # keycap bottom (inside the cover) and top (cover top surface is Y 0.0)
keys = []
for k in range(1, n + 1):
    ys, xs = np.where(lab == k); area = len(xs) / S / S
    if not (60 <= area <= 2000): continue                                  # key-sized openings only (excludes perforations and the touchpad)
    if ys.min() / S < 8 or ys.max() / S > 130: continue                    # inside the keyboard area
    runs = []                                                              # one box per pixel-row run -> exact opening outline
    for r in np.unique(ys):
        cols = np.sort(xs[ys == r]); br = np.flatnonzero(np.diff(cols) > 1); st = np.r_[cols[0], cols[br + 1]]; en = np.r_[cols[br], cols[-1]]
        for a, b in zip(st, en): runs.append(box(x0 + a / S, z0 + r / S, x0 + (b + 1) / S, z0 + (r + 1) / S))
    poly = unary_union(runs).buffer(-GAP - R).buffer(R).simplify(0.05)
    if poly.is_empty or poly.geom_type != "Polygon": continue
    keys.append(poly)
print("keys", len(keys))
protos_v, protos_f, inst = [], [], []
for k, poly in enumerate(keys):
    ex = trimesh.creation.extrude_polygon(poly, Y_TOP - Y_BOT)             # local z = extrusion; polygon in (x, z_cad)
    V = np.c_[ex.vertices[:, 0], ex.vertices[:, 2] + Y_BOT, ex.vertices[:, 1]]
    Fc = ex.faces[:, [0, 2, 1]]                                            # axis swap flips handedness -> restore outward winding
    mesh = trimesh.Trimesh(V, Fc, process=True); mesh.fix_normals()
    mesh = trimesh.Trimesh(mesh.vertices[mesh.faces].reshape(-1, 3), np.arange(len(mesh.faces) * 3).reshape(-1, 3), process=False)
    protos_v.append(mesh.vertices.astype(np.float32)); protos_f.append(mesh.faces.astype(np.int32))
    inst.append({"proto": k, "path": "keys", "name": f"KEYCAP_{k:02d}", "m": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]]})
arrs = {}
for k, (a, b) in enumerate(zip(protos_v, protos_f)): arrs[f"v{k}"], arrs[f"f{k}"] = a, b
np.savez_compressed(f"{ROOT}/cad/keysparts.npz", **arrs)
json.dump({"protos": [f"KEYCAP_{k:02d}" for k in range(len(keys))], "instances": inst}, open(f"{ROOT}/cad/keysparts.json", "w"))
allv = np.vstack(protos_v); print("bbox", allv.min(0).round(1), allv.max(0).round(1), "tris", sum(len(b) for b in protos_f))
