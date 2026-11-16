#!/usr/bin/env python3
r"""Assemble the FOMOD packages for Truly Nordic Skyforged Armor and Weapons (named Nordic Skyforged Armor and Weapons
until 2026-11-16).

TWO PACKAGES SINCE 1.0.0 (the owner, 2026-11-16: the 3D build is the MAIN file, the flat build the OPTIONAL file)
    <version folder>\Flat\   the texture-only set described below - built here from the Nexus downloads;
    <version folder>\3D\     the same package with the full-3D build laid over it (every mail ring, rivet, stud, buckle,
                             strap and lamellar scale modelled; 3D CBBE 3BA / HIMBO fits) - tools/package3d.py, which
                             refuses a 3D build made from other meshes than the flat package ships (--rebuild-3d
                             rebuilds it with tools/full3d/).
    Each is its own FOMOD with the same body choices. 11. Nexus distro\<mod>\nexus-files.json names them for the upload.

WHAT THIS PACKAGES
    NordwarUA's steel wolf armour and weapons from Legacy of Ysgramor (Nexus 109963), under this
    mod's own folders, in an all-black look of our own - NordwarUA's ORIGINAL diffuses recoloured by
    tools/recolour_black.py (the owner, 2026-11-15 21:54: Xtudo's colourway needs his permission, so
    none of his files is read or shipped) - as Community Shaders TRUEPBR materials (the owner 21:55;
    tools/truepbr.py), one texture set in the core (NordwarUA ships one resolution), plus the light
    plugin from build-esp.py. Body options (2026-11-16, loy-refits.py + body_fits.py): CBBE 3BA on our own slider
    data and our own HIMBO fit, meshes prebuilt by BodySlide plus the projects; vanilla is the default.

WHY THE MESHES ARE REWRITTEN
    The meshes name their textures under textures\NordWar\Companions\ - Legacy of Ysgramor's own
    folder. Shipping black textures there would recolour the Wolf Armor of anyone who also has
    that mod installed, which is exactly the armour the owner said to leave alone. So every
    texture path inside every shipped mesh is rewritten to textures\NordicSkyforge\Set\, a name
    chosen to be the SAME LENGTH as the original (28 bytes) so the .nif's block sizes stay true
    and no NIF parser is needed. The textures are then shipped under that folder.

THE TEXTURE LIST IS DERIVED, NOT WRITTEN DOWN
    Every texture is found by reading the shipped meshes. A hand-written list is how a replacer
    ends up with one purple shape.

WHAT IT REFUSES TO DO
    * ship if a download is missing;
    * ship if a mesh the plugin points at is not in the source archive;
    * ship if a texture a shipped mesh references cannot be found in any source archive;
    * ship if the path rewrite would change a mesh's length;
    * ship if any folder ModuleConfig.xml installs from is missing or empty, or an image is absent.

Usage:  python tools/build-package.py [version folder] [--test] [--flat-only] [--rebuild-3d]
"""
import os
import re
import shutil
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
DOWNLOADS = os.environ.get("NSAW_DOWNLOADS", r"C:\Modlists\Njordlinger-downloads")   # Njordlinger's download_directory
SEVENZIP = [r"C:\Program Files\7-Zip\7z.exe", r"C:\Program Files (x86)\7-Zip\7z.exe", "7z"]

A_BASE = "Main Archive SE-109963"              # NordwarUA - meshes, normals, masks, steel diffuses
A_FURFIX = "Patch Fur Lighting Bug-109963"     # NordwarUA - corrected FurCollar_n
PBR_FOLDER = "NordicSkyforge"                 # textures\pbr\NordicSkyforge\
MAX_DDS = 2048

MOD_NAME = "Truly Nordic Skyforged Armor and Weapons"
PLUGIN = MOD_NAME + ".esp"
FLAT, FULL3D = "Flat", "3D"        # the two packages' folders (zips: "<mod> <ver> - Flat.zip" / "- 3D.zip")
SRC_MESH = "meshes/NordWar/Companions"
OLD_TEX = b"textures\\NordWar\\Companions\\"
NEW_TEX = b"textures\\NordicSkyforge\\Set\\"
assert len(OLD_TEX) == len(NEW_TEX)
TEX_RE = re.compile(rb"textures[\\/]NordWar[\\/]Companions[\\/]", re.IGNORECASE)
TEXPAT = re.compile(rb"[Tt]extures.{1,180}?\.dds")
VANILLA_TEXTURES = ("textures\\blood\\", "textures\\cubemaps\\")
IMAGES = ("header.png", "vanilla_f.png", "vanilla_m.png", "cbbe3ba.png", "himbo.png")   # rendered from a built package by tools/installer-images.py


def supersede(folder):
    """NEVER DELETE A PACKAGE (2026-10-25): the package folder this build replaces is MOVED to
    <project>/_work/superseded-packages/<date>/ - <project> being the nearest folder above it that has a _work folder
    (SUPERSEDED_PACKAGES_DIR overrides; with neither, a _superseded folder beside it) - and stays there until someone
    clears it by hand. This script used to shutil.rmtree it."""
    import time
    root = os.environ.get("SUPERSEDED_PACKAGES_DIR")
    here = os.path.dirname(os.path.abspath(folder))
    p = here
    while not root:
        if os.path.isdir(os.path.join(p, "_work")):
            root = os.path.join(p, "_work", "superseded-packages")
        elif os.path.dirname(p) == p:
            root = os.path.join(here, "_superseded")
        else:
            p = os.path.dirname(p)
    day = os.path.join(root, time.strftime("%Y-%m-%d"))
    os.makedirs(day, exist_ok=True)
    to = base = os.path.join(day, "%s (replaced %s)" % (os.path.basename(os.path.normpath(folder)), time.strftime("%H%M%S")))
    i = 2
    while os.path.exists(to):
        to, i = "%s %d" % (base, i), i + 1
    shutil.move(folder, to)
    print("the package this build replaces was moved to %s (never deleted)" % to)
    return to


def fail(msg):
    raise SystemExit("build-package: " + msg)


def sevenzip():
    for c in SEVENZIP:
        if os.path.isfile(c):
            return c
        if shutil.which(c):
            return shutil.which(c)
    fail("7-Zip not found")


def version():
    t = open(os.path.join(REPO, "fomod", "info.xml"), encoding="utf-8").read()
    m = re.search(r"<Version>\s*(\d+\.\d+\.\d+)\s*</Version>", t)
    if not m:
        fail("no <Version>x.y.z</Version> in fomod/info.xml")
    return m.group(1)


def find_archive(fragment):
    for fn in sorted(os.listdir(DOWNLOADS)):
        if fragment.lower() in fn.lower() and fn.lower().endswith(".7z"):
            return os.path.join(DOWNLOADS, fn)
    fail("no archive matching '%s' in %s - download it from Nexus first" % (fragment, DOWNLOADS))


def extract(fragment, dest):
    os.makedirs(dest, exist_ok=True)
    p = subprocess.run([sevenzip(), "x", "-y", "-o" + dest, find_archive(fragment)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        fail("7-Zip failed on %s:\n%s" % (fragment, p.stdout + p.stderr))
    data = os.path.join(dest, "Data")
    if os.path.isdir(data):
        for name in os.listdir(data):
            target = os.path.join(dest, name)
            if os.path.isdir(target):
                for dp, _, fns in os.walk(os.path.join(data, name)):
                    for fn in fns:
                        s = os.path.join(dp, fn)
                        d = os.path.join(target, os.path.relpath(s, os.path.join(data, name)))
                        os.makedirs(os.path.dirname(d), exist_ok=True)
                        shutil.move(s, d)
            else:
                shutil.move(os.path.join(data, name), target)
        shutil.rmtree(data, ignore_errors=True)
    return dest


def ci_find(root, rel):
    cur = root
    for part in rel.replace("\\", "/").split("/"):
        if not part:
            continue
        entries = os.listdir(cur) if os.path.isdir(cur) else []
        match = next((e for e in entries if e.lower() == part.lower()), None)
        if match is None:
            return None
        cur = os.path.join(cur, match)
    return cur


def main(version_root=None, test=False, flat_only=False, rebuild_3d=False):
    """Both packages under <version_root>: Flat\\ built from the downloads, then 3D\\ from it (tools/package3d.py)."""
    ver = version()
    if version_root is None:
        version_root = os.path.normpath(os.path.join(REPO, "..", "..", "7. current test builds",
                                                     "Skyrim - " + MOD_NAME, "%s %s" % (MOD_NAME, ver)))
    if os.path.isdir(version_root):
        supersede(version_root)     # never deleted (2026-10-25); this script used to shutil.rmtree it
    flat = build_flat(os.path.join(version_root, FLAT), test)
    if flat_only:
        print("  --flat-only: no 3D package built. Not shippable as a release.")
        return version_root
    import package3d
    out3d = package3d.make("skyforged", flat, os.path.join(version_root, FULL3D), rebuild_3d=rebuild_3d)
    set_module_name(flat, MOD_NAME + " - Flat textures")
    set_module_name(out3d, MOD_NAME)
    return version_root


def set_module_name(pkg, name):
    p = os.path.join(pkg, "fomod", "ModuleConfig.xml")
    t = open(p, encoding="utf-8").read()
    t2 = re.sub(r"<moduleName>[^<]*</moduleName>", "<moduleName>%s</moduleName>" % name, t, count=1)
    if t2 == t and ("<moduleName>%s</moduleName>" % name) not in t:
        fail("no <moduleName> in %s" % p)
    open(p, "w", encoding="utf-8", newline="").write(t2)


def build_flat(out_root, test=False):
    ver = version()
    work = os.path.join(out_root, "_work")

    base = extract(A_BASE, os.path.join(work, "base"))
    furfix = extract(A_FURFIX, os.path.join(work, "furfix"))

    plugin = os.path.join(REPO, "plugin", PLUGIN)
    needed = os.path.join(REPO, "plugin", "meshes-needed.txt")
    if not os.path.isfile(plugin) or not os.path.isfile(needed):
        fail("run tools/build-esp.py first - the plugin and its mesh list are missing")

    # ---- meshes: every path the plugin names, plus the _0 twin of every _1
    wanted_meshes = set()
    for line in open(needed, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        wanted_meshes.add(line)
        if line.lower().endswith("_1.nif"):
            wanted_meshes.add(line[:-6] + "_0.nif")

    core = os.path.join(out_root, "00 Core")
    shipped = []
    for ours in sorted(wanted_meshes):
        # NordicSkyforge\armor\X.nif <- NordWar\Companions\X.nif ; ...\weapons\X.nif <- ...\Weapons\X.nif
        rel = ours.replace("\\", "/")
        parts = rel.split("/")
        if parts[0].lower() != "nordicskyforge" or len(parts) != 3:
            fail("unexpected mesh path in the plugin: %s" % ours)
        src_rel = SRC_MESH + ("/Weapons/" if parts[1].lower() == "weapons" else "/") + parts[2]
        s = ci_find(base, src_rel)
        if s is None:
            fail("Legacy of Ysgramor has no '%s' - the plugin would point at nothing" % src_rel)
        raw = open(s, "rb").read()
        new = TEX_RE.sub(lambda m: NEW_TEX, raw)   # a function, so the backslashes are literal
        if len(new) != len(raw):
            fail("rewriting texture paths changed the size of %s - the block sizes would lie" % parts[2])
        d = os.path.join(core, "meshes", ours.replace("/", os.sep))
        os.makedirs(os.path.dirname(d), exist_ok=True)
        open(d, "wb").write(new)
        shipped.append(d)

    # ---- the shield to the Truly Nordic Carved "Shield - Clean" face size (the owner, 2026-11-15, as on the Nordic Ebony
    # replacer): scaled about its grip in place. Legacy of Ysgramor's steel shield is the same mesh as its ebony one, so
    # the Ebony replacer's tools\missing_weapons\shield_size.py is used unchanged.
    # build-esp.py runs this same resize on a temporary copy (its GROUND_MODEL_STEPS) to write the shield's object
    # bounds from the model as shipped - change one, change both.
    sys.path.insert(0, os.path.join(HERE, "missing_weapons"))
    import shield_size
    sh = shield_size.resize(os.path.join(core, "meshes", "NordicSkyforge", "weapons", "ShieldSteel.nif"))
    print("  shield ................ rim %.2f -> %.2f (x%.4f about %s)" % (
        sh["rim_diameter_before"], sh["rim_diameter_after"], sh["scale"], sh["pivot"]))

    # ---- the new weapon types' meshes, built from Legacy of Ysgramor's pieces by tools/build-missing-weapons.py
    built_list = os.path.join(REPO, "plugin", "meshes-built.txt")
    built_wanted = [l.strip() for l in open(built_list, encoding="utf-8") if l.strip()] if os.path.isfile(built_list) else []
    if built_wanted:
        bm = os.path.join(work, "built_meshes")
        env = dict(os.environ, NSAW_DOWNLOADS=DOWNLOADS)
        r = subprocess.run([sys.executable, os.path.join(HERE, "build-missing-weapons.py"), bm, "--work", os.path.join(work, "built_work")],
                           capture_output=True, text=True, env=env)
        if r.returncode != 0:
            fail("the new weapon types failed to build:\n" + (r.stdout + r.stderr).strip()[-3000:])
        print(r.stdout.strip().splitlines()[-1])
        for ours in built_wanted:
            s = os.path.join(bm, ours.replace("\\", os.sep))
            if not os.path.isfile(s):
                fail("the plugin points at '%s' and build-missing-weapons.py did not build it" % ours)
            raw = open(s, "rb").read()
            new = TEX_RE.sub(lambda m: NEW_TEX, raw)
            if len(new) != len(raw):
                fail("rewriting texture paths changed the size of %s" % ours)
            d = os.path.join(core, "meshes", ours.replace("\\", os.sep))
            os.makedirs(os.path.dirname(d), exist_ok=True)
            open(d, "wb").write(new)
            shipped.append(d)
    # The plugin installs with the core. A no-ESP (SkyPatcher) option was offered from 2026-11-16 02:43 and dropped at
    # 04:10 (the owner: "drop the no plugin option") - it could only re-model vanilla's five Skyforge Steel weapons, as
    # SkyPatcher cannot create records. Its INI (skypatcher\weapon\TrulyNordicSkyforged\) stays in git history only.
    shutil.copy2(plugin, core)

    # ---- body option: CBBE 3BA BodySlide files (Xonek, Nexus 111209); see tools/loy-refits.py. Built before the
    # textures, because its shape data names the same materials and is converted to TruePBR with the rest.
    r = subprocess.run([sys.executable, os.path.join(HERE, "loy-refits.py"), "--profile", "skyforged",
                        "--out", out_root, "--first", "30"], capture_output=True, text=True)
    if r.returncode != 0:
        fail("body options failed:\n" + (r.stdout + r.stderr).strip())
    for line in r.stdout.strip().splitlines():
        print(line)

    # ---- textures: every material the shipped meshes use, found by reading them (never a hand list), made into our
    # black recolour as TruePBR maps from NordwarUA's own files (looked up under his ORIGINAL names); then every shader
    # of ours is converted (tools/truepbr.py). One set, in the core.
    sys.path.insert(0, HERE)
    import truepbr
    old = (NEW_TEX.decode().lower(), OLD_TEX.decode().lower())
    mesh_roots = [os.path.join(out_root, d) for d in sorted(os.listdir(out_root))
                  if os.path.isdir(os.path.join(out_root, d)) and d[:2].isdigit()]
    mats = truepbr.scan(mesh_roots, old)
    if not mats:
        fail("no shipped mesh names a texture of the set - the scan is looking in the wrong place")

    def find_src(stem):
        """NordwarUA's file by name: the Fur Lighting Bug patch's FurCollar_n wins over the main archive's"""
        for root in (furfix, base):
            p = ci_find(root, "textures/NordWar/Companions/%s.dds" % stem)
            if p:
                return p
        return None
    truepbr.build_textures(mats, find_src, "steel", PBR_FOLDER, core, os.path.join(work, "pbr"))
    n_files, n_shaders = truepbr.convert(mesh_roots, old, PBR_FOLDER)
    n_ok = truepbr.verify(mesh_roots, old, PBR_FOLDER, [core])
    n_tex = 0; biggest = 0
    for dp, _, fs in os.walk(os.path.join(core, "textures")):
        for f in fs:
            hdr = open(os.path.join(dp, f), "rb").read(20)
            h, w = struct.unpack_from("<II", hdr, 12)
            if hdr[:4] != b"DDS " or max(w, h) > MAX_DDS:
                fail("'%s' is %dx%d - over 2K" % (f, w, h))
            biggest = max(biggest, w, h); n_tex += 1

    # ---- fomod
    fomod = os.path.join(out_root, "fomod")
    os.makedirs(os.path.join(fomod, "images"), exist_ok=True)
    shutil.copy2(os.path.join(REPO, "fomod", "ModuleConfig.xml"), fomod)
    shutil.copy2(os.path.join(REPO, "fomod", "info.xml"), fomod)
    for img in IMAGES:
        s = os.path.join(REPO, "fomod", "images", img)
        if not os.path.isfile(s):
            if not test:
                fail("installer image '%s' is missing. Pass --test to build anyway for local testing." % img)
            continue
        shutil.copy2(s, os.path.join(fomod, "images", img))
    for name in ("README.md", "NOTICE.md", "CHANGELOG.md", "LICENSE"):
        shutil.copy2(os.path.join(REPO, name), os.path.join(out_root, name))

    root = ET.parse(os.path.join(fomod, "ModuleConfig.xml")).getroot()
    sources = sorted({e.get("source") for e in root.iter("folder") if e.get("source")})
    for s in sources:
        p = os.path.join(out_root, s.replace("\\", os.sep).replace("/", os.sep))
        if not os.path.isdir(p) or not any(os.path.isfile(os.path.join(dp, f)) for dp, _, fs in os.walk(p) for f in fs):
            fail("ModuleConfig.xml installs from '%s', but the package has nothing there" % s)
    for e in list(root.iter("image")) + list(root.iter("moduleImage")):
        if not os.path.isfile(os.path.join(out_root, e.get("path").replace("\\", os.sep))) and not test:
            fail("ModuleConfig.xml shows '%s', which is not in the package" % e.get("path"))

    shutil.rmtree(work, ignore_errors=True)
    total = sum(len(fs) for _, _, fs in os.walk(out_root))
    print("built %s" % out_root)
    print("  version ............... %s" % ver)
    print("  meshes ................ %d, texture paths rewritten to %s" % (len(shipped), NEW_TEX.decode()))
    print("  plugin ................ %s" % PLUGIN)
    print("  TruePBR ............... %d materials, %d shaders in %d meshes converted, %d verified" % (len(mats), n_shaders, n_files, n_ok))
    print("  textures .............. %d (largest %d px), under textures\\pbr\\%s" % (n_tex, biggest, PBR_FOLDER))
    print("  installer sources ..... %d, every one present" % len(sources))
    print("  files ................. %d" % total)
    return out_root


if __name__ == "__main__":
    flags = {"--test", "--flat-only", "--rebuild-3d"}
    args = [a for a in sys.argv[1:] if a not in flags]
    is_test = "--test" in sys.argv[1:]
    main(args[0] if args else None, test=is_test, flat_only="--flat-only" in sys.argv[1:],
         rebuild_3d="--rebuild-3d" in sys.argv[1:])
    if is_test:
        print()
        print("  *** --test: built WITHOUT the installer images. Not shippable. ***")
