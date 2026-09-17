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

## What IS ours

`tools/`, `fomod/ModuleConfig.xml`, the plugin generator and the documentation.
GPL-3.0-or-later, Copyright (C) 2026 ApocryphaRealm.
