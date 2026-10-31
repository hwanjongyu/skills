#!/usr/bin/env python3
"""
Overlay Comparator: Visual Parity & Alpha Blend Verification Tool
Part of rea-screenshot-game-builder skill.

Generates a 3-panel side-by-side comparison:
[ Reference Ground Truth | Captured Device Screen | 50:50 Alpha Blend Overlay ]
"""

import argparse
import sys
import os
from PIL import Image


def generate_comparison_overlay(ref_path: str, dev_path: str, output_path: str, alpha: float = 0.5):
    if not os.path.exists(ref_path):
        raise FileNotFoundError(f"Reference image not found: {ref_path}")
    if not os.path.exists(dev_path):
        raise FileNotFoundError(f"Device screenshot not found: {dev_path}")

    # Load images and convert to RGBA
    ref_img = Image.open(ref_path).convert("RGBA")
    dev_img = Image.open(dev_path).convert("RGBA")

    # Resize device image to match reference image dimensions for exact overlay
    if dev_img.size != ref_img.size:
        print(f"[INFO] Resizing device image from {dev_img.size} to reference size {ref_img.size} (LANCZOS)...")
        dev_img = dev_img.resize(ref_img.size, Image.LANCZOS)

    # 50:50 (or custom alpha) blend
    blended = Image.blend(ref_img, dev_img, alpha)

    # Construct 3-panel comparison composite: [ Reference | Device | Blended ]
    w, h = ref_img.size
    composite = Image.new("RGBA", (w * 3, h), (0, 0, 0, 255))
    composite.paste(ref_img, (0, 0))
    composite.paste(dev_img, (w, 0))
    composite.paste(blended, (w * 2, 0))

    # Ensure parent output directory exists
    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    composite.save(output_path, "PNG")
    print(f"[SUCCESS] 3-Panel comparison saved to: {output_path}")
    print(f"          - Panel 1 (0..{w}): Reference")
    print(f"          - Panel 2 ({w}..{w*2}): Device Screen")
    print(f"          - Panel 3 ({w*2}..{w*3}): {int(alpha*100)}:{(100-int(alpha*100))} Alpha Blend Overlay")


def main():
    parser = argparse.ArgumentParser(
        description="Generate 3-panel visual parity comparison and alpha overlay."
    )
    parser.add_argument("ref", help="Path to reference screenshot (ground truth)")
    parser.add_argument("dev", help="Path to captured device screenshot")
    parser.add_argument(
        "-o", "--output",
        default="docs/screenshots/comparison_overlay.png",
        help="Output comparison image path (default: docs/screenshots/comparison_overlay.png)"
    )
    parser.add_argument(
        "-a", "--alpha",
        type=float,
        default=0.5,
        help="Alpha blend weight between 0.0 and 1.0 (default: 0.5)"
    )

    args = parser.parse_args()

    try:
        generate_comparison_overlay(args.ref, args.dev, args.output, args.alpha)
    except Exception as e:
        print(f"[ERROR] Failed to generate comparison: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
