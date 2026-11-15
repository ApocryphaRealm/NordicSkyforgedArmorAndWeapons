#!/usr/bin/env python3
r"""Build the game meshes of the Skyforge Steel weapon types the game has no Skyforge version of - the same set the
Nordic Ebony Armor and Weapons Replacer gained in 1.1.0 (mace, warhammer, bow, arrows and quiver), built one at a time
(the owner, 2026-11-15: "start building the other weapon types that we haven't built yet. Just do them one at a time").

BUILT SO FAR
    mace       ->  meshes\NordicSkyforge\weapons\Mace.nif and 1stPersonMace.nif       (missing_weapons\stage_mace.py)
    warhammer  ->  meshes\NordicSkyforge\weapons\Warhammer.nif and 1stPersonWarhammer.nif (missing_weapons\stage_warhammer.py)

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
    "warhammer": {"stage": "stage_warhammer.py", "loy": "BattleAxe.nif", "env": "NSAW_BAXE", "van_env": "NSAW_VAN_WARHAMMER",
                  "outputs": {"Warhammer.nif": ("ebonywarhammer.nif", "EbonyWarhammer:0"),
                              "1stPersonWarhammer.nif": ("1stpersonebonywarhammer.nif", "1stPersonEbonyWarhammer:0")}},
}
# atlas -> (LoY file, the shape whose shader and texture set the built shape takes)
LOY_SHADER = {"axe1h": ("Axe.nif", "Axe2"), "axe2h": ("BattleAxe.nif", "BattleAxe2")}


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
    for name in sorted({it["loy"] for it in ITEMS.values()}):
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
    data = game_data(); want = ["meshes\\weapons\\ebony\\" + v for it in ITEMS.values() for v, _ in it["outputs"].values()]; got = {}
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


def build_item(item, spec, loy, van, work, out_dir):
    import assemble, verify
    bw = os.path.join(work, "blender_" + item)
    first3 = [v for v, _ in spec["outputs"].values() if not v.startswith("1stperson")][0]
    first1 = [v for v, _ in spec["outputs"].values() if v.startswith("1stperson")][0]
    env = dict(os.environ, NSAW_WORK=bw, **{spec["env"]: os.path.join(loy, spec["loy"]), spec["van_env"]: os.path.join(van, first3)})
    log = os.path.join(work, "blender_%s.log" % item)
    with open(log, "w", encoding="utf-8") as lf:
        r = subprocess.run([blender(), "--background", "--factory-startup", "--python-exit-code", "1", "--python",
                            os.path.join(MW, spec["stage"])], env=env, stdout=lf, stderr=subprocess.STDOUT, cwd=MW)
    if r.returncode != 0:
        tail = open(log, encoding="utf-8", errors="replace").read()[-3000:]
        fail("the Blender stage for the %s failed (log %s):\n%s" % (item, log, tail))
    stage = json.load(open(os.path.join(bw, "stage_report.json")))
    assemble.LOY_SHADER = LOY_SHADER
    shapes = os.path.join(bw, "shapes"); split = stage["head_split_y"][item]
    off = assemble.first_person_offset(os.path.join(van, first3), os.path.join(van, first1))
    rep = {"stage": stage, "assemble": {}, "verify": {}}
    for out_name, (van_name, _) in spec["outputs"].items():
        rep["assemble"][out_name] = assemble.build_static(item, os.path.join(van, van_name), os.path.join(out_dir, out_name),
                                                          shapes, loy, split, [0, 0, 0] if van_name == first3 else off)
    faults = 0
    for out_name, (van_name, ours) in spec["outputs"].items():
        v = verify.check(os.path.join(out_dir, out_name), os.path.join(van, van_name), {ours})
        rep["verify"][out_name] = v; faults += len(v["faults"])
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
    json.dump(rep, open(os.path.join(work, "build_report.json"), "w"), indent=1, default=str)
    missing = [f for f in outputs if not os.path.isfile(os.path.join(out_dir, f))]
    if missing:
        fail("not built: %s" % missing)
    if faults:
        fail("%d verification fault(s) - see %s" % (faults, os.path.join(work, "build_report.json")))
    st = {k: v["see_through_share"] for r in rep.values() for k, v in r["verify"].items()}
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
