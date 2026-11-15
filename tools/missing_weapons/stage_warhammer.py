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

# the hammer (owner 2026-11-15: "the Warhammer doesn't match the Ebony version, because the Skyforged version is square
# shaped currently, but it should be the rounded shape with the same design work equivalent"). The steel axes have no
# paw cap, so the round barrel takes the SHAPE of the Ebony hammer's - Legacy of Ysgramor's ebony battle axe paw cap
# (battleaxe_26), placed exactly as the Ebony recipe places it - and is re-surfaced from scratch on the steel atlas: the
# rune band engraved on the steel battle axe's haft wrapped round it in two rows, as the Ebony head carries its handle's braid.
EB = load_parts(os.environ["NSAW_BAXE_EBONY"], "ebaxe")
paw = EB["ebaxe_26"]; plo, phi = obb(paw)
assert max(abs(plo[i] - v) for i, v in enumerate((-3.65, -49.0, -2.77))) < 0.02 and \
       max(abs(phi[i] - v) for i, v in enumerate((2.44, -42.36, 1.56))) < 0.02, ("not the ebony paw cap", plo, phi)
ham = dup(paw, "wh_hammer"); ham["tex"] = "axe2h"; ham["src"] = "ebony battleaxe_26, shape only"
c = Vector((-0.6, -42.36, -0.6))                                     # the Ebony recipe's own pivot on the paw
xform(ham, T(HX, CY, CZ) @ R(-90, "Z") @ S(1.75) @ T(-c.x, -c.y, -c.z))

def profile(o):
    vs = [v.co for v in o.data.vertices]; xs = [p.x for p in vs]; xmin, xmax = min(xs), max(xs); bins = {}
    for p in vs:
        k = round(p.x * 4) / 4; r = math.hypot(p.y - CY, p.z - CZ); bins[k] = max(bins.get(k, 0), r)
    front = {k: r for k, r in bins.items() if k < (xmin + xmax) / 2}
    xc = max(front, key=lambda k: front[k]); return xc, front[xc], bins
R_EBONY = 5.340781689697771                 # the Ebony face's radius (its round3\face_ext_art_ch.json)
XC, r_cut, bins = profile(ham)
REP["hammer"] = {"shape": "ebony paw cap x1.75 (the Ebony recipe)", "cut_x": XC, "cut_r": round(r_cut, 3),
                 "profile": sorted((k, round(r, 2)) for k, r in bins.items())}
assert abs(r_cut - R_EBONY) < 0.15, ("the cut radius is not the Ebony face's", r_cut)
add(ham, "ebony battleaxe_26", "a round barrel in the shape of the Ebony hammer's (the ebony paw cap x1.75, placed as the Ebony recipe places it), "
    "surfaced from scratch on the steel atlas")
def ang(p): return math.atan2(p.z - CZ, -(p.y - CY))

# the cut: flat at the widest front section (Ebony round 3)
bm = bmesh.new(); bm.from_mesh(ham.data)
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(XC, 0, 0), plane_no=(-1, 0, 0), clear_outer=True)
bm.to_mesh(ham.data); bm.free()
bnd = []
bm = bmesh.new(); bm.from_mesh(ham.data)
for e in bm.edges:
    if len(e.link_faces) == 1 and all(abs(v.co.x - XC) < 1e-3 for v in e.verts):
        bnd.append((e.verts[0].co.copy(), e.verts[1].co.copy()))
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
E_REACH = (-7.25 - 5.0) - (-1.1)            # the Ebony face plane relative to its hammer's socket end (round3 face json)
PITCH, HT, NSEG, CH = 0.62, 0.31, 96, 0.8
EXT = max(2.0, (XC - HX) - E_REACH)
FU0, FV0, FUW = 1392 / 2048, 1 - 440 / 2048, 72 / 2048              # the blade's flat-normal steel (re-measured on axe2h)
XF = XC - EXT

# ---- the surface: zones along the hammer (a = distance from the socket end), each on its own atlas window
# the owner, 2026-11-15 15:11: "wrap the added hammerhead with the Nordic text that's on the handle, since the ebony piece has
# what's on its handle wrapped around it" - the haft's rune band (the strip that reads the right way round; the one above
# it is its mirror), once round the drum per row, never mirrored so the runes read
RUNES = (690, 1400, 1797, 1903)  # atlas px x0, x1, y0, y1: the engraved rune band on the battle axe haft
RSIGN = 1                        # which way round the runes run (checked on the render: they must read, not mirror)
PLAIN = (1364, 1420, 388, 444)   # plain head-plate steel beside the face window (lowest texture + normal variation, 64 px scan)
RING = (0.7759, 0.9756, 0.9544, 0.9721)                              # the steel collar ring's own strip (u0, u1, v0, v1)
def px(x, y): return (x / 2048, 1 - y / 2048)
def tri(t):
    t = t % 2.0; return t if t <= 1 else 2 - t
def frac_of(p, turn=0.0): return ((ang(p) + math.pi) / (2 * math.pi) + turn) % 1.0
A0 = min(HX - v.co.x for v in ham.data.vertices)                    # where the barrel starts, socket end
AL = HX - (XF + CH)                                                  # where the lip starts
MARG = 0.45
NROW = 2                         # two rows: one rune band round the drum is close to the band's own proportions
HROW = (AL - A0 - 2 * MARG) / NROW
CUTS = [A0 + MARG + k * HROW for k in range(NROW + 1)]               # zone boundaries (geometry is cut there)
def zone(a):
    if a > AL + 1e-4: return "lip"
    if a < CUTS[0] or a > CUTS[-1]: return "plain"
    return "row%d" % min(int((a - CUTS[0]) / HROW), NROW - 1)
def uv_at(p, z, flat=False, fr=None):
    a = HX - p.x
    if flat:   # a face square to the axis (a step or end ring): its depth along the zone runs with the radius instead
        r = math.hypot(p.y - CY, p.z - CZ); a = A0 + (r / RAD) * (AL - A0) if z == "plain" else a
    if z == "lip":
        f = frac_of(p); t = min(max((a - AL) / CH, 0), 1)
        return (RING[0] + f * (RING[1] - RING[0]), RING[3] - t * (RING[3] - RING[2]))
    if z == "plain":
        s = tri(4 * frac_of(p)); t = min(max(a - A0, 0) / max(AL - A0, 1e-3), 1)
        return px(PLAIN[0] + s * (PLAIN[1] - PLAIN[0]), PLAIN[2] + t * (PLAIN[3] - PLAIN[2]))
    k = int(z[3:])
    s = fr if fr is not None else rune_frac(p, k); t = min(max((a - CUTS[k]) / HROW, 0), 1)
    return px(RUNES[0] + s * (RUNES[1] - RUNES[0]), RUNES[2] + t * (RUNES[3] - RUNES[2]))
def rune_frac(p, k): return (RSIGN * frac_of(p) + 0.5 * k) % 1.0     # the second row turned half round: seams apart
def surface(o):
    """cut the mesh at every zone boundary, then give each face the UVs of its zone (no face spans two windows)"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    for a in CUTS + [AL]:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(HX - a, 0, 0), plane_no=(1, 0, 0))
    uvl = bm.loops.layers.uv.active or bm.loops.layers.uv.new("UVMap")
    count = {}
    for f in bm.faces:
        f.normal_update(); flat = abs(f.normal.x) > 0.7
        z = "plain" if flat and zone(HX - f.calc_center_median().x) != "lip" else zone(HX - f.calc_center_median().x)
        count[z] = count.get(z, 0) + 1
        frs = [None] * len(f.loops)
        if z.startswith("row"):    # one band round, not mirrored: a face across the band's seam keeps its corners together
            frs = [rune_frac(l.vert.co, int(z[3:])) for l in f.loops]
            if max(frs) - min(frs) > 0.5: frs = [x + 1.0 if x < 0.5 else x for x in frs]
        for l, fr in zip(f.loops, frs):
            l[uvl].uv = uv_at(l.vert.co, z, flat, fr)
    bm.to_mesh(o.data); bm.free(); count["hard_edges_split"] = harden(o); return count
REP["surface"] = {"runes_px": RUNES, "plain_px": PLAIN, "ring_uv": RING, "a0": round(A0, 3), "lip_a": round(AL, 3),
                  "row_h": round(HROW, 3), "barrel_faces_by_zone": surface(ham)}

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
# the extension (a drum of radius RAD from the cut to the lip) and the 45-degree lip: their own object, surfaced by zone
eb_ = bmesh.new()
XS = sorted({XC, XF + CH, XF} | {HX - a for a in CUTS if XF + CH < HX - a < XC}, reverse=True)
def r_of(x): return RAD if x >= XF + CH - 1e-6 else RAD - (XF + CH - x)
for xa, xb in zip(XS, XS[1:]):
    for i in range(NSEG):
        a0, a1 = 2 * math.pi * i / NSEG, 2 * math.pi * (i + 1) / NSEG; ra, rb = r_of(xa), r_of(xb)
        Pq = [Vector((xa, CY + ra * math.cos(a0), CZ + ra * math.sin(a0))), Vector((xa, CY + ra * math.cos(a1), CZ + ra * math.sin(a1))),
              Vector((xb, CY + rb * math.cos(a1), CZ + rb * math.sin(a1))), Vector((xb, CY + rb * math.cos(a0), CZ + rb * math.sin(a0)))]
        vv = [eb_.verts.new(q) for q in Pq]; f = eb_.faces.new(vv); f.normal_update()
        mid = Vector((0, math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2)))
        if f.normal.dot(mid) < 0: f.normal_flip()
        f.smooth = True
bmesh.ops.remove_doubles(eb_, verts=eb_.verts[:], dist=1e-5)
xme = bpy.data.meshes.new("wh_ext"); eb_.to_mesh(xme); eb_.free(); xme.uv_layers.new(name="UVMap")
ext = bpy.data.objects.new("wh_ext", xme); bpy.context.scene.collection.objects.link(ext); ext["tex"] = "axe2h"; ext["src"] = "new"
REP["surface"]["ext_faces_by_zone"] = surface(ext)
add(ext, "new", "a %.2f round extension continuing the barrel's rune rows, and a 45-degree lip on the steel collar ring's own strip" % EXT)
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
    "on the blade's flat-normal steel" % (teeth, PITCH, HT))
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
print("STAGE DONE", json.dumps(REP["face"]), REP["hammer"]["cut_r"], REP["bbox"])
