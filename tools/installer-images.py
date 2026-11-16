#!/usr/bin/env python3
r"""Render the installer pictures from a BUILT package (gate fomod-model-options-have-a-picture: every option that
installs a model shows that model). Each picture is a render of exactly the meshes its option installs, with the
package's own TruePBR textures (tools/render_lib.py: game-like lighting, the gradient world standing in for Community
Shaders' cube-map reflections); the header lines up the whole set. (The Nordic Ebony replacer's script, pointed at this
mod's own meshes and texture folder - never the Ebony pictures.)

Usage:  python tools/installer-images.py "<package folder>"   (the FLAT package: <version folder>\Flat)      -> fomod/images/*.png in the repository
Needs Blender with PyNifly (BLENDER, or on PATH, or under Program Files) and Pillow.
"""
import os, sys, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import render_lib  # noqa: E402
IMG = os.path.join(REPO, "fomod", "images")
PREFIXES = ("textures\\pbr\\nordicskyforge\\",)

# picture -> (meshes relative to the package, a camera yaw)
SHOTS = {
    "outfit": (["00 Core/meshes/NordicSkyforge/armor/%s.nif" % p for p in ("ArmorM_1", "BootsM_1", "GauntletsM_1", "HelmetM_1")], 20),
    # every body option shows the set on that body (2026-11-16: the HIMBO option had no picture and failed
    # fomod-model-options-have-a-picture): the vanilla sets from the core, CBBE 3BA and HIMBO from the meshes BodySlide
    # prebuilt for those options (the 3BA ShapeData NIFs do not open in PyNifly; the prebuilt game meshes do)
    "vanilla_f": (["00 Core/meshes/NordicSkyforge/armor/%s_1.nif" % p for p in ("ArmorF", "BootsF", "GauntletsF")], 20),
    "vanilla_m": (["00 Core/meshes/NordicSkyforge/armor/%s_1.nif" % p for p in ("ArmorM", "BootsM", "GauntletsM")], 20),
    "cbbe3ba": (["32 CBBE 3BA meshes/meshes/NordicSkyforge/armor/%s_1.nif" % p for p in ("ArmorF", "BootsF", "GauntletsF")], 20),
    "himbo": (["36 HIMBO meshes/meshes/NordicSkyforge/armor/%s_1.nif" % p for p in ("ArmorM", "BootsM", "GauntletsM")], 20),
    "w_sword": (["00 Core/meshes/NordicSkyforge/weapons/Sword.nif"], 0), "w_greatsword": (["00 Core/meshes/NordicSkyforge/weapons/Greatsword.nif"], 0),
    "w_waraxe": (["00 Core/meshes/NordicSkyforge/weapons/Axe.nif"], 0), "w_battleaxe": (["00 Core/meshes/NordicSkyforge/weapons/BattleAxe.nif"], 0),
    "w_dagger": (["00 Core/meshes/NordicSkyforge/weapons/Dagger.nif"], 0), "w_mace": (["00 Core/meshes/NordicSkyforge/weapons/Mace.nif"], 0),
    "w_shield": (["00 Core/meshes/NordicSkyforge/weapons/ShieldSteel.nif"], 0),
    "w_warhammer": (["00 Core/meshes/NordicSkyforge/weapons/Warhammer.nif"], 0), "w_bow": (["00 Core/meshes/NordicSkyforge/weapons/Bow.nif"], 0),
    # the arrow's model carries the quiver and its six arrows: the header shows them together
    "w_arrows": (["00 Core/meshes/NordicSkyforge/weapons/Arrow.nif"], 0),
}


def main(pkg, tex_pkg=None):
    from PIL import Image, ImageDraw
    import tempfile
    work = tempfile.mkdtemp(prefix="installer-images-")     # never inside the package (2026-11-16)
    shots = {k: ([os.path.join(pkg, p) for p in ps], yaw) for k, (ps, yaw) in SHOTS.items()}
    # textures: the package's own core, or (second argument) another built package's core with the same textures
    tex = [os.path.join(tex_pkg or pkg, "00 Core")]
    render_lib.render(shots, tex, work, PREFIXES)
    os.makedirs(IMG, exist_ok=True)
    bg = (38, 39, 42)
    for name in ("vanilla_f", "vanilla_m", "cbbe3ba", "himbo"):
        render_lib.card(os.path.join(work, name + ".png"), (800, 1000)).save(os.path.join(IMG, name + ".png"))
    # header: the armour and every weapon in a row (the bow and the quiver of arrows included)
    order = ["outfit", "w_sword", "w_greatsword", "w_waraxe", "w_battleaxe", "w_dagger", "w_mace", "w_warhammer", "w_bow", "w_arrows", "w_shield"]
    H = 520; head = Image.new("RGB", (1800, H + 60), bg); x = 10
    widths = {k: (260 if k == "outfit" else 230 if k == "w_shield" else 170 if k == "w_bow" else 150 if k == "w_arrows" else 140) for k in order}
    scale = (1780 - 10 * (len(order) - 1)) / sum(widths.values())
    for k in order:
        # the quiver model runs mouth-down along y: shown as it hangs, arrows up
        w = int(widths[k] * scale)
        head.paste(render_lib.card(os.path.join(work, k + ".png"), (w, H), rotate=180 if k == "w_arrows" else 0), (x, 10)); x += w + 10
    d = ImageDraw.Draw(head)
    d.text((14, H + 22), "Truly Nordic Skyforged Armor and Weapons - NordwarUA's steel Wolf set from Legacy of Ysgramor, all black, in TruePBR", fill=(225, 205, 150))
    head.save(os.path.join(IMG, "header.png"))
    shutil.rmtree(work, ignore_errors=True)
    print("installer images written to", IMG)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
