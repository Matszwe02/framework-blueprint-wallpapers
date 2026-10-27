# FW_LAPTOP=fw16 blender -b --python scripts/build_scene.py   (run from the repo root; geometry sources + grouping come from <laptop dir>/laptop.py)
# writes <laptop dir>/scene.blend (or $FW_SCENE_OUT) and <laptop dir>/cad/groups.json. Line-ribbon width is baked for the width in FW_RES (default 1920).
import bpy, bmesh, json, sys, math, os, numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, "scripts"); import fwconfig as C
L = C.L; ROOT = C.LDIR                       # ROOT = this laptop's directory (cad/ data in, scene.blend + groups.json out)
SRC = {k: (np.load(f"{ROOT}/cad/{b}.npz"), json.load(open(f"{ROOT}/cad/{b}.json")), np.load(f"{ROOT}/cad/{b}_edges.npz")) for k, b in L.SOURCES.items()}
FILL_SHRINK = float(os.environ.get("FW_SHRINK", "0.03"))
LINE_W = 0.5 * 1920 / C.RES[0]      # mm (constant ~1.4 px)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
CAD2BL = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))

# ---------------------------------------------------------------- materials
def emission_mat(name, build):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); build(nt, out); return m

def passnode(nt):
    v = nt.nodes.new("ShaderNodeValue"); v.name = "PASS"; v.label = "PASS"; v.outputs[0].default_value = 0.0   # 0 = glow pass (fill visible), 1 = line pass (fill = holdout)
    return v

def fill_build(nt, out):
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.0
    nt.links.new(lw.outputs["Facing"], pw.inputs[0])      # facing: 0 = face-on, 1 = grazing
    col = nt.nodes.new("ShaderNodeValToRGB")
    col.color_ramp.elements[0].color = (0.035, 0.075, 0.30, 1); col.color_ramp.elements[1].color = (0.75, 0.88, 1.0, 1)
    nt.links.new(pw.outputs[0], col.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(col.outputs["Color"], em.inputs["Color"])
    ho = nt.nodes.new("ShaderNodeHoldout"); mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(passnode(nt).outputs[0], mix.inputs["Fac"]); nt.links.new(em.outputs[0], mix.inputs[1]); nt.links.new(ho.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])

def line_build(nt, out):
    pn = passnode(nt)                                                          # strength = 1 in line pass, 0 (black) in glow pass
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.92, 0.97, 1.0, 1)
    nt.links.new(pn.outputs[0], em.inputs["Strength"]); nt.links.new(em.outputs[0], out.inputs["Surface"])

M_FILL = emission_mat("FILL", fill_build); M_LINE = emission_mat("LINE", line_build)

# ---------------------------------------------------------------- meshes
def ribbons(P):
    a, b = P[:, 0].astype(np.float64), P[:, 1].astype(np.float64)
    d = b - a; d /= np.linalg.norm(d, axis=1)[:, None]
    ref = np.where(np.abs(d[:, [2]]) < 0.9, np.array([[0, 0, 1.0]]), np.array([[1.0, 0, 0]]))
    n1 = np.cross(d, ref); n1 /= np.linalg.norm(n1, axis=1)[:, None]; n2 = np.cross(d, n1)
    h = LINE_W / 2; ext = d * h * 0.0
    V = []; 
    for n in (n1, n2):
        V += [a - n * h - ext, a + n * h - ext, b + n * h + ext, b - n * h + ext]
    V = np.stack(V, axis=1).reshape(-1, 3)             # 8 verts per segment
    base = (np.arange(len(P)) * 8)[:, None]
    F = np.concatenate([base + [0, 1, 2, 3], base + [4, 5, 6, 7]]).reshape(-1, 4)
    return V, F

mesh_cache = {}
def get_meshes(k, src="p"):
    if (src, k) in mesh_cache: return mesh_cache[(src, k)]
    P_, _, E_ = SRC[src]
    V, F = P_[f"v{k}"], P_[f"f{k}"]
    V = V.astype(np.float64); tn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); vn = np.zeros_like(V)
    for c in range(3): np.add.at(vn, F[:, c], tn)
    vn /= np.maximum(np.linalg.norm(vn, axis=1), 1e-12)[:, None]; V = V - vn * FILL_SHRINK        # fill sits FILL_SHRINK mm under the true surface: edge lines always win the depth test (no z-fighting)
    fill = bpy.data.meshes.new(f"fill_{src}{k}"); fill.from_pydata(V.tolist(), [], F.tolist())
    fill.polygons.foreach_set("use_smooth", [True] * len(fill.polygons)); fill.materials.append(M_FILL)
    ln = None
    if f"e{k}" in E_:
        rv, rf = ribbons(E_[f"e{k}"]); ln = bpy.data.meshes.new(f"line_{src}{k}"); ln.from_pydata(rv.tolist(), [], rf.tolist()); ln.materials.append(M_LINE)
    mesh_cache[(src, k)] = (fill, ln); return mesh_cache[(src, k)]

# ---------------------------------------------------------------- hierarchy
def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); e.empty_display_type = "PLAIN_AXES"; e.location = loc
    sc.collection.objects.link(e)
    if parent: e.parent = parent
    return e

hinge_bl = Vector(C.cad2bl((0, C.HINGE_CAD[0], C.HINGE_CAD[1])))
def attach(node, parent, parent_rest_world):       # parent a node without moving it at rest
    node.parent = parent; node.matrix_parent_inverse = Matrix.Translation(parent_rest_world).inverted()
root_bl = Vector(C.cad2bl(tuple(C.FLIP["center"]))) if C.FLIP else None
root = empty("ROOT", root_bl) if root_bl is not None else None      # optional flip-over of the whole machine about this CAD point (width axis, or depth axis if FLIP['axis'] == 'depth')
if C.HINGE2_CAD:                                  # two chained pivots: world = Root * Link(base pivot) * Lid(lid pivot) * lid
    hinge2_bl = Vector(C.cad2bl((0, C.HINGE2_CAD[0], C.HINGE2_CAD[1])))
    lid_pivot2 = empty("LID_PIVOT_2", hinge2_bl)
    if root: attach(lid_pivot2, root, root_bl)
    lid_pivot = empty("LID_PIVOT", hinge_bl - hinge2_bl, lid_pivot2)
else:
    lid_pivot2 = None; lid_pivot = empty("LID_PIVOT", hinge_bl)
    if root: attach(lid_pivot, root, root_bl)
gemp = {}
for gid, label, side, off, _ in C.GROUPS:
    g = empty("G_" + gid, (0, 0, 0))
    if side == "lid": attach(g, lid_pivot, hinge_bl)
    elif side == "link" and lid_pivot2: attach(g, lid_pivot2, hinge2_bl)          # the hinge link: turns by half the lid angle about the base pivot
    elif root: attach(g, root, root_bl)
    gemp[gid] = g
bpy.context.view_layer.update()

gverts = {gid: [] for gid in C.GROUP_IDS}; gobjs = {gid: [] for gid in C.GROUP_IDS}
ginfo = {gid: {"label": l, "side": s, "offset": o, "parts": {}, "lo": [1e9] * 3, "hi": [-1e9] * 3, "n": 0} for gid, l, s, o, _ in C.GROUPS}
instances = [dict(i, src=k) for k in L.USE_ALL for i in SRC[k][1]["instances"]] + L.extra_instances(SRC)
used = dropped = 0
for n, inst in enumerate(instances):
    k = inst["proto"]; src = inst["src"]; P_ = SRC[src][0]
    if len(P_[f"v{k}"]) == 0: continue
    gid = L.FORCE_GROUP.get(src) or C.classify(inst["name"], inst["path"])
    if gid is None: dropped += 1; continue
    fill, ln = get_meshes(k, src)
    Mc = Matrix([*inst["m"], [0, 0, 0, 1]]); W = CAD2BL @ Mc
    for kind, mesh in (("f", fill), ("l", ln)):
        if mesh is None: continue
        o = bpy.data.objects.new(f"{gid}.{inst['name']}.{n}.{kind}", mesh); sc.collection.objects.link(o)
        o.parent = gemp[gid]; o.matrix_basis = W; gobjs[gid].append(o)
    V = P_[f"v{k}"]; Vw = V @ np.array(inst["m"])[:, :3].T + np.array(inst["m"])[:, 3]       # CAD-space world
    gi = ginfo[gid]; gi["lo"] = np.minimum(gi["lo"], Vw.min(0)).tolist(); gi["hi"] = np.maximum(gi["hi"], Vw.max(0)).tolist()
    gverts[gid].append(Vw)
    gi["n"] += 1; gi["parts"][inst["name"]] = gi["parts"].get(inst["name"], 0) + 1
    used += 1
print("instances used", used, "variants dropped", dropped)
for gid, gi in ginfo.items():                       # fixed leader anchors on the real geometry: left/right edge, top surface, mid depth
    P = np.vstack(gverts[gid]); ymid = P[:, 2].max() - 0.12 * (P[:, 2].max() - P[:, 2].min())      # CAD z (depth): near the front edge, always visible from the camera
    for side, sel in (("anchorL", P[:, 0] <= P[:, 0].min() + 1.0), ("anchorR", P[:, 0] >= P[:, 0].max() - 1.0)):
        Q = P[sel]; q = Q[np.argmin(np.abs(Q[:, 2] - ymid) + 2.0 * (Q[:, 1].max() - Q[:, 1]))]
        gi[side] = list(C.cad2bl(q.tolist()))
json.dump({"groups": ginfo, "hinge_bl": list(hinge_bl), "used": used, "dropped": dropped}, open(f"{ROOT}/cad/groups.json", "w"), indent=1)

# ---------------------------------------------------------------- camera rig
cam_d = bpy.data.cameras.new("CAM"); cam_d.type = "ORTHO"; cam_d.clip_start = 10; cam_d.clip_end = 8000
cam = bpy.data.objects.new("CAM", cam_d); sc.collection.objects.link(cam); sc.camera = cam
tgt = empty("CAM_TARGET"); tc = cam.constraints.new("TRACK_TO"); tc.target = tgt; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"

# ---------------------------------------------------------------- animation (sampled from fwconfig, linear keys)
sc.render.fps = C.BAKED_FPS; sc.frame_start = 1; sc.frame_end = C.BAKED_NFRAMES
for f in range(C.BAKED_NFRAMES):
    t = f / C.BAKED_FPS; sc.frame_set(f + 1)
    a1, a2 = C.lid_angles(t)
    lid_pivot.rotation_euler = (-math.radians(a1), 0, 0); lid_pivot.keyframe_insert("rotation_euler", frame=f + 1)
    if lid_pivot2: lid_pivot2.rotation_euler = (-math.radians(a2), 0, 0); lid_pivot2.keyframe_insert("rotation_euler", frame=f + 1)
    if root: root.rotation_euler = (0, math.radians(C.flip_angle(t)), 0) if C.FLIP.get("axis") == "depth" else (math.radians(C.flip_angle(t)), 0, 0); root.keyframe_insert("rotation_euler", frame=f + 1)
    for gid, _, _, off, _ in C.GROUPS:
        sdx, sdz = C.group_slide(gid, t); gemp[gid].location = (sdx, -sdz, off * C.explode(gid, t)); gemp[gid].keyframe_insert("location", frame=f + 1)
    az, el, width, tg, shx = C.camera(t); az, el = math.radians(az), math.radians(el); D = 3000
    tgt.location = tg; tgt.keyframe_insert("location", frame=f + 1)
    cam.location = Vector(tg) + D * Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    cam.keyframe_insert("location", frame=f + 1)
    cam_d.ortho_scale = width; cam_d.keyframe_insert("ortho_scale", frame=f + 1)
    cam_d.shift_x = shx; cam_d.keyframe_insert("shift_x", frame=f + 1)
# optional per-laptop INTERNAL layers (laptop.py): not rendered until they have moved apart, so they do not show through gaps in the covers
for gid in getattr(L, "INTERNAL", []):
    prev = None
    for f in range(C.BAKED_NFRAMES):
        hide = C.explode(gid, f / C.BAKED_FPS) < 0.08
        if hide != prev or f == C.BAKED_NFRAMES - 1:
            for o in gobjs[gid]: o.hide_render = hide; o.keyframe_insert("hide_render", frame=f + 1)
        prev = hide
    for o in gobjs[gid]:
        for fc in o.animation_data.action.fcurves:
            if fc.data_path == "hide_render":
                for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
for ob in bpy.data.objects:
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            if fc.data_path == "hide_render": continue
            for kp in fc.keyframe_points: kp.interpolation = "LINEAR"
for fc in cam_d.animation_data.action.fcurves:
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"

# ---------------------------------------------------------------- label slots (fixed for the whole hold: screen y of each anchor at mid-hold)
from bpy_extras.object_utils import world_to_camera_view
sc.frame_set(int(round(0.5 * (C.T_EXPLODE + C.T_HOLD) * C.BAKED_FPS)) + 1); bpy.context.view_layer.update()
hold_y = {}
for gid, gi in ginfo.items():
    hold_y[gid] = {}
    for side in ("L", "R"):
        wp = gemp[gid].matrix_world @ Vector(gi["anchor" + side]); hold_y[gid][side] = 1.0 - world_to_camera_view(sc, cam, wp).y      # 0 = top of frame
meta_out = json.load(open(f"{ROOT}/cad/groups.json")); meta_out["hold_y"] = hold_y; json.dump(meta_out, open(f"{ROOT}/cad/groups.json", "w"), indent=1)

# ---------------------------------------------------------------- render settings
r = sc.render; r.engine = "CYCLES"; r.resolution_x, r.resolution_y = C.RES; r.film_transparent = True
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA"
cy = sc.cycles; cy.device = "CPU"; cy.samples = C.SAMPLES; cy.use_denoising = False; cy.max_bounces = 0
cy.pixel_filter_type = "BLACKMAN_HARRIS"; cy.filter_width = 1.2; cy.use_adaptive_sampling = False
sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"
sc.world = bpy.data.worlds.new("W"); sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
sc.frame_set(1)
out_blend = os.environ.get("FW_SCENE_OUT") or f"{ROOT}/scene.blend"; os.makedirs(os.path.dirname(os.path.abspath(out_blend)), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("saved")
