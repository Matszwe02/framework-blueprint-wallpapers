"""ESTIMATED battery for the Framework Laptop 16 (Framework publishes no battery CAD or dimensions, only 85 Wh / 4S1P).
Sized from the free pocket in the official chassis CAD: D-cover floor top Y -12.1, touchpad plate underside Y -3.0, mainboard ends at Z 189.9, D-cover walls at x = +-175,
front wall ~Z 266. Four pouch cells (4S) side by side across the width."""
import json, os, numpy as np, trimesh
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Y0, Y1 = -11.5, -3.7                 # 0.6 mm above the floor, 0.7 mm under the touchpad plate
Z0, Z1 = 196.0, 262.0                # 6 mm in front of the mainboard, 4 mm behind the front wall
X_HALF, GAP, N = 168.0, 2.7, 4       # 7 mm inside the side walls
cw = (2 * X_HALF - GAP * (N - 1)) / N
box = trimesh.creation.box(extents=(cw, Y1 - Y0, Z1 - Z0)); box.apply_translation((0, 0, 0))
tri = trimesh.Trimesh(box.vertices[box.faces].reshape(-1, 3), np.arange(len(box.faces) * 3).reshape(-1, 3), process=False)   # hard edges
np.savez_compressed(f"{ROOT}/cad/bestparts.npz", v0=tri.vertices.astype(np.float32), f0=tri.faces.astype(np.int32))
inst = []
for k in range(N):
    cx = -X_HALF + cw / 2 + k * (cw + GAP)
    inst.append({"proto": 0, "path": "estimate", "name": "FW16_BATTERY_CELL_ESTIMATE", "m": [[1, 0, 0, cx], [0, 1, 0, (Y0 + Y1) / 2], [0, 0, 1, (Z0 + Z1) / 2]]})
json.dump({"protos": ["FW16_BATTERY_CELL_ESTIMATE"], "instances": inst}, open(f"{ROOT}/cad/bestparts.json", "w"))
print("cell", round(cw, 1), "x", round(Y1 - Y0, 1), "x", Z1 - Z0, "mm  x", N, " pack volume", round(2 * X_HALF * (Y1 - Y0) * (Z1 - Z0) / 1000, 1), "cm3")
