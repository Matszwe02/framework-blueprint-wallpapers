"""STEP (official Framework 13 Pro CAD) -> per-prototype meshes + per-instance matrices."""
import sys, json, time, numpy as np
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFApp import XCAFApp_Application
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.IFSelect import IFSelect_RetDone
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
from OCP.TopoDS import TopoDS
from OCP.TopLoc import TopLoc_Location
from OCP.gp import gp_Trsf

src, out = sys.argv[1], sys.argv[2]
app = XCAFApp_Application.GetApplication_s()
doc = TDocStd_Document(TCollection_ExtendedString("x"))
app.NewDocument(TCollection_ExtendedString("MDTV-XCAF"), doc)
r = STEPCAFControl_Reader(); r.SetNameMode(True)
assert r.ReadFile(src) == IFSelect_RetDone
r.Transfer(doc)
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

def name(l):
    n = TDataStd_Name()
    return n.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), n) else "?"

def mat(loc):
    t = loc.Transformation()
    return [[t.Value(i, j) for j in range(1, 5)] for i in range(1, 4)] + [[0, 0, 0, 1]]

protos = {}   # label tag-entry -> dict
inst = []
def entry(l):
    from OCP.TCollection import TCollection_AsciiString
    from OCP.TDF import TDF_Tool
    s = TCollection_AsciiString(); TDF_Tool.Entry_s(l, s); return s.ToCString()

def mesh(shape):
    BRepMesh_IncrementalMesh(shape, 0.15, False, 0.35, True)
    V, F = [], []
    ex = TopExp_Explorer(shape, TopAbs_FACE)
    while ex.More():
        f = TopoDS.Face_s(ex.Current()); loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(f, loc)
        if tri is not None:
            tr = loc.Transformation(); base = len(V)
            for i in range(1, tri.NbNodes() + 1):
                p = tri.Node(i).Transformed(tr); V.append((p.X(), p.Y(), p.Z()))
            rev = f.Orientation() == TopAbs_REVERSED
            for i in range(1, tri.NbTriangles() + 1):
                a, b, c = tri.Triangle(i).Get()
                F.append((base+a-1, base+c-1, base+b-1) if rev else (base+a-1, base+b-1, base+c-1))
        ex.Next()
    return np.array(V, np.float32), np.array(F, np.int32)

def walk(l, M, path):
    if st.IsReference_s(l):
        loc = st.GetLocation_s(l); ref = TDF_Label(); st.GetReferredShape_s(l, ref)
        t = gp_Trsf(); 
        Mn = M * loc.Transformation() if False else None
        walk2(ref, M.Multiplied(loc.Transformation()), path + [name(l)]); return
    walk2(l, M, path)

def walk2(l, M, path):
    if st.IsAssembly_s(l):
        comps = TDF_LabelSequence(); st.GetComponents_s(l, comps)
        for i in range(1, comps.Length() + 1): walk(comps.Value(i), M, path)
    else:
        e = entry(l)
        if e not in protos:
            shp = st.GetShape_s(l); protos[e] = {"name": name(l), "mesh": mesh(shp)}
        t = M
        inst.append({"proto": e, "path": "/".join(path), "name": name(l),
                     "m": [[t.Value(i, j) for j in range(1, 5)] for i in range(1, 4)]})

fr = TDF_LabelSequence(); st.GetFreeShapes(fr)
t0 = time.time()
for i in range(1, fr.Length() + 1): walk(fr.Value(i), gp_Trsf(), [])
print("instances", len(inst), "protos", len(protos), time.time() - t0)
keys = list(protos)
arrs = {}
for k, e in enumerate(keys):
    arrs[f"v{k}"], arrs[f"f{k}"] = protos[e]["mesh"]
np.savez_compressed(out + ".npz", **arrs)
for d in inst: d["proto"] = keys.index(d["proto"])
json.dump({"protos": [protos[k]["name"] for k in keys], "instances": inst}, open(out + ".json", "w"))
