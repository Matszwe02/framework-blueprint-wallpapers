#!/usr/bin/env python3
"""Download a laptop's official source CAD (laptop.py CAD_FILES) from github.com/FrameworkComputer into <laptop dir>/cad/.   usage: fetch_cad.py <laptop> [--force]"""
import os, sys, urllib.request, urllib.parse, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import laptops
if len(sys.argv) < 2: sys.exit("usage: fetch_cad.py <laptop>   (one of: %s)" % ", ".join(laptops.available()))
slug, ldir = laptops.resolve(sys.argv[1]); force = "--force" in sys.argv
L = laptops.load_module(ldir); os.makedirs(os.path.join(ldir, "cad"), exist_ok=True)
for name, (repo, path) in L.CAD_FILES.items():
    dst = os.path.join(ldir, "cad", name)
    if os.path.exists(dst) and not force: print("have", name); continue
    url = f"https://github.com/FrameworkComputer/{repo}/raw/main/{urllib.parse.quote(path)}"; print("fetching", name, "<-", url)
    urllib.request.urlretrieve(url, dst)
    if name.endswith(".zip"):
        with zipfile.ZipFile(dst) as z: z.extractall(os.path.join(ldir, "cad", name[:-4]))
print("done:", slug)
