#!/usr/bin/env python3
"""
build_clay.py - Standalone CLI for procedural Blender character catalog, expressions, and demo.

Usage inside Blender:
  blender -b -P scripts/build_clay.py -- --mode catalog --output ./output
  blender -b -P scripts/build_clay.py -- --mode expressions --character F01 --output ./output
  blender -b -P scripts/build_clay.py -- --mode demo --character F01 --output ./output
"""

import os
import sys
import json
import argparse
from typing import Dict, Any

try:
    import bpy
except ImportError:
    sys.stderr.write("Error: bpy module not found. This script must be run inside Blender:\n")
    sys.stderr.write("  blender -b -P scripts/build_clay.py -- --mode catalog [args]\n")
    sys.exit(1)

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import clay_lib


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    clay_lib.MATERIAL_CACHE.clear()


def load_characters_config(config_path: str) -> Dict[str, Any]:
    if not os.path.exists(config_path):
        search_paths = [
            config_path,
            os.path.join(script_dir, "..", config_path),
            os.path.join(script_dir, config_path),
            "characters.json"
        ]
        for sp in search_paths:
            if os.path.exists(sp):
                config_path = sp
                break
        else:
            sys.stderr.write(f"Error: Cannot find character config at {config_path}\n")
            sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        sys.stderr.write(f"Error parsing {config_path}: {e}\n")
        sys.exit(1)


def build_catalog(args, config: Dict[str, Any]):
    output_dir = os.path.abspath(args.output)
    os.makedirs(output_dir, exist_ok=True)

    characters = config.get("characters", {})
    expressions = config.get("expressions", {})
    manifest_characters = []

    for char_id, char_spec in characters.items():
        print(f"[Catalog] Generating {char_id} ({char_spec.get('name')})...")
        reset_scene()
        clay_lib.configure_render_settings(width=args.width, height=args.height, samples=args.samples)

        lights = clay_lib.setup_studio_environment()
        fig = clay_lib.build_character_mesh(char_id, char_spec, bpy.context.scene.collection)

        clay_lib.pose_actor(
            fig,
            position=(0.0, 0.0, 0.0),
            yaw=0.0,
            hand_targets=[
                (-char_spec["proportions"]["shoulder_width"] * 0.65, 0.0, char_spec["proportions"]["leg_length"] * 0.85),
                (char_spec["proportions"]["shoulder_width"] * 0.65, 0.0, char_spec["proportions"]["leg_length"] * 0.85)
            ]
        )
        clay_lib.apply_expression(fig, "neutral", expressions)

        h = char_spec["proportions"]["total_height"]
        cam = clay_lib.create_camera(
            name=f"Cam_Catalog_{char_id}",
            location=(.78, -2.9, h * 0.63),
            target=(0.0, 0.0, h * 0.50),
            focal_length=65.0
        )
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = h * 1.3
        bpy.context.scene.camera = cam

        blend_filename = f"catalog_{char_id}.blend"
        blend_path = os.path.join(output_dir, blend_filename)
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)

        render_filename = f"catalog_{char_id}.png"
        render_path = os.path.join(output_dir, render_filename)
        bpy.context.scene.render.filepath = render_path
        bpy.ops.render.render(write_still=True)

        manifest_characters.append({
            "id": char_id,
            "name": char_spec.get("name"),
            "description": char_spec.get("description"),
            "blend_file": blend_filename,
            "render_file": render_filename,
            "camera": cam.name,
            "controls": [
                fig["root"].name,
                fig["hips"].name,
                fig["chest"].name,
                fig["head"].name,
                fig["mouth"].name
            ]
        })

    manifest_path = os.path.join(output_dir, "catalog_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "mode": "catalog",
            "resolution": [args.width, args.height],
            "samples": args.samples,
            "characters": manifest_characters
        }, f, indent=2, ensure_ascii=False)

    print(f"[Catalog] Done. Manifest saved to {manifest_path}")


def build_expressions(args, config: Dict[str, Any]):
    output_dir = os.path.abspath(args.output)
    os.makedirs(output_dir, exist_ok=True)

    char_id = args.character
    characters = config.get("characters", {})
    if char_id not in characters:
        sys.stderr.write(f"Error: Character {char_id} not found in configuration.\n")
        sys.exit(1)

    char_spec = characters[char_id]
    expressions = config.get("expressions", {})
    expr_list = ["neutral", "awkward", "puzzled", "annoyed", "ashamed", "happy"]

    print(f"[Expressions] Building expressions for {char_id}...")
    reset_scene()
    clay_lib.configure_render_settings(width=args.width, height=args.height, samples=args.samples)

    clay_lib.setup_studio_environment()
    fig = clay_lib.build_character_mesh(char_id, char_spec, bpy.context.scene.collection)

    clay_lib.pose_actor(fig, position=(0.0, 0.0, 0.0), yaw=0.0)

    h = char_spec["proportions"]["total_height"]
    head_z = h - char_spec["proportions"]["head_scale"][2]
    cam = clay_lib.create_camera(
        name=f"Cam_Closeup_{char_id}",
        location=(0.0, -1.25, head_z),
        target=(0.0, 0.0, head_z - 0.02),
        focal_length=85.0
    )
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = .9
    bpy.context.scene.camera = cam

    blend_filename = f"expressions_{char_id}.blend"
    blend_path = os.path.join(output_dir, blend_filename)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)

    rendered_expressions = []
    for expr in expr_list:
        print(f"  Rendering expression '{expr}'...")
        clay_lib.apply_expression(fig, expr, expressions)
        bpy.context.view_layer.update()

        render_filename = f"{char_id}_{expr}.png"
        render_path = os.path.join(output_dir, render_filename)
        bpy.context.scene.render.filepath = render_path
        bpy.ops.render.render(write_still=True)

        rendered_expressions.append({
            "expression": expr,
            "render_file": render_filename
        })

    manifest_path = os.path.join(output_dir, "expressions_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "mode": "expressions",
            "character": char_id,
            "blend_file": blend_filename,
            "resolution": [args.width, args.height],
            "expressions": rendered_expressions
        }, f, indent=2, ensure_ascii=False)

    print(f"[Expressions] Done. Manifest saved to {manifest_path}")


def build_demo(args, config: Dict[str, Any]):
    output_dir = os.path.abspath(args.output)
    os.makedirs(output_dir, exist_ok=True)

    char_id = args.character
    characters = config.get("characters", {})
    if char_id not in characters:
        sys.stderr.write(f"Error: Character {char_id} not in configuration.\n")
        sys.exit(1)

    char_spec = characters[char_id]
    expressions = config.get("expressions", {})

    print(f"[Demo] Building 8-second 24fps office demo for {char_id}...")
    reset_scene()
    clay_lib.configure_render_settings(width=args.width, height=args.height, samples=args.samples)

    clay_lib.setup_studio_environment()
    office = clay_lib.build_miniature_office()
    fig = clay_lib.build_character_mesh(char_id, char_spec, bpy.context.scene.collection)

    cam = clay_lib.create_camera(
        name="Cam_Office_Demo",
        location=(.5, -2.8, 1.8),
        target=(0.0, .40, 1.0),
        focal_length=50.0
    )
    bpy.context.scene.camera = cam

    cam.data.type="ORTHO"
    cam.data.ortho_scale=1.9
    total_frames = 192
    clay_lib.animate_demo_scene(fig, office, expressions, total_frames=total_frames)

    blend_filename = f"demo_{char_id}_office.blend"
    blend_path = os.path.join(output_dir, blend_filename)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)

    manifest_path = os.path.join(output_dir, "demo_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "mode": "demo",
            "character": char_id,
            "blend_file": blend_filename,
            "frame_start": 1,
            "frame_end": total_frames,
            "fps": 24,
            "duration_seconds": 8.0,
            "resolution": [args.width, args.height],
            "camera": cam.name,
            "key_events": [
                {"frame": 1, "t": "0.0s", "description": "Sitting at desk holding phone, neutral reading"},
                {"frame": 60, "t": "2.5s", "description": "Awkward glance sideways, eyebrow shift"},
                {"frame": 115, "t": "4.8s", "description": "Held torso, head briefly lifts before sigh"},
                {"frame": 140, "t": "5.8s", "description": "The sigh: head tilts down, hand lowers phone to desk"},
                {"frame": 170, "t": "7.1s", "description": "Subtle blink, calm resigned settlement"}
            ],
            "controls": [
                fig["root"].name,
                fig["hips"].name,
                fig["chest"].name,
                fig["head"].name,
                office["smartphone"].name
            ]
        }, f, indent=2, ensure_ascii=False)

    print(f"[Demo] Saved editable 8-second animation to {blend_path}")
    print(f"[Demo] Manifest saved to {manifest_path}")


def main():
    raw_args = sys.argv[1:]
    if "--" in raw_args:
        idx = raw_args.index("--")
        cli_args = raw_args[idx + 1:]
    else:
        cli_args = raw_args

    parser = argparse.ArgumentParser(
        description="Build procedural clay characters, expressions, and animations for 퇴근각."
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["catalog", "expressions", "demo"],
        help="Execution mode: catalog (all 6 portraits), expressions (6 expressions closeup), or demo (8s office animation)"
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Directory to store generated .blend files, renders, and manifests"
    )
    parser.add_argument(
        "--character",
        default="F01",
        help="Character ID (e.g. F01, F02, F03, M01, M02, M03). Default: F01"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=900,
        help="Render width in pixels (default: 900)"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1100,
        help="Render height in pixels (default: 1100)"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=32,
        help="Render samples (default: 32)"
    )
    parser.add_argument(
        "--config",
        default="characters.json",
        help="Path to characters.json configuration file"
    )

    try:
        args = parser.parse_args(cli_args)
    except SystemExit:
        sys.exit(1)

    if args.width <= 0 or args.height <= 0 or args.samples <= 0:
        sys.stderr.write("Error: --width, --height, and --samples must be positive integers.\n")
        sys.exit(1)

    config = load_characters_config(args.config)

    if args.mode == "catalog":
        build_catalog(args, config)
    elif args.mode == "expressions":
        build_expressions(args, config)
    elif args.mode == "demo":
        build_demo(args, config)


if __name__ == "__main__":
    main()
