"""Extrude the official mainboard outline (2D DWG sheet 2) into a mesh placed in the Pro chassis frame.
Placement: X centred (board +-117 mm ~ inner edges of the card slots, +-118.3); Z from the card-connector notch rows
(notch pitch in the drawing ~ 40.6 mm = card pitch in the CAD); Y centred on the card bodies."""
import json, os, numpy as np, trimesh
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # this laptop's directory
from shapely.geometry import Polygon
poly = Polygon(json.load(open(f"{ROOT}/cad/mb_polys.json"))[0])
minx, miny, maxx, maxy = poly.bounds
H_TOP, H_BOT = 3.0, 1.0                      # component height limits printed on the drawing ("H=3.0" top, "H=1.0" bottom)
T = H_TOP + H_BOT; Y0 = -7.2 - T / 2          # card bodies span Y -10.6..-3.8 -> centre -7.2
BRK_CENTRE = 63.4                           # z-centre of the expansion-card brackets in the Pro CAD (LFP30_LOW_IO_CARD_BRK z 20..107): board centred between them
cx, z0 = (minx + maxx) / 2, (miny + maxy) / 2 - BRK_CENTRE
pts = np.array(poly.exterior.coords)[:-1]; pts = np.c_[pts[:, 0] - cx, pts[:, 1] - z0]      # (x, z) CAD
m = trimesh.creation.extrude_polygon(Polygon(pts), T)                                          # extrudes along +z (local) -> use as CAD Y
V = np.c_[m.vertices[:, 0], m.vertices[:, 2] + Y0, m.vertices[:, 1]]; F = m.faces[:, [0, 2, 1]]
mesh = trimesh.Trimesh(V, F, process=True); mesh.fix_normals()
assert mesh.volume > 0, "inward-facing normals"
mesh = trimesh.Trimesh(mesh.vertices[mesh.faces].reshape(-1, 3), np.arange(len(mesh.faces) * 3).reshape(-1, 3), process=False)   # un-weld: every triangle owns its vertices -> hard edges, no smoothed normals across the 90-degree corners
print("bbox", mesh.bounds.round(1).tolist(), "faces", len(mesh.faces), "winding consistent", mesh.is_winding_consistent)
np.savez_compressed(f"{ROOT}/cad/mbparts.npz", v0=mesh.vertices.astype(np.float32), f0=mesh.faces.astype(np.int32))
json.dump({"protos": ["MAINBOARD_OUTLINE"], "instances": [{"proto": 0, "path": "mainboard", "name": "MAINBOARD_OUTLINE", "m": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]]}]}, open(f"{ROOT}/cad/mbparts.json", "w"))
