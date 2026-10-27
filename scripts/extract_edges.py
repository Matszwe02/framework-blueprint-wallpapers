"""Feature edges (crease > 38 deg, boundary and non-manifold edges) per prototype from the tessellated CAD.  usage: FW_LAPTOP=<laptop> extract_edges.py <source base name in the laptop's cad/, e.g. system>"""
import numpy as np, sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import laptops
_, ROOT = laptops.current()
src = sys.argv[1]; z = np.load(f"{ROOT}/cad/{src}.npz"); meta = json.load(open(f"{ROOT}/cad/{src}.json"))
THRESH = np.cos(np.radians(38.0)); out = {}; tot = 0
for k in range(len(meta["protos"])):
    V, F = z[f"v{k}"], z[f"f{k}"]
    if len(F) == 0: continue
    q = np.round(V / 0.002).astype(np.int64)
    _, inv = np.unique(q, axis=0, return_inverse=True); inv = inv.reshape(-1)
    W = np.zeros((inv.max() + 1, 3)); W[inv] = V
    T = inv[F]; T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
    n = np.cross(W[T[:, 1]] - W[T[:, 0]], W[T[:, 2]] - W[T[:, 0]])
    ln = np.linalg.norm(n, axis=1); ok = ln > 1e-12; T, n, ln = T[ok], n[ok], ln[ok]; n /= ln[:, None]
    E = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); fi = np.tile(np.arange(len(T)), 3)
    Es = np.sort(E, axis=1); key = Es[:, 0].astype(np.int64) * (len(W) + 1) + Es[:, 1]
    order = np.argsort(key, kind="stable"); key, Es, fi = key[order], Es[order], fi[order]
    first = np.r_[True, key[1:] != key[:-1]]; idx = np.flatnonzero(first); cnt = np.diff(np.r_[idx, len(key)])
    two = cnt == 2; i2 = idx[two]
    crease = np.einsum("ij,ij->i", n[fi[i2]], n[fi[i2 + 1]]) < THRESH
    sel = np.concatenate([i2[crease], idx[~two]])                      # creases + boundary / non-manifold
    if not len(sel): continue
    P = W[Es[sel]]                                                      # (N,2,3)
    L_ = np.linalg.norm(P[:, 0] - P[:, 1], axis=1); P = P[L_ > 0.12]
    if len(P): out[f"e{k}"] = P.astype(np.float32); tot += len(P)
np.savez_compressed(f"{ROOT}/cad/{src}_edges.npz", **out); print(src, "protos with edges", len(out), "segments", tot)
