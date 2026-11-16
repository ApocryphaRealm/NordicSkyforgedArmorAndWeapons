# Truly Nordic Skyforged Armor and Weapons

NordwarUA's steel Wolf weapons from **Legacy of Ysgramor** on the five Skyforge Steel weapons, plus a Skyforge Steel
armour set made from his steel Wolf armour, all black - his own textures recoloured - in **TruePBR**. Legacy of
Ysgramor has no **mace, warhammer, bow, arrows or quiver** for this set, so those are assembled from pieces of his steel
weapons. The armour and the new weapons are forged at the Skyforge. (Named Nordic Skyforged Armor and Weapons while in
development.)

## Two downloads

* **Main file - full 3D.** The chain mail is modelled ring by ring, each ring linked four-in-one to its neighbours. The
  rivets, studs, buckles, straps and lamellar scales are raised geometry on the helmet, cuirass, gauntlets, boots,
  shield and weapons. Measured in one launch, ten NPCs in the 3D set cost about 0.8-1.1 ms of GPU time more than the
  same ten in the flat set, and in that CPU-bound scene the frame time stayed within noise. First-person mail has no
  measurable cost.
* **Optional file - flat.** The same set with the mail as a TruePBR material, for big battles or older PCs.

Both are FOMOD installers. One light plugin (ESL-flagged, `Truly Nordic Skyforged Armor and Weapons.esp`) installs
with the core. There is no no-ESP option, because the armour, the new weapons and their recipes are new records. Body
choices: vanilla, or our own **CBBE 3BA** (female) and **HIMBO** (male) fits, made by running BodySlide ourselves.
Each fit has prebuilt meshes plus the BodySlide project for your own preset.

The Skyforge Steel Shield is a real shield record: it has the record's Shield flag (0x40), so shield-on-back mods
carry it, plus object bounds from its model and a female worn model.

## Requirements

* Community Shaders with TruePBR support. Its Dynamic Cubemaps feature is recommended.

## Credits

* **NordwarUA** - [Legacy of Ysgramor](https://www.nexusmods.com/skyrimspecialedition/mods/109963): every mesh,
  every texture the materials are made from, and every piece of the new weapons. Used and modified under its
  permissions (modification and asset use with credit; Nexus only; never sold).
* **Xonek** - [Legacy of Ysgramor - 3BA Bodyslide](https://www.nexusmods.com/skyrimspecialedition/mods/111209): the
  CBBE 3BA fit starts from his sets.

Details and permissions: [NOTICE.md](NOTICE.md). Changes: [CHANGELOG.md](CHANGELOG.md).

## Building

Run `python tools/build-esp.py` for the plugin, then `python tools/build-package.py [--rebuild-3d]` for both installers.
The second one builds `Flat\` from the Legacy of Ysgramor downloads (`NSAW_DOWNLOADS`) and then `3D\` from it
(`tools/package3d.py`, with the full-3D build in `tools/full3d/`). You need Python 3 (numpy, scipy, lz4, Pillow),
7-Zip, texconv, Blender with PyNifly, BodySlide and Git Bash.
