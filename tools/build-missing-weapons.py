#!/usr/bin/env python3
r"""Build the game meshes of the Skyforge Steel weapon types the game has no Skyforge version of - the same set the
Nordic Ebony Armor and Weapons Replacer gained in 1.1.0 (mace, warhammer, bow, arrows and quiver), built one at a time
(the owner, 2026-11-15: "start building the other weapon types that we haven't built yet. Just do them one at a time").

BUILT SO FAR
    mace       ->  meshes\NordicSkyforge\weapons\Mace.nif and 1stPersonMace.nif       (missing_weapons\stage_mace.py)
    warhammer  ->  meshes\NordicSkyforge\weapons\Warhammer.nif and 1stPersonWarhammer.nif (missing_weapons\stage_warhammer.py)
    arrow      ->  meshes\NordicSkyforge\weapons\Arrow.nif (with the quiver) and ArrowProjectile.nif (missing_weapons\stage_arrow.py)
    bow        ->  meshes\NordicSkyforge\weapons\Bow.nif (the Ebony r03 bow, ebony_pipeline\ + assemble_bow.py; its first-person
                   record uses the same file)
    first person -> meshes\NordicSkyforge\weapons\1stPersonSword/Greatsword/Axe/BattleAxe/Dagger.nif for the five weapons
                   the mod already had (FIRST_PERSON, first_person_files)

WHERE THE ART COMES FROM
    Every piece is cut from NordwarUA's own STEEL Wolf war axe (Legacy of Ysgramor, Nexus 109963 - modification and
    asset use allowed with credit) and keeps its own UVs on that axe's atlas, which this mod already ships in Xtudo's
    Wolf Black colourway. No new texture. The recipe is the Ebony replacer's approved mace (2026-11-14), re-mapped onto
    the steel axe's parts - see missing_weapons\stage_mace.py. The repository carries no Legacy of Ysgramor art and no
    Bethesda art:
      * Legacy of Ysgramor's steel war axe is read out of its Nexus download at build time;
      * the vanilla ebony mace's NIFs - the node tree, blood shapes and collision the new meshes are built on, as the
        Ebony replacer's mace is - are read out of the player's own Skyrim - Meshes0/1.bsa.

STEPS
    1. extract Axe.nif (Main Archive) and vanilla ebonymace.nif / 1stpersonebonymace.nif (game BSA) into the work folder
    2. Blender, headless: missing_weapons\stage_mace.py builds the mace and exports single shapes
    3. missing_weapons\assemble.py (shared with the Ebony replacer) splices them into vanilla's NIFs and takes the steel
       war axe's own shader and texture set; the two collision boxes are refitted
    4. missing_weapons\verify.py (shared): node tree, collision node, texture paths, UVs and tangent frames, smoothed-over
       hard edges, winding - fails the build. Light-through is measured and reported, as on the Ebony mace.
    niflib.py, winding.py, bsa.py, assemble.py, verify.py and wolf_lib.py are the Ebony replacer's, copied unchanged.

ENVIRONMENT (each optional)
    NSAW_DOWNLOADS  the folder holding the Nexus downloads (default: the MO2 instance's download_directory)
    NSAW_MO2        an MO2 instance folder (default D:\Modlists\Njordlinger)
    SKYRIM_DATA     the game's Data folder (default: the MO2 instance's gamePath + \Data)
    BLENDER         blender.exe (default: on PATH, else the newest under Program Files\Blender Foundation)

Usage:  python tools/build-missing-weapons.py <output meshes folder> [--work <folder>]
        (build-package.py calls it and ships the result in 00 Core)
"""
import glob, json, os, re, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MW = os.path.join(HERE, "missing_weapons")
sys.path.insert(0, MW)

MESH_DIR = ("NordicSkyforge", "weapons")
# item -> its Blender stage, the Legacy of Ysgramor steel weapon it is cut from (and the env var the stage reads it from),
# the vanilla ebony NIFs it is built on, and the built files: {our file: (vanilla file, vanilla main shape - verify's "ours")}
ITEMS = {
    "mace": {"stage": "stage_mace.py", "loy": "Axe.nif", "env": "NSAW_AXE", "van_env": "NSAW_VAN_MACE",
             "outputs": {"Mace.nif": ("ebonymace.nif", "EbonyMace:0"),
                         "1stPersonMace.nif": ("1stpersonebonymace.nif", "1stPersonEbonyMace:0")}},
    # the hammer's round barrel is the shape of Legacy of Ysgramor's EBONY battle axe paw cap (the Ebony replacer's hammer),
    # re-surfaced on the steel atlas - so the ebony battle axe is read too (owner 2026-11-15: rounded, as the Ebony one)
    "warhammer": {"stage": "stage_warhammer.py", "loy": "BattleAxe.nif", "env": "NSAW_BAXE", "van_env": "NSAW_VAN_WARHAMMER",
                  "extra_loy": {"NSAW_BAXE_EBONY": "BattleAxeEbony.nif"},
                  "outputs": {"Warhammer.nif": ("ebonywarhammer.nif", "EbonyWarhammer:0"),
                              "1stPersonWarhammer.nif": ("1stpersonebonywarhammer.nif", "1stPersonEbonyWarhammer:0")}},
    # the arrow (with its quiver and six quiver arrows) and the arrow in flight; no first-person file (ammunition has none)
    "arrow": {"stage": "stage_arrow.py", "loy": "Axe.nif", "env": "NSAW_AXE", "van_env": "NSAW_VAN_ARROW", "kind": "arrow",
              "extra_loy": {"NSAW_DAGGER": "Dagger.nif"},
              "outputs": {"Arrow.nif": ("ebonyarrow.nif", ("Arrow:0", "ArrowQuiver:0", "ArrowQuiver:1") + tuple("Arrow%d" % k for k in range(1, 7))),
                          "ArrowProjectile.nif": ("ebonyarrowprojectile.nif", ("EbonyArrowFlight:0",))}},
    # the bow: the Ebony replacer's approved r03 bow built by its own pipeline (missing_weapons\ebony_pipeline\, copied
    # unchanged), then moved onto the steel sword's and steel war axe's textures by missing_weapons\assemble_bow.py
    "bow": {"kind": "bow", "loy": "Sword.nif", "env": "NSAW_SWORD", "van_env": "NSAW_VAN_BOW",
            "outputs": {"Bow.nif": ("ebonybowskinned.nif", ("BowMesh:0", "BowMesh:1"))}},
}
# FIRST-PERSON FILES for the five Skyforge weapons the mod already had (sword, greatsword, war axe, battleaxe, dagger) -
# the way the Nordic Ebony replacer made its first-person set (assemble.first_person_copy): the Legacy of Ysgramor
# weapon's 3rd-person model under a first-person name, its root renamed to vanilla's first-person root, NOT moved.
# Not moved because Legacy of Ysgramor's own plugin points these same five Skyforge Steel weapons' first-person statics
# at the 3rd-person file (checked 2026-11-15: SkyforgeSteelSword WNAM -> NordWar\Companions\Weapons\Sword.nif, and so on).
# Vanilla's own steel pairs are moved slightly (greatsword 1.79 along the blade, war axe 0.99 across) - reported, not used.
#   LoY 3rd-person file: (our 1st-person file, vanilla 3rd-person steel file, vanilla 1st-person steel file)
FIRST_PERSON = {"Sword.nif": ("1stPersonSword.nif", "steelsword.nif", "1stpersonsteelsword.nif"),
                "Greatsword.nif": ("1stPersonGreatsword.nif", "steelgreatsword.nif", "1stpersonsteelgreatsword.nif"),
                "Axe.nif": ("1stPersonAxe.nif", "steelwaraxe.nif", "1stpersonsteelwaraxe.nif"),
                "BattleAxe.nif": ("1stPersonBattleAxe.nif", "steelbattleaxe.nif", "1stpersonsteelbattleaxe.nif"),
                "Dagger.nif": ("1stPersonDagger.nif", "steeldagger.nif", "1stpersonsteeldagger.nif")}
# the Ebony pipeline's inputs: Legacy of Ysgramor's ebony weapons under the vanilla names it reads them by, and the vanilla
# ebony meshes it builds on (the Ebony replacer's build-missing-weapons.py LOY and VANILLA lists)
EBONY_LOY = {"SwordEbony.nif": "ebonysword.nif", "GreatswordEbony.nif": "ebonygreatsword.nif", "AxeEbony.nif": "ebonywaraxe.nif",
             "BattleAxeEbony.nif": "ebonybattleaxe.nif", "DaggerEbony.nif": "ebonydagger.nif", "ShieldEbony.nif": "ebonyshield.nif"}
EBONY_VANILLA = ["ebonymace.nif", "1stpersonebonymace.nif", "ebonywarhammer.nif", "1stpersonebonywarhammer.nif",
                 "ebonybowskinned.nif", "ebonyarrow.nif", "ebonyarrowprojectile.nif",
                 "ebonysword.nif", "1stpersonebonysword.nif", "ebonygreatsword.nif", "1stpersonebonygreatsword.nif",
                 "ebonywaraxe.nif", "1stpersonebonywaraxe.nif", "ebonybattleaxe.nif", "1stpersonebonybattleaxe.nif",
                 "ebonydagger.nif", "1stpersonebonydagger.nif", "ebonyshield.nif"]
# light through the mesh, gated on the arrow files as on the Ebony replacer (owner 2026-11-14 07:15: light through the
# nocked arrow); the mace and warhammer are measured and reported
SEE_THROUGH_MAX, SEE_THROUGH_GATED = 0.004, {"Arrow.nif", "ArrowProjectile.nif", "Bow.nif"}
# atlas -> (LoY file, the shape whose shader and texture set the built shape takes)
LOY_SHADER = {"axe1h": ("Axe.nif", "Axe2"), "axe2h": ("BattleAxe.nif", "BattleAxe2"), "dagger": ("Dagger.nif", "Scb"),
              "sword1h": ("Sword.nif", "Blade2")}


def fail(msg):
    raise SystemExit("build-missing-weapons: " + msg)


def mo2_ini():
    p = os.path.join(os.environ.get("NSAW_MO2", r"D:\Modlists\Njordlinger"), "ModOrganizer.ini")
    return open(p, encoding="utf-8", errors="replace").read() if os.path.isfile(p) else ""


def ini_path(key):
    m = re.search(r"^%s=(.*)$" % key, mo2_ini(), re.M)
    if not m:
        return None
    v = m.group(1).strip()
    v = re.sub(r"^@ByteArray\((.*)\)$", r"\1", v).replace("\\\\", "\\")
    return v.replace("/", "\\")


def downloads():
    d = os.environ.get("NSAW_DOWNLOADS") or ini_path("download_directory")
    if not d or not os.path.isdir(d):
        fail("no downloads folder - set NSAW_DOWNLOADS to the folder holding the Legacy of Ysgramor download")
    return d


def game_data():
    d = os.environ.get("SKYRIM_DATA") or (ini_path("gamePath") and os.path.join(ini_path("gamePath"), "Data"))
    if not d or not os.path.isdir(d):
        fail("no game Data folder - set SKYRIM_DATA")
    return d


def blender():
    b = os.environ.get("BLENDER") or shutil.which("blender")
    if not b:
        c = sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe"))
        b = c[-1] if c else None
    if not b or not os.path.isfile(b):
        fail("Blender not found - set BLENDER to blender.exe (with the PyNifly add-on installed)")
    return b


def sevenzip():
    for c in (r"C:\Program Files\7-Zip\7z.exe", r"C:\Program Files (x86)\7-Zip\7z.exe", shutil.which("7z") or ""):
        if c and os.path.isfile(c):
            return c
    fail("7-Zip not found")


def loy_weapons(work):
    dl = downloads()
    arc = [f for f in sorted(os.listdir(dl)) if "main archive se-109963" in f.lower() and f.lower().endswith(".7z")]
    if not arc:
        fail("no 'Main Archive SE-109963' in %s - download Legacy of Ysgramor's main file from Nexus first" % dl)
    tmp = os.path.join(work, "loy_x"); out = os.path.join(work, "loy"); os.makedirs(out, exist_ok=True)
    for name in sorted({it["loy"] for it in ITEMS.values()} | {f for it in ITEMS.values() for f in it.get("extra_loy", {}).values()} | set(EBONY_LOY) | set(FIRST_PERSON)):
        p = subprocess.run([sevenzip(), "x", "-y", "-o" + tmp, os.path.join(dl, arc[-1]), "-ir!*Companions\\Weapons\\" + name],
                           capture_output=True, text=True)
        if p.returncode != 0:
            fail("7-Zip failed on %s:\n%s" % (arc[-1], p.stdout + p.stderr))
        hits = [os.path.join(dp, fn) for dp, _, fns in os.walk(tmp) for fn in fns
                if fn.lower() == name.lower() and dp.lower().endswith(os.path.join("companions", "weapons"))]
        if len(hits) != 1:
            fail("Legacy of Ysgramor's archive has %d copies of Companions\\Weapons\\%s - its layout has changed" % (len(hits), name))
        shutil.copy2(hits[0], os.path.join(out, name))
    return out


def vanilla_meshes(work):
    import bsa
    data = game_data(); want = sorted({"meshes\\weapons\\ebony\\" + v for it in ITEMS.values() for v, _ in it["outputs"].values()} | {"meshes\\weapons\\ebony\\" + v for v in EBONY_VANILLA}); got = {}
    for name in ("Skyrim - Meshes0.bsa", "Skyrim - Meshes1.bsa"):
        p = os.path.join(data, name)
        if not os.path.isfile(p):
            continue
        try:
            got.update(bsa.extract(p, [w for w in want if w not in got], strict=False))
        except Exception as e:
            fail("could not read %s: %s" % (p, e))
    missing = [w for w in want if w not in got]
    if missing:
        fail("the game's mesh archives have no %s" % missing)
    root = os.path.join(work, "vanilla")
    for w, b in got.items():
        d = os.path.join(root, os.path.basename(w)); os.makedirs(root, exist_ok=True); open(d, "wb").write(b)
    return root


def first_person_files(loy, work, out_dir):
    """the five existing weapons' first-person files - see FIRST_PERSON"""
    import bsa, assemble, niflib, struct
    data = game_data(); want = ["meshes\\weapons\\steel\\" + f for v in FIRST_PERSON.values() for f in v[1:]]; got = {}
    for name in ("Skyrim - Meshes0.bsa", "Skyrim - Meshes1.bsa"):
        p = os.path.join(data, name)
        if os.path.isfile(p):
            got.update(bsa.extract(p, [w for w in want if w not in got], strict=False))
    if any(w not in got for w in want):
        fail("the game's mesh archives have no %s" % [w for w in want if w not in got])
    van = os.path.join(work, "vanilla_steel"); os.makedirs(van, exist_ok=True)
    for w, b in got.items(): open(os.path.join(van, os.path.basename(w)), "wb").write(b)
    rep, faults = {}, []
    for third, (first, v3, v1) in FIRST_PERSON.items():
        n = niflib.Nif(os.path.join(loy, third)); vn = niflib.Nif(os.path.join(van, v1)); root = n.roots[0]
        n.blocks[root][0:4] = struct.pack("<i", assemble.new_string(n, vn.name(vn.roots[0])))
        out = os.path.join(out_dir, first); assemble.save(n, out)
        a, b = niflib.Nif(os.path.join(loy, third)), niflib.Nif(out)       # read back: the same shapes, the same geometry
        sa = {a.name(x): bytes(a.blocks[x][4:]) for x in assemble.shapes_of(a)}; sb = {b.name(x): bytes(b.blocks[x][4:]) for x in assemble.shapes_of(b)}
        if sa != sb or b.name(b.roots[0]) != vn.name(vn.roots[0]):
            faults.append((first, "read-back differs from %s" % third))
        rep[first] = {"from": third, "root": b.name(b.roots[0]), "shapes": sorted(sb),
                      "vanilla_steel_1st_vs_3rd_offset (not applied)": assemble.first_person_offset(os.path.join(van, v3), os.path.join(van, v1)).tolist()}
    return rep, faults


def ebony_stage(loy, van, work):
    """the Ebony replacer's Blender stage, unchanged, on Legacy of Ysgramor's ebony weapons: its shapes folder"""
    eb_loy = os.path.join(work, "eb_loy"); d = os.path.join(eb_loy, "weapons", "ebony"); os.makedirs(d, exist_ok=True)
    for src, dst in EBONY_LOY.items(): shutil.copy2(os.path.join(loy, src), os.path.join(d, dst))
    eb_van = os.path.join(work, "eb_van"); d = os.path.join(eb_van, "meshes", "weapons", "ebony"); os.makedirs(d, exist_ok=True)
    for v in EBONY_VANILLA: shutil.copy2(os.path.join(van, v), os.path.join(d, v))
    bw = os.path.join(work, "blender_ebony"); ep = os.path.join(MW, "ebony_pipeline")
    env = dict(os.environ, NEAW_LOY_MESHES=eb_loy, NEAW_VANILLA=eb_van, NEAW_WORK=bw)
    log = os.path.join(work, "blender_ebony.log")
    with open(log, "w", encoding="utf-8") as lf:
        r = subprocess.run([blender(), "--background", "--factory-startup", "--python-exit-code", "1", "--python",
                            os.path.join(ep, "build_stage.py"), "--", "ext=5.0", "art", "chamfer=0.8"], env=env, stdout=lf, stderr=subprocess.STDOUT, cwd=ep)
    if r.returncode != 0:
        fail("the Ebony pipeline's Blender stage failed (log %s):\n%s" % (log, open(log, encoding="utf-8", errors="replace").read()[-3000:]))
    return os.path.join(bw, "shapes"), json.load(open(os.path.join(bw, "stage_report.json")))


def build_item(item, spec, loy, van, work, out_dir):
    import assemble, verify
    if spec.get("kind") == "bow":
        import assemble_bow, niflib
        assemble.LOY_SHADER = LOY_SHADER
        shapes, stage = ebony_stage(loy, van, work)
        (out_name, (van_name, ours)), = list(spec["outputs"].items())
        rep = {"stage": {"bow": stage.get("bow"), "bow_vanilla_split_verts": stage.get("bow_vanilla_split_verts")},
               "assemble": {out_name: assemble_bow.build_bow(os.path.join(van, van_name), os.path.join(out_dir, out_name), shapes, loy)}, "verify": {}}
        v = verify.check(os.path.join(out_dir, out_name), os.path.join(van, van_name), set(ours))
        if v["see_through_share"] is None or v["see_through_share"] > SEE_THROUGH_MAX:
            v["faults"].append(("light through the mesh: rays meet a back face first and no front face after", v["see_through_share"]))
        bf, br = verify.bow_checks(niflib.Nif(os.path.join(out_dir, out_name)), niflib.Nif(os.path.join(van, van_name)))
        v["bow"] = br; v["faults"] += bf
        rep["verify"][out_name] = v
        return rep, len(v["faults"])
    bw = os.path.join(work, "blender_" + item)
    first3 = [v for v, _ in spec["outputs"].values() if not v.startswith("1stperson")][0]
    env = dict(os.environ, NSAW_WORK=bw, **{spec["env"]: os.path.join(loy, spec["loy"]), spec["van_env"]: os.path.join(van, first3)})
    env.update({k: os.path.join(loy, v) for k, v in spec.get("extra_loy", {}).items()})
    log = os.path.join(work, "blender_%s.log" % item)
    with open(log, "w", encoding="utf-8") as lf:
        r = subprocess.run([blender(), "--background", "--factory-startup", "--python-exit-code", "1", "--python",
                            os.path.join(MW, spec["stage"])], env=env, stdout=lf, stderr=subprocess.STDOUT, cwd=MW)
    if r.returncode != 0:
        tail = open(log, encoding="utf-8", errors="replace").read()[-3000:]
        fail("the Blender stage for the %s failed (log %s):\n%s" % (item, log, tail))
    stage = json.load(open(os.path.join(bw, "stage_report.json")))
    assemble.LOY_SHADER = LOY_SHADER
    shapes = os.path.join(bw, "shapes")
    rep = {"stage": stage, "assemble": {}, "verify": {}}
    if spec.get("kind") == "arrow":
        import assemble_arrow
        (a_out, (a_van, _)), (f_out, (f_van, _)) = list(spec["outputs"].items())
        rep["assemble"]["Arrow"] = assemble_arrow.build_arrow(os.path.join(van, a_van), os.path.join(van, f_van), os.path.join(out_dir, a_out),
                                                              os.path.join(out_dir, f_out), shapes, loy, "axe1h", "dagger", "axe1h")
    else:
        first1 = [v for v, _ in spec["outputs"].values() if v.startswith("1stperson")][0]
        split = stage["head_split_y"][item]
        off = assemble.first_person_offset(os.path.join(van, first3), os.path.join(van, first1))
        for out_name, (van_name, _) in spec["outputs"].items():
            rep["assemble"][out_name] = assemble.build_static(item, os.path.join(van, van_name), os.path.join(out_dir, out_name),
                                                              shapes, loy, split, [0, 0, 0] if van_name == first3 else off)
    faults = 0
    for out_name, (van_name, ours) in spec["outputs"].items():
        v = verify.check(os.path.join(out_dir, out_name), os.path.join(van, van_name), {ours} if isinstance(ours, str) else set(ours))
        if out_name in SEE_THROUGH_GATED and (v["see_through_share"] is None or v["see_through_share"] > SEE_THROUGH_MAX):
            v["faults"].append(("light through the mesh: rays meet a back face first and no front face after", v["see_through_share"]))
        rep["verify"][out_name] = v; faults += len(v["faults"])
    if spec.get("kind") == "arrow":     # the game hides the quiver arrows one by one by name: exactly Arrow1..6 under ArrowQuiver
        import niflib
        n = niflib.Nif(os.path.join(out_dir, "Arrow.nif"))
        q = [b for b in range(len(n.blocks)) if n.btypes[b] == "NiNode" and n.name(b) == "ArrowQuiver"][0]
        kids = sorted(n.name(c) for c in n.children(q)[0] if c >= 0 and n.btypes[c] == "BSTriShape" and n.name(c)[5:].isdigit())
        if kids != ["Arrow%d" % k for k in range(1, 7)]:
            rep["verify"]["Arrow.nif"]["faults"].append(("quiver arrows", kids)); faults += 1
    return rep, faults


def main(out_meshes, work=None, only=None):
    work = work or os.path.join(os.path.dirname(os.path.abspath(out_meshes)), "_work_missing_weapons")
    if os.path.isdir(work):
        shutil.rmtree(work)
    os.makedirs(work)
    loy = loy_weapons(work); van = vanilla_meshes(work)
    out_dir = os.path.join(out_meshes, *MESH_DIR)
    rep, faults, outputs = {}, 0, []
    for item, spec in ITEMS.items():
        if only and item not in only:
            continue
        rep[item], f = build_item(item, spec, loy, van, work, out_dir); faults += f; outputs += list(spec["outputs"])
    if not only or "first" in only:
        rep["first_person"], fp_faults = first_person_files(loy, work, out_dir)
        faults += len(fp_faults); outputs += [v[0] for v in FIRST_PERSON.values()]
        if fp_faults: rep["first_person"]["faults"] = fp_faults
    json.dump(rep, open(os.path.join(work, "build_report.json"), "w"), indent=1, default=str)
    missing = [f for f in outputs if not os.path.isfile(os.path.join(out_dir, f))]
    if missing:
        fail("not built: %s" % missing)
    if faults:
        fail("%d verification fault(s) - see %s" % (faults, os.path.join(work, "build_report.json")))
    st = {k: v["see_through_share"] for r in rep.values() for k, v in r.get("verify", {}).items()}
    print("missing weapons built: %d files in %s (light-through, reported: %s; report %s)"
          % (len(outputs), out_dir, st, os.path.join(work, "build_report.json")))
    return out_dir, rep


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        fail("usage: build-missing-weapons.py <output meshes folder> [--work <folder>] [--only mace,warhammer]")
    w = a[a.index("--work") + 1] if "--work" in a else None
    o = a[a.index("--only") + 1].split(",") if "--only" in a else None
    main(a[0], w, o)
