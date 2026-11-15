# The Blender half of the Skyforge Steel MACE: the Ebony replacer's approved mace recipe (its build_designs.py, MACE
# section, 2026-11-14) re-mapped onto Legacy of Ysgramor's STEEL war axe, then made game-ready exactly as the Ebony
# build_stage.py makes its mace (one shape per atlas, faces turned outward, edge blood) and exported as single-shape
# NIFs for assemble.py.
#
# WHY A RE-MAP AND NOT A COPY (measured 2026-11-15, every loose part of both axes compared): the steel war axe is cut
# differently from the ebony one - its spike and head plate are one piece per side, it has no separate wrapped grip (one
# plain haft piece), a different pommel and a slightly smaller bit (12.4 vs 13.6 units). So each Ebony part id is mapped
# to the steel part that plays the same role, and the transforms are re-solved so the mace comes out the SAME SIZE as
# the approved Ebony mace (flange height, flange reach, head core span, crown ring and point heights).
#
#   Ebony part (role)                          Steel part
#   waraxe_12 twist-langet tube                waraxe_10
#   waraxe_13..20 rivets and studs             waraxe_11..16, 18, 19
#   waraxe_21 socket cup                       waraxe_17
#   waraxe_22 flared collar disc               waraxe_20
#   waraxe_24 collar ring                      waraxe_21
#   waraxe_23 + 25 haft and wrapped grip       waraxe_22 (one piece on the steel axe)
#   waraxe_26 paw pommel                       waraxe_23
#   waraxe_04/06 head plate (bit side)         waraxe_00/01 (bit side: faces left of the haft and below the bit's top)
#   waraxe_05 / 07 / 11 bit edge strips        waraxe_04 / 05 / 08
#   waraxe_00..03 top spike                    waraxe_00/01 (faces above the bit's top, near the haft) + waraxe_02/03
#
# Every piece keeps its own UVs on the steel war axe's atlas (axe1h - Xtudo's Wolf Black at packaging). The steel set
# has no gold: the collar rings take the steel ring's own texture.
# Run (by tools/build-missing-weapons.py):
#   blender --background --factory-startup --python-exit-code 1 --python stage_mace.py
#   env NSAW_AXE (the LoY steel Axe.nif), NSAW_VAN_MACE (vanilla ebonymace.nif - its blood UVs), NSAW_WORK
import bpy, bmesh, sys, os, json, math, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import addon_utils
HERE = os.path.dirname(os.path.abspath(__file__))
addon_utils.enable("io_scene_nifly", default_set=True)
from io_scene_nifly.pyn.pynifly import NifFile
AXE = os.environ["NSAW_AXE"]; VAN_MACE = os.environ["NSAW_VAN_MACE"]
OUTD = os.path.join(os.environ["NSAW_WORK"], "shapes"); os.makedirs(OUTD, exist_ok=True)
REP = {"notes": []}
HIDE = ("blood", "bhk", "collision")

for o in list(bpy.data.objects): bpy.data.objects.remove(o)

# ---------------------------------------------------------------- the steel war axe's loose parts (as build_designs.load_parts)
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

P = load_parts(AXE, "waraxe")

def obb(o):
    P_ = [o.matrix_world @ v.co for v in o.data.vertices]
    return Vector([min(p[i] for p in P_) for i in range(3)]), Vector([max(p[i] for p in P_) for i in range(3)])

# the parts are the ones this recipe was written against (count, bounding box, atlas of every part)
exp = json.load(open(os.path.join(HERE, "parts_expected_steel.json")))
bad = []
for pid, e in exp.items():
    if pid not in P: bad.append((pid, "missing")); continue
    lo, hi = obb(P[pid])
    if (max(abs(lo[i] - e["lo"][i]) for i in range(3)) > 0.011 or max(abs(hi[i] - e["hi"][i]) for i in range(3)) > 0.011
            or P[pid]["tex"] != e["tex"] or len(P[pid].data.vertices) != e["v"]):
        bad.append((pid, [round(x, 2) for x in lo], [round(x, 2) for x in hi], P[pid]["tex"], len(P[pid].data.vertices), e))
extra = sorted(set(P) - set(exp))
assert not bad and not extra, ("Legacy of Ysgramor's steel war axe splits differently from the recipe's", bad[:5], extra[:5])
REP["parts_checked"] = len(exp)

# ---------------------------------------------------------------- the recipe helpers (build_designs.py's, unchanged)
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

MACE, LOG = [], []
def add(o, part, how):
    o["item"] = "mace"; MACE.append(o)
    if how: LOG.append({"part": part, "how": how})

# ---------------------------------------------------------------- the steel axe's measures (from the parts, not typed in)
lo_r, hi_r = obb(P["waraxe_21"]); AX = (lo_r.x + hi_r.x) / 2          # the haft axis: the centre of the collar ring
RING_Y = (lo_r.y + hi_r.y) / 2
lo_t, hi_t = obb(P["waraxe_10"])                                     # the twist-langet tube
BIT_PARTS = ["waraxe_00", "waraxe_01", "waraxe_04", "waraxe_05", "waraxe_08"]
blo = Vector((min(obb(P[p])[0][i] for p in BIT_PARTS) for i in range(3)))
BIT_TOP = obb(P["waraxe_04"])[1].y                                    # the bit's top edge strip: the top of the bit
BIT_LO_Y = min(obb(P[p])[0].y for p in ("waraxe_05", "waraxe_08"))   # the bit's lower end (cutting edge and beard strips)
BIT_CY = (BIT_LO_Y + BIT_TOP) / 2; BIT_H = BIT_TOP - BIT_LO_Y; BIT_REACH = AX - blo.x
SPIKE_TOP = max(obb(P[p])[1].y for p in ("waraxe_02", "waraxe_03"))

# the approved Ebony mace's measures (its build_designs.py constants on the ebony axe's parts)
E_CORE = (29.5, 29.5 + 0.75 * (32.81 - 16.25))      # head core span
E_FLANGE_H = 0.62 * (40.13 - 21.13)                # flange height
E_FLANGE_REACH = 0.48 * (13.6 + 0.65)              # flange reach from the haft axis before the 0.9 pull-in
E_RINGS = (41.6 - 4.0 + (3.57 + 4.5) / 2, 29.4 - 4.0 + (3.57 + 4.5) / 2)     # crown and base ring centres
E_SPIKE = (42.0, 42.0 + 0.85 * (46.42 - 38.03), 0.85 * (2.2 + 1.0))          # point base, tip, width

REP["measures"] = {"axis_x": round(AX, 3), "bit": [round(BIT_LO_Y, 2), round(BIT_TOP, 2), round(BIT_REACH, 2)],
                   "tube": [round(lo_t.y, 2), round(hi_t.y, 2)], "ring_y": round(RING_Y, 2), "spike_top": round(SPIKE_TOP, 2)}

# ---------------------------------------------------------------- MACE (one-handed) - all steel war axe, atlas axe1h
HAFT = ["waraxe_10"] + ["waraxe_%02d" % i for i in range(11, 24)]
for pid in HAFT:
    add(dup(P[pid], "mace_" + pid), pid, "haft, socket, collar, grip and pommel kept as the steel war axe has them" if pid == HAFT[0] else None)
# head core: a second twist-langet tube stacked above the first, spanning what the Ebony core spans
sy = (E_CORE[1] - E_CORE[0]) / (hi_t.y - lo_t.y)
core = dup(P["waraxe_10"], "mace_core"); xform(core, T(0, E_CORE[0], 0) @ S(1, sy, 1) @ T(0, -lo_t.y, 0))
add(core, "waraxe_10", "a second twist-langet tube (x%.3f tall) as the head core, %.2f..%.2f as the Ebony mace's" % (sy, E_CORE[0], E_CORE[1]))
# six flanges: the steel bit (head plate faces left of the haft and below the bit's top, and its three edge strips),
# scaled to the Ebony flange's height and reach, arrayed every 60 deg
fy = E_FLANGE_H / BIT_H; fx = E_FLANGE_REACH / BIT_REACH; fz = 0.62
CUT_X = AX - 1.15                                    # the Ebony recipe kept faces left of x = -0.5 with its axis at 0.65
for k in range(6):
    for pid in ["waraxe_00", "waraxe_01", "waraxe_04", "waraxe_05", "waraxe_08"]:
        f = dup(P[pid], "mace_flange%d_%s" % (k, pid))
        if pid in ("waraxe_00", "waraxe_01"): keep_faces(f, lambda c: c.x < CUT_X and c.y < BIT_TOP + 0.01)
        M = T(AX, 0, 0) @ R(60 * k, "Y") @ T(-0.9, 36.0, 0) @ S(fx, fy, fz) @ T(-AX, -BIT_CY, 0)
        xform(f, M)
        add(f, pid, ("the steel axe's knotwork bit as a flange (x%.3f tall, x%.3f deep, x%.2f thick - the Ebony flange's size), "
                     "6 around the head" % (fy, fx, fz)) if k == 0 and pid == "waraxe_00" else None)
# crown: collar ring at the top band and under the flanges, at the Ebony mace's heights. The steel ring is sized for the
# haft and sat flush inside the head core's +x langet (draft 1: both bands hidden); it is widened so it stands proud of
# the core by the margin the Ebony ring has over the Ebony core (+0.09 at +x), and given the Ebony band's height (0.93)
RCZ = (lo_r.z + hi_r.z) / 2
RK = (hi_t.x + 0.09 - AX) / (hi_r.x - AX); RKY = (4.5 - 3.57) / (hi_r.y - lo_r.y)
for nm, yc in (("mace_crownring", E_RINGS[0]), ("mace_basering", E_RINGS[1])):
    r_ = dup(P["waraxe_21"], nm); xform(r_, T(AX, yc, RCZ) @ S(RK, RKY, RK) @ T(-AX, -RING_Y, -RCZ))
    add(r_, "waraxe_21", "the steel collar ring as the head's %s band, x%.3f wide and x%.3f tall to stand proud of the core as the Ebony band does"
        % ("top" if "crown" in nm else "lower", RK, RKY))
# point: the steel axe's top spike (plate faces above the bit near the haft + its two edge strips), scaled to the Ebony
# point's length and width, its foot (cut at the bit's top) seated just inside the crown ring
SPK_LO = BIT_TOP
spk = []
for pid in ["waraxe_00", "waraxe_01", "waraxe_02", "waraxe_03"]:
    s = dup(P[pid], "mace_spike_" + pid)
    keep_faces(s, lambda c: c.y > SPK_LO and abs(c.x - AX) < 2.0)
    spk.append(s)
slo = Vector((min(obb(o)[0][i] for o in spk) for i in range(3))); shi = Vector((max(obb(o)[1][i] for o in spk) for i in range(3)))
sw = shi.x - slo.x; sl = shi.y - SPK_LO
base = E_SPIKE[0] - 0.25
ky = (E_SPIKE[1] - base) / sl; kx = E_SPIKE[2] / sw
for s in spk:
    xform(s, T(AX, base, 0) @ S(kx, ky, kx) @ T(-AX, -SPK_LO, 0))
    add(s, s["from"], "the steel axe's top spike above the bit as the crown point (x%.2f wide, x%.2f long - the Ebony point's size)" % (kx, ky) if s is spk[0] else None)
REP["recipe"] = {"core_scale_y": round(sy, 4), "flange_scale": [round(fx, 4), round(fy, 4), fz], "spike_scale": [round(kx, 4), round(ky, 4)],
                 "spike_source_y": [round(SPK_LO, 2), round(shi.y, 2)], "pieces": len(MACE)}
json.dump(LOG, open(os.path.join(os.environ["NSAW_WORK"], "provenance_mace.json"), "w"), indent=1)

# ---------------------------------------------------------------- game-ready (the Ebony build_stage.py functions, unchanged)
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

for o in MACE: assert o.matrix_world == Matrix.Identity(4), o.name
atlases = sorted({o["tex"] for o in MACE}); assert atlases == ["axe1h"], atlases
for o in list(bpy.data.objects):
    if o not in MACE: bpy.data.objects.remove(o)

HEAD_Y = 26.0                                       # where the head starts (blood region, collision split) - as Ebony's
REP["head_split_y"] = {"mace": HEAD_Y}
mace = join(MACE, "mace_axe1h"); mace["tex"] = "axe1h"
REP["orient"] = orient_outward([mace])
export_single(mace, os.path.join(OUTD, "mace_axe1h.nif")); dump_points([mace], "mace")
before = set(bpy.data.objects); bpy.ops.import_scene.pynifly(filepath=VAN_MACE, import_collisions=False)
van = [o for o in bpy.data.objects if o not in before]; uvb = blood_uv_box(van)
for o in van: bpy.data.objects.remove(o)
b = make_blood([mace], HEAD_Y, "mace_blood", uvb)
export_single(b, os.path.join(OUTD, "mace_blood.nif"))
REP["blood"] = {"faces": len(b.data.polygons), "uv_box": [list(uvb[0]), list(uvb[1])]}
lo, hi = obb(mace); REP["mace_bbox"] = [[round(x, 2) for x in lo], [round(x, 2) for x in hi]]; REP["faces"] = len(mace.data.polygons)
json.dump(REP, open(os.path.join(os.environ["NSAW_WORK"], "stage_report.json"), "w"), indent=1, default=str)
print("STAGE DONE", json.dumps(REP["recipe"]), REP["mace_bbox"])
