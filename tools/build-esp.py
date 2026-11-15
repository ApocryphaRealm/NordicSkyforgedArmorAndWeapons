#!/usr/bin/env python3
r"""Generate the light plugin for Nordic Skyforged Armor and Weapons.

WHAT THE PLUGIN DOES
    Two things, in one ESPFE (a .esp carrying the light flag, so it costs no load-order slot and
    can still be positioned):

    1. REPLACES the five vanilla Skyforge Steel weapons' models with NordwarUA's steel wolf
       weapons from Legacy of Ysgramor: the sword, greatsword, war axe, battleaxe and dagger.
       Everything else about those records - damage, value, keywords, sounds - stays vanilla,
       because the body is copied from Skyrim.esm and only MODL changes.

    2. ADDS a Skyforge Steel armour set - cuirass, boots, gauntlets, helmet and shield - built
       from the steel wolf armour of the same mod (the fur-collared cuirass). The stats are the
       game's own Wolf Armor stats, record for record, so the set sits where Wolf Armor sits:
       heavy, steel material, tempered with a steel ingot. It is forged at the Skyforge with the
       Steel Smithing perk. The Wolf Armor itself is not touched - the owner, 2026-09-16:
       "i dont want to replace wolf armor, i want to replace skyforged weapons and add skyforged
       armor, leave wolf alone".

    3. ADDS the Skyforge Steel weapon types the game has none of (the owner, 2026-11-15: the same
       weapon types the Nordic Ebony replacer gained), one at a time - so far the MACE and the WARHAMMER. See
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
}
SKYFORGE_UPLIFT = {"one-handed": {"damage": 3, "value": 25}, "two-handed": {"damage": 3, "value": 50}}
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
}


def fail(msg):
    raise SystemExit("build-esp: " + msg)


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
                    rec = {"type": t.decode(), "fid": fid, "ver": ver, "subs": subs, "edid": edid}
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?")
    ap.add_argument("--loy", default=LOY_DEFAULT)
    a = ap.parse_args()

    skyrim = Plugin(os.path.join(GAME_DATA, "Skyrim.esm"), ["ARMO", "WEAP", "COBJ", "STAT"])
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
        records.append(("WEAP", rec["fid"], rec["ver"], subs))

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
            check_refs("ARMA", subs, loy_ix, addon)
            records.append(("ARMA", fid, src["ver"], subs))

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
        records.append(("ARMO", fid, src["ver"], subs))

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
        records.append(("COBJ", fid, temper_ver, subs))
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
        records.append(("COBJ", fid, src["ver"], subs))

    # ---- 5. new weapon types: vanilla Steel bodies + the Skyforge uplift, own first-person static, forge and temper
    new_weapon_meshes = []
    for our_edid, (full, template, recipe, mesh3, mesh1, stat_template, hands) in NEW_WEAPONS.items():
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
        records.append(("STAT", stat_fid, st["ver"], subs))

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
        records.append(("WEAP", fid, src["ver"], subs))
        new_weapon_meshes += ["%s\\weapons\\%s" % (MESH_ROOT, mesh3), "%s\\weapons\\%s" % (MESH_ROOT, mesh1)]

        # forge at the Skyforge: the vanilla Steel recipe, created object and workbench swapped
        rc = skyrim.get(recipe)
        rfid = allot("Recipe" + our_edid)
        subs = []
        for s, v in rc["subs"]:
            if s == b"EDID":
                v = ("Recipe" + our_edid).encode("latin-1") + b"\x00"
            elif s == b"CNAM":
                v = struct.pack("<I", fid)
            elif s == b"BNAM":
                v = struct.pack("<I", K_SKYFORGE)
            subs.append((s, v))
        check_refs("COBJ", subs, sky_ix, "Recipe" + our_edid)
        records.append(("COBJ", rfid, rc["ver"], subs))
        # temper: the vanilla Skyforge war axe's recipe with the created object swapped
        tc = skyrim.get(NEW_WEAPON_TEMPER)
        tfid = allot("Temper" + our_edid)
        subs = []
        for s, v in tc["subs"]:
            if s == b"EDID":
                v = ("Temper" + our_edid).encode("latin-1") + b"\x00"
            elif s == b"CNAM":
                v = struct.pack("<I", fid)
            subs.append((s, v))
        check_refs("COBJ", subs, sky_ix, "Temper" + our_edid)
        records.append(("COBJ", tfid, tc["ver"], subs))

    # ---- emit, one group per type
    order = ["ARMA", "ARMO", "STAT", "WEAP", "COBJ"]
    groups = bytearray()
    counts = {}
    for rtype in order:
        payload = bytearray()
        for t, fid, ver, subs in sorted((r for r in records if r[0] == rtype), key=lambda r: r[1]):
            body = pack(subs)
            payload += (t.encode("latin-1") + struct.pack("<IIIIHH", len(body), 0, fid, 0, ver, 0) + body)
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
    print("  light flag ............ set")


if __name__ == "__main__":
    main()
