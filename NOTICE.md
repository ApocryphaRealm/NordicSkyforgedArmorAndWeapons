# Whose work this is

**The art is NordwarUA's.** This mod is a mapping job: it takes his steel Wolf armour set and weapons from Legacy of
Ysgramor and puts them where the game's Skyforge Steel gear sits. Since 1.1.0 the textures are **his own textures
recoloured all-black and made into TruePBR materials** by our build scripts. All of it is modification and asset use of
Legacy of Ysgramor under its permissions (below): with credit to NordwarUA as the original creator, on Nexus only,
never sold.

## The armour and weapons - Legacy of Ysgramor

[Nexus 109963](https://www.nexusmods.com/skyrimspecialedition/mods/109963), by **NordwarUA**. Every mesh, and every
diffuse, normal and mask texture the materials are made from, comes from its main archive and its Fur Lighting Bug
patch (the corrected FurCollar_n). The armour ADDON records in the plugin - the body slots and race list of each piece -
are copied from his plugin at build time, so each piece behaves as he built it.

## The textures - our black recolour of his originals, in TruePBR

`tools/recolour_black.py` turns NordwarUA's original diffuses all-black: the red and brown cloth, tabard, leather
straps, hafts and shield planks and the fur go black-grey, and the grey steel is left alone. It is a hue- and
saturation-masked recolour tuned by overall numbers only; no other author's texture is read or shipped.
`tools/truepbr.py` then makes each material a Community Shaders **TruePBR** material, the way our Truly Nordic Carved
Weapons Replacer does: an albedo (the recolour, its baked highlights taken out), **his own normal map unchanged**, and
an RMAOS map (roughness, metal, ambient occlusion, specular) worked out from his own environment mask - metal where his
mask says the surface shines, leather, cloth, wood and fur never metal. His damascus-look and wear detail stays as he
painted it. One texture set ships in the core: NordwarUA ships one resolution, so the 1K/2K/4K choice is gone.

**The repository carries none of his files.** `tools/build-package.py` opens the Nexus downloads at build time and
derives the material list from the meshes it is shipping. The texture paths inside the shipped meshes point at this
mod's own folder, `textures\pbr\NordicSkyforge\`, so installing it next to Legacy of Ysgramor leaves that mod's Wolf
Armor exactly as it was.

## The new weapon types (1.1.0 on)

The Skyforge Steel Mace (and the weapon types that follow it) is assembled at build time by
`tools/build-missing-weapons.py` from pieces of NordwarUA's steel war axe in the same Legacy of Ysgramor download, each
piece keeping its own texture; the node tree, blood shapes and collision it is built on come from the game's own ebony
mace in the player's Skyrim - Meshes BSA. The bow is built by the Nordic Ebony replacer's own pipeline from
NordwarUA's ebony Wolf weapons in the same download (the same sword mesh as the steel one), then given this mod's steel
materials. The repository carries none of these files.

## The CBBE 3BA BodySlide files - Legacy of Ysgramor - 3BA Bodyslide

[Nexus 111209](https://www.nexusmods.com/skyrimspecialedition/mods/111209), **Legacy of Ysgramor - 3BA Bodyslide** by
**Xonek**: the CBBE 3BA slider sets and shape data, installed as an optional choice, renamed and repathed to this mod's
folders by `tools/loy-refits.py`, their materials made TruePBR like the rest. Credited to Xonek and to NordwarUA.

## Not included - the HIMBO conversion

[Nexus 110002](https://www.nexusmods.com/skyrimspecialedition/mods/110002), **Legacy of Ysgramor - HIMBO Conversion**
by **Trexasle**, asks for his permission before its assets are used, so it is not packaged here (it was an option
before 1.1.0 was posted). The mod page points HIMBO players at his page.

## What IS ours

`tools/` (including the recolour and the TruePBR conversion), `fomod/ModuleConfig.xml`, the plugin generator and the
documentation. The recoloured textures and derived meshes themselves are NordwarUA's art modified and stay under his
permissions, not under our licence. GPL-3.0-or-later, Copyright (C) 2026 ApocryphaRealm.

## Permissions, read per shipped source

Every source the build scripts open, with its Nexus permissions box as read. A source whose box says "You must get
permission" is not shipped until a written permission is recorded here.

| Source (what the build opens) | Nexus | Author | Permissions read | Shipped? |
|---|---|---|---|---|
| Legacy of Ysgramor - Main Archive SE, Patch Fur Lighting Bug | 109963 | NordwarUA | Permissions read 2026-11-12, again 2026-11-15: modification allowed with credit; asset use allowed with credit; conversion allowed with credit; no upload to other sites; no use in sold mods; donation points allowed | Yes - meshes, textures (recoloured), derived weapons |
| Legacy of Ysgramor - 3BA Bodyslide | 111209 | Xonek | Permissions read 2026-11-15: author's instructions "The same as in original mod" (no separate permission lines); file credits NordwarUA; not opted into donation points. The owner (2026-11-15 21:54): "consider it as permission granted" - so under Legacy of Ysgramor's terms, with credit | Yes - optional CBBE 3BA BodySlide files |
| Legacy of Ysgramor - HIMBO Conversion | 110002 | Trexasle | Permissions read 2026-11-15: asset use needs his permission; some assets belong to other authors | **No** - not read by the build, not shipped; the page points at it |
| Legacy of Ysgramor - My patches and fixes (Wolf Black, Full Collar Black) | 111121 | Xtudo | Permissions read 2026-11-15: modification and asset use need his permission; no donation points on mods using his assets | **No** - not read by the build, not shipped (up to the unposted 1.1.0 builds of 2026-11-15 his black diffuses were used; replaced by our own recolour of NordwarUA's originals) |

The NordwarUA box in full, read 2026-11-12 (the owner: this mod "has permission for use since this is the mod its
from" - the same permission applies to both of our mods built from that source, Nordic Ebony Armor and Weapons
Replacer and Nordic Skyforged Armor and Weapons):

- Other user's assets: all the assets belong to the author or are free-to-use modder's resources.
- **Modification permission: allowed** - "You are allowed to modify my files and release bug fixes or improve on the
  features so long as you credit me as the original creator".
- **Asset use permission: allowed** - "You are allowed to use the assets in this file without permission as long as you
  credit me".
- Conversion permission: allowed, with credit.
- Upload permission: NOT allowed to upload the file to other sites - so this mod is posted on Nexus only.
- Assets in mods that are being sold: NOT allowed - this mod is never sold or paywalled.
- Assets in mods that earn Donation Points: allowed.

Conditions we keep: credit NordwarUA as the original creator (and Xonek for the 3BA files) on the mod page and in this
file, link back to Legacy of Ysgramor, post on Nexus only, and never sell it.
