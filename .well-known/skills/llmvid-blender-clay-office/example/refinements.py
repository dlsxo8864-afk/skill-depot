"""Main-agent finishing of the reviewed Gemini diorama foundation.

All artwork is original mesh/curve construction. Animation is baked into object
transforms; the saved blend needs no handlers or external rig at playback time.
"""
import math
import bpy
from mathutils import Vector, Quaternion


def smooth(value):
    value = min(1.0, max(0.0, value))
    return value * value * (3.0 - 2.0 * value)


def curve(g, name, points, material, thickness=.009, parent=None, cyclic=False):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 12
    data.bevel_depth = thickness
    data.bevel_resolution = 3
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, xyz in zip(spline.bezier_points, points):
        point.co = xyz
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, data)
    bpy.data.collections["Characters"].objects.link(obj)
    obj.data.materials.append(material)
    obj.parent = parent
    return obj


def ellipsoid(g, name, radii, location, material, parent=None):
    obj = g.add_sphere(name, 1, location, material, bpy.data.collections["Characters"])
    obj.scale = radii
    obj.parent = parent
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def replace_sphere(g, name, radii):
    old = bpy.data.objects[name]
    parent, pos, mat = old.parent, old.location.copy(), old.data.materials[0]
    bpy.data.objects.remove(old, do_unlink=True)
    return ellipsoid(g, name, radii, pos, mat, parent)


def enhance_characters(g, figures):
    for fig, name in zip(figures, ("Protagonist", "Newcomer", "TeamLead")):
        replace_sphere(g, name + "_HeadMesh", (.235, .205, .24))
        fig["head"].location.z = .49
        fig["hips"].location.z = .54
        if name == "Protagonist":
            for suffix, size in (("HairTop", (.253, .228, .135)), ("Hair_L", (.077, .186, .163)),
                                 ("Hair_R", (.077, .186, .163)), ("HairBack", (.224, .084, .177))):
                hair = replace_sphere(g, name + "_" + suffix, size)
                if suffix != "HairTop":
                    hair.location.z = .245
            for i in range(4):
                hair = ellipsoid(g, name + f"_Fringe_{i}", (.10, .04, .045),
                                 (-.15 + i * .085, -.183, .347 + i * .009), g.MATS["HairDark"], fig["head"])
                hair.rotation_euler.y = -.22
        else:
            replace_sphere(g, name + "_HairDome", (.248, .222, .137))
            for i in range(3):
                ellipsoid(g, name + f"_Fringe_{i}", (.105, .055, .072),
                          (-.13 + i * .11, -.18, .32), g.MATS["HairDark"], fig["head"])
        for side, sign in (("L", -1), ("R", 1)):
            eye = bpy.data.objects[name + "_Eye_" + side]
            eye.location = (sign * .094, -.198, .18)
            eye.scale = (.73, .65, .92)
            for polygon in eye.data.polygons:
                polygon.use_smooth = True
            ellipsoid(g, name + "_EyeSpark_" + side, (.007, .004, .007),
                      (sign * .094 - .008, -.221, .19), g.MATS["PaperWhite"], fig["head"])
            ellipsoid(g, name + "_Ear_" + side, (.042, .045, .075),
                      (sign * .223, .01, .17), g.MATS["SkinWarm"], fig["head"])
            old_brow = bpy.data.objects[name + "_Brow_" + side]
            bpy.data.objects.remove(old_brow, do_unlink=True)
            brow = curve(g, name + "_Brow_" + side, [(-.037, 0, 0), (0, -.002, .009), (.035, 0, .002)],
                         g.MATS["HairDark"], .009, fig["head"])
            brow.location = (sign * .094, -.2, .256)
            fig["brow_" + side.lower()] = brow
            # Extend lower legs so seated shoes touch the floor, then use two-bone IK.
            hip, knee = fig["hip_" + side.lower()], fig["kn_" + side.lower()]
            thigh = bpy.data.objects[name + "_Thigh_" + side]
            thigh.location.z = -.14
            thigh.scale.z = .28 / .24
            knee.location.z = -.28
            calf = bpy.data.objects[name + "_Calf_" + side]
            calf.location.z = -.21
            calf.scale.z = .42 / .24
            foot = bpy.data.objects[name + "_Foot_" + side]
            foot.location = (0, -.035, -.42)
            fig["foot_" + side.lower()] = foot
            shoulder, elbow = fig["sh_" + side.lower()], fig["el_" + side.lower()]
            shoulder.location.z = .35
            upper = bpy.data.objects[name + "_UpperArm_" + side]
            upper.location.z = -.115
            upper.scale.z = .23 / .18
            elbow.location.z = -.23
            lower = bpy.data.objects[name + "_Forearm_" + side]
            lower.location.z = -.11
            lower.scale.z = .22 / .16
            hand = bpy.data.objects[name + "_Hand_" + side]
            hand.location.z = -.23
            hand.scale = (.88, .8, 1.1)
            fig["hand_" + side.lower()] = hand
            for bone in (hip, knee, shoulder, elbow, foot):
                bone.rotation_mode = "QUATERNION"
        nose = bpy.data.objects[name + "_Nose"]
        bpy.data.objects.remove(nose, do_unlink=True)
        ellipsoid(g, name + "_Nose", (.026, .035, .029), (0, -.204, .139), g.MATS["SkinWarm"], fig["head"])
        bpy.data.objects.remove(bpy.data.objects[name + "_Mouth"], do_unlink=True)
        curve(g, name + "_Mouth", [(-.036, -.198, .079), (0, -.204, .076), (.035, -.198, .08)],
              g.MATS["MouthRose"], .0065, fig["head"])
        chest = bpy.data.objects[name + "_Chest"]
        for vertex in chest.data.vertices:
            vertex.co.x *= 1.10 if vertex.co.z > 0 else .86
        # Collar leaves sit on the front of the blouse rather than floating above it.
        for side, sign in (("L", -1), ("R", 1)):
            collar = g.add_beveled_box(name + "_Collar_" + side, (.09, .022, .062),
                                      (sign * .045, -.133, .348), g.MATS["PaperWhite"], .009, 3,
                                      bpy.data.collections["Characters"])
            collar.parent = fig["hips"]
            collar.rotation_euler.y = sign * .25
        for i in range(2):
            button = bpy.data.objects.get(name + f"_Btn_{i}")
            if button:
                button.parent = fig["hips"]
                button.location = (0, -.132, .19 + i * .07)
        if name == "TeamLead":
            bpy.data.objects.remove(bpy.data.objects[name + "_Glasses"], do_unlink=True)
            for sign in (-1, 1):
                points = [(sign * .095 + .061 * math.cos(t), -.23, .18 + .046 * math.sin(t))
                          for t in [i * math.tau / 8 for i in range(8)]]
                curve(g, f"Glasses_{sign}", points, g.MATS["GlassesGold"], .006, fig["head"], True)
            curve(g, "GlassesBridge", [(-.035, -.231, .185), (0, -.235, .19), (.035, -.231, .185)],
                  g.MATS["GlassesGold"], .006, fig["head"])


def enhance_set(g):
    colors = {"SkinWarm": (.72, .43, .28, 1), "SkinLead": (.65, .38, .25, 1),
              "HairDark": (.028, .019, .017, 1), "BlouseTeal": (.045, .24, .27, 1),
              "ShirtCoral": (.63, .20, .12, 1), "DeskTop": (.43, .28, .16, 1),
              "FloorTile": (.54, .46, .37, 1), "FloorBoard": (.38, .31, .24, 1),
              "Wall": (.75, .70, .61, 1)}
    for name, rgba in colors.items():
        node = next(n for n in g.MATS[name].node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        node.inputs["Base Color"].default_value = rgba
    props = bpy.data.collections["Props"]
    for name, position in (("Desk_Protagonist", (-1, -.65, 0)), ("Desk_Newcomer", (1.5, -.60, 0)),
                           ("Desk_Lead", (.5, 1.8, 0))):
        root = bpy.data.objects[name + "_Root"]
        root.location = position
        if "Newcomer" in name:
            root.rotation_euler.z = math.pi
        for suffix in ("MonBase", "MonStand", "MonBody", "Screen"):
            obj = bpy.data.objects[name + "_" + suffix]
            obj.location.x += .31
            if suffix in {"MonBody", "Screen"}:
                obj.scale *= .70
                obj.location.z -= .15
            elif suffix == "MonStand":
                obj.scale.z *= .65
                obj.location.z -= .04
        for row in range(4):
            for column in range(10):
                key = g.add_beveled_box(name + f"_Key_{row}_{column}", (.031, .024, .009),
                                        (-.176 + column * .039, -.205 + row * .035, .815),
                                        g.MATS["PrinterIvory"], .002, 1, props)
                key.parent = root
        for line in range(4):
            bar = g.add_beveled_box(name + f"_ScreenLine_{line}", (.15 + .03 * (line % 2), .009, .012),
                                    (.265, .139, 1.06 - line * .032), g.MATS["BlouseTeal"], .003, 2, props)
            bar.parent = root
        mug = g.add_cylinder(name + "_Mug", .047, .09, (-.55, -.08, .83), material=g.MATS["ShirtCoral"], collection=props)
        mug.parent = root
    for name, position, angle in (("Protagonist", (-1, .08, 0), math.pi),
                                  ("Newcomer", (1.5, -1.22, 0), 0), ("Lead", (.5, 2.4, 0), math.pi)):
        chair = bpy.data.objects["Chair_" + name + "_Root"]
        chair.location = position
        chair.rotation_euler.z = angle
    bpy.data.objects["Printer_Root"].location = (-2.05, -.05, 0)
    old = bpy.data.objects.get("Bookshelf")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    for x in (1.25, 2.75):
        g.add_beveled_box("ShelfSide", (.07, .45, 2.42), (x, 3.6, 1.2), g.MATS["WalnutWood"], .012, 2, props)
    g.add_beveled_box("ShelfBack", (1.5, .04, 2.4), (2, 3.82, 1.2), g.MATS["DeskTop"], .006, 2, props)
    for z in (.25, .96, 1.67, 2.4):
        g.add_beveled_box("ShelfBoard", (1.5, .45, .055), (2, 3.6, z), g.MATS["WalnutWood"], .012, 2, props)
    # A low, cutaway window and shaped foliage carry depth without external textures.
    g.create_matte_material("WindowBlue", (.53, .73, .79, 1), .8)
    g.add_beveled_box("WindowGlass", (.018, 2.12, 1.65), (-2.84, .8, 1.8), g.MATS["WindowBlue"], .001, 1, props)
    # 세로 화면은 위아래 화각이 넓다. 낮은 카메라에서 벽 위로 빈 배경이 보이지 않게 벽을 위로 잇는다
    g.add_beveled_box("WallBackUpper", (6.0, .15, 4.0), (0, 3.9, 5.4), g.MATS["Wall"], 0, 1, props)
    g.add_beveled_box("WallLeftUpper", (.15, 7.0, 4.0), (-3.0, .5, 5.4), g.MATS["Wall"], 0, 1, props)
    for i in range(8):
        angle = i * math.tau / 8
        leaf = ellipsoid(g, "PlantShapedLeaf", (.07, .29, .035),
                         (-2.4 + .17 * math.cos(angle), 2.4 + .17 * math.sin(angle), .66 + .12 * (i % 3)),
                         g.MATS["PlantLeaf"])
        leaf.rotation_euler = (.5, .25 * math.cos(angle), angle)
    for name, xyz, target, power in (("Key_Daylight", (-2, -2.5, 4.7), (-.3, .2, .8), 500),
                                     ("Fill_Warm", (3.2, -1.6, 3.6), (0, .3, 1), 280),
                                     ("Rim_Accent", (-.6, 3.2, 4), (0, .2, 1), 380)):
        light = bpy.data.objects[name]
        light.location = xyz
        light.rotation_euler = (Vector(target) - light.location).to_track_quat("-Z", "Y").to_euler()
        light.data.energy = power
        light.data.size = 4


def camera_pose(camera, position, target):
    camera.location = position
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


# [풀이] 구간 id → 카메라 (위치, 바라볼 점, 렌즈 mm). 표에 없는 id 는 "wide" 를 쓴다
CAMERA_SETUPS = {
    "hook": ((-2.4, -3.1, 2.15), (-1, -.08, .97), 85),     # 주인공 책상
    "ask": ((.1, -4.6, 5.8), (.1, 1.0, .3), 55),           # 세 사람이 다 보이는 내려다본 전경
    "wait": ((-1.0, -3.4, 1.55), (-.92, 1.0, 1.42), 62),   # 주인공 정면 + 뒤 벽시계
    "decide": ((2.1, -.5, 2.1), (.5, 2.4, 1.15), 60),      # 팀장 자리
    "punch": ((1.2, -5.0, 3.5), (.15, -.07, .95), 62),     # 세 사람 + 주인공 책상 위 냄비
    "wide": ((.1, -4.6, 5.8), (.1, 1.0, .3), 55),
}


def setup_cameras(g, col):
    cameras = {}
    scene = bpy.context.scene
    scene.timeline_markers.clear()
    for shot in g.SHOT_TIMELINES:
        sid = shot["id"]
        position, target, lens = CAMERA_SETUPS.get(sid, CAMERA_SETUPS["wide"])
        data = bpy.data.cameras.new("Camera_" + sid)
        data.lens = lens
        data.sensor_fit = "HORIZONTAL"
        data.clip_start, data.clip_end = .05, 100
        camera = bpy.data.objects.new("Camera_" + sid, data)
        col.objects.link(camera)
        camera_pose(camera, position, target)
        marker = scene.timeline_markers.new(shot["name"], frame=round(shot["start"] * g.FPS) + 1)
        marker.camera = camera
        cameras[sid] = camera
        camera["initial_position"] = position
        camera["initial_target"] = target
    return cameras


def build_story_props(g):
    """대본 풀이에 쓰는 소품: 뒤 벽시계(바늘이 돈다)와 김 나는 찌개 냄비(결말에 튀어나온다)."""
    props = bpy.data.collections["Props"]
    g.create_matte_material("ClockFace", (.93, .90, .82, 1), .6)
    g.create_matte_material("StewRed", (.62, .10, .05, 1), .45)
    g.create_matte_material("PotDark", (.035, .035, .045, 1), .5)
    g.create_matte_material("Steam", (.92, .92, .92, 1), .9)
    half = math.pi / 2
    cx, cy, cz = -.6, 3.78, 2.15
    g.add_cylinder("Clock_Rim", .47, .05, (cx, cy, cz), rotation=(half, 0, 0), material=g.MATS["WalnutWood"], collection=props)
    g.add_cylinder("Clock_Face", .42, .06, (cx, cy - .01, cz), rotation=(half, 0, 0), material=g.MATS["ClockFace"], collection=props)
    for i in range(12):
        a = i * math.tau / 12
        g.add_beveled_box("Clock_Tick", (.03, .012, .07 if i % 3 == 0 else .035),
                          (cx + math.sin(a) * .35, cy - .045, cz + math.cos(a) * .35), g.MATS["PrinterDark"], .002, 1, props).rotation_euler.y = a
    hands = {}
    for name, length, width in (("minute", .32, .028), ("hour", .21, .042)):
        pivot = g.create_empty("Clock_" + name, (cx, cy - .06, cz), collection=props)
        hand = g.add_beveled_box("Clock_" + name + "_Hand", (width, .014, length), (0, 0, length / 2 - .03), g.MATS["PrinterDark"], .003, 1, props)
        hand.parent = pivot
        hands[name] = pivot
    pot = g.create_empty("Pot_Root", (-.72, -.72, .79), collection=props)
    for obj in (g.add_cylinder("Pot_Body", .21, .16, (0, 0, .08), material=g.MATS["PotDark"], collection=props),
                g.add_cylinder("Pot_Stew", .185, .02, (0, 0, .16), material=g.MATS["StewRed"], collection=props),
                g.add_beveled_box("Pot_HandleL", (.09, .05, .03), (-.25, 0, .12), g.MATS["PotDark"], .008, 2, props),
                g.add_beveled_box("Pot_HandleR", (.09, .05, .03), (.25, 0, .12), g.MATS["PotDark"], .008, 2, props)):
        obj.parent = pot
    steam = []
    for i, (x, z, radius) in enumerate(((-.07, .30, .045), (.05, .40, .06), (-.01, .52, .045))):
        puff = g.add_sphere("Pot_Steam_%d" % i, radius, (x, 0, z), material=g.MATS["Steam"], collection=props)
        puff.parent = pot
        puff["base_z"] = z
        steam.append(puff)
    return {"clock": hands, "pot": pot, "steam": steam}


def _minutes(text):
    hour, minute = text.split(":")
    return int(hour) % 12 * 60 + int(minute)


def solve_two_bone(upper, lower, target, l1, l2, bend):
    bpy.context.view_layer.update()
    origin = upper.matrix_world.translation.copy()
    vector = Vector(target) - origin
    length = max(.001, min(vector.length, l1 + l2 - .001))
    direction = vector.normalized()
    perpendicular = Vector(bend) - direction * Vector(bend).dot(direction)
    if perpendicular.length < .01:
        perpendicular = direction.cross(Vector((0, 0, 1)))
    perpendicular.normalize()
    along = (l1 * l1 - l2 * l2 + length * length) / (2 * length)
    height = math.sqrt(max(0, l1 * l1 - along * along))
    elbow = origin + direction * along + perpendicular * height
    world_q = (elbow - origin).to_track_quat("-Z", "Y")
    upper.rotation_quaternion = upper.parent.matrix_world.to_quaternion().inverted() @ world_q
    bpy.context.view_layer.update()
    lower.rotation_quaternion = upper.matrix_world.to_quaternion().inverted() @ (Vector(target) - elbow).to_track_quat("-Z", "Y")


def key(obj, frame, paths):
    for path in paths:
        obj.keyframe_insert(path, frame=frame)


def actor_pose(fig, position, yaw, hips, hand_targets, walking=None, progress=0):
    root = fig["root"]
    root.location = position
    root.rotation_euler = (0, 0, yaw)
    fig["hips"].location.z = hips
    bpy.context.view_layer.update()
    rot = root.matrix_world.to_quaternion()
    for side, sign in (("l", -1), ("r", 1)):
        if walking:
            start, finish = walking[:2]
            cycles = walking[2] if len(walking) > 2 else 6
            phase = progress * cycles + (0 if side == "l" else .5)
            index, local = math.floor(phase), phase % 1
            swing = smooth((local - .57) / .43)
            foot_progress = (index - (0 if side == "l" else .5) + .22 + swing) / cycles
            foot = Vector(start).lerp(Vector(finish), max(0, min(1, foot_progress)))
            foot += rot @ Vector((sign * .108, 0, 0))
            foot.z = .06 + math.sin(swing * math.pi) * .11
        else:
            foot = Vector(position) + rot @ Vector((sign * .11, -.30 if hips < .65 else -.025, .06))
        solve_two_bone(fig["hip_" + side], fig["kn_" + side], foot, .28, .42, rot @ Vector((0, -1, .1)))
        bpy.context.view_layer.update()
        fig["foot_" + side].rotation_quaternion = fig["kn_" + side].matrix_world.to_quaternion().inverted() @ rot
        target = hand_targets[0 if side == "l" else 1]
        solve_two_bone(fig["sh_" + side], fig["el_" + side], target, .23, .23,
                       rot @ Vector((sign * .8, .2, -.35)))


def local_hands(position, yaw, height, forward=-.32):
    rot = Quaternion(Vector((0, 0, 1)), yaw)
    return [Vector(position) + rot @ Vector((sign * .17, forward, height)) for sign in (-1, 1)]


def bake_story(g, figures, paper, flashpaper, cameras):
    """[풀이] 대본의 구간마다 인물의 자세를 프레임별로 구워 넣는다.

    예제 풀이(구간 id 기준): hook 주인공이 손을 들어 묻는다 / ask 동료와 팀장이 차례로 으쓱한다 /
    wait 주인공이 책상에 처지고 벽시계가 돈다 / decide 팀장이 일어나 손을 든다 / punch 둘이 끄덕이고 냄비가 나온다.
    대화 시각은 대본(g.SCRIPT)에서 읽는다. 구간 id 가 다른 대본이면 아래 if 블록을 고친다.
    """
    woman, newcomer, lead = figures
    scene = bpy.context.scene
    fps = g.FPS
    props = build_story_props(g)
    beats = {b["id"]: b for b in g.SCRIPT["beats"]}
    cast = [c["id"] for c in g.SCRIPT["cast"]]
    me_id, lead_id = cast[0], cast[-1]
    stamp = next((b["stamp"]["t"] for b in g.SCRIPT["beats"] if "stamp" in b), None)
    clock = beats.get("wait", {}).get("clock")
    m0 = _minutes(clock["from"]) if clock else 0
    m1 = _minutes(clock["to"]) if clock else 0
    if m1 < m0:
        m1 += 720
    wait_start, wait_end = (beats["wait"]["start"], beats["wait"]["end"]) if "wait" in beats else (0, 0)

    def pulse(time, at, length=.8):
        """at 초에 시작해 length 초 동안 0 → 1 → 0."""
        return math.sin(max(0, min(1, (time - at) / length)) * math.pi) if at is not None else 0

    def said(bid, who_is_lead):
        """구간 bid 에서 팀장(또는 팀장 아닌 사람)이 말하는 첫 시각."""
        for c in beats.get(bid, {}).get("chat", []):
            if (c["who"] == lead_id) == who_is_lead and c["who"] != me_id:
                return c["t"]
        return None

    def raised(position, yaw, spread, forward, height):
        rot = Quaternion(Vector((0, 0, 1)), yaw)
        return [Vector(position) + rot @ Vector((sign * spread, forward, height)) for sign in (-1, 1)]

    for obj in bpy.data.objects:
        obj.animation_data_clear()
    paper.location, paper.rotation_euler = (-2.05, -.64, .708), (0, 0, 0)
    flashpaper.location = (0, 0, -8)
    me_ask = next((c["t"] for c in beats.get("hook", {}).get("chat", []) if c["who"] == me_id), None)
    decide_at = said("decide", True)
    # 컷이 바뀌는 프레임마다 모든 자세를 찍는다(컷을 넘어 미끄러지지 않게)
    for frame in sorted(set(range(1, g.TOTAL_FRAMES + 1, 2)) | {g.TOTAL_FRAMES} |
                        {round(s["start"] * fps) + 1 for s in g.SHOT_TIMELINES} |
                        {round(s["end"] * fps) for s in g.SHOT_TIMELINES}):
        time = (frame - 1) / fps
        shot = next((s for s in g.SHOT_TIMELINES if s["start"] <= time < s["end"]), g.SHOT_TIMELINES[-1])
        sid = shot["id"]
        p = (time - shot["start"]) / (shot["end"] - shot["start"])
        woman_pos, woman_yaw, woman_hips = (-1, .0, 0), 0, .54
        new_pos, new_yaw, new_hips = (1.5, -1.22, 0), math.pi, .54
        lead_pos, lead_yaw, lead_hips = (.5, 2.43, 0), 0, .54
        woman_hands = local_hands(woman_pos, woman_yaw, .80)
        new_hands = local_hands(new_pos, new_yaw, .80)
        lead_hands = local_hands(lead_pos, lead_yaw, .80)
        woman_head, new_head, lead_head = [0, 0, 0], [0, 0, 0], [.06, 0, 0]
        woman_brow = 0
        if sid == "hook":  # 주인공이 고개를 돌려 한 손을 들고 묻는다
            k = smooth((time - (me_ask if me_ask is not None else shot["start"]) + .5) / .5)
            woman_head[2] = -.45 * k
            woman_hands[1] = woman_hands[1].lerp(raised(woman_pos, woman_yaw, .30, -.12, 1.22)[1], k)
            woman_brow = .027 * k
        if sid == "ask":  # 동료가 돌아보며 으쓱, 이어서 팀장이 으쓱
            a, b = said("ask", False), said("ask", True)
            turn = smooth((time - shot["start"]) / .6)
            new_yaw = math.pi + 1.05 * turn
            woman_head[2] = -.45
            if a is not None:
                k = pulse(time, a)
                new_hands = [h.lerp(t, k) for h, t in zip(local_hands(new_pos, new_yaw, .80), raised(new_pos, new_yaw, .40, -.10, 1.0))]
                new_head[2] = .30 * math.sin(max(0, time - a) * 9) * k
            else:
                new_hands = local_hands(new_pos, new_yaw, .80)
            if b is not None:
                k = pulse(time, b)
                lead_hands = [h.lerp(t, k) for h, t in zip(lead_hands, raised(lead_pos, lead_yaw, .40, -.10, 1.0))]
                lead_head[2] = .30 * math.sin(max(0, time - b) * 9) * k
        if sid == "wait":  # 주인공이 점점 처진다
            k = smooth(p / .8)
            woman_head[0] = .42 * k
            woman_hands = [h.lerp(t, k) for h, t in zip(woman_hands, raised(woman_pos, woman_yaw, .22, -.46, .80))]
            woman_brow = -.016 * k
        if sid in {"decide", "punch"}:  # 팀장이 일어나 한 손을 든다. 결말에서는 든 채로 있다
            k = 1 if sid == "punch" else smooth((time - (decide_at if decide_at is not None else shot["start"])) / .5)
            lead_hips = .54 + .23 * k
            lead_pos = (.5, 2.43 + .12 * k, 0)
            lead_hands = local_hands(lead_pos, lead_yaw, .80 + .16 * k, -.16)
            lead_hands[1] = lead_hands[1].lerp(raised(lead_pos, lead_yaw, .40, -.26, 1.58)[1], k)
            woman_head[2] = .0 if sid == "punch" else .35 * k
            woman_brow = .027 * (k if sid == "decide" else 0)
        if sid == "punch":  # 둘이 차례로 끄덕인다
            for c in beats.get("punch", {}).get("chat", []):
                nod = .34 * pulse(time, c["t"], .7)
                if c["who"] == me_id:
                    woman_head[0] = max(woman_head[0], nod)
                else:
                    new_head[0] = max(new_head[0], nod)
            new_yaw = math.pi + 1.05
            new_hands = local_hands(new_pos, new_yaw, .80)
        actor_pose(woman, woman_pos, woman_yaw, woman_hips, woman_hands)
        actor_pose(newcomer, new_pos, new_yaw, new_hips, new_hands)
        actor_pose(lead, lead_pos, lead_yaw, lead_hips, lead_hands)
        woman["head"].rotation_euler = woman_head
        newcomer["head"].rotation_euler = new_head
        lead["head"].rotation_euler = lead_head
        for fig in figures:
            fig["brow_l"].location.z = .256
            fig["brow_r"].location.z = .256
        woman["brow_r"].location.z += woman_brow
        if woman_brow < 0:
            woman["brow_l"].location.z += woman_brow
        for fig in figures:
            key(fig["root"], frame, ("location", "rotation_euler"))
            key(fig["hips"], frame, ("location",))
            key(fig["head"], frame, ("rotation_euler",))
            for side in ("l", "r"):
                key(fig["brow_" + side], frame, ("location",))
                for prefix in ("hip_", "kn_", "sh_", "el_", "foot_"):
                    key(fig[prefix + side], frame, ("rotation_quaternion",))
        # 벽시계: wait 구간 동안 대본의 clock.from → clock.to
        now = m0 + (m1 - m0) * max(0, min(1, (time - wait_start) / max(.01, wait_end - wait_start - .3)))
        props["clock"]["minute"].rotation_euler = (0, now / 60 * math.tau, 0)
        props["clock"]["hour"].rotation_euler = (0, now / 720 * math.tau, 0)
        for hand in props["clock"].values():
            key(hand, frame, ("rotation_euler",))
        # 냄비: 도장 시각(없으면 마지막 구간 시작)에 통통 튀며 나온다
        pop_at = stamp if stamp is not None else g.SHOT_TIMELINES[-1]["start"]
        k = max(0, min(1, (time - pop_at) / .25))
        size = 0 if time < pop_at else .01 + .99 * smooth(k) + .18 * math.sin(k * math.pi)
        props["pot"].scale = (size, size, size)
        key(props["pot"], frame, ("scale",))
        for i, puff in enumerate(props["steam"]):
            puff.location.z = puff["base_z"] + .04 * math.sin(time * 4 + i * 2)
            key(puff, frame, ("location",))
        key(paper, frame, ("location", "rotation_euler"))
        key(flashpaper, frame, ("location", "rotation_euler"))
        camera = cameras[sid]
        start = Vector(camera["initial_position"])
        target = Vector(camera["initial_target"])
        camera_pose(camera, start.lerp(target, p * .035), target)  # 컷 안에서 아주 조금 다가간다
        key(camera, frame, ("location", "rotation_euler"))
    # 컷 경계에서는 값을 붙들어 두고(CONSTANT) 그 밖은 직선으로 잇는다
    boundaries = {round(s["end"] * fps) for s in g.SHOT_TIMELINES}
    for action in bpy.data.actions:
        for channel in _action_fcurves(action):
            for point in channel.keyframe_points:
                point.interpolation = "CONSTANT" if round(point.co.x) in boundaries else "LINEAR"
    scene.frame_set(1)


def _action_fcurves(action):
    """액션의 F-커브를 모두 돌려준다. Blender 4.x 는 action.fcurves, 5.x 는 레이어·스트립·채널백 아래에 있다."""
    if hasattr(action, "fcurves"):
        yield from action.fcurves
        return
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                yield from bag.fcurves
