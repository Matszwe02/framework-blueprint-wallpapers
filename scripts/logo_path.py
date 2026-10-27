"""(FW_LAPTOP=<laptop>) Gear logo (top face of the lid logo part, laptop.py LOGO_PART / LOGO_SOURCE) -> cad/logo_loops.json: [outer gear boundary, inner circle] in mm, for a solid even-odd fill."""
import json, os, sys, numpy as np
from shapely.geometry import LineString
from shapely.ops import unary_union, linemerge
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import laptops
_, ROOT = laptops.current(); sys.path.insert(0, ROOT); import laptop as L
base = L.SOURCES[L.LOGO_SOURCE]; meta = json.load(open(f"{ROOT}/cad/{base}.json")); E = np.load(f"{ROOT}/cad/{base}_edges.npz")
inst = [i for i in meta["instances"] if i["name"] == L.LOGO_PART][0]; k = inst["proto"]
M = np.array(inst["m"]); P = E[f"e{k}"].astype(np.float64)
W = P @ M[:, :3].T + M[:, 3]; top = W[:, :, 1].min(axis=1) > W[:, :, 1].max() - 0.05
S = W[top][:, :, [0, 2]]; c = (S.reshape(-1, 2).min(0) + S.reshape(-1, 2).max(0)) / 2; S = S - c
print("segments", len(S), "extent", (S.reshape(-1, 2).max(0) - S.reshape(-1, 2).min(0)).round(2))
m = linemerge(unary_union([LineString(x) for x in S.tolist()])); parts = list(m.geoms) if hasattr(m, "geoms") else [m]
chains = [np.array(g.coords) for g in parts if len(g.coords) > 8]
ext = lambda c_: np.ptp(c_[:, 0]) * np.ptp(c_[:, 1])
outer = max(chains, key=ext)                                                           # the gear boundary is the chain with the largest extent
inner = np.vstack([c_ for c_ in chains if c_ is not outer])                              # everything else = the inner circle (one closed chain, or two half arcs)
ctr = inner.mean(0); r = np.hypot(*(inner - ctr).T).mean(); th = np.linspace(0, 2 * np.pi, 96)
circle = np.c_[ctr[0] + r * np.cos(th), ctr[1] + r * np.sin(th)]
print("inner circle centre", ctr.round(2), "radius", round(float(r), 2))
json.dump([np.round(outer, 3).tolist(), np.round(circle, 3).tolist()], open(f"{ROOT}/cad/logo_loops.json", "w"))
