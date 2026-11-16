#!/usr/bin/env python3
r"""Generate the light plugin for Nordic Skyforged Armor and Weapons.

WHAT THE PLUGIN DOES
    Two things, in one ESPFE (a .esp carrying the light flag, so it costs no load-order slot and
    can still be positioned):

    1. REPLACES the five vanilla Skyforge Steel weapons' models with NordwarUA's steel wolf
       weapons from Legacy of Ysgramor: the sword, greatsword, war axe, battleaxe and dagger.
       Everything else about those records - damage, value, keywords, sounds - stays vanilla,
       because the body is copied from Skyrim.esm and only MODL changes - and, since 1.1.0, WNAM, which
       names each weapon's own first-person static (section 7) instead of vanilla Steel's shared one.

    2. ADDS a Skyforge Steel armour set - cuirass, boots, gauntlets, helmet and shield - built
       from the steel wolf armour of the same mod (the fur-collared cuirass). The stats are the
       game's own Wolf Armor stats, record for record, so the set sits where Wolf Armor sits:
       heavy, steel material, tempered with a steel ingot. It is forged at the Skyforge with the
       Steel Smithing perk. The Wolf Armor itself is not touched - the owner, 2026-09-16:
       "i dont want to replace wolf armor, i want to replace skyforged weapons and add skyforged
       armor, leave wolf alone".

    3. ADDS the Skyforge Steel weapon types the game has none of (the owner, 2026-11-15: the same
       weapon types the Nordic Ebony replacer gained), one at a time - so far the MACE, the WARHAMMER, the BOW and the
       ARROW (NEW_AMMO: its own projectile, the quiver is part of the arrow's model). See
       NEW_WEAPONS: the vanilla Steel record plus the vanilla Skyforge uplift, its own first-person
       static, forged at the Skyforge, tempered like the Skyforge war axe. Meshes from
       tools/build-missing-weapons.py.

WHERE THE RECORDS COME FROM
    Nothing is typed in from memory. The weapon and armour bodies are copied out of Skyrim.esm
    at build time; the armour ADDON bodies (the records that carry the worn model paths, the
    race list and the body slots) are copied out of Legacy of Ysgramor's own plugin, so the
    helmet keeps the open-helm slot word its author gave it - the mistake that hid the head in
    the ebony replacer is not repeatable here. The tempering recipes are the game's own Wolf
    Armor tempering recipes with the created object swapped.

MASTERS
    Skyrim.esm only. Every reference copied in is checked to resolve there; a reference into any
    other file is refused rather than shipped pointing at the wrong record.

Usage:  python tools/build-esp.py [--loy <NW_Companions_Replacer_Light.esp>] [output .esp]
"""
import argparse
import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))

GAME_DATA = os.environ.get("SKYRIM_DATA", r"D:\modlists\Njordlinger\Stock Game\Data")
LOY_DEFAULT = os.environ.get("LOY_PLUGIN", r"D:\modlists\Njordlinger\mods\Legacy of Ysgramor\NW_Companions_Replacer_Light.esp")

PLUGIN_NAME = "Nordic Skyforged Armor and Weapons.esp"
AUTHOR = "ApocryphaRealm"
DESCRIPTION = ("NordwarUA's steel wolf weapons on the Skyforge Steel weapons, and a Skyforge Steel "
               "armour set built from his steel wolf armour.")

MESH_ROOT = "NordicSkyforge"          # meshes\NordicSkyforge\...
ESL_FLAG = 0x00000200
COMPRESSED = 0x00040000
FIRST_NEW = 0x800

# ---- vanilla FormIDs (Skyrim.esm), by name so the intent is readable
K_SKYFORGE = 0x000F46CE       # CraftingSmithingSkyforge
K_ARMOR_TABLE = 0x000ADB78    # CraftingSmithingArmorTable
PERK_STEEL = 0x000CB40D       # SteelSmithing
INGOT_STEEL = 0x0005ACE5
LEATHER_STRIPS = 0x000800E4
LEATHER = 0x000DB5D2
RACE_DRAUGR = 0x00000D53
RACE_DRAUGR_MAGIC = 0x000F71DC

# vanilla weapon record -> LoY steel wolf mesh (under meshes\NordWar\Companions\Weapons\)
# Skyrim.esm is a LOCALIZED master: its FULL and DESC are 4-byte string-table ids, not text.
# This plugin is not localized, so a copied FULL would be read as four bytes of gibberish. The
# names are therefore written here, in the game's own words, and DESC is emptied.
WEAPONS = {
    "SkyforgeSteelSword": ("Sword.nif", "Skyforge Steel Sword"),
    "SkyforgeSteelGreatsword": ("Greatsword.nif", "Skyforge Steel Greatsword"),
    "SkyforgeSteelWarAxe": ("Axe.nif", "Skyforge Steel War Axe"),
    "SkyforgeSteelBattleaxe": ("BattleAxe.nif", "Skyforge Steel Battleaxe"),
    "SkyforgeSteelDagger": ("Dagger.nif", "Skyforge Steel Dagger"),
}

# NEW Skyforge Steel weapons of the types the game has no Skyforge version of (built by tools/build-missing-weapons.py,
# one at a time - the owner, 2026-11-15). Each is the vanilla Steel record of its type with the vanilla Skyforge uplift
# the game gives its Skyforge weapons over Steel (one-handed - sword, war axe: damage +3, value +25; two-handed -
# greatsword: damage +3, value +50; weight unchanged),
# critical damage half the damage rounded down (the game's own rule on the Steel and Skyforge swords). A new first-person
# static (vanilla's are shared with the Steel weapons), forged at the Skyforge with Steel Smithing from the vanilla Steel
# recipe's ingredients, tempered with the vanilla Skyforge war axe's recipe.
#   our EDID: (name, vanilla template WEAP, its recipe, 3rd-person mesh, 1st-person mesh, template 1st-person STAT, uplift)
NEW_WEAPONS = {
    "SkyforgeSteelMace": ("Skyforge Steel Mace", "SteelMace", "RecipeWeaponSteelMace", "Mace.nif", "1stPersonMace.nif",
                          "1stPersonSteelMace", "one-handed"),
    "SkyforgeSteelWarhammer": ("Skyforge Steel Warhammer", "SteelWarhammer", "RecipeWeaponSteelWarhammer", "Warhammer.nif",
                               "1stPersonWarhammer.nif", "1stPersonSteelWarhammer", "two-handed"),
    # the game has no Steel bow: the Imperial Bow is its steel-tier bow (tempered with a steel ingot) and is not craftable,
    # so the recipe is written here - 3 steel ingots + 1 leather strips, as the game's own Skyforge bow recipe (Nord Hero
    # Bow: 3 steel ingots + 1 more item) and the Ebony bow (3 ingots); tempered with its Imperial Bow recipe. Its first-
    # person static points at the same file as the third-person model, as vanilla's skinned bows and the Ebony bow do.
    "SkyforgeSteelBow": ("Skyforge Steel Bow", "ImperialBow", [(INGOT_STEEL, 3), (LEATHER_STRIPS, 1)], "Bow.nif", "Bow.nif",
                         "1stPersonEbonyBow", "two-handed", "TemperWeaponImperialBow"),
}
SKYFORGE_UPLIFT = {"one-handed": {"damage": 3, "value": 25}, "two-handed": {"damage": 3, "value": 50}}
# the arrow: the game has no Skyforge Steel arrow (its only Skyforge-made arrow is the Nord Hero arrow, damage 24, a far
# higher tier). The Skyforge Steel Arrow is the vanilla Steel Arrow with the weapons' Skyforge pattern: damage +3 (10 -> 13),
# value x1.5 as the Skyforge one-handed weapons cost over Steel (sword 70/45, war axe 80/55: 2 -> 3). Its own projectile
# (the vanilla steel arrow's, model swapped). Forged at the Skyforge with Steel Smithing: 1 steel ingot + 1 firewood -> 24,
# the game's own arrow-forging proportions (Dawnguard), since Skyrim.esm has no arrow recipe to copy.
NEW_AMMO = {"SkyforgeSteelArrow": ("Skyforge Steel Arrow", "SteelArrow", "ArrowSteelProjectile", "Arrow.nif", "ArrowProjectile.nif",
                                   {"damage": 3.0, "value_mult": 1.5}, [(0x0005ACE5, 1), (0x0006F993, 1)], 24)}
NEW_WEAPON_TEMPER = "TemperWeaponSkyforgeSteelWarAxe"

# the armour set: (our EDID, display name, vanilla template ARMO, LoY addon EDIDs, LoY ground mesh,
#                  forge ingredients [(formid, count)])
ARMOUR = [
    ("SkyforgeSteelCuirass", "Skyforge Steel Armor", "ArmorCompanionsCuirass",
     ["NW_Wolf_Armor_1_AA"], "Armor_Gnd.nif",
     [(INGOT_STEEL, 5), (LEATHER_STRIPS, 3), (LEATHER, 1)]),
    ("SkyforgeSteelBoots", "Skyforge Steel Boots", "ArmorCompanionsBoots",
     ["NW_Wolf_Boots_AA"], "Boots_Gnd.nif",
     [(INGOT_STEEL, 3), (LEATHER_STRIPS, 2), (LEATHER, 1)]),
    ("SkyforgeSteelGauntlets", "Skyforge Steel Gauntlets", "ArmorCompanionsGauntlets",
     ["NW_Wolf_Gauntlets_AA"], "Gauntlets_Gnd.nif",
     [(INGOT_STEEL, 3), (LEATHER_STRIPS, 2)]),
    ("SkyforgeSteelHelmet", "Skyforge Steel Helmet", "ArmorCompanionsHelmet",
     ["NW_Wolf_Helmet_H", "NW_Wolf_Helmet_K", "NW_Wolf_Helmet_A", "NW_Wolf_Helmet_O"], "Helmet_Gnd.nif",
     [(INGOT_STEEL, 3), (LEATHER_STRIPS, 2), (LEATHER, 1)]),
    ("SkyforgeSteelShield", "Skyforge Steel Shield", "NW_Wolf_Shield_Steel",
     ["NW_Wolf_Shield_Steel_AA"], "Weapons/ShieldSteel.nif",
     [(INGOT_STEEL, 4), (LEATHER_STRIPS, 2)]),
]
# the vanilla tempering recipe each piece's is copied from (the shield borrows the cuirass's)
TEMPER_TEMPLATE = {
    "SkyforgeSteelCuirass": "TemperArmorCompanionsCuirass",
    "SkyforgeSteelBoots": "TemperArmorCompanionsBoots",
    "SkyforgeSteelGauntlets": "TemperArmorCompanionsGauntlets",
    "SkyforgeSteelHelmet": "TemperArmorCompanionsHelmet",
    "SkyforgeSteelShield": "TemperArmorCompanionsCuirass",
}

# FormID-bearing subrecords of the record types this script copies, so every reference can be
# checked against the master list. "*" = array, 1 = single, "cnto" = FormID then a count.
REFS = {
    "ARMO": {"MODL": "*", "EITM": 1, "ETYP": 1, "BIDS": 1, "BAMT": 1, "KWDA": "*", "RNAM": 1,
             "TNAM": 1, "YNAM": 1, "ZNAM": 1},
    "ARMA": {"RNAM": 1, "MODL": "*", "SNDD": 1, "NAM0": 1, "NAM1": 1, "NAM2": 1, "NAM3": 1},
    "WEAP": {"ETYP": 1, "BIDS": 1, "BAMT": 1, "INAM": 1, "WNAM": 1, "TNAM": 1, "NAM9": 1,
             "NAM8": 1, "KWDA": "*", "CNAM": 1, "EITM": 1, "YNAM": 1, "ZNAM": 1},
    "COBJ": {"CNAM": 1, "BNAM": 1, "CNTO": "cnto"},
    "STAT": {},
    "AMMO": {"YNAM": 1, "ZNAM": 1, "KWDA": "*", "DATA": 1},
    "PROJ": {},
}


def fail(msg):
    raise SystemExit("build-esp: " + msg)


# Record-header flags are carried from each record's template (1.1.0 fix). Until then every record was written with
# flags 0, so the Skyforge Steel Shield lost the ARMO "Shield" flag (0x40) that ArmorEbonyShield and Legacy of
# Ysgramor's NW_Wolf_Shield_Steel carry; Simple Dual Sheath's shield-on-back reads it, and the owner saw our sheathed
# shield stay on the arm while the Ebony Shield went to the back (2026-11-16). The compressed bit is dropped (we write
# every record uncompressed); a template marked deleted or ignored is refused rather than copied.
HDR_DELETED, HDR_IGNORED = 0x20, 0x1000
ARMO_SHIELD = 0x40
SLOT_39 = 1 << (39 - 30)        # BOD2/BODT body-slot bit for slot 39, the shield


def hdr(rec):
    f = rec["flags"] & ~COMPRESSED
    if f & (HDR_DELETED | HDR_IGNORED):
        fail("template %s (%08X) is marked deleted/ignored (flags %08X)" % (rec["edid"], rec["fid"], rec["flags"]))
    return f


def body_slots(subs):
    v = next((v for s, v in subs if s in (b"BOD2", b"BODT")), None)
    return struct.unpack_from("<I", v)[0] if v and len(v) >= 4 else 0


def subrecords(data):
    i = 0
    while i + 6 <= len(data):
        sig = data[i:i+4]
        n = struct.unpack("<H", data[i+4:i+6])[0]
        i += 6
        yield sig, data[i:i+n]
        i += n


def pack(subs):
    out = bytearray()
    for sig, data in subs:
        out += sig + struct.pack("<H", len(data)) + data
    return bytes(out)


class Plugin(object):
    """Every record of the types we care about, by EDID and by FormID."""
    def __init__(self, path, types):
        d = open(path, "rb").read()
        self.path = path
        hs = struct.unpack("<I", d[4:8])[0]
        self.masters, i = [], 24
        while i + 6 <= 24 + hs:
            s = d[i:i+4]
            n = struct.unpack("<H", d[i+4:i+6])[0]
            i += 6
            if s == b"MAST":
                self.masters.append(d[i:i+n].split(b"\x00")[0].decode("latin-1"))
            i += n
        self.by_edid, self.by_fid = {}, {}
        types = set(t.encode() for t in types)

        def walk(off, end):
            while off < end:
                t = d[off:off+4]
                n = struct.unpack("<I", d[off+4:off+8])[0]
                if t == b"GRUP":
                    walk(off + 24, off + n)
                    off += n
                    continue
                if t in types:
                    flags = struct.unpack("<I", d[off+8:off+12])[0]
                    fid = struct.unpack("<I", d[off+12:off+16])[0]
                    ver = struct.unpack("<H", d[off+20:off+22])[0]
                    body = d[off+24:off+24+n]
                    if flags & COMPRESSED:
                        body = zlib.decompress(body[4:])
                    subs = list(subrecords(body))
                    edid = next((v.split(b"\x00")[0].decode("latin-1") for s, v in subs if s == b"EDID"), "")
                    rec = {"type": t.decode(), "fid": fid, "ver": ver, "subs": subs, "edid": edid, "flags": flags}
                    self.by_fid[fid] = rec
                    if edid:
                        self.by_edid[edid] = rec
                off += 24 + n
        walk(24 + hs, len(d))

    def get(self, edid):
        rec = self.by_edid.get(edid)
        if rec is None:
            fail("%s has no record '%s'" % (os.path.basename(self.path), edid))
        return rec


# Ground models changed at packaging time, AFTER this script runs (tools/build-package.py copies Legacy of Ysgramor's
# mesh into the package, then calls these on it). The bounds must describe the model as it ships, so the same step runs
# here on a temporary copy. Keep this table and build-package.py's steps in step.
def _resize_shield(path):
    import sys
    sys.path.insert(0, os.path.join(HERE, "missing_weapons"))
    import shield_size
    shield_size.resize(path)


GROUND_MODEL_STEPS = {"nordicskyforge\\weapons\\shieldsteel.nif": _resize_shield}


def ground_model_bounds(model, loy_meshes):
    """OBND for an item whose template carries none (1.1.0: the Skyforge Steel Shield shipped 0,0,0 / 0,0,0 because
    Legacy of Ysgramor's own shield record has zero bounds - with Immersive Equipment Displays the favourited shield did
    not show on the back while the vanilla-record Ebony Shield did). Computed the way the Creation Kit does: the extents
    of every vertex of every shape in the model's root frame, rounded outward to whole units (int16).
    The model is our path (NordicSkyforge\\{armor|weapons}\\X.nif), read from Legacy of Ysgramor's mesh it is packaged
    from, with any packaging step (GROUND_MODEL_STEPS) applied first to a temporary copy."""
    import math
    import shutil
    import sys
    import tempfile
    sys.path.insert(0, os.path.join(HERE, "missing_weapons"))
    import niflib
    import shield_size
    parts = model.replace("/", "\\").split("\\")
    if len(parts) != 3 or parts[0].lower() != MESH_ROOT.lower():
        fail("cannot compute bounds for '%s' - not one of Legacy of Ysgramor's meshes" % model)
    rel = ["NordWar", "Companions"] + (["Weapons"] if parts[1].lower() == "weapons" else []) + [parts[2]]
    src = loy_meshes
    for seg in rel:
        hit = [e for e in os.listdir(src) if e.lower() == seg.lower()] if os.path.isdir(src) else []
        if not hit:
            fail("cannot compute bounds for '%s': %s has no %s" % (model, src, seg))
        src = os.path.join(src, hit[0])
    tmp = tempfile.mkdtemp(prefix="nsaw-obnd-")
    try:
        work = os.path.join(tmp, parts[2])
        shutil.copy2(src, work)
        step = GROUND_MODEL_STEPS.get("\\".join(parts).lower())
        if step:
            step(work)
        P = shield_size.world_points(niflib.Nif(work))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    lo = [int(math.floor(x)) for x in P.min(0)]
    hi = [int(math.ceil(x)) for x in P.max(0)]
    ob = lo + hi
    if not all(-32768 <= x <= 32767 for x in ob) or not any(ob):
        fail("bounds for '%s' are out of range or zero: %s" % (model, ob))
    return ob


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?")
    ap.add_argument("--loy", default=LOY_DEFAULT)
    a = ap.parse_args()

    skyrim = Plugin(os.path.join(GAME_DATA, "Skyrim.esm"), ["ARMO", "WEAP", "COBJ", "STAT", "AMMO", "PROJ", "MISC"])
    loy = Plugin(a.loy, ["ARMA", "ARMO"])
    # a plugin's own records sit at index len(masters) in its own numbering
    sky_ix = skyrim.masters + ["Skyrim.esm"]
    loy_ix = loy.masters + [os.path.basename(a.loy)]

    masters = ["Skyrim.esm"]
    own = len(masters)           # 1
    nxt = FIRST_NEW
    records = []                 # (type, fid, ver, subs)
    new_fid = {}                 # our EDID -> FormID

    def allot(edid):
        nonlocal nxt
        if nxt > 0xFFF:
            fail("more than 2048 new records - not a light plugin any more")
        fid = (own << 24) | nxt
        nxt += 1
        new_fid[edid] = fid
        return fid

    def check_refs(rtype, subs, source_masters, where):
        """Every FormID in the copied body must resolve inside Skyrim.esm, or be one of ours."""
        for s, v in subs:
            spec = REFS[rtype].get(s.decode("latin-1"))
            if not spec:
                continue
            offs = [0] if spec in (1, "cnto") else list(range(0, len(v) - 3, 4))
            for o in offs:
                fid = struct.unpack_from("<I", v, o)[0]
                if fid in (0, 0xFFFFFFFF):
                    continue
                idx = fid >> 24
                if idx == own and (fid & 0xFFFFFF) >= FIRST_NEW and fid in new_fid.values():
                    continue
                if idx >= len(source_masters) or source_masters[idx].lower() != "skyrim.esm":
                    fail("%s: %s carries %08X, which is not a Skyrim.esm record - this plugin "
                         "masters Skyrim.esm only" % (where, s.decode(), fid))

    # ---- 1. the weapons: vanilla bodies, models repointed
    replaced_weapons = {}
    for edid, (mesh, full) in WEAPONS.items():
        rec = skyrim.get(edid)
        subs = []
        for s, v in rec["subs"]:
            if s == b"FULL":
                v = full.encode("latin-1") + b"\x00"
            elif s == b"DESC":
                v = b"\x00"
            elif s == b"MODL":
                # relative to meshes\, exactly as vanilla's "Weapons\Steel\SteelSword.nif" is
                v = ("%s\\weapons\\%s" % (MESH_ROOT, mesh)).encode("latin-1") + b"\x00"
            elif s == b"MODT":
                continue   # the texture-hash blob describes the old mesh; the game copes without it
            subs.append((s, v))
        check_refs("WEAP", subs, sky_ix, edid)
        records.append(("WEAP", rec["fid"], rec["ver"], subs, hdr(rec)))
        replaced_weapons[edid] = subs        # WNAM repointed at the end (section 7), so 1.0.0's FormIDs stay put

    # ---- 2. the armour addons: LoY's bodies, models repointed, one per piece/race
    def repath(v):
        p = v.split(b"\x00")[0].decode("latin-1")
        low = p.replace("/", "\\").lower()
        prefix = "nordwar\\companions\\"
        if not low.startswith(prefix):
            fail("LoY addon model '%s' is not under NordWar\\Companions - layout changed" % p)
        rest = p.replace("/", "\\")[len(prefix):]
        if rest.lower().startswith("weapons\\"):
            return ("%s\\weapons\\%s" % (MESH_ROOT, rest[len("weapons\\"):])).encode("latin-1") + b"\x00"
        return ("%s\\armor\\%s" % (MESH_ROOT, rest)).encode("latin-1") + b"\x00"

    arma_fid = {}
    meshes_needed = set()
    for our_edid, full, template, addons, gnd, ingredients in ARMOUR:
        for addon in addons:
            src = loy.get(addon)
            new_edid = "Skyforge_" + addon[len("NW_Wolf_"):] if addon.startswith("NW_Wolf_") else "Skyforge_" + addon
            fid = allot(new_edid)
            arma_fid[addon] = fid
            subs = []
            for s, v in src["subs"]:
                if s == b"EDID":
                    v = new_edid.encode("latin-1") + b"\x00"
                elif s in (b"MOD2", b"MOD3", b"MOD4", b"MOD5"):
                    v = repath(v)
                    meshes_needed.add(v.split(b"\x00")[0].decode("latin-1"))
                elif s in (b"MO2T", b"MO3T", b"MO4T", b"MO5T"):
                    continue
                subs.append((s, v))
            if body_slots(subs) & SLOT_39:
                # the shield addon, as the game's EbonyShieldAA has it: the same model as the FEMALE world model too
                # (Legacy of Ysgramor's addon carries the male one only), and the two Draugr races among the additional
                # races (its list stops at the playable races and their vampires).
                if not any(s == b"MOD3" for s, v in subs):
                    i = max(j for j, (s, v) in enumerate(subs) if s in (b"MOD2", b"MO2S"))
                    subs.insert(i + 1, (b"MOD3", next(v for s, v in subs if s == b"MOD2")))
                have = {struct.unpack("<I", v)[0] for s, v in subs if s == b"MODL"}
                last = max(j for j, (s, v) in enumerate(subs) if s == b"MODL")
                for race in (RACE_DRAUGR, RACE_DRAUGR_MAGIC):
                    if race not in have:
                        last += 1
                        subs.insert(last, (b"MODL", struct.pack("<I", race)))
            check_refs("ARMA", subs, loy_ix, addon)
            records.append(("ARMA", fid, src["ver"], subs, hdr(src)))

    # ---- 3. the armour items: vanilla Wolf Armor bodies (LoY's for the shield), renamed and repointed
    armo_fid = {}
    for our_edid, full, template, addons, gnd, ingredients in ARMOUR:
        src = skyrim.get(template) if template in skyrim.by_edid else loy.get(template)
        src_masters = sky_ix if template in skyrim.by_edid else loy_ix
        fid = allot(our_edid)
        armo_fid[our_edid] = fid
        gnd_path = ("%s\\%s\\%s" % (MESH_ROOT, "weapons" if gnd.lower().startswith("weapons/") else "armor",
                                     gnd.split("/")[-1]))
        meshes_needed.add(gnd_path)
        subs = []
        for s, v in src["subs"]:
            if s == b"EDID":
                v = our_edid.encode("latin-1") + b"\x00"
            elif s == b"FULL":
                v = full.encode("latin-1") + b"\x00"
            elif s == b"MOD2":
                v = gnd_path.encode("latin-1") + b"\x00"
            elif s in (b"MO2T", b"MO4T", b"MOD4"):
                continue
            elif s == b"MODL":
                # ONE MODL SUBRECORD PER ADDON, 4 bytes each - the way the template carries them.
                # The first cut packed all four helmet addons into a single 16-byte MODL; the
                # engine reads MODL as one FormID and threw the record's addon list away, so the
                # Skyforge Steel Helmet was invisible while Legacy of Ysgramor's own helmet, on
                # otherwise identical records, rendered (the owner, 2026-09-17: "the skyforged
                # made the head look wierd"). Written at the first template MODL, in addon order;
                # the template's later MODLs are dropped.
                if any(x[0] == b"MODL" for x in subs):
                    continue
                for ad in addons:
                    subs.append((b"MODL", struct.pack("<I", arma_fid[ad])))
                continue
            elif s == b"DESC":
                v = b"\x00"
            subs.append((s, v))
        # MODL may sit anywhere in the template; if the template had none (it always does), refuse
        if not any(s == b"MODL" for s, v in subs):
            fail("template %s has no MODL - nothing to point at our addons" % template)
        # a template with several addons but our piece listing more/less: MODL was rebuilt above
        check_refs("ARMO", subs, src_masters, our_edid)
        records.append(("ARMO", fid, src["ver"], subs, hdr(src)))

    # ---- 4. recipes: forge at the Skyforge, temper at the armour table
    def ctda_has_perk(perk):
        # type/flags 0 (==, subject), value 1.0, function 448 HasPerk, then the game's own padding
        return (b"\x00\x00\x00\x00" + struct.pack("<f", 1.0) + struct.pack("<H", 448) + b"\x54\x00"
                + struct.pack("<I", perk) + struct.pack("<I", 0) + struct.pack("<I", 0)
                + struct.pack("<I", 0) + struct.pack("<i", -1))

    temper_ver = skyrim.get("TemperArmorCompanionsCuirass")["ver"]
    for our_edid, full, template, addons, gnd, ingredients in ARMOUR:
        # forge
        fid = allot("Recipe" + our_edid)
        subs = [(b"EDID", ("Recipe" + our_edid).encode("latin-1") + b"\x00"),
                (b"COCT", struct.pack("<I", len(ingredients)))]
        for item, count in ingredients:
            subs.append((b"CNTO", struct.pack("<II", item, count)))
        subs += [(b"CTDA", ctda_has_perk(PERK_STEEL)),
                 (b"CNAM", struct.pack("<I", armo_fid[our_edid])),
                 (b"BNAM", struct.pack("<I", K_SKYFORGE)),
                 (b"NAM1", struct.pack("<H", 1))]
        check_refs("COBJ", subs, sky_ix, "Recipe" + our_edid)
        records.append(("COBJ", fid, temper_ver, subs, 0))         # written here, no template
        # temper: the vanilla Wolf Armor recipe with the created object swapped
        src = skyrim.get(TEMPER_TEMPLATE[our_edid])
        fid = allot("Temper" + our_edid)
        subs = []
        for s, v in src["subs"]:
            if s == b"EDID":
                v = ("Temper" + our_edid).encode("latin-1") + b"\x00"
            elif s == b"CNAM":
                v = struct.pack("<I", armo_fid[our_edid])
            subs.append((s, v))
        check_refs("COBJ", subs, sky_ix, "Temper" + our_edid)
        records.append(("COBJ", fid, src["ver"], subs, hdr(src)))

    # ---- 5. new weapon types: vanilla Steel bodies + the Skyforge uplift, own first-person static, forge and temper
    new_weapon_meshes = []
    for our_edid, spec in NEW_WEAPONS.items():
        full, template, recipe, mesh3, mesh1, stat_template, hands = spec[:7]
        temper_template = spec[7] if len(spec) > 7 else NEW_WEAPON_TEMPER
        st = skyrim.get(stat_template)
        stat_edid = "1stPerson" + our_edid
        stat_fid = allot(stat_edid)
        subs = []
        for s, v in st["subs"]:
            if s == b"EDID":
                v = stat_edid.encode("latin-1") + b"\x00"
            elif s == b"MODL":
                v = ("%s\\weapons\\%s" % (MESH_ROOT, mesh1)).encode("latin-1") + b"\x00"
            elif s == b"MODT":
                continue
            subs.append((s, v))
        if not any(s == b"MODL" for s, v in subs):
            fail("%s has no MODL" % stat_template)
        check_refs("STAT", subs, sky_ix, stat_edid)
        records.append(("STAT", stat_fid, st["ver"], subs, hdr(st)))

        src = skyrim.get(template)
        fid = allot(our_edid)
        subs, seen = [], set()
        for s, v in src["subs"]:
            seen.add(s)
            if s == b"EDID":
                v = our_edid.encode("latin-1") + b"\x00"
            elif s == b"FULL":
                v = full.encode("latin-1") + b"\x00"
            elif s == b"DESC":
                v = b"\x00"
            elif s == b"MODL":
                v = ("%s\\weapons\\%s" % (MESH_ROOT, mesh3)).encode("latin-1") + b"\x00"
            elif s == b"MODT":
                continue
            elif s == b"WNAM":
                v = struct.pack("<I", stat_fid)
            elif s == b"DATA":
                val, wt, dmg = struct.unpack_from("<IfH", v)
                dmg += SKYFORGE_UPLIFT[hands]["damage"]; val += SKYFORGE_UPLIFT[hands]["value"]
                v = struct.pack("<IfH", val, wt, dmg) + v[10:]
                new_dmg = dmg
            elif s == b"CRDT":
                v = struct.pack("<H", new_dmg // 2) + v[2:]
            subs.append((s, v))
        for need in (b"MODL", b"WNAM", b"DATA", b"CRDT"):
            if need not in seen:
                fail("%s has no %s" % (template, need.decode()))
        check_refs("WEAP", subs, sky_ix, our_edid)
        records.append(("WEAP", fid, src["ver"], subs, hdr(src)))
        for m_ in dict.fromkeys(["%s\\weapons\\%s" % (MESH_ROOT, mesh3), "%s\\weapons\\%s" % (MESH_ROOT, mesh1)]):
            new_weapon_meshes.append(m_)

        # forge at the Skyforge: the vanilla Steel recipe, created object and workbench swapped (or written, see the bow)
        rfid = allot("Recipe" + our_edid)
        if isinstance(recipe, str):
            rc = skyrim.get(recipe); rver = rc["ver"]; rflags = hdr(rc)
            subs = []
            for s, v in rc["subs"]:
                if s == b"EDID":
                    v = ("Recipe" + our_edid).encode("latin-1") + b"\x00"
                elif s == b"CNAM":
                    v = struct.pack("<I", fid)
                elif s == b"BNAM":
                    v = struct.pack("<I", K_SKYFORGE)
                subs.append((s, v))
        else:
            rver = temper_ver; rflags = 0     # written here, no template
            subs = [(b"EDID", ("Recipe" + our_edid).encode("latin-1") + b"\x00"), (b"COCT", struct.pack("<I", len(recipe)))]
            subs += [(b"CNTO", struct.pack("<II", item, n_)) for item, n_ in recipe]
            subs += [(b"CTDA", ctda_has_perk(PERK_STEEL)), (b"CNAM", struct.pack("<I", fid)), (b"BNAM", struct.pack("<I", K_SKYFORGE)),
                     (b"NAM1", struct.pack("<H", 1))]
        check_refs("COBJ", subs, sky_ix, "Recipe" + our_edid)
        records.append(("COBJ", rfid, rver, subs, rflags))
        # temper: the vanilla Skyforge war axe's recipe with the created object swapped
        tc = skyrim.get(temper_template)
        tfid = allot("Temper" + our_edid)
        subs = []
        for s, v in tc["subs"]:
            if s == b"EDID":
                v = ("Temper" + our_edid).encode("latin-1") + b"\x00"
            elif s == b"CNAM":
                v = struct.pack("<I", fid)
            subs.append((s, v))
        check_refs("COBJ", subs, sky_ix, "Temper" + our_edid)
        records.append(("COBJ", tfid, tc["ver"], subs, hdr(tc)))

    # ---- 6. new ammunition: the vanilla arrow + projectile, models swapped, Skyforge pattern, forged at the Skyforge
    for our_edid, (full, template, proj_template, mesh, flight, uplift, ingredients, count) in NEW_AMMO.items():
        pj = skyrim.get(proj_template)
        proj_edid = our_edid + "Projectile"
        proj_fid = allot(proj_edid)
        subs = []
        for s, v in pj["subs"]:
            if s == b"EDID":
                v = proj_edid.encode("latin-1") + b"\x00"
            elif s == b"FULL":
                v = full.encode("latin-1") + b"\x00"
            elif s == b"MODL":
                v = ("%s\\weapons\\%s" % (MESH_ROOT, flight)).encode("latin-1") + b"\x00"
            elif s == b"MODT":
                continue
            subs.append((s, v))
        check_refs("PROJ", subs, sky_ix, proj_edid)
        records.append(("PROJ", proj_fid, pj["ver"], subs, hdr(pj)))
        am = skyrim.get(template)
        fid = allot(our_edid)
        subs = []
        for s, v in am["subs"]:
            if s == b"EDID":
                v = our_edid.encode("latin-1") + b"\x00"
            elif s == b"FULL":
                v = full.encode("latin-1") + b"\x00"
            elif s == b"DESC":
                v = b"\x00"
            elif s == b"MODL":
                v = ("%s\\weapons\\%s" % (MESH_ROOT, mesh)).encode("latin-1") + b"\x00"
            elif s == b"MODT":
                continue
            elif s == b"DATA":
                _, flags, dmg, val = struct.unpack_from("<IIfI", v)
                v = struct.pack("<IIfI", proj_fid, flags, dmg + uplift["damage"], int(round(val * uplift["value_mult"]))) + v[16:]
            subs.append((s, v))
        check_refs("AMMO", subs, sky_ix, our_edid)
        records.append(("AMMO", fid, am["ver"], subs, hdr(am)))
        new_weapon_meshes += ["%s\\weapons\\%s" % (MESH_ROOT, mesh), "%s\\weapons\\%s" % (MESH_ROOT, flight)]
        for item, _ in ingredients:
            if item not in skyrim.by_fid:
                fail("ingredient %08X is not in Skyrim.esm" % item)
        rfid = allot("Recipe" + our_edid)
        subs = [(b"EDID", ("Recipe" + our_edid).encode("latin-1") + b"\x00"), (b"COCT", struct.pack("<I", len(ingredients)))]
        subs += [(b"CNTO", struct.pack("<II", item, n)) for item, n in ingredients]
        subs += [(b"CTDA", ctda_has_perk(PERK_STEEL)), (b"CNAM", struct.pack("<I", fid)), (b"BNAM", struct.pack("<I", K_SKYFORGE)),
                 (b"NAM1", struct.pack("<H", count))]
        check_refs("COBJ", subs, sky_ix, "Recipe" + our_edid)
        records.append(("COBJ", rfid, temper_ver, subs, 0))       # written here, no template

    # ---- 7. first person for the five replaced weapons (1.1.0): their WNAM named vanilla's Steel first-person statics,
    # which the Steel weapons share, so in first person they showed vanilla steel. Each gets its own static (vanilla's
    # copied, model swapped) on tools/build-missing-weapons.py's first-person copy of its model. Allotted LAST so every
    # 1.0.0 FormID stays where it was.
    for edid, (mesh, full) in WEAPONS.items():
        subs = replaced_weapons[edid]
        wi = [i for i, (s, v) in enumerate(subs) if s == b"WNAM"]
        if len(wi) != 1:
            fail("%s has %d WNAM" % (edid, len(wi)))
        st = skyrim.by_fid.get(struct.unpack("<I", subs[wi[0]][1])[0])
        if st is None or st["type"] != "STAT":
            fail("%s's WNAM is not a Skyrim.esm static" % edid)
        stat_edid = "1stPerson" + edid
        stat_fid = allot(stat_edid)
        mesh1 = "%s\\weapons\\1stPerson%s" % (MESH_ROOT, mesh)
        ssubs = []
        for s, v in st["subs"]:
            if s == b"EDID":
                v = stat_edid.encode("latin-1") + b"\x00"
            elif s == b"MODL":
                v = mesh1.encode("latin-1") + b"\x00"
            elif s == b"MODT":
                continue
            ssubs.append((s, v))
        check_refs("STAT", ssubs, sky_ix, stat_edid)
        records.append(("STAT", stat_fid, st["ver"], ssubs, hdr(st)))
        subs[wi[0]] = (b"WNAM", struct.pack("<I", stat_fid))
        new_weapon_meshes.append(mesh1)

    # ---- 8. object bounds (1.1.0 fix): every item carries real OBND. A template with all-zero bounds (Legacy of
    # Ysgramor's NW_Wolf_Shield_Steel, copied for the shield) gets them computed from the item's own ground model as it
    # ships; any item still at zero refuses the build. See ground_model_bounds.
    loy_meshes = os.path.join(os.path.dirname(os.path.abspath(a.loy)), "meshes")
    bounds_written = []
    for rtype, fid, ver, subs, _f in records:
        if rtype not in ("ARMO", "WEAP", "AMMO"):
            continue
        edid = next(v.split(b"\x00")[0].decode("latin-1") for s, v in subs if s == b"EDID")
        oi = [i for i, (s, v) in enumerate(subs) if s == b"OBND"]
        if len(oi) != 1 or len(subs[oi[0]][1]) != 12:
            fail("%s has no single 12-byte OBND" % edid)
        if any(struct.unpack("<6h", subs[oi[0]][1])):
            continue
        model_sig = b"MOD2" if rtype == "ARMO" else b"MODL"     # ARMO's MODL is an addon FormID; its ground model is MOD2
        model = next((v.split(b"\x00")[0].decode("latin-1") for s, v in subs if s == model_sig), None)
        if not model:
            fail("%s has all-zero OBND and no ground model to compute them from" % edid)
        ob = ground_model_bounds(model, loy_meshes)
        subs[oi[0]] = (b"OBND", struct.pack("<6h", *ob))
        bounds_written.append((edid, model, ob))
    for rtype, fid, ver, subs, _f in records:
        if rtype in ("ARMO", "WEAP", "AMMO"):
            v = next(v for s, v in subs if s == b"OBND")
            if not any(struct.unpack("<6h", v)):
                fail("%08X (%s) would ship with all-zero OBND" % (fid, rtype))

    # ---- 9. every shield (an ARMO on body slot 39) carries the ARMO "Shield" header flag - see hdr()
    for rtype, fid, ver, subs, rflags in records:
        if rtype == "ARMO" and body_slots(subs) & SLOT_39 and not rflags & ARMO_SHIELD:
            fail("%08X is a slot-39 armour without the Shield flag (0x40) - shield-on-back mods would leave it on the arm"
                 % fid)

    # ---- emit, one group per type
    order =["ARMA", "ARMO", "STAT", "PROJ", "WEAP", "AMMO", "COBJ"]
    groups = bytearray()
    counts = {}
    for rtype in order:
        payload = bytearray()
        for t, fid, ver, subs, rflags in sorted((r for r in records if r[0] == rtype), key=lambda r: r[1]):
            body = pack(subs)
            payload += (t.encode("latin-1") + struct.pack("<IIIIHH", len(body), rflags, fid, 0, ver, 0) + body)
            counts[rtype] = counts.get(rtype, 0) + 1
        groups += (b"GRUP" + struct.pack("<I", len(payload) + 24) + rtype.encode("latin-1")
                   + struct.pack("<iii", 0, 0, 0) + payload)

    head = bytearray()
    head += b"HEDR" + struct.pack("<H", 12) + struct.pack("<fiI", 1.7, len(records), nxt)
    head += b"CNAM" + struct.pack("<H", len(AUTHOR) + 1) + AUTHOR.encode("latin-1") + b"\x00"
    head += b"SNAM" + struct.pack("<H", len(DESCRIPTION) + 1) + DESCRIPTION.encode("latin-1") + b"\x00"
    for m in masters:
        head += b"MAST" + struct.pack("<H", len(m) + 1) + m.encode("latin-1") + b"\x00"
        head += b"DATA" + struct.pack("<H", 8) + struct.pack("<Q", 0)
    tes4 = b"TES4" + struct.pack("<IIIIHH", len(head), ESL_FLAG, 0, 0, 44, 0) + bytes(head)

    out = a.out or os.path.join(REPO, "plugin", PLUGIN_NAME)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "wb").write(tes4 + bytes(groups))

    # the mesh list the package builder must satisfy
    with open(os.path.join(REPO, "plugin", "meshes-needed.txt"), "w", encoding="utf-8") as f:
        for m in sorted(meshes_needed):
            f.write(m + "\n")
        for edid, (mesh, full) in WEAPONS.items():
            f.write("%s\\weapons\\%s\n" % (MESH_ROOT, mesh))
    # the meshes tools/build-missing-weapons.py builds (not in Legacy of Ysgramor's archive)
    with open(os.path.join(REPO, "plugin", "meshes-built.txt"), "w", encoding="utf-8") as f:
        for m in new_weapon_meshes:
            f.write(m + "\n")

    print("wrote %s" % out)
    print("  masters ............... %s" % ", ".join(masters))
    print("  records ............... %s" % ", ".join("%s %d" % (k, counts[k]) for k in order))
    print("  new records ........... %d at 0x%06X-0x%06X" % (nxt - FIRST_NEW, FIRST_NEW, nxt - 1))
    print("  weapon models moved ... %d" % len(WEAPONS))
    print("  new weapon types ...... %d (%s), built meshes %d (plugin/meshes-built.txt)"
          % (len(NEW_WEAPONS), ", ".join(NEW_WEAPONS), len(new_weapon_meshes)))
    print("  meshes the package owes  %d (plugin/meshes-needed.txt)" % (len(meshes_needed) + len(WEAPONS)))
    for edid, model, ob in bounds_written:
        print("  bounds computed ....... %s from %s%s: %d,%d,%d / %d,%d,%d" % (
            (edid, model, " (as packaged)" if model.replace("/", "\\").lower() in GROUND_MODEL_STEPS else "") + tuple(ob)))
    print("  light flag ............ set")


if __name__ == "__main__":
    main()
