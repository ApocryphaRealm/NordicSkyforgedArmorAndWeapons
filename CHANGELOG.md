# Changelog - Nordic Skyforged Armor and Weapons

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
