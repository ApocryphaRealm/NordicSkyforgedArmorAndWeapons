# Changelog - Nordic Skyforged Armor and Weapons

## 1.1.0 - 2026-11-15 - untested

### Added
- A Skyforge Steel Bow - the Nordic Ebony replacer's bow (its approved design: the Wolf sword's blades bent into recurved limbs, a round braided collar at each end of the grip, round limb roots easing into the flat limb, one mounted claw per limb, the string's loops seated in notches at the tips, an arrow shelf, fitted to the vanilla bow rig and closed so no light shows through) on this set's own steel textures: the steel sword's for the limbs, grip, collars and claws, and the steel war axe's braided grip for the string. A new record (the game has no steel bow): the Imperial Bow, the game's steel-tier bow, with the two-handed Skyforge uplift - damage 12, value 140 - forged at the Skyforge with Steel Smithing from 3 steel ingots and 1 leather strips, tempered with a steel ingot; its first-person record uses the same model, as vanilla's bows do.
- Skyforge Steel Arrows, with their quiver and the arrow in flight - the Nordic Ebony arrow and quiver re-made from NordwarUA's own steel war axe and steel dagger: the axe's spike above its bit as the head, its back fang as three vanes, its braided grip as the shaft, a slotted steel nock (the slot across the arrow, square to the cock vane) with the axe's collar ring where it meets the shaft; the quiver is the steel dagger's scabbard scaled up, with the collar ring round its mouth and the back fang as a plate, decorated side out and the ring against the back, holding six of the same arrows (one shape each, so the game hides them one by one as they are used). Head, vanes and collar are closed so no light shows through. A new arrow (the game has no Skyforge Steel arrow): the vanilla Steel Arrow with the weapons' Skyforge pattern - damage 13, value 3 - and its own projectile, forged at the Skyforge with Steel Smithing, 24 from a steel ingot and a firewood.
- A Skyforge Steel Warhammer - the Nordic Ebony warhammer's design re-made from NordwarUA's own STEEL battle axe: the battle axe without its bit (haft, socket, top spike and back fang as they are), the axe's steel butt - its studded cuff and moulded end cap - turned forward as the hammer, cut flat at its widest point and carried on as a short round extension of the cap's own moulding with a 45-degree lip, ending in a flat circular striking face of square pyramid teeth (the Ebony face's 193 teeth, each facet with its own vertices so it lights as teeth, on blade steel whose normal map is flat), and the axe's collar ring where the hammer meets the socket. Same face size and reach as the Ebony warhammer. A new record: the vanilla Steel Warhammer with the game's two-handed Skyforge uplift (damage 23, value 160, weight 25), forged at the Skyforge with Steel Smithing from the Steel Warhammer's ingredients, tempered with a steel ingot; its own first-person model and static.
- A Skyforge Steel Mace - the first of the weapon types the game has no Skyforge version of (the same set the Nordic Ebony replacer gained: mace, warhammer, bow, arrows and quiver), built one at a time. It is the Nordic Ebony mace's recipe re-made from NordwarUA's own STEEL war axe in Legacy of Ysgramor: the axe's haft, socket, collar, braided grip and pommel; a second twist-langet tube as the head core; the axe's knotwork bit six times round it as flanges; the axe's collar ring as the top and lower bands; and the axe's spike as the crown point - each piece keeping its own texture on the steel axe's atlas (Xtudo's Wolf Black, which this mod already ships; no new texture). Sized to match the Ebony mace's head. A new record (the game has no Skyforge mace): the vanilla Steel Mace with the game's own Skyforge uplift over Steel (damage 13, value 90, weight 14), forged at the Skyforge with Steel Smithing from the Steel Mace's ingredients and tempered with a steel ingot like the Skyforge war axe. It has its own first-person model and static. Built by tools/build-missing-weapons.py from the Legacy of Ysgramor download and the game's own meshes at build time - the repository carries no art.
- Installer pictures, rendered from this mod's own built meshes: the header (the outfit and every weapon - sword, greatsword, war axe, battleaxe, dagger, mace, warhammer, bow, the quiver of arrows and the shield - drawn, with the steel lit as the game lights it) and the HIMBO and CBBE 3BA options.

### Changed
- The Skyforge Steel Shield is the size of the Truly Nordic Carved "Shield - Clean" (the face 62.2 -> 52.8 units, x0.848), as the Nordic Ebony replacer's shield was made in 1.1.0. Scaled about the grip, so it sits where it did on the arm and on the back; the collision shrinks with it. Done at build time on Legacy of Ysgramor's own file (the steel shield is the same mesh as the ebony one, so the same tool is used unchanged).
- First-person models for the five Skyforge weapons the set already had (sword, greatsword, war axe, battleaxe, dagger): until now their first-person records were vanilla Steel's, so in first person they showed the vanilla steel weapons. Each now has its own first-person record on a first-person copy of its Legacy of Ysgramor model (the way the Nordic Ebony replacer made its first-person set, and the way Legacy of Ysgramor's own plugin does for these five weapons). The five new records are added after every 1.0.0 record, so no earlier FormID moves.

### Known
- Untested in game: the mace, warhammer, bow and arrows in the hand, on the hip and back, in first person, the bow draw, arrows in flight, the quiver on the back (its six arrows disappearing as they are used) and at the Skyforge. Not yet in any levelled list or merchant - forged at the Skyforge only.

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
