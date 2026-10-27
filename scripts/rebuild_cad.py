#!/usr/bin/env python3
"""Rebuild a laptop's derived meshes (cad/*.npz|json) from its source CAD using the REBUILD recipe in laptop.py, then bake scene.blend.
usage: rebuild_cad.py <laptop> [--no-scene] [--blender PATH]      (needs the dev requirements: cadquery, trimesh, shapely, ezdxf, ...; run fetch_cad.py first)"""
import os, sys, subprocess, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import laptops
if len(sys.argv) < 2: sys.exit("usage: rebuild_cad.py <laptop>   (one of: %s)" % ", ".join(laptops.available()))
slug, ldir = laptops.resolve(sys.argv[1]); L = laptops.load_module(ldir); S = os.path.join(laptops.REPO, "scripts")
env = dict(os.environ, FW_LAPTOP=slug); py = sys.executable
def run(*cmd): print("+", " ".join(os.path.relpath(c, laptops.REPO) if os.path.isabs(c) else c for c in cmd), flush=True); subprocess.run(cmd, cwd=laptops.REPO, env=env, check=True)
for step in L.REBUILD:
    kind = step[0]
    if kind == "export": run(py, f"{S}/export_parts.py", f"{ldir}/cad/{step[1]}", f"{ldir}/cad/{step[2]}")
    elif kind == "edges": run(py, f"{S}/extract_edges.py", step[1])
    elif kind == "tool": run(py, f"{ldir}/tools/{step[1]}")
    elif kind == "logo": run(py, f"{S}/logo_path.py")
if "--no-scene" not in sys.argv:
    blender = sys.argv[sys.argv.index("--blender") + 1] if "--blender" in sys.argv else shutil.which("blender") or sys.exit("blender not found (--blender PATH)")
    run(blender, "-b", "--python", f"{S}/build_scene.py")
print("rebuilt:", slug)
