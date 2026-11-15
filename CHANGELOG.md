# Changelog - Nordic Skyforged Armor and Weapons

## 1.1.0 - 2026-11-15 - untested

### Added
- A Skyforge Steel Warhammer - the Nordic Ebony warhammer's design re-made from NordwarUA's own STEEL battle axe: the battle axe without its bit (haft, socket, top spike and back fang as they are), the axe's steel butt - its studded cuff and moulded end cap - turned forward as the hammer, cut flat at its widest point and carried on as a short round extension of the cap's own moulding with a 45-degree lip, ending in a flat circular striking face of square pyramid teeth (the Ebony face's 193 teeth, each facet with its own vertices so it lights as teeth, on blade steel whose normal map is flat), and the axe's collar ring where the hammer meets the socket. Same face size and reach as the Ebony warhammer. A new record: the vanilla Steel Warhammer with the game's two-handed Skyforge uplift (damage 23, value 160, weight 25), forged at the Skyforge with Steel Smithing from the Steel Warhammer's ingredients, tempered with a steel ingot; its own first-person model and static.
- A Skyforge Steel Mace - the first of the weapon types the game has no Skyforge version of (the same set the Nordic Ebony replacer gained: mace, warhammer, bow, arrows and quiver), built one at a time. It is the Nordic Ebony mace's recipe re-made from NordwarUA's own STEEL war axe in Legacy of Ysgramor: the axe's haft, socket, collar, braided grip and pommel; a second twist-langet tube as the head core; the axe's knotwork bit six times round it as flanges; the axe's collar ring as the top and lower bands; and the axe's spike as the crown point - each piece keeping its own texture on the steel axe's atlas (Xtudo's Wolf Black, which this mod already ships; no new texture). Sized to match the Ebony mace's head. A new record (the game has no Skyforge mace): the vanilla Steel Mace with the game's own Skyforge uplift over Steel (damage 13, value 90, weight 14), forged at the Skyforge with Steel Smithing from the Steel Mace's ingredients and tempered with a steel ingot like the Skyforge war axe. It has its own first-person model and static. Built by tools/build-missing-weapons.py from the Legacy of Ysgramor download and the game's own meshes at build time - the repository carries no art.
- Installer pictures, rendered from this mod's own built meshes: the header (the outfit and every weapon) and the HIMBO and CBBE 3BA options.

### Known
- Untested in game: the mace and warhammer in the hand, on the hip and back, in first person and at the Skyforge. Not yet in any levelled list or merchant - forged at the Skyforge only. The other new weapon types (arrows and quiver, bow) follow one at a time.

## 1.0.0

First release. The owner, 2026-09-16: *"i want to replace skyforged weapons and add skyforged armor,
leave wolf alone"*, and *"SKYFORGED IS BUILT FROM LEGACY OF YSGRAMOR WOLF ARMOR and skyforged weapons"*.

* NordwarUA's steel wolf weapons from Legacy of Ysgramor on the five vanilla Skyforge Steel weapons -
  sword, greatsword, war axe, battleaxe and dagger. The records are the game's own with only the
  model changed, so damage, value, keywords and sounds are untouched.
* A Skyforge Steel armour set - cuirass (fur-collared), boots, gauntlets, helmet and shield - built
  from the same mod's steel wolf armour, as NEW items. Stats are the game's Wolf Armor stats record
  for record (heavy, steel material), forged at the Skyforge with Steel Smithing and tempered with a
  steel ingot at an armour table. The Wolf Armor itself is not touched.
* Xtudo's black colourway - Wolf Black for the straps and cloth, Full Collar Black for the fur - at a
  choice of 1K, 2K or 4K in the installer.
* One light plugin, a `.esp` with the light flag (an ESPFE): 23 new records, Skyrim.esm as its only
  master, every reference checked to resolve there at build time.
* The shipped meshes have their texture paths rewritten to this mod's own folder (a same-length
  rewrite, so the files need no re-parsing), which is what lets it sit beside Legacy of Ysgramor
  without recolouring that mod's Wolf Armor.
* **Fixed before release: the helmet was invisible** (the owner, 2026-09-17: *"the skyforged made
  the head look wierd"*). The helmet's ARMO carries one armour-addon link per race family, four in
  all; the generator had packed the four FormIDs into a single 16-byte `MODL` subrecord, which the
  engine reads as one FormID and discards. One `MODL` per addon now, and the package gate refuses
  any ARMO whose `MODL` is not 4 bytes.
* **HIMBO and CBBE 3BA options in the installer.** Prebuilt HIMBO male meshes (zeroed sliders) and
  HIMBO BodySlide files from Trexasle's Legacy of Ysgramor - HIMBO Conversion (Nexus 110002), and
  CBBE 3BA BodySlide files from Xonek's Legacy of Ysgramor - 3BA Bodyslide (Nexus 111209), renamed
  and repathed to this mod's folders by `tools/loy-refits.py`, texture paths rewritten the same way
  as the base meshes. The 3BA set is BodySlide-only: build it once.
