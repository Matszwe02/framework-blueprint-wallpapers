import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFApp import XCAFApp_Application
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.IFSelect import IFSelect_RetDone
import time
t=time.time()
app=XCAFApp_Application.GetApplication_s()
doc=TDocStd_Document(TCollection_ExtendedString("x")); app.NewDocument(TCollection_ExtendedString("MDTV-XCAF"),doc)
r=STEPCAFControl_Reader(); r.SetNameMode(True); r.SetColorMode(True)
assert r.ReadFile(sys.argv[1])==IFSelect_RetDone
r.Transfer(doc); print("loaded",time.time()-t)
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
def name(l):
    n=TDataStd_Name()
    return n.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(),n) else "?"
def walk(l,d,maxd):
    if st.IsReference_s(l):
        ref=TDF_Label(); st.GetReferredShape_s(l,ref); 
        print("  "*d+"->"+name(l)+" :: "+name(ref)) if d<=maxd else None
        walk(ref,d,maxd); return
    comps=TDF_LabelSequence(); 
    if st.IsAssembly_s(l):
        st.GetComponents_s(l,comps)
        if d<=maxd: print("  "*d+"[A] "+name(l)+f" ({comps.Length()})")
        for i in range(1,comps.Length()+1): walk(comps.Value(i),d+1,maxd)
    else:
        if d<=maxd: print("  "*d+"[P] "+name(l))
fr=TDF_LabelSequence(); st.GetFreeShapes(fr)
for i in range(1,fr.Length()+1): walk(fr.Value(i),0,int(sys.argv[2]))
