# The Blender half of the Skyforge Steel ARROW (the loose arrow, the arrow in flight) and the QUIVER with its six quiver
# arrows: the Ebony replacer's approved designs (build_designs.py ARROW, build_round2.py quiver, and build_stage.py's arrow
# shaft, nock, closing and quiver turn, 2026-11-14) re-mapped onto Legacy of Ysgramor's STEEL war axe and steel dagger,
# made game-ready as the Ebony build_stage.py does, and exported as single-shape NIFs for assemble_arrow.py.
#
# THE OWNER'S CORRECTIONS ON THE EBONY ARROW AND QUIVER, all carried:
#   * one shape per quiver arrow on one atlas (the game hides Arrow1..Arrow6 by name) - the shaft is the war axe's wrapped
#     grip, like the head, vanes and nock;
#   * 2026-11-14 06:48 - the nock: a slotted steel nock (slot across the arrow, square to the cock vane at +z) with a collar
#     where it meets the shaft, the vanes moved back to meet it; 07:15 - no light through the nocked arrow: the head and
#     each vane welded whole, their holes capped, the caps two-sided;
#   * 06:48 - "the quiver is inside out": turned 180 degrees about its long axis, the decorated side out, the ring at the
#     mouth against the back and still pointing up; the six quiver arrows turn with it.
#
# WHAT CHANGES FOR THE STEEL PIECES (measured 2026-11-15):
#   * dagger: identical to the ebony dagger (parts, positions, UVs) - the quiver body ports as it is, on the steel atlas;
#   * war axe: cut differently. Arrowhead = the steel axe's spike above the bit (its head plate and spike are one piece),
#     scaled to the Ebony head's length and width; vanes and the quiver's fang plate = the steel back fang, first mapped into
#     the ebony fang's frame (its bounding box: x 1.57..10.72 -> 1.33..11.18, y 30.97..38.17 -> 31.56..39.2) so the Ebony
#     placements apply unchanged; the shaft = the steel axe's braided grip (waraxe_22, one piece, 21 units) in 3 lengths
#     (the ebony grip was 12.8 units, in 4) at the Ebony shaft's length and radius; the collars (nock, quiver mouth) = the
#     steel collar ring (waraxe_21) at the Ebony gold collar's size;
#   * no gold: the nock's steel window was re-picked on the Wolf Black atlas - the Ebony window (px 1656-1688 x 328-360)
#     is NOT flat on axe1h (normal map green std 49 of 255); px 1960-1992 x 1792-1824 is the plain steel of the braided
#     grip's cuff beside its rivets (colour std 3.9, normal std ~2).
# Run (by tools/build-missing-weapons.py): blender --background --factory-startup --python-exit-code 1 --python stage_arrow.py
#   env NSAW_AXE, NSAW_DAGGER (LoY steel Axe.nif, Dagger.nif), NSAW_VAN_ARROW (vanilla ebonyarrow.nif), NSAW_WORK
import bpy, bmesh, sys, os, json, math, random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from stage_lib import *
import niflib
AXE = os.environ["NSAW_AXE"]; DAG = os.environ["NSAW_DAGGER"]; VAN_ARROW = os.environ["NSAW_VAN_ARROW"]
REP = {"notes": []}
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
P = load_parts(AXE, "waraxe"); REP["parts_checked"] = check_parts(P, os.path.join(HERE, "parts_expected_steel.json"))
PD = load_parts(DAG, "dagger"); REP["parts_checked"] += check_parts(PD, os.path.join(HERE, "parts_expected_steel_dagger.json"))
P.update(PD)
LOG = []
def note(item, part, how): LOG.append({"item": item, "part": part, "how": how})

lo_r, hi_r = obb(P["waraxe_21"]); AX = (lo_r.x + hi_r.x) / 2; RCZ = (lo_r.z + hi_r.z) / 2
BIT_TOP = obb(P["waraxe_04"])[1].y
SPIKE_TOP = max(obb(P[p])[1].y for p in ("waraxe_02", "waraxe_03"))

def fang_pieces(prefix):
    """the steel back fang (plate faces behind the haft below the spike, + its three edge strips) in the EBONY fang's frame"""
    out = []
    for pid in ("waraxe_00", "waraxe_01", "waraxe_06", "waraxe_07", "waraxe_09"):
        f = dup(P[pid], "%s_%s" % (prefix, pid))
        for v in f.data.vertices:
            x, y, z = v.co; v.co = Vector((1.33 + (x - 1.57) * (9.85 / 9.15), 31.56 + (y - 30.97) * (7.64 / 7.20), z))
        f.data.update()
        if pid in ("waraxe_00", "waraxe_01"): keep_faces(f, lambda c: c.x > 2.0 and c.y < 39.2)
        out.append(f)
    return out

# ---------------------------------------------------------------- ARROW (design frame: points -y, nock at 0; Ebony round 1)
ARROW = []
# head: the steel spike above the bit, at the Ebony head's size (0.78 x its 8.39-long, 3.2-wide spike)
spk = []
for pid in ("waraxe_00", "waraxe_01", "waraxe_02", "waraxe_03"):
    s = dup(P[pid], "arrow_waraxe_" + pid[-2:]); keep_faces(s, lambda c: c.y > BIT_TOP and abs(c.x - AX) < 2.0); spk.append(s)
slo = Vector((min(obb(o)[0][i] for o in spk) for i in range(3))); shi = Vector((max(obb(o)[1][i] for o in spk) for i in range(3)))
hky = 0.78 * (46.42 - 38.03) / (shi.y - BIT_TOP); hkx = 0.78 * 3.2 / (shi.x - slo.x)
for s in spk: xform(s, T(0, -55.0, 0) @ R(180, "Z") @ S(hkx, hky, hkx) @ T(-AX, -BIT_TOP, -RCZ)); ARROW.append(s)
note("arrow", "waraxe_00..03", "the steel axe's spike above the bit as the arrowhead (x%.3f wide, x%.3f long - the Ebony head's size)" % (hkx, hky))
# vanes: the back fang x3 (Ebony placement on the ebony-frame fang)
for k in range(3):
    for f in fang_pieces("arrow_vane%d" % k):
        for v in f.data.vertices:
            x, y, z = v.co; ylow = 34.0 - (x - 2.0) * (2.5 / 9.2)
            v.co = Vector((z * 0.5, -4.5 + (x - 11.2) * 0.9, 0.33 + max(0.0, y - ylow) * 0.30))
        f.data.update(); xform(f, R(120 * k, "Y")); ARROW.append(f)
note("arrow", "waraxe fang", "the steel axe's back fang (x0.9 long, x0.3 high, in the ebony fang's frame) as each of three vanes")
for o in ARROW: xform(o, T(0, -61.5, 0) @ R(180, "Z"))      # vanilla's arrow points +y (Ebony design, 2026-11-14)

# shaft (Ebony build_stage: the approved shaft's length and radius, y -60.0..-6.5, radius 0.3315, on the axe's grip wrap)
SH_LO, SH_HI, rad, cx, cz = -60.0, -6.5, 0.3315, 0.0, 0.0
g = P["waraxe_22"]; glo, ghi = obb(g); gcen = (glo + ghi) / 2; glen = ghi.y - glo.y; grad = max(ghi.x - glo.x, ghi.z - glo.z) / 2
NSEG = max(1, round((SH_HI - SH_LO) / glen * 1.2)); seg = (SH_HI - SH_LO) / NSEG
for k in range(NSEG):
    s = dup(g, "arrow_shaftseg%d" % k)
    xform(s, T(cx, SH_LO + (k + 0.5) * seg, cz) @ S(rad / grad, seg / glen, rad / grad) @ T(-gcen.x, -gcen.y, -gcen.z)); ARROW.append(s)
REP["arrow_shaft"] = {"length": SH_HI - SH_LO, "radius": rad, "segments": NSEG, "source": "waraxe_22 (the steel axe's braided grip, axe1h)"}
note("arrow", "waraxe_22", "the steel axe's braided grip, %d lengths stacked, as the shaft" % NSEG)

# nock (Ebony build_stage, owner 2026-11-14 06:48) on the steel window
YEND = -61.5
RN = rad * 1.35; DN = 2 * rad; NL, SD, SW = 3.0 * DN, 1.3 * DN, 0.55 * DN
NU0, NV0, NUW = 1960 / 2048, 1 - 1824 / 2048, 32 / 2048
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=24, radius1=RN, radius2=RN, depth=NL)
bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(-90), 3, "X"))
bmesh.ops.translate(bm, verts=bm.verts, vec=(cx, YEND + NL / 2, cz))
me = bpy.data.meshes.new("arrow_nock_new"); bm.to_mesh(me); bm.free()
nock = bpy.data.objects.new("arrow_nocknew", me); bpy.context.scene.collection.objects.link(nock)
cut = bpy.data.objects.new("nock_slot", bpy.data.meshes.new("nock_slot")); bpy.context.scene.collection.objects.link(cut)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
bmesh.ops.scale(bm, verts=bm.verts, vec=(4 * RN, 2 * SD, SW)); bmesh.ops.translate(bm, verts=bm.verts, vec=(cx, YEND, cz)); bm.to_mesh(cut.data); bm.free()
bo = nock.modifiers.new("slot", "BOOLEAN"); bo.operation = "DIFFERENCE"; bo.solver = "EXACT"; bo.object = cut
dg = bpy.context.evaluated_depsgraph_get(); me2 = bpy.data.meshes.new_from_object(nock.evaluated_get(dg))
nock.modifiers.clear(); nock.data = me2; bpy.data.objects.remove(cut)
bm = bmesh.new(); bm.from_mesh(nock.data); uvl = bm.loops.layers.uv.new("UVMap"); bm.normal_update()
for f in bm.faces:
    ax = max(range(3), key=lambda i: abs(f.normal[i])); a, b = [i for i in range(3) if i != ax]
    for l in f.loops:
        q = l.vert.co; o_ = (cx, YEND + NL / 2, cz)
        l[uvl].uv = (NU0 + (0.5 + (q[a] - o_[a]) / NL) * NUW, NV0 + (0.5 + (q[b] - o_[b]) / NL) * NUW)
bm.to_mesh(nock.data); bm.free()
nhard = harden(nock)
assert len(nock.data.polygons) > 26, ("the slot boolean failed", len(nock.data.polygons))
gap = [v.co for v in nock.data.vertices if v.co.y < YEND + 1e-4]
assert gap and min(abs(p.z - cz) for p in gap) > SW / 2 - 1e-3, "the nock's end is not slotted"
nock["tex"] = "axe1h"; nock["src"] = "new_nock"
col = dup(P["waraxe_21"], "arrow_nockcollar"); c21 = Vector((AX, lo_r.y + (hi_r.y - lo_r.y) / 2, RCZ))
RC = RN * 1.12
xform(col, T(cx, YEND + NL, cz) @ S(2 * RC / (hi_r.x - lo_r.x), 0.24 * NL / (hi_r.y - lo_r.y), 2 * RC / (hi_r.z - lo_r.z)) @ T(-c21.x, -c21.y, -c21.z))
vanes = [o for o in ARROW if o.name.startswith("arrow_vane")]
vrear = min(min(v.co.y for v in o.data.vertices) for o in vanes); DV = (YEND + NL) - vrear
for o in vanes: xform(o, T(0, DV, 0))
ARROW += [nock, col]
REP["arrow_nock"] = {"end_y": YEND, "length": round(NL, 3), "radius": round(RN, 3), "slot_depth": round(SD, 3), "slot_width": round(SW, 3),
                     "uv_window_px": [1960, 1792, 32], "hard_edges_split": nhard, "vanes_moved_back_by": round(-DV, 3), "collar": "waraxe_21"}
# every arrow piece closed (owner 07:15): head and each vane welded whole, holes capped
# the steel collar ring is an open band (the ebony gold collar was closed): light came through it at the nock (0.0047
# on the arrow in flight, first build 2026-11-15) - it is welded and capped like the head and vanes
for nm_, pre in [("arrow_head", "arrow_waraxe_"), ("arrow_collar", "arrow_nockcollar")] + [("arrow_vane%d" % k, "arrow_vane%d_" % k) for k in range(3)]:
    pcs = [o for o in ARROW if o.name.startswith(pre)]; assert pcs, pre
    for o in pcs: ARROW.remove(o)
    ARROW.append(weld_join(pcs, nm_))
REP["arrow_holes_capped"] = {o.name: n_ for o in ARROW if o.name.startswith(("arrow_head", "arrow_vane", "arrow_collar")) for n_ in [cap_holes(o)] if n_}
REP["arrow_welded_hard_edges_split"] = {o.name: harden(o) for o in ARROW if o.name.startswith(("arrow_head", "arrow_vane", "arrow_collar"))}

# ---------------------------------------------------------------- QUIVER (Ebony round 2) on vanilla ebonyarrow.nif's layout
van = import_nif(VAN_ARROW)
vq = [o for o in van if o.name.startswith("ArrowQuiver")][0]
varrows = sorted([o for o in van if o.name[:5] == "Arrow" and o.name[5:6].isdigit()], key=lambda o: o.name)
def pca(pts):
    c = sum(pts, Vector()) / len(pts)
    C = [[sum((p[i] - c[i]) * (p[j] - c[j]) for p in pts) / len(pts) for j in range(3)] for i in range(3)]
    v = Vector((0.3, 1.0, 0.1)).normalized()
    for _ in range(60): v = Vector([sum(C[i][j] * v[j] for j in range(3)) for i in range(3)]).normalized()
    return c, v
qp = [vq.matrix_world @ v.co for v in vq.data.vertices]; qc, _ = pca(qp); qd = Vector()
for o in varrows:
    _, d = pca([o.matrix_world @ v.co for v in o.data.vertices]); qd += d if d.y > 0 else -d
qd.normalize()
ap = sum([[o.matrix_world @ v.co for v in o.data.vertices] for o in varrows], []); ac = sum(ap, Vector()) / len(ap)
if (ac - qc).dot(qd) > 0: qd = -qd
proj = [(p - qc).dot(qd) for p in qp]; qlen = max(proj) - min(proj)
axis0 = ac - qd * (ac - qc).dot(qd)
mouth = axis0 + qd * ((qc - axis0).dot(qd) + min(proj))
side = [(p - qc) - qd * (p - qc).dot(qd) for p in qp]
_, e2 = pca([qc + s for s in side])
e3 = e2.cross(qd).normalized(); e2 = qd.cross(e3).normalized()
w2 = max(s.dot(e2) for s in side) - min(s.dot(e2) for s in side); w3 = max(s.dot(e3) for s in side) - min(s.dot(e3) for s in side)
Q = [dup(P["dagger_%02d" % i], "q_dagger_%02d" % i) for i in range(7, 42)]
note("quiver", "dagger_07..41", "the steel dagger's whole scabbard scaled up as the quiver body")
qcol = dup(P["waraxe_21"], "q_collar"); cq = Vector((AX, lo_r.y, RCZ))
xform(qcol, T(0, 4.55, 0) @ S(1.28 * 3.89 / (hi_r.x - lo_r.x), 0.9 * 0.93 / (hi_r.y - lo_r.y), 1.45 * 2.83 / (hi_r.z - lo_r.z)) @ T(-cq.x, -cq.y, -cq.z)); Q.append(qcol)
note("quiver", "waraxe_21", "the steel collar ring, at the Ebony gold collar's size, round the quiver mouth")
for f in fang_pieces("q_fang"):
    for v in f.data.vertices:
        x, y, z = v.co; v.co = Vector(((y - 35.3) * 0.36, 20.8 + (x - 2.0) * 0.52, 1.62 + (z + 0.6) * 0.35))
    f.data.update(); Q.append(f)
note("quiver", "waraxe fang", "the steel back fang, x0.52, on the front of the quiver between the lower strap and the chape")
sy = qlen / (34.3 - 4.7); sx = min(max(w2 / 5.6, 1.6), 3.0); sz = min(max(w3 / 3.4, 1.6), 2.8)
Mbasis = Matrix((e2, qd, e3)).transposed().to_4x4()
MQ = T(*mouth) @ Mbasis @ S(sx, sy, sz) @ T(0, -4.7, 0)
for o in Q: xform(o, MQ)
QA = []
for k, va in enumerate(varrows):
    pts = [va.matrix_world @ v.co for v in va.data.vertices]; c, d = pca(pts)
    pr = [(p - c).dot(d) for p in pts]; e_a = c + d * min(pr); e_b = c + d * max(pr)
    nk, inner = (e_a, e_b) if (e_a - mouth).dot(-qd) > (e_b - mouth).dot(-qd) else (e_b, e_a)
    L = (inner - nk).length; dirv = (inner - nk).normalized()
    rot = Vector((0, 1, 0)).rotation_difference(dirv).to_matrix().to_4x4()
    for o in ARROW:
        n = dup(o, "qa%d_%s" % (k, o.name)); keep_faces(n, lambda cc: cc.y < -61.5 + L)
        if not n.data.polygons: bpy.data.objects.remove(n); continue
        xform(n, T(*nk) @ rot @ R(40 * k, "Y") @ T(0, 61.5, 0)); n["qa"] = va.name.split(".")[0]; QA.append(n)
note("quiver", "arrow", "six of the new arrows (nock half) on vanilla's six quiver-arrow placements")
# the quiver turned 180 degrees about its body's long axis (owner 2026-11-14 06:48), the quiver arrows with it
_qd, _e3 = qd.normalized(), e3.normalized(); _e2 = _qd.cross(_e3).normalized(); _m = mouth
_body = [o for o in Q if o.name.startswith("q_dagger_")]
_pts = [v.co - _m for o in _body for v in o.data.vertices]
_c = _m + _e2 * ((max(p.dot(_e2) for p in _pts) + min(p.dot(_e2) for p in _pts)) / 2) + _e3 * ((max(p.dot(_e3) for p in _pts) + min(p.dot(_e3) for p in _pts)) / 2)
_turn = Matrix.Translation(_c) @ Matrix.Rotation(math.pi, 4, _qd) @ Matrix.Translation(-_c)
for o in Q + QA: xform(o, _turn)
REP["quiver"] = {"scale": [round(sx, 3), round(sy, 3), round(sz, 3)], "turned_deg": 180, "axis": [round(x, 4) for x in _qd]}
for o in van: bpy.data.objects.remove(o)
json.dump(LOG, open(os.path.join(os.environ["NSAW_WORK"], "provenance_arrow.json"), "w"), indent=1)

# ---------------------------------------------------------------- game-ready (the Ebony build_stage.py arrow and quiver)
def shapes_by_atlas(item, objs):
    groups = {}
    for o in objs: groups.setdefault(o["tex"], []).append(o)
    return {tex: join(groups[tex], "%s_%s" % (item, tex)) for tex in sorted(groups)}
for o in ARROW + Q + QA: assert o.matrix_world == Matrix.Identity(4), o.name
qn = niflib.Nif(VAN_ARROW)
aq = [b for b in range(len(qn.blocks)) if qn.btypes[b] == "NiNode" and qn.name(b) == "ArrowQuiver"][0]
_, qt, qr, qs = qn.transform(aq)
assert max(abs(qr[i] - (1, 0, 0, 0, 1, 0, 0, 0, 1)[i]) for i in range(9)) < 1e-5 and abs(qs - 1) < 1e-6, ("ArrowQuiver is turned or scaled", qr, qs)
QAN = {}
for o in QA: QAN.setdefault(o["qa"], []).append(o)
assert sorted(QAN) == ["Arrow%d" % i for i in range(1, 7)], sorted(QAN)
for nm, lst in QAN.items(): assert {o["tex"] for o in lst} == {"axe1h"}, (nm, {o["tex"] for o in lst})
arrow = shapes_by_atlas("arrow", ARROW); assert list(arrow) == ["axe1h"], list(arrow)
quiver = shapes_by_atlas("quiver", Q); assert sorted(quiver) == ["axe1h", "dagger"], sorted(quiver)
qarrows = {nm: join(lst, nm) for nm, lst in sorted(QAN.items())}
REP["orient"] = orient_outward([arrow["axe1h"]])
REP["orient"].update(orient_outward(list(quiver.values()) + list(qarrows.values())))
REP["arrow_cap_twins"] = {o.name: double_caps(o) for o in [arrow["axe1h"]] + list(qarrows.values())}
export_single(arrow["axe1h"], os.path.join(OUTD, "arrow.nif")); dump_points([arrow["axe1h"]], "arrow")
for o in list(quiver.values()) + list(qarrows.values()):
    o.data.transform(Matrix.Translation((-qt[0], -qt[1], -qt[2]))); o.data.update()
dump_points(list(quiver.values()), "quiver")
for tex, o in quiver.items(): export_single(o, os.path.join(OUTD, "quiver_%s.nif" % tex))
for nm, o in qarrows.items(): export_single(o, os.path.join(OUTD, "quiver_%s.nif" % nm))
REP["head_split_y"] = {}
lo, hi = obb(arrow["axe1h"]); REP["arrow_bbox"] = [[round(x, 2) for x in lo], [round(x, 2) for x in hi]]
json.dump(REP, open(os.path.join(os.environ["NSAW_WORK"], "stage_report.json"), "w"), indent=1, default=str)
print("STAGE DONE", REP["arrow_bbox"], REP["quiver"])
