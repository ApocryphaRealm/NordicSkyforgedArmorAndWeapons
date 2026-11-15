# The Skyforge Steel BOW's game NIF. The bow is the Ebony replacer's approved bow (rendition r03, owner-reviewed
# 2026-11-14) built by its own unchanged pipeline (ebony_pipeline\, run by tools/build-missing-weapons.py), then moved onto
# the Skyforged set's own STEEL textures:
#   * BowMesh:0 (limbs, grip, collars, rings, talons - all cut from the Wolf sword) takes the steel sword's shader and
#     texture set (Legacy of Ysgramor's Sword.nif, sword1h). Measured 2026-11-15: the steel and ebony swords are the same
#     mesh with the same UVs part for part, and their atlases share one layout (the normal maps are identical at the
#     collar's chosen windows: guard border px 855-975 x 1127-1187, bar px 1246-1258 x 130-222) - so every UV the Ebony
#     bow uses lands on the same feature of the steel sword: the gold of the ebony colourway is the steel sword's own dark
#     steel there.
#   * BowMesh:1 (the string and its nock loops - the ebony war axe's wrapped grip) is re-mapped onto the steel war axe's
#     braided grip: the ebony wrap's island (u 0.5361..0.8262 along the grip, decreasing toward the head; v 0.0479..0.2764
#     round it) -> the steel grip's (v 0.1357..0.6255 along, increasing toward the head; u 0.7485..0.9702 round), the same
#     fraction along and round, then the steel war axe's shader and texture set (axe1h).
# Everything else is the Ebony assemble.build_bow: vanilla's ebonybowskinned.nif node tree and bones, our skinned shapes
# spliced in, SLSF1 Skinned on both shaders, the convex hull rebuilt on Bow_MidBone's frame.
import os, sys, struct
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import niflib
from assemble import shape, shapes_of, give_shader, parent_of, new_string, append_child, rewrite_hull, drop_orphans, save

ROLE_ATLAS = {"bow_sword1hebony": "sword1h", "bow_axe1hebony": "axe1h"}
WRAP_EBONY = {"u": (0.5361328125, 0.826171875), "v": (0.0478515625, 0.2763671875)}     # along = u (decreasing), round = v
WRAP_STEEL = {"u": (0.74853515625, 0.97021484375), "v": (0.1357421875, 0.62548828125)}  # along = v (increasing), round = u


def remap_wrap_uv(n, b):
    """the string/loop shape's UVs, in its skin partition's vertex buffer (SSE: 40-byte vertices, UV half floats at 16)"""
    o = n.av_end(b, 0, [], []); sk = struct.unpack_from("<i", n.blocks[b], o + 16)[0]; assert sk >= 0
    part = struct.unpack_from("<i", n.blocks[sk], 4)[0]; pb = n.blocks[part]
    _, dsize, stride = struct.unpack_from("<III", pb, 0); assert stride == 40, stride
    raw = np.frombuffer(bytes(pb[20:20 + dsize]), np.uint8).reshape(-1, stride).copy()
    U = raw[:, 16:20].copy().view(np.float16).astype(np.float64)
    fa = (WRAP_EBONY["u"][1] - U[:, 0]) / (WRAP_EBONY["u"][1] - WRAP_EBONY["u"][0])      # 0 at the pommel end, 1 at the head end
    # the ranges above are Blender's (v up); a NIF stores v down: v_nif = 1 - v
    fr = ((1 - U[:, 1]) - WRAP_EBONY["v"][0]) / (WRAP_EBONY["v"][1] - WRAP_EBONY["v"][0])
    # the nock loops' faces given their own flat UV windows (Ebony build_stage flat_uv_faces) run past the ebony island
    # round the grip (0.3 below it, 0.1 above); on the steel atlas the island ends at the atlas' black padding, so the
    # round-the-grip range actually used is fitted inside the steel island instead of copied 1:1
    out_ = int(((fr < -0.02) | (fr > 1.02) | (fa < -0.02) | (fa > 1.02)).sum())
    lo_, hi_ = min(0.0, fr.min()), max(1.0, fr.max()); fr = 0.01 + 0.98 * (fr - lo_) / (hi_ - lo_)
    nu = WRAP_STEEL["u"][0] + fr * (WRAP_STEEL["u"][1] - WRAP_STEEL["u"][0])
    nv = 1 - (WRAP_STEEL["v"][0] + fa * (WRAP_STEEL["v"][1] - WRAP_STEEL["v"][0]))
    raw[:, 16:20] = np.stack([nu, nv], 1).astype(np.float16).view(np.uint8).reshape(-1, 4)
    pb[20:20 + dsize] = raw.tobytes()
    return {"vertices": int(len(raw)), "ebony_uv_range": [np.round(U.min(0), 4).tolist(), np.round(U.max(0), 4).tolist()],
            "steel_uv_range": [[round(float(nu.min()), 4), round(float(nv.min()), 4)], [round(float(nu.max()), 4), round(float(nv.max()), 4)]],
            "outside_ebony_island": out_, "round_range_fitted": [round(float(lo_), 3), round(float(hi_), 3)]}


def build_bow(van_path, out_path, shapes_dir, loy_dir):
    """the Ebony assemble.build_bow with the role -> steel atlas map, then the wrap re-map"""
    n = niflib.Nif(van_path); s = niflib.Nif(os.path.join(shapes_dir, "bow_skinned.nif"))
    bones_v = {n.name(b): b for b, t in enumerate(n.btypes) if t == "NiNode"}
    main = shape(n, "BowMesh:0")
    ne0 = struct.unpack_from("<I", n.blocks[main], 4)[0]; vflags = struct.unpack_from("<I", n.blocks[main], 8 + 4 * ne0 + 4)[0]
    vskin = n.i32(main, n.av_end(main, 0, [], []) + 16); vdata, vpart = struct.unpack_from("<ii", n.blocks[vskin], 0)
    assert n.btypes[vskin] == "NiSkinInstance"
    skel_root = struct.unpack_from("<i", n.blocks[vskin], 8)[0]
    src = {s.name(b): b for b in shapes_of(s)}; rep = {"vanilla_skin": n.btypes[vskin]}
    order = ["bow_sword1hebony", "bow_axe1hebony"]; assert sorted(src) == sorted(order), sorted(src)
    for role in order:
        sb = src[role]; so = s.av_end(sb, 0, [], []); sk = s.i32(sb, so + 16); sd, sp = struct.unpack_from("<ii", s.blocks[sk], 0)
        assert s.btypes[sk] in ("NiSkinInstance", "BSDismemberSkinInstance"), s.btypes[sk]
        if role == order[0]:
            idx_shape, idx_skin, idx_data, idx_part = main, vskin, vdata, vpart; nm = struct.unpack_from("<i", n.blocks[main], 0)[0]
        else:
            idx_shape, idx_skin, idx_data, idx_part = (len(n.blocks) + i for i in range(4))
            for t in ("BSTriShape", "NiSkinInstance", "NiSkinData", "NiSkinPartition"): n.btypes.append(t); n.blocks.append(bytearray())
            nm = new_string(n, "BowMesh:1"); append_child(n, parent_of(n, main), idx_shape)
        blk = bytearray(s.blocks[sb]); struct.pack_into("<i", blk, 0, nm); struct.pack_into("<3i", blk, so + 16, idx_skin, -1, -1)
        n.btypes[idx_shape] = "BSTriShape"; n.blocks[idx_shape] = blk
        k = bytearray(s.blocks[sk]); nb = struct.unpack_from("<I", k, 12)[0]; k = k[:16 + 4 * nb]
        struct.pack_into("<iii", k, 0, idx_data, idx_part, skel_root)
        names = []
        for j in range(nb):
            nmj = s.name(struct.unpack_from("<i", k, 16 + 4 * j)[0]); names.append(nmj); struct.pack_into("<i", k, 16 + 4 * j, bones_v[nmj])
        n.btypes[idx_skin] = "NiSkinInstance"; n.blocks[idx_skin] = k
        n.btypes[idx_data] = "NiSkinData"; n.blocks[idx_data] = bytearray(s.blocks[sd])
        n.btypes[idx_part] = "NiSkinPartition"; n.blocks[idx_part] = bytearray(s.blocks[sp])
        give_shader(n, idx_shape, loy_dir, ROLE_ATLAS[role], skinned=True)
        ne = struct.unpack_from("<I", n.blocks[idx_shape], 4)[0]; struct.pack_into("<I", n.blocks[idx_shape], 8 + 4 * ne + 4, vflags)
        rep[role] = {"shape": n.name(idx_shape), "atlas": ROLE_ATLAS[role], "bones": names}
        if ROLE_ATLAS[role] == "axe1h":
            rep[role]["wrap_uv_remap"] = remap_wrap_uv(n, idx_shape)
    rep["collision"] = rewrite_hull(n, np.load(os.path.join(shapes_dir, "points_bow.npy")))
    rep["orphans_dropped"] = drop_orphans(n)
    save(n, out_path); rep["blocks"] = len(n.blocks); return rep
