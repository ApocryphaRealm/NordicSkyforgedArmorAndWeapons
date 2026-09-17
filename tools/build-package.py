#!/usr/bin/env python3
r"""Assemble the FOMOD package for Nordic Skyforged Armor and Weapons.

WHAT THIS PACKAGES
    NordwarUA's steel wolf armour and weapons from Legacy of Ysgramor (Nexus 109963), under this
    mod's own folders, in Xtudo's black colourway from Nexus 111121 (Wolf Black for the straps and
    cloth, Full Collar Black for the fur), plus the light plugin from build-esp.py.

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

Usage:  python tools/build-package.py [output folder] [--test]
"""
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
DOWNLOADS = os.environ.get("NSAW_DOWNLOADS", r"D:\modlists\Njordlinger\downloads")
SEVENZIP = [r"C:\Program Files\7-Zip\7z.exe", r"C:\Program Files (x86)\7-Zip\7z.exe", "7z"]

A_BASE = "Main Archive SE-109963"              # NordwarUA - meshes, normals, masks, steel diffuses
A_FURFIX = "Patch Fur Lighting Bug-109963"     # NordwarUA - corrected FurCollar_n
A_COLLAR = "Color - Full Collar Black-111121"  # Xtudo - the black fur collar
A_WOLF = {"1K": "Color - Wolf Black 1K-111121",
          "2K": "Color - Wolf Black 2K-111121",
          "4K": "Color - Wolf Black 4K-111121"}

PLUGIN = "Nordic Skyforged Armor and Weapons.esp"
SRC_MESH = "meshes/NordWar/Companions"
OLD_TEX = b"textures\\NordWar\\Companions\\"
NEW_TEX = b"textures\\NordicSkyforge\\Set\\"
assert len(OLD_TEX) == len(NEW_TEX)
TEX_RE = re.compile(rb"textures[\\/]NordWar[\\/]Companions[\\/]", re.IGNORECASE)
TEXPAT = re.compile(rb"[Tt]extures.{1,180}?\.dds")
VANILLA_TEXTURES = ("textures\\blood\\", "textures\\cubemaps\\")
IMAGES = ("header.png",)


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


def main(out_root=None, test=False):
    ver = version()
    if out_root is None:
        out_root = os.path.normpath(os.path.join(REPO, "..", "..", "7. current test builds",
                                                 "Nordic Skyforged Armor and Weapons %s" % ver))
    if os.path.isdir(out_root):
        shutil.rmtree(out_root)
    work = os.path.join(out_root, "_work")

    base = extract(A_BASE, os.path.join(work, "base"))
    furfix = extract(A_FURFIX, os.path.join(work, "furfix"))
    collar = extract(A_COLLAR, os.path.join(work, "collar"))
    wolf = {k: extract(v, os.path.join(work, "wolf" + k)) for k, v in A_WOLF.items()}

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
    shutil.copy2(plugin, core)

    # ---- textures, derived from the rewritten meshes; looked up under the ORIGINAL names
    wanted = set()
    for s in shipped:
        for m in TEXPAT.findall(open(s, "rb").read()):
            p = m.decode("latin-1").replace("/", "\\").lower()
            if not any(p.startswith(v) for v in VANILLA_TEXTURES):
                wanted.add(p)
    new_prefix = NEW_TEX.decode().lower()
    old_prefix = OLD_TEX.decode()

    def sources_for(res):
        return [collar, wolf[res], furfix, base]   # colour packs win over the base mod's own

    n_tex = {}
    for res in ("1K", "2K", "4K"):
        dest = os.path.join(out_root, "0%d Textures - %s" % (1 + ("1K", "2K", "4K").index(res), res))
        found = 0
        for rel in sorted(wanted):
            if not rel.startswith(new_prefix):
                fail("shipped mesh still names '%s' outside this mod's texture folder" % rel)
            orig = old_prefix + rel[len(new_prefix):]
            src = None
            for root in sources_for(res):
                src = ci_find(root, orig)
                if src:
                    break
            if src is None:
                fail("a shipped mesh asks for '%s' and no source archive has it - in game that "
                     "shape renders purple" % orig)
            d = os.path.join(dest, rel.replace("\\", os.sep))
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(src, d)
            found += 1
        n_tex[res] = found

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
    for name in ("NOTICE.md", "CHANGELOG.md", "LICENSE"):
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
    print("  textures per resolution %d  (1K/2K/4K)" % n_tex["2K"])
    print("  installer sources ..... %d, every one present" % len(sources))
    print("  files ................. %d" % total)
    return out_root


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--test"]
    is_test = "--test" in sys.argv[1:]
    main(args[0] if args else None, test=is_test)
    if is_test:
        print()
        print("  *** --test: built WITHOUT the installer images. Not shippable. ***")
