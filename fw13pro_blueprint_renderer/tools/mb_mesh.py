"""Place the detailed 3D mainboard (Printables 'Framework Mainboard v2', cad/mainboard.step) in the Laptop 13 chassis frame.
Board frame: x = width, y = depth (fan at +y), z = up (components on +z). CAD frame: x = width, y = thickness, z = depth (hinge at 0).
The fan sits at the hinge side (exhaust through the hinge vents), so board y -> -CAD z; board z -> CAD y.
Placement: X centred; Z centred between the card brackets (z-centre 63.4); Y centred on the card bodies (-7.2). Placement is inferred."""
import json, os, subprocess, sys, tempfile, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # this laptop's directory
SCRIPTS = os.path.join(os.path.dirname(ROOT), "scripts")
BRK_CENTRE, Y_CENTRE = 63.4, -7.2
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run([sys.executable, f"{SCRIPTS}/export_parts.py", f"{ROOT}/cad/mainboard.step", f"{tmp}/mb"], check=True)
    d = np.load(f"{tmp}/mb.npz"); inst = json.load(open(f"{tmp}/mb.json"))["instances"]
V, F = d["v0"].astype(np.float64), d["f0"]
if len(inst) != 1: raise SystemExit("expected a single-solid board")
lo, hi = V.min(0), V.max(0); c = (lo + hi) / 2
W = np.c_[V[:, 0] - c[0], V[:, 2] - c[2] + Y_CENTRE, -(V[:, 1] - c[1]) + BRK_CENTRE]      # (x, y, z) CAD
F = F[:, [0, 2, 1]]                                                                           # the axis flip mirrors -> restore winding
print("bbox", W.min(0).round(1).tolist(), W.max(0).round(1).tolist(), "faces", len(F))
np.savez_compressed(f"{ROOT}/cad/mbparts.npz", v0=W.astype(np.float32), f0=F.astype(np.int32))
json.dump({"protos": ["MAINBOARD"], "instances": [{"proto": 0, "path": "mainboard", "name": "MAINBOARD", "m": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]]}]}, open(f"{ROOT}/cad/mbparts.json", "w"))
