"""Find the hinge pin axis (CAD Y, Z) from cylindrical faces whose axis is parallel to X.
usage: hinge_axis.py <file.stp> <part name regex> [min radius mm]"""
import sys, re, collections
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFApp import XCAFApp_Application
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.IFSelect import IFSelect_RetDone
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
from OCP.TopoDS import TopoDS
from OCP.TopLoc import TopLoc_Location
from OCP.gp import gp_Trsf
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder
path, pat = sys.argv[1], re.compile(sys.argv[2]); rmin = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
app = XCAFApp_Application.GetApplication_s(); doc = TDocStd_Document(TCollection_ExtendedString("x")); app.NewDocument(TCollection_ExtendedString("MDTV-XCAF"), doc)
r = STEPCAFControl_Reader(); r.SetNameMode(True); assert r.ReadFile(path) == IFSelect_RetDone; r.Transfer(doc)
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
def name(l):
    n = TDataStd_Name(); return n.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), n) else "?"
found = collections.Counter()
def walk(l, T):
    if st.IsReference_s(l):
        ref = TDF_Label(); st.GetReferredShape_s(l, ref); walk(ref, T.Multiplied(st.GetLocation_s(l).Transformation())); return
    if st.IsAssembly_s(l):
        c = TDF_LabelSequence(); st.GetComponents_s(l, c)
        for i in range(1, c.Length() + 1): walk(c.Value(i), T)
    elif pat.search(name(l)):
        shp = st.GetShape_s(l).Moved(TopLoc_Location(T)); ex = TopExp_Explorer(shp, TopAbs_FACE)
        while ex.More():
            s = BRepAdaptor_Surface(TopoDS.Face_s(ex.Current()))
            if s.GetType() == GeomAbs_Cylinder:
                c = s.Cylinder(); a = c.Axis(); p = a.Location(); d = a.Direction()
                if c.Radius() >= rmin and abs(d.X()) > 0.99:
                    # axis point projected onto the YZ plane through x=0 is already (p.Y, p.Z) because the axis is parallel to X
                    found[(name(l), round(p.Y(), 1), round(p.Z(), 1), round(c.Radius(), 2))] += 1
            ex.Next()
fr = TDF_LabelSequence(); st.GetFreeShapes(fr)
for i in range(1, fr.Length() + 1): walk(fr.Value(i), gp_Trsf())
for k, n in sorted(found.items()): print(k, "faces", n)
