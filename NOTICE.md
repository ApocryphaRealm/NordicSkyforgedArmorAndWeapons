# Whose work this is

**None of the art is ours.** This mod is a mapping job: it takes an existing armour set and a
set of weapons and puts them where the game's Skyforge Steel gear sits.

## The armour and weapons - Legacy of Ysgramor

[Nexus 109963](https://www.nexusmods.com/skyrimspecialedition/mods/109963), by **NordwarUA**. Every
mesh, and every normal and mask texture, comes from its main archive and its Fur Lighting Bug patch.
The armour ADDON records in the plugin - the body slots and race list of each piece - are copied
from his plugin at build time, so each piece behaves as he built it.

## The black colourway - Legacy of Ysgramor, my patches and fixes

[Nexus 111121](https://www.nexusmods.com/skyrimspecialedition/mods/111121), by **Xtudo**. The
diffuse textures come from his Wolf Black download (1K, 2K and 4K) and his Full Collar Black.

**The repository carries none of these files.** `tools/build-package.py` opens the Nexus downloads at
build time and derives the texture list from the meshes it is shipping. The texture paths inside the
shipped meshes are rewritten to this mod's own folder, so installing it next to Legacy of Ysgramor
leaves that mod's Wolf Armor exactly as it was.

**Permissions.** Per the owner's standing policy for our asset mods, set 2026-09-16, the mod page
names both authors and links back to both mod pages.

## The body refits - HIMBO and CBBE 3BA options

[Nexus 110002](https://www.nexusmods.com/skyrimspecialedition/mods/110002), **Legacy of Ysgramor - HIMBO
Conversion** by **Trexasle**: the prebuilt HIMBO male meshes and the HIMBO BodySlide slider sets and
shape data. [Nexus 111209](https://www.nexusmods.com/skyrimspecialedition/mods/111209), **Legacy of
Ysgramor - 3BA Bodyslide** by **Xonek**: the CBBE 3BA slider sets and shape data. Both are installed
as optional choices, renamed and repathed to this mod's folders by `tools/loy-refits.py`; the mod page
names both authors and links back to both pages.

## The new weapon types (1.1.0 on)

The Skyforge Steel Mace (and the weapon types that follow it) is assembled at build time by
`tools/build-missing-weapons.py` from pieces of NordwarUA's steel war axe in the same Legacy of Ysgramor download,
each piece keeping its own texture; the node tree, blood shapes and collision it is built on come from the game's own
ebony mace in the player's Skyrim - Meshes BSA. The repository carries none of these files.

## What IS ours

`tools/`, `fomod/ModuleConfig.xml`, the plugin generator and the documentation.
GPL-3.0-or-later, Copyright (C) 2026 ApocryphaRealm.

## Permission to use Legacy of Ysgramor's assets (recorded 2026-11-12)

The owner (2026-11-12): this mod "has permission for use since this is the mod its from" - and the same permission
applies to both of our mods built from that source (Nordic Ebony Armor and Weapons Replacer and Nordic Skyforged Armor
and Weapons). The permissions box on
[Legacy of Ysgramor](https://www.nexusmods.com/skyrimspecialedition/mods/109963) (NordwarUA), read 2026-11-12, says:

- Other user's assets: all the assets belong to the author or are free-to-use modder's resources.
- **Modification permission: allowed** - "You are allowed to modify my files and release bug fixes or improve on the
  features so long as you credit me as the original creator".
- **Asset use permission: allowed** - "You are allowed to use the assets in this file without permission as long as you
  credit me".
- Conversion permission: allowed, with credit.
- Upload permission: NOT allowed to upload the file to other sites - so this mod is posted on Nexus only, never on
  another site.
- Assets in mods that are being sold: NOT allowed - this mod is never sold or paywalled.
- Assets in mods that earn Donation Points: allowed.

Conditions we keep: credit NordwarUA as the original creator on the mod page and in this file, link back to Legacy of
Ysgramor, post on Nexus only, and never sell it. The other sources named above (Xtudo's colourways, the HIMBO and 3BA
conversions) keep their own credit lines and are checked against their own pages.
