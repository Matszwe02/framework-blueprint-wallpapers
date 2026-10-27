"""Finds the laptop directories (<slug>_blueprint_renderer/) of this repo and resolves which one a script works on.
The laptop is chosen with the FW_LAPTOP environment variable: a slug ("fw16") or a directory name ("fw16_blueprint_renderer")."""
import os, sys, glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUFFIX = "_blueprint_renderer"

def available():
    """Slugs of every laptop directory present (it must contain laptop.py)."""
    return sorted(os.path.basename(p)[:-len(SUFFIX)] for p in glob.glob(os.path.join(REPO, "*" + SUFFIX)) if os.path.exists(os.path.join(p, "laptop.py")))

def resolve(name):
    """slug or directory name -> (slug, absolute directory)."""
    slug = os.path.basename(str(name).rstrip("/")); slug = slug[:-len(SUFFIX)] if slug.endswith(SUFFIX) else slug
    if slug not in available(): raise SystemExit(f"unknown laptop '{name}' - available: {', '.join(available())}")
    return slug, os.path.join(REPO, slug + SUFFIX)

def current():
    name = os.environ.get("FW_LAPTOP")
    if not name: raise SystemExit(f"set FW_LAPTOP to one of: {', '.join(available())}")
    return resolve(name)

def load_module(directory):
    """Import <directory>/laptop.py without touching sys.path permanently (used by the TUI to read titles)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("laptop_" + os.path.basename(directory), os.path.join(directory, "laptop.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
