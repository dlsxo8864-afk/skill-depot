"""scene.blend 를 카툰 질감(단계 명암 + 잉크선)으로 바꿔 scene_toon.blend 로 저장한다. 작업 폴더에서 실행.

사용: blender -b scene.blend --python-exit-code 1 -P make_toon.py
렌더: blender -b scene_toon.blend --python-exit-code 1 -P rnd_ssul.py -- 1-720 1080 1920 16 frames_toon/f BLENDER_EEVEE
- 모든 재질을 '단계 명암(3단) × 원래 색' 발광으로 바꾸고 Freestyle 잉크선을 켠다.
- SKIP 에 든 이름(화면·도장 자국·서류)은 그림이 그대로 보여야 하므로 바꾸지 않고 발광만 더한다.
  build_ssul.py 에서 재질 이름을 바꾸면 SKIP 과 아래 (screen, paper, mark) 표도 같이 고친다.
"""
import os

import bpy

SKIP = ("screen", "mark", "paper", "gobo", "dust")
n_done = 0
for m in bpy.data.materials:
    if not m.use_nodes or m.node_tree is None or any(s in m.name.lower() for s in SKIP):
        continue
    nt = m.node_tree
    out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
    pr = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if out is None or pr is None:
        continue
    if "glass" in m.name.lower() or "lens" in m.name.lower():
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        nt.links.new(tr.outputs[0], out.inputs["Surface"])
        continue
    base_links = list(pr.inputs["Base Color"].links)
    base_color = tuple(pr.inputs["Base Color"].default_value)
    source = base_links[0].from_socket if base_links else None
    for name in ("Base Color", "Normal", "Roughness", "Metallic"):
        for link in list(pr.inputs[name].links):
            nt.links.remove(link)
    pr.inputs["Base Color"].default_value = (1, 1, 1, 1)
    pr.inputs["Metallic"].default_value = 0.0
    pr.inputs["Roughness"].default_value = 0.6
    s2 = nt.nodes.new("ShaderNodeShaderToRGB")
    nt.links.new(pr.outputs[0], s2.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    els[0].position = 0.0
    els[0].color = (0.30, 0.27, 0.42, 1)
    els[1].position = 0.38
    els[1].color = (1, 1, 1, 1)
    mid = els.new(0.12)
    mid.color = (0.62, 0.58, 0.68, 1)
    nt.links.new(s2.outputs["Color"], ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    nt.links.new(ramp.outputs["Color"], mix.inputs[6])
    if source is not None:
        sat = nt.nodes.new("ShaderNodeHueSaturation")
        sat.inputs["Saturation"].default_value = 1.35
        sat.inputs["Value"].default_value = 1.25
        nt.links.new(source, sat.inputs["Color"])
        nt.links.new(sat.outputs["Color"], mix.inputs[7])
    else:
        mix.inputs[7].default_value = base_color
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(mix.outputs[2], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    n_done += 1

for name, strength in (("screen", 0.8), ("paper", 0.55), ("mark", 0.55)):
    m = bpy.data.materials.get(name)
    pr = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    img = next(n for n in m.node_tree.nodes if n.type == "TEX_IMAGE")
    m.node_tree.links.new(img.outputs["Color"], pr.inputs["Emission Color"])
    pr.inputs["Emission Strength"].default_value = strength

scene = bpy.context.scene
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.use_freestyle = True
scene.render.line_thickness_mode = "ABSOLUTE"
scene.render.line_thickness = 2.4
vl = scene.view_layers[0]
vl.use_freestyle = True
fs = vl.freestyle_settings
if not fs.linesets:
    fs.linesets.new("ink")
ls = fs.linesets[0]
ls.select_silhouette = True
ls.select_border = True
ls.select_crease = True
if ls.linestyle is None:
    ls.linestyle = bpy.data.linestyles.new("ink")
ls.linestyle.color = (0.05, 0.04, 0.08)
ls.linestyle.thickness = 2.4
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.getcwd(), "scene_toon.blend"))
print("TOON", n_done)
