# Shared Blender helpers for the Skyforge Steel weapon stages (stage_mace.py, stage_warhammer.py): loading Legacy of
# Ysgramor's steel weapons as loose parts exactly as the Ebony replacer's build_designs.load_parts does, the recipe helpers
# of its build_designs.py, and the game-ready functions of its build_stage.py (join with one UV layer, orient_outward,
# export_single with the 65535-triangle stop, edge blood, harden), unchanged.
import bpy, bmesh, sys, os, json, math, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import addon_utils
addon_utils.enable("io_scene_nifly", default_set=True)
from io_scene_nifly.pyn.pynifly import NifFile
HIDE = ("blood", "bhk", "collision")
OUTD = os.path.join(os.environ["NSAW_WORK"], "shapes"); os.makedirs(OUTD, exist_ok=True)

def import_nif(path):
    f = NifFile(path); tex = {}
    for s in f.shapes:
        try: d = s.shader.textures.get("Diffuse", "")
        except Exception: d = ""
        tex[s.name] = os.path.splitext(os.path.basename(d.replace("\\", "/")))[0].lower()
    before = set(bpy.data.objects)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.pynifly(filepath=path, import_collisions=False)
    shown = []
    for o in [o for o in bpy.data.objects if o not in before]:
        if o.type != "MESH": continue
        nm = o.name if o.name in tex else o.name.split(".")[0]; st = tex.get(nm, "")
        if any(h in (o.name + " " + st).lower() for h in HIDE) or not st:
            o.hide_render = True; o.hide_viewport = True; continue
        o["tex"] = st; o["shape"] = nm; shown.append(o)
    for o in shown:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    return shown

def load_parts(path, key):
    objs = import_nif(path)
    for o in objs:
        bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.mesh.separate(type="LOOSE"); bpy.ops.object.mode_set(mode="OBJECT")
    parts = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render and o.get("src") is None]
    parts.sort(key=lambda o: (o.name.split(".")[0], -max(v.co.y for v in o.data.vertices)))
    out = {}
    for i, p in enumerate(parts):
        pid = "%s_%02d" % (key, i)
        mw = p.matrix_world.copy(); p.data.transform(mw); p.matrix_world = Matrix.Identity(4)
        p["src"] = pid; p.name = "SRC_" + pid; p.hide_render = True; out[pid] = p
    return out

def obb(o):
    P_ = [o.matrix_world @ v.co for v in o.data.vertices]
    return Vector([min(p[i] for p in P_) for i in range(3)]), Vector([max(p[i] for p in P_) for i in range(3)])

# the parts are the ones this recipe was written against (count, bounding box, atlas of every part)
def check_parts(P, expected_json):
    """the parts are the ones the recipe was written against (count, bounding box, vertex count, atlas of every part)"""
    exp = json.load(open(expected_json))
    bad = []
    for pid, e in exp.items():
        if pid not in P: bad.append((pid, "missing")); continue
        lo, hi = obb(P[pid])
        if (max(abs(lo[i] - e["lo"][i]) for i in range(3)) > 0.011 or max(abs(hi[i] - e["hi"][i]) for i in range(3)) > 0.011
                or P[pid]["tex"] != e["tex"] or len(P[pid].data.vertices) != e["v"]):
            bad.append((pid, [round(x, 2) for x in lo], [round(x, 2) for x in hi], P[pid]["tex"], len(P[pid].data.vertices), e))
    extra = sorted(set(P) - set(exp))
    assert not bad and not extra, ("Legacy of Ysgramor's steel weapon splits differently from the recipe's", bad[:5], extra[:5])
    return len(exp)

def harden(o, deg=35.0):
    """the Ebony build_stage.py harden(): split every edge sharper than deg so each facet has its own vertices (PyNifly
    exports one normal per vertex; the Ebony warhammer's teeth drew as a flat disc until this, 1.1.0 2026-11-14)"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    sharp = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(deg)]
    bmesh.ops.split_edges(bm, edges=sharp)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    for f in bm.faces: f.smooth = True
    bm.to_mesh(o.data); bm.free(); o.data.update()
    return len(sharp)

def dup(src, name):
    o = src.copy(); o.data = src.data.copy(); o.name = name; bpy.context.scene.collection.objects.link(o)
    o.hide_render = False; o.hide_viewport = False; o["from"] = src["src"]; return o

def keep_faces(o, pred):
    bm = bmesh.new(); bm.from_mesh(o.data)
    kill = [f for f in bm.faces if not pred(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(o.data); bm.free()

def xform(o, M):
    o.data.transform(M)
    if M.to_3x3().determinant() < 0: o.data.flip_normals()
    o.data.update()

def T(x, y, z): return Matrix.Translation((x, y, z))
def S(x, y=None, z=None): return Matrix.Diagonal((x, x if y is None else y, x if z is None else z, 1.0))
def R(deg, ax): return Matrix.Rotation(math.radians(deg), 4, ax)

def select_only(o):
    for x in bpy.context.scene.objects:
        if x.select_get(): x.select_set(False)
    o.hide_set(False); o.hide_viewport = False
    o.select_set(True); bpy.context.view_layer.objects.active = o

def join(objs, name):
    objs = list(objs)
    for o in objs:
        o.data = o.data.copy()
        uvs = o.data.uv_layers; assert len(uvs) >= 1, (name, o.name, "a piece without UVs")
        keep_uv = uvs.active.name
        for nm in [l.name for l in uvs if l.name != keep_uv]: uvs.remove(uvs[nm])
        uvs[keep_uv].name = "UVMap"
    select_only(objs[0])
    for o in objs[1:]: o.hide_set(False); o.hide_viewport = False; o.select_set(True)
    nsel = sum(1 for x in bpy.context.scene.objects if x.select_get())
    assert nsel == len(objs), (name, 'selected', nsel, 'meant', len(objs))
    if len(objs) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name; o.data.name = name
    assert [l.name for l in o.data.uv_layers] == ["UVMap"], (name, "UV layers after the join", [l.name for l in o.data.uv_layers])
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bm.to_mesh(o.data); bm.free(); o.data.update()
    return o

def orient_outward(objs, rays=12, samples=300, seed=7):
    rnd = random.Random(seed)
    V, Pl, off = [], [], 0
    for o in objs:
        M = o.matrix_world; V += [M @ v.co for v in o.data.vertices]; Pl += [[off + i for i in p.vertices] for p in o.data.polygons]; off += len(o.data.vertices)
    tree = BVHTree.FromPolygons(V, Pl)
    def cone(n):
        while True:
            d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
            if d.dot(n) > 0.5: return d
    rep = {}
    for o in objs:
        me = o.data; before = [tuple(p.normal) for p in me.polygons]
        bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
        key = lambda v: (round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))
        emap = {}
        for f in bm.faces:
            ks = [key(v) for v in f.verts]
            for i in range(len(ks)):
                emap.setdefault(frozenset((ks[i], ks[(i + 1) % len(ks)])), []).append(f.index)
        par = list(range(len(bm.faces)))
        def find(i):
            while par[i] != i: par[i] = par[par[i]]; i = par[i]
            return i
        for fs in emap.values():
            if len(fs) == 2: par[find(fs[0])] = find(fs[1])
        groups = {}
        for f in bm.faces: groups.setdefault(find(f.index), []).append(f)
        islands = list(groups.values())
        fk = {f.index: [key(v) for v in f.verts] for f in bm.faces}
        nbr = {}
        for fs in emap.values():
            if len(fs) == 2: nbr.setdefault(fs[0], []).append(fs[1]); nbr.setdefault(fs[1], []).append(fs[0])
        def walks(ks, a, b):
            for i in range(len(ks)):
                if ks[i] == a and ks[(i + 1) % len(ks)] == b: return True
            return False
        flipc = set()
        for isl in islands:
            seed_ = max(isl, key=lambda f: f.calc_area()).index; state = {seed_: False}; stack = [seed_]
            while stack:
                i = stack.pop()
                for j in nbr.get(i, []):
                    shared = set(fk[i]) & set(fk[j])
                    if len(shared) != 2: continue
                    a, b = tuple(shared)
                    same = walks(fk[i], a, b) == walks(fk[j], a, b)
                    want = state[i] ^ same
                    if j not in state: state[j] = want; stack.append(j)
            flipc |= {i for i, s in state.items() if s}
        if flipc:
            bm.faces.ensure_lookup_table(); bmesh.ops.reverse_faces(bm, faces=[bm.faces[i] for i in flipc])
        bm.normal_update()
        nflip = 0
        for isl in islands:
            pick = isl if len(isl) <= samples else rnd.sample(isl, samples)
            sc = [0.0, 0.0]
            for f in pick:
                c = f.calc_center_median(); n = f.normal; a = f.calc_area()
                if n.length < 0.5 or a <= 0: continue
                for k, s in enumerate((1.0, -1.0)):
                    esc = 0
                    for _ in range(rays):
                        if tree.ray_cast(c + n * s * 1e-3, cone(n * s), 1000.0)[0] is None: esc += 1
                    sc[k] += a * esc / rays
            if sc[1] > sc[0]:
                nflip += 1; bmesh.ops.reverse_faces(bm, faces=isl)
        bm.normal_update(); bm.faces.ensure_lookup_table(); after = [tuple(f.normal) for f in bm.faces]
        bm.to_mesh(me); me.update()
        changed = sum(1 for a, b in zip(before, after) if a[0] * b[0] + a[1] * b[1] + a[2] * b[2] < 0)
        bm.free()
        rep[o.name] = {"islands": len(islands), "faces": len(before), "faces_reversed_vs_design": changed, "islands_flipped_by_vote": nflip}
    return rep

def dump_points(objs, name):
    import numpy as np
    np.save(os.path.join(OUTD, "points_%s.npy" % name), np.array([tuple(o.matrix_world @ v.co) for o in objs for v in o.data.vertices], np.float64))

def export_single(o, path):
    o.data.calc_loop_triangles(); nt_ = len(o.data.loop_triangles)
    assert nt_ <= 65535, ("over a BSTriShape's 65535 triangles", o.name, nt_)
    select_only(o)
    r = bpy.ops.export_scene.pynifly(filepath=path, target_game="SKYRIMSE", export_colors=False, blender_xf=False, intuit_defaults=False)
    print("EXPORT", path, r)

def blood_uv_box(van_objs):
    us, vs = [], []
    for o in van_objs:
        if "blood" not in o.name.lower() or o.type != "MESH": continue
        for d in o.data.uv_layers.active.data: us.append(d.uv[0]); vs.append(d.uv[1])
    return (min(us), min(vs)), (max(us), max(vs))

def make_blood(srcs, ylo, name, uvbox, offset=0.012, cap=900):
    parts = []
    for s in srcs:
        b = s.copy(); b.data = s.data.copy(); bpy.context.scene.collection.objects.link(b); parts.append(b)
    b = join(parts, name); me = b.data
    bm = bmesh.new(); bm.from_mesh(me)
    kill = [f for f in bm.faces if not all(v.co.y >= ylo for v in f.verts)]
    bmesh.ops.delete(bm, geom=kill, context="FACES"); bm.to_mesh(me); bm.free()
    n = len(me.polygons)
    if n > cap:
        select_only(b); m = b.modifiers.new("dec", "DECIMATE"); m.decimate_type = "COLLAPSE"; m.ratio = cap / n
        bpy.ops.object.modifier_apply(modifier=m.name)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3]); bm.normal_update()
    for v in bm.verts: v.co += v.normal * offset
    lo = Vector([min(v.co[i] for v in bm.verts) for i in range(3)]); hi = Vector([max(v.co[i] for v in bm.verts) for i in range(3)])
    uvl = bm.loops.layers.uv.active; (u0, v0), (u1, v1) = uvbox
    for f in bm.faces:
        for l in f.loops:
            l[uvl].uv = (u0 + (u1 - u0) * (l.vert.co.y - lo.y) / (hi.y - lo.y), v0 + (v1 - v0) * (l.vert.co.x - lo.x) / (hi.x - lo.x))
    bm.to_mesh(me); bm.free(); me.update()
    return b
