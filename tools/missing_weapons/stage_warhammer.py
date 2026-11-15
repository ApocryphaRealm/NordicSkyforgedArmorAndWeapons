# The Blender half of the Skyforge Steel WARHAMMER: the Ebony replacer's approved warhammer (its build_designs.py
# WARHAMMER section, round 1, and build_v1face.py round 3 "ext=5.0 art chamfer=0.8" with the build_stage.py face fix,
# 2026-11-14) re-mapped onto Legacy of Ysgramor's STEEL battle axe, then made game-ready as the Ebony build_stage.py
# makes its warhammer, and exported as single-shape NIFs for assemble.py.
#
# THE OWNER'S CORRECTIONS ON THE EBONY WARHAMMER, all carried:
#   * 2026-11-14 00:36 - the V1 head (the battle axe minus its bit, the butt cap turned forward as the hammer, a ring
#     where it meets the socket); only the striking end changes: cut flat at the cap's widest front section, a FLAT
#     CIRCULAR face built from scratch, gnarled edge to edge with square pyramid teeth (45-degree facets, clipped to the
#     circle, a wall closing each clipped edge);
#   * 01:09 - a plain round extension (5.0 on the Ebony paw; here the length that keeps the Ebony reach) before the face; 01:17 - the extension carries the butt cap's own band;
#     01:30 - the lip tapered in at 45 degrees (chamfer 0.8);
#   * 06:48 (in game: "a flat tan disc with a diagonal smear") - the face on blade steel whose NORMAL map is flat, and
#     every tooth facet on its own vertices (harden) so the teeth light as teeth.
#
# WHAT CHANGES FOR THE STEEL BATTLE AXE (measured 2026-11-15, every loose part compared):
#   * the steel axe's parts are the ebony axe's, moved by (-0.30, 0, -1.13) - the recipe's coordinates are shifted by the
#     measured offset of the haft tube (battleaxe_10), not typed in;
#   * the steel axe has NO paw butt cap: its butt is a studded cuff (battleaxe_24) and a moulded end cap (battleaxe_25).
#     Those two are the hammer, turned forward as the paw was, scaled so the cut face has the Ebony face's radius (5.34);
#   * no gold in the Wolf Black atlas: the ring is the steel collar ring (battleaxe_21), the lip takes the end cap's own
#     rim rows, the extension continues the steel end cap's moulded band from the cut (its UVs read off the cut itself);
#   * the face window (atlas px 1392-1464 x 368-440, the blade) was re-measured on the steel atlas axe2h: normal map
#     red/green std 2.3 / 3.0 of 255 (flat, as on the ebony atlas), plain brushed steel - the same window is kept.
# Run (by tools/build-missing-weapons.py): blender --background --factory-startup --python-exit-code 1 --python stage_warhammer.py
#   env NSAW_BAXE (the LoY steel BattleAxe.nif), NSAW_VAN_WARHAMMER (vanilla ebonywarhammer.nif - its blood UVs), NSAW_WORK
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from stage_lib import *
BAXE = os.environ["NSAW_BAXE"]; VAN_WH = os.environ["NSAW_VAN_WARHAMMER"]
REP = {"notes": []}

for o in list(bpy.data.objects): bpy.data.objects.remove(o)
P = load_parts(BAXE, "battleaxe")
REP["parts_checked"] = check_parts(P, os.path.join(HERE, "parts_expected_steel_battleaxe.json"))

WH, LOG = [], []
def add(o, part, how):
    o["item"] = "warhammer"; WH.append(o)
    if how: LOG.append({"part": part, "how": how})

# ---------------------------------------------------------------- the offset from the ebony battle axe (its haft tube)
E_TUBE_X, E_TUBE_Z = (-1.54 + 2.93) / 2, (-0.62 + 2.8) / 2          # ebony battleaxe_10 (parts_expected.json of the Ebony repo)
lo10, hi10 = obb(P["battleaxe_10"])
DX = (lo10.x + hi10.x) / 2 - E_TUBE_X; DZ = (lo10.z + hi10.z) / 2 - E_TUBE_Z
CY, CZ = 43.5, 1.1 + DZ                     # the hammer axis (the Ebony design's CY, CZ moved with the axe)
HX = -1.1 + DX                              # the hammer's socket end
REP["offset_from_ebony"] = [round(DX, 3), 0.0, round(DZ, 3)]

# ---------------------------------------------------------------- round 1: the battle axe minus its bit
for i in range(26):
    pid = "battleaxe_%02d" % i
    if pid in ("battleaxe_04", "battleaxe_05", "battleaxe_08"): continue          # the bit's edge strips go with the bit
    o = dup(P[pid], "wh_" + pid)
    if pid in ("battleaxe_00", "battleaxe_03"):
        keep_faces(o, lambda c: c.x > -1.3 + DX or (c.y > 49.0 and c.x > -2.6 + DX))   # head plate minus the bit
    add(o, pid, "battle axe kept: haft, grip, butt, socket, top spike, back fang" if i == 0 else None)

# the hammer: the steel butt (studded cuff + moulded end cap) turned forward as the Ebony paw cap was
ham_parts = [dup(P["battleaxe_24"], "wh_hammer_cuff"), dup(P["battleaxe_25"], "wh_hammer_end")]
blo = Vector((min(obb(o)[0][i] for o in ham_parts) for i in range(3))); bhi = Vector((max(obb(o)[1][i] for o in ham_parts) for i in range(3)))
c = Vector(((blo.x + bhi.x) / 2, bhi.y, (blo.z + bhi.z) / 2))
ham = join(ham_parts, "wh_hammer"); ham["tex"] = "axe2h"; ham["src"] = "battleaxe_24+25"
xform(ham, T(HX, CY, CZ) @ R(-90, "Z") @ S(1.75) @ T(-c.x, -c.y, -c.z))

def profile(o):
    vs = [v.co for v in o.data.vertices]; xs = [p.x for p in vs]; xmin, xmax = min(xs), max(xs); bins = {}
    for p in vs:
        k = round(p.x * 4) / 4; r = math.hypot(p.y - CY, p.z - CZ); bins[k] = max(bins.get(k, 0), r)
    front = {k: r for k, r in bins.items() if k < (xmin + xmax) / 2}
    xc = max(front, key=lambda k: front[k]); return xc, front[xc], bins
R_EBONY = 5.340781689697771                 # the Ebony face's radius (its round3\face_ext_art_ch.json)
_, r175, _ = profile(ham)
HS = 1.75 * R_EBONY / r175                  # the scale that gives the Ebony face's radius
xform(ham, T(HX, CY, CZ) @ S(HS / 1.75) @ T(-HX, -CY, -CZ))
XC, _, bins = profile(ham)
REP["hammer"] = {"scale": round(HS, 4), "cut_x": XC, "profile": sorted((k, round(r, 2)) for k, r in bins.items())}
add(ham, "battleaxe_24+25", "the steel butt (studded cuff + moulded end cap) turned to face forward, x%.3f (the Ebony face's radius) - the hammer" % HS)

# the rows of the end cap the extension continues: per angle, the cut row's UV (read off the cut below) and the UV of
# the cap's frontmost point at that angle (its rim) - sampled BEFORE the cut takes the front away
def ang(p): return math.atan2(p.z - CZ, -(p.y - CY))
me = ham.data; uvd = me.uv_layers.active.data
front_uv = {}
for l in me.loops:
    p = me.vertices[l.vertex_index].co
    if math.hypot(p.y - CY, p.z - CZ) < 0.5: continue
    k = int((ang(p) + math.pi) / (2 * math.pi) * 48) % 48
    if k not in front_uv or p.x < front_uv[k][0]: front_uv[k] = (p.x, tuple(uvd[l.index].uv))

# the cut: flat at the widest front section (Ebony round 3)
bm = bmesh.new(); bm.from_mesh(ham.data)
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(XC, 0, 0), plane_no=(-1, 0, 0), clear_outer=True)
bm.to_mesh(ham.data); bm.free()
bnd, cut_uv = [], []
bm = bmesh.new(); bm.from_mesh(ham.data); uvl0 = bm.loops.layers.uv.active
for e in bm.edges:
    if len(e.link_faces) == 1 and all(abs(v.co.x - XC) < 1e-3 for v in e.verts):
        bnd.append((e.verts[0].co.copy(), e.verts[1].co.copy()))
        for v in e.verts:
            for l in v.link_loops: cut_uv.append((ang(v.co), tuple(l[uvl0].uv)))
bm.free()
RAD = max(math.hypot(p.y - CY, p.z - CZ) for e in bnd for p in e)

# the steel collar ring where the hammer meets the socket (the Ebony gold ring's place), standing proud of the hammer
rg = dup(P["battleaxe_21"], "wh_hammerring"); rlo, rhi = obb(rg); rc = (rlo + rhi) / 2
RX = -2.0 + DX
r_at = max((r for k, r in bins.items() if abs(k - RX) <= 0.5), default=RAD)
rk = 1.08 * r_at / (max(rhi.x - rlo.x, rhi.z - rlo.z) / 2)
xform(rg, T(RX, CY, CZ) @ R(-90, "Z") @ S(rk) @ T(-rc.x, -rc.y, -rc.z))
add(rg, "battleaxe_21", "the steel collar ring (x%.3f, 8%% proud of the hammer) where the hammer meets the socket" % rk)

# ---------------------------------------------------------------- round 3: extension, 45-degree lip, gnarled face
# the Ebony extension is 5.0; scaled to the Ebony face radius the steel butt reaches further than the paw did, so the
# extension is shortened by that much to keep the Ebony hammer's reach (socket end to face)
E_REACH = (-7.25 - 5.0) - (-1.1)            # the Ebony face plane relative to its hammer's socket end (round3 face json)
PITCH, HT, NSEG, CH = 0.62, 0.31, 96, 0.8
EXT = max(2.0, (XC - HX) - E_REACH)
FU0, FV0, FUW = 1392 / 2048, 1 - 440 / 2048, 72 / 2048              # the blade's flat-normal steel (re-measured on axe2h)

# the band's u round the circle, from the cut's own UVs: u = U_LO + frac((s * a - a0) / 2pi) * (U_HI - U_LO)
us = [uv[0] for a, uv in cut_uv]; U_LO, U_HI = min(us), max(us)
best = None
for s in (1, -1):
    for i in range(360):
        a0 = 2 * math.pi * i / 360
        err = sum((U_LO + (((s * a - a0) / (2 * math.pi)) % 1.0) * (U_HI - U_LO) - uv[0]) ** 2 for a, uv in cut_uv)
        if best is None or err < best[0]: best = (err, s, a0)
_, SGN, A0 = best
REP["band_u_fit"] = {"u": [round(U_LO, 4), round(U_HI, 4)], "sign": SGN, "seam_deg": round(math.degrees(A0), 1),
                     "rms": round(math.sqrt(best[0] / len(cut_uv)), 4)}
def frac(a): return ((SGN * a - A0) / (2 * math.pi)) % 1.0
def nearest_v(samples, a):
    return min(samples, key=lambda t: abs(math.atan2(math.sin(t[0] - a), math.cos(t[0] - a))))[1]
cut_v = [(a, uv[1]) for a, uv in cut_uv]
# the rim rows, median-filtered over 5 neighbouring angles (the end cap is lobed: its frontmost point jumps between lobes)
_rv = {k: uv[1] for k, (x, uv) in front_uv.items()}
rim_v = [(-math.pi + (k + 0.5) / 48 * 2 * math.pi, sorted(_rv[(k + d) % 48] for d in range(-2, 3) if (k + d) % 48 in _rv)[2 if all((k + d) % 48 in _rv for d in range(-2, 3)) else 0])
         for k in _rv]
# draft 1 (2026-11-15) ran the band 0.92 of the way to the rim and the lip just inside it: both landed in the island's
# lobes and its stretched padding (streaks). The drum takes the moulding's first half from the cut, the lip the row
# just past it (the ridge), clear of the lobes.
DRUM_SPAN, LIP_ROWS = 0.50, (0.50, 0.56)

fb = bmesh.new(); uvl = fb.loops.layers.uv.new("UVMap")
def uv_of(p): return (FU0 + (p.y - CY + RAD) / (2 * RAD) * FUW, FV0 + (p.z - CZ + RAD) / (2 * RAD) * FUW)
def poly(pts, outward):
    vv = [fb.verts.new(p) for p in pts]; f = fb.faces.new(vv); f.normal_update()
    if f.normal.dot(outward) < 0: f.normal_flip()
    f.smooth = False
    for l in f.loops: l[uvl].uv = uv_of(l.vert.co)
    return f
RF = RAD - CH
circle = [(RF * math.cos(2 * math.pi * i / NSEG), RF * math.sin(2 * math.pi * i / NSEG)) for i in range(NSEG)]
def clip(poly2):
    out = poly2
    for i in range(NSEG):
        a, b = circle[i], circle[(i + 1) % NSEG]; inp = out; out = []
        if not inp: break
        def side(p): return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        for j in range(len(inp)):
            Pp, Q = inp[j], inp[(j + 1) % len(inp)]; sp, sq = side(Pp), side(Q)
            if sp >= 0: out.append(Pp)
            if (sp >= 0) != (sq >= 0):
                t = sp / (sp - sq); out.append(tuple(Pp[k] + (Q[k] - Pp[k]) * t for k in range(3)))
    return out
XF = XC - EXT
def W(u, v, h): return Vector((XF - h, CY + u, CZ + v))
n = int(math.ceil(2 * RF / PITCH)); off = -n * PITCH / 2
teeth = whole = walls = 0
for i in range(n):
    for j in range(n):
        u0, v0 = off + i * PITCH, off + j * PITCH; u1, v1 = u0 + PITCH, v0 + PITCH; ap = ((u0 + u1) / 2, (v0 + v1) / 2, HT)
        corners = [(u0, v0, 0), (u1, v0, 0), (u1, v1, 0), (u0, v1, 0)]
        if all(math.hypot(cc[0], cc[1]) <= RF for cc in corners): whole += 1
        any_in = False
        for k in range(4):
            cp = clip([corners[k], corners[(k + 1) % 4], ap])
            if len(cp) < 3: continue
            area = abs(sum(cp[m][0] * cp[(m + 1) % len(cp)][1] - cp[(m + 1) % len(cp)][0] * cp[m][1] for m in range(len(cp)))) / 2
            if area < 1e-6: continue
            any_in = True
            poly([W(*p) for p in cp], Vector((-1, 0, 0)))
            for m in range(len(cp)):
                Pp, Q = cp[m], cp[(m + 1) % len(cp)]
                if abs(math.hypot(Pp[0], Pp[1]) - RF) < 1e-4 and abs(math.hypot(Q[0], Q[1]) - RF) < 1e-4 and (Pp[2] > 1e-5 or Q[2] > 1e-5):
                    mid = Vector((0, (Pp[0] + Q[0]) / 2, (Pp[1] + Q[1]) / 2))
                    poly([W(*Pp), W(*Q), W(Q[0], Q[1], 0), W(Pp[0], Pp[1], 0)], mid); walls += 1
        teeth += any_in
def to_circle(p):
    dy, dz = p.y - CY, p.z - CZ; r = math.hypot(dy, dz) or 1; return Vector((XC, CY + dy * RAD / r, CZ + dz * RAD / r))
for a, b in bnd:                             # skirt: the cut section out to the face circle, flat in the cut plane
    if (to_circle(a) - a).length < 1e-4 and (to_circle(b) - b).length < 1e-4: continue
    poly([a, b, to_circle(b), to_circle(a)] if (to_circle(b) - b).length > 1e-4 and (to_circle(a) - a).length > 1e-4 else
         ([a, b, to_circle(b)] if (to_circle(b) - b).length > 1e-4 else [a, b, to_circle(a)]), Vector((-1, 0, 0)))
# the extension (a drum of radius R from the cut to the lip) and the 45-degree lip, on the end cap's own band
bands = [(XC, RAD, XF + CH, RAD), (XF + CH, RAD, XF, RAD - CH)]
for (xa, ra, xb, rb), i in [(b, i) for b in bands for i in range(NSEG)]:
    a0, a1 = 2 * math.pi * i / NSEG, 2 * math.pi * (i + 1) / NSEG
    Pq = [Vector((xa, CY + ra * math.cos(a0), CZ + ra * math.sin(a0))), Vector((xa, CY + ra * math.cos(a1), CZ + ra * math.sin(a1))),
          Vector((xb, CY + rb * math.cos(a1), CZ + rb * math.sin(a1))), Vector((xb, CY + rb * math.cos(a0), CZ + rb * math.sin(a0)))]
    vv = [fb.verts.new(q) for q in Pq]; f = fb.faces.new(vv); f.normal_update()
    mid = Vector((0, math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2)))
    if f.normal.dot(mid) < 0: f.normal_flip()
    f.smooth = True
    angs = [ang(l.vert.co) for l in f.loops]; frs = [frac(a) for a in angs]
    if max(frs) - min(frs) > 0.5:            # a face across the band's seam: its corners on one side, as the Ebony face does
        low = sum(1 for x in frs if x < 0.5) * 2 >= len(frs)
        frs = [0.0 if (low and x > 0.5) else (1.0 if (not low and x < 0.5) else x) for x in frs]
    lip = min(l.vert.co.x for l in f.loops) < XF + CH - 1e-4
    for l, a, fr in zip(f.loops, angs, frs):
        vc, vr = nearest_v(cut_v, a), nearest_v(rim_v, a)
        if lip:   # the lip: a narrow run of rows just inside the end cap's rim (the Ebony lip's gold rows' place)
            t = (XF + CH - l.vert.co.x) / CH; v = vc + (vr - vc) * (LIP_ROWS[0] + (LIP_ROWS[1] - LIP_ROWS[0]) * t)
        else:
            t = (XC - l.vert.co.x) / (EXT - CH); v = vc + (vr - vc) * DRUM_SPAN * t
        l[uvl].uv = (U_LO + fr * (U_HI - U_LO), v)
bmesh.ops.remove_doubles(fb, verts=fb.verts[:], dist=1e-5)
fme = bpy.data.meshes.new("wh_face"); fb.to_mesh(fme); fb.free()
face = bpy.data.objects.new("wh_face", fme); bpy.context.scene.collection.objects.link(face)
face["tex"] = "axe2h"; face["src"] = "new"
for p in fme.polygons: p.use_smooth = p.use_smooth and abs(p.normal.x) < 0.2
# the rim walls stand edge-on to the face's planar projection: each projected along its own normal (build_stage.py)
uvd = fme.uv_layers.active.data; nwall = 0
for p in fme.polygons:
    uv = [uvd[li].uv.copy() for li in p.loop_indices]
    if not all(FU0 - 1e-4 <= u <= FU0 + FUW + 1e-4 and FV0 - 1e-4 <= v <= FV0 + FUW + 1e-4 for u, v in uv): continue
    area = abs(sum(uv[i].x * uv[(i + 1) % len(uv)].y - uv[(i + 1) % len(uv)].x * uv[i].y for i in range(len(uv)))) / 2
    if area > 1e-9: continue
    nrm = p.normal; tang = Vector((0, -nrm.z, nrm.y)).normalized()
    for li in p.loop_indices:
        q = fme.vertices[fme.loops[li].vertex_index].co - Vector((XF, CY, CZ))
        uvd[li].uv = (FU0 + FUW / 2 + q.dot(tang) / (2 * RAD) * FUW, FV0 + FUW / 2 + q.x / (2 * RAD) * FUW)
    nwall += 1
REP["face"] = {"cut_x": round(XC, 3), "radius": round(RAD, 4), "teeth": teeth, "whole": whole, "walls": walls, "faces": len(fme.polygons),
               "walls_reprojected": nwall, "hard_edges_split": harden(face), "uv_window_px": [1392, 368, 72], "ext": EXT, "chamfer": CH}
add(face, "new", "a flat circular striking face from scratch: %d square pyramid teeth (pitch %.2f, height %.2f, 45 deg) clipped to the circle, "
    "on the blade's flat-normal steel; a %.2f extension and a 45-degree lip on the end cap's own band" % (teeth, PITCH, HT, EXT))
json.dump(LOG, open(os.path.join(os.environ["NSAW_WORK"], "provenance_warhammer.json"), "w"), indent=1)

# ---------------------------------------------------------------- game-ready (as the Ebony build_stage.py's warhammer)
for o in WH: assert o.matrix_world == Matrix.Identity(4), o.name
atlases = sorted({o["tex"] for o in WH}); assert atlases == ["axe2h"], atlases
for o in list(bpy.data.objects):
    if o not in WH: bpy.data.objects.remove(o)
HEAD_Y = 38.0
REP["head_split_y"] = {"warhammer": HEAD_Y}
wh = join(WH, "warhammer_axe2h"); wh["tex"] = "axe2h"
REP["orient"] = orient_outward([wh])
export_single(wh, os.path.join(OUTD, "warhammer_axe2h.nif")); dump_points([wh], "warhammer")
before = set(bpy.data.objects); bpy.ops.import_scene.pynifly(filepath=VAN_WH, import_collisions=False)
van = [o for o in bpy.data.objects if o not in before]; uvb = blood_uv_box(van)
for o in van: bpy.data.objects.remove(o)
b = make_blood([wh], HEAD_Y, "warhammer_blood", uvb)
export_single(b, os.path.join(OUTD, "warhammer_blood.nif"))
REP["blood"] = {"faces": len(b.data.polygons), "uv_box": [list(uvb[0]), list(uvb[1])]}
lo, hi = obb(wh); REP["bbox"] = [[round(x, 2) for x in lo], [round(x, 2) for x in hi]]; REP["faces"] = len(wh.data.polygons)
json.dump(REP, open(os.path.join(os.environ["NSAW_WORK"], "stage_report.json"), "w"), indent=1, default=str)
print("STAGE DONE", json.dumps(REP["face"]), REP["hammer"]["scale"], REP["bbox"])
