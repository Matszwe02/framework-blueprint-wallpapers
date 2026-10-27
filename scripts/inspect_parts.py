"""Per-name bounding boxes of an exported CAD (cad/<src>.npz/json): python inspect_parts.py cad/system"""
import sys, json, numpy as np, collections
d = json.load(open(sys.argv[1] + ".json")); z = np.load(sys.argv[1] + ".npz"); g = collections.OrderedDict(); allv = []
for i in d["instances"]:
    v = z[f"v{i['proto']}"]
    if not len(v): continue
    m = np.array(i["m"]); w = v @ m[:, :3].T + m[:, 3]; allv.append(w)
    g.setdefault(i["name"], []).append((w.min(0), w.max(0), len(z[f"f{i['proto']}"])))
for n, L in g.items():
    lo = np.min([a for a, _, _ in L], 0); hi = np.max([b for _, b, _ in L], 0)
    print(f"{n[:46]:46s} x{len(L):<3d} X{lo[0]:>7.1f}..{hi[0]:<7.1f} Y{lo[1]:>6.1f}..{hi[1]:<6.1f} Z{lo[2]:>6.1f}..{hi[2]:<6.1f} tri{L[0][2]}")
A = np.vstack(allv); print("BBOX", A.min(0).round(1), A.max(0).round(1), "SIZE", (A.max(0) - A.min(0)).round(1), "tris", sum(len(z[k]) for k in z.files if k[0] == "f"))
