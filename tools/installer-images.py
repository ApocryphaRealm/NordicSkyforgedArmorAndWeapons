#!/usr/bin/env python3
r"""Render the installer pictures from a BUILT package (gate fomod-model-options-have-a-picture: every option that
installs a model shows that model). Each picture is a render of exactly the meshes its option installs, textured from the
package's own 2K textures; the header lines up the whole set. (The Nordic Ebony replacer's script, pointed at this
mod's own meshes and texture folder - never the Ebony pictures.)

Usage:  python tools/installer-images.py "<package folder>"      -> fomod/images/*.png in the repository
Needs Blender with PyNifly (BLENDER, or on PATH, or under Program Files) and Pillow.
"""
import json, os, subprocess, sys, glob, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
IMG = os.path.join(REPO, "fomod", "images")

# picture -> (meshes relative to the package, a camera yaw)
SHOTS = {
    "outfit": (["00 Core/meshes/NordicSkyforge/armor/%s.nif" % p for p in ("ArmorM_1", "BootsM_1", "GauntletsM_1", "HelmetM_1")], 20),
    "himbo": (["30 HIMBO meshes/meshes/NordicSkyforge/armor/%s_1.nif" % p for p in ("ArmorM", "BootsM", "GauntletsM")], 20),
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

BLENDER_SCRIPT = r'''
import bpy, os, sys, json, math, addon_utils
from mathutils import Vector, Matrix
addon_utils.enable("io_scene_nifly", default_set=True)
from io_scene_nifly.pyn.pynifly import NifFile
job = json.load(open(sys.argv[sys.argv.index("--") + 1]))
sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 48; sc.cycles.use_denoising = True
sc.view_settings.view_transform = "Standard"; sc.render.film_transparent = True
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.35, 0.36, 0.38, 1)
# GAME-LIKE LIGHTING (the owner, 2026-11-15 07:26, on steel rendered black): Skyrim keeps a weapon's diffuse and ADDS an
# environment reflection where the _m mask allows. A metallic material under a flat grey world has nothing to mirror and
# draws steel near-black. So: no metallic, specular strength from the _m mask, and reflections see a sky-to-ground
# gradient (the camera still sees the plain backdrop). The same shading as the review sheets' render_compare.py.
nt_ = w.node_tree; tc = nt_.nodes.new("ShaderNodeTexCoord"); sep = nt_.nodes.new("ShaderNodeSeparateXYZ")
ramp = nt_.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[0].color = (0.10, 0.10, 0.11, 1)
ramp.color_ramp.elements[1].position = 0.75; ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.02, 1)
mapr = nt_.nodes.new("ShaderNodeMapRange"); mapr.inputs["From Min"].default_value = -1.0; mapr.inputs["From Max"].default_value = 1.0
nt_.links.new(tc.outputs["Generated"], sep.inputs[0]); nt_.links.new(sep.outputs["Z"], mapr.inputs["Value"]); nt_.links.new(mapr.outputs["Result"], ramp.inputs["Fac"])
bg2 = nt_.nodes.new("ShaderNodeBackground"); nt_.links.new(ramp.outputs["Color"], bg2.inputs["Color"]); bg2.inputs["Strength"].default_value = 1.3
lp = nt_.nodes.new("ShaderNodeLightPath"); mx = nt_.nodes.new("ShaderNodeMixShader")
nt_.links.new(lp.outputs["Is Camera Ray"], mx.inputs["Fac"]); nt_.links.new(bg2.outputs[0], mx.inputs[1]); nt_.links.new(bg.outputs[0], mx.inputs[2])
nt_.links.new(mx.outputs[0], nt_.nodes["World Output"].inputs["Surface"])
mats = {}
def material(d):
    if d in mats: return mats[d]
    m = bpy.data.materials.new(d); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    p = os.path.join(job["tex"], d.replace("\\", os.sep))
    if os.path.isfile(p):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(p, check_existing=True); nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    pn = p[:-4] + "_n.dds"
    if os.path.isfile(pn):
        tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = bpy.data.images.load(pn, check_existing=True); tn.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Metallic"].default_value = 0.0
    pm = p[:-4] + "_m.dds"
    if os.path.isfile(pm):
        tm = nt.nodes.new("ShaderNodeTexImage"); tm.image = bpy.data.images.load(pm, check_existing=True); tm.image.colorspace_settings.name = "Non-Color"
        sm = nt.nodes.new("ShaderNodeMath"); sm.operation = "MULTIPLY_ADD"; sm.inputs[1].default_value = 0.9; sm.inputs[2].default_value = 0.3
        nt.links.new(tm.outputs["Color"], sm.inputs[0]); nt.links.new(sm.outputs[0], b.inputs["Specular IOR Level"]); b.inputs["Roughness"].default_value = 0.3
    else:
        b.inputs["Roughness"].default_value = 0.5
    mats[d] = m; return m
for name, (paths, yaw) in job["shots"].items():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    objs = []
    for p in paths:
        tex = {}
        for s in NifFile(p).shapes:
            try: tex[s.name] = s.shader.textures.get("Diffuse", "")
            except Exception: tex[s.name] = ""
        before = set(bpy.data.objects)
        bpy.ops.import_scene.pynifly(filepath=p, import_collisions=False)
        for o in [o for o in bpy.data.objects if o not in before]:
            if o.type != "MESH": continue
            nm = o.name if o.name in tex else o.name.split(".")[0]; d = tex.get(nm, "")
            if "blood" in (nm + d).lower() or nm == "Scb" or not d.lower().startswith("textures\\nordicskyforge"): o.hide_render = True; continue
            o.data.materials.clear(); o.data.materials.append(material(d)); objs.append(o)
    for L, rot, e in (("key", (math.radians(40), math.radians(-35), 0), 3.0), ("rim", (math.radians(-55), math.radians(145), 0), 2.0), ("fill", (math.radians(60), math.radians(160), 0), 1.0)):
        l = bpy.data.lights.new(L, "SUN"); l.energy = e; lo = bpy.data.objects.new(L, l); lo.rotation_euler = rot; sc.collection.objects.link(lo)
    dg = bpy.context.evaluated_depsgraph_get(); P = []
    for o in objs:
        e = o.evaluated_get(dg); me = e.to_mesh(); P += [e.matrix_world @ v.co for v in me.vertices]; e.to_mesh_clear()
    # armour stands up along z, weapons along y
    upv = Vector((0, 0, 1)) if job["armour"].get(name) else Vector((0, 1, 0))
    yw = math.radians(yaw)
    if upv.z: fwd = Vector((math.sin(yw), -math.cos(yw), 0.08)).normalized()
    else: fwd = Vector((math.sin(yw), 0, math.cos(yw)))
    right = upv.cross(fwd).normalized(); up = fwd.cross(right)
    xs = [p.dot(right) for p in P]; ys = [p.dot(up) for p in P]; zs = [p.dot(fwd) for p in P]
    W, H = job["size"]; w_, h_ = max(xs) - min(xs), max(ys) - min(ys)
    cam = bpy.data.cameras.new("c"); cam.type = "ORTHO"; cam.clip_start = 1; cam.clip_end = 5000
    cam.ortho_scale = 1.08 * (max(h_, w_ * H / W) if H >= W else max(w_, h_ * W / H))
    co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
    co.location = right * (max(xs) + min(xs)) / 2 + up * (max(ys) + min(ys)) / 2 + fwd * (max(zs) + 300)
    co.rotation_mode = "QUATERNION"; co.rotation_quaternion = Matrix((right, up, fwd)).transposed().to_quaternion()
    sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.filepath = os.path.join(job["out"], name + ".png")
    bpy.ops.render.render(write_still=True); print("SHOT", name, len(objs))
'''


def blender():
    b = os.environ.get("BLENDER") or shutil.which("blender")
    if not b:
        c = sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe")); b = c[-1] if c else None
    if not b: raise SystemExit("installer-images: Blender not found - set BLENDER")
    return b


def main(pkg):
    from PIL import Image, ImageDraw
    work = os.path.join(pkg, "_images_work"); os.makedirs(work, exist_ok=True)
    shots = {k: ([os.path.join(pkg, p) for p in ps], yaw) for k, (ps, yaw) in SHOTS.items()}
    for k, (ps, _) in shots.items():
        for p in ps:
            if not os.path.isfile(p): raise SystemExit("installer-images: the package has no %s" % p)
    job = {"shots": shots, "tex": os.path.join(pkg, "02 Textures - 2K"), "out": work, "size": [900, 1200],
           "armour": {k: not k.startswith("w_") for k in shots}}
    jp = os.path.join(work, "job.json"); json.dump(job, open(jp, "w"))
    sp = os.path.join(work, "render.py"); open(sp, "w", encoding="utf-8").write(BLENDER_SCRIPT)
    r = subprocess.run([blender(), "--background", "--factory-startup", "--python-exit-code", "1", "--python", sp, "--", jp], capture_output=True, text=True)
    if r.returncode != 0: raise SystemExit("installer-images: Blender failed\n" + (r.stdout + r.stderr)[-3000:])
    os.makedirs(IMG, exist_ok=True)
    bg = (38, 39, 42)
    def card(name, size):
        im = Image.open(os.path.join(work, name + ".png")).convert("RGBA")
        if name == "w_arrows": im = im.rotate(180)     # the quiver model runs mouth-down along y: shown as it hangs, arrows up
        box = im.getbbox(); im = im.crop(box) if box else im
        im.thumbnail(size); c = Image.new("RGB", size, bg); c.paste(im, ((size[0] - im.width) // 2, (size[1] - im.height) // 2), im); return c
    for name in ("himbo", "cbbe3ba"):
        card(name, (800, 1000)).save(os.path.join(IMG, name + ".png"))
    # header: the armour and every weapon in a row (the bow and the quiver of arrows included)
    order = ["outfit", "w_sword", "w_greatsword", "w_waraxe", "w_battleaxe", "w_dagger", "w_mace", "w_warhammer", "w_bow", "w_arrows", "w_shield"]
    H = 520; head = Image.new("RGB", (1800, H + 60), bg); x = 10
    widths = {k: (260 if k == "outfit" else 230 if k == "w_shield" else 170 if k == "w_bow" else 150 if k == "w_arrows" else 140) for k in order}
    scale = (1780 - 10 * (len(order) - 1)) / sum(widths.values())
    for k in order:
        w = int(widths[k] * scale); head.paste(card(k, (w, H)), (x, 10)); x += w + 10
    d = ImageDraw.Draw(head); d.text((14, H + 22), "Nordic Skyforged Armor and Weapons - NordwarUA's steel Wolf set from Legacy of Ysgramor in Xtudo's Wolf Black", fill=(225, 205, 150))
    head.save(os.path.join(IMG, "header.png"))
    shutil.rmtree(work, ignore_errors=True)
    print("installer images written to", IMG)


if __name__ == "__main__":
    main(sys.argv[1])
