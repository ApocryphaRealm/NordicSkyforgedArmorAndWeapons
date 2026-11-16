#!/usr/bin/env python3
r"""Render the installer pictures from a BUILT package (gate fomod-model-options-have-a-picture: every option that
installs a model shows that model). Each picture is a render of exactly the meshes its option installs, with the
package's own TruePBR textures (tools/render_lib.py: game-like lighting, the gradient world standing in for Community
Shaders' cube-map reflections); the header lines up the whole set. (The Nordic Ebony replacer's script, pointed at this
mod's own meshes and texture folder - never the Ebony pictures.)

Usage:  python tools/installer-images.py "<package folder>"      -> fomod/images/*.png in the repository
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
    # the 3BA ShapeData NIFs do not open in PyNifly; the female set (the same outfit, before BodySlide) stands in
    "cbbe3ba": (["00 Core/meshes/NordicSkyforge/armor/%s_1.nif" % p for p in ("ArmorF", "BootsF", "GauntletsF")], 20),
    "w_sword": (["00 Core/meshes/NordicSkyforge/weapons/Sword.nif"], 0), "w_greatsword": (["00 Core/meshes/NordicSkyforge/weapons/Greatsword.nif"], 0),
    "w_waraxe": (["00 Core/meshes/NordicSkyforge/weapons/Axe.nif"], 0), "w_battleaxe": (["00 Core/meshes/NordicSkyforge/weapons/BattleAxe.nif"], 0),
    "w_dagger": (["00 Core/meshes/NordicSkyforge/weapons/Dagger.nif"], 0), "w_mace": (["00 Core/meshes/NordicSkyforge/weapons/Mace.nif"], 0),
    "w_shield": (["00 Core/meshes/NordicSkyforge/weapons/ShieldSteel.nif"], 0),
    "w_warhammer": (["00 Core/meshes/NordicSkyforge/weapons/Warhammer.nif"], 0), "w_bow": (["00 Core/meshes/NordicSkyforge/weapons/Bow.nif"], 0),
    # the arrow's model carries the quiver and its six arrows: the header shows them together
    "w_arrows": (["00 Core/meshes/NordicSkyforge/weapons/Arrow.nif"], 0),
}


def main(pkg):
    from PIL import Image, ImageDraw
    work = os.path.join(pkg, "_images_work")
    shots = {k: ([os.path.join(pkg, p) for p in ps], yaw) for k, (ps, yaw) in SHOTS.items()}
    render_lib.render(shots, [os.path.join(pkg, "00 Core")], work, PREFIXES)
    os.makedirs(IMG, exist_ok=True)
    bg = (38, 39, 42)
    render_lib.card(os.path.join(work, "cbbe3ba.png"), (800, 1000)).save(os.path.join(IMG, "cbbe3ba.png"))
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
    d.text((14, H + 22), "Nordic Skyforged Armor and Weapons - NordwarUA's steel Wolf set from Legacy of Ysgramor, all black, in TruePBR", fill=(225, 205, 150))
    head.save(os.path.join(IMG, "header.png"))
    shutil.rmtree(work, ignore_errors=True)
    print("installer images written to", IMG)


if __name__ == "__main__":
    main(sys.argv[1])
