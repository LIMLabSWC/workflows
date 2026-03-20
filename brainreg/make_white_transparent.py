#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def white_to_transparent(img: Image.Image) -> Image.Image:
    # Work in RGBA so we can edit alpha.
    rgba = img.convert("RGBA")
    pixels = rgba.getdata()

    new_pixels = []
    for r, g, b, a in pixels:
        if (r, g, b) == (255, 255, 255):
            new_pixels.append((r, g, b, 0))  # transparent
        else:
            new_pixels.append((r, g, b, a))  # keep as-is

    rgba.putdata(new_pixels)
    return rgba


def main() -> None:
    p = argparse.ArgumentParser(description="Make pure-white (255,255,255) pixels transparent in PNGs.")
    p.add_argument("input_dir", type=Path, help="Folder containing PNGs")
    p.add_argument("output_dir", type=Path, help="Folder to write new PNGs")
    p.add_argument("--overwrite", action="store_true", help="Overwrite output files if they already exist")
    args = p.parse_args()

    in_dir: Path = args.input_dir
    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    pngs = sorted(in_dir.glob("*.png"))
    if not pngs:
        raise SystemExit(f"No .png files found in: {in_dir}")

    for src in pngs:
        dst = out_dir / src.name
        if dst.exists() and not args.overwrite:
            print(f"skip (exists): {dst}")
            continue

        with Image.open(src) as im:
            out = white_to_transparent(im)
            out.save(dst, format="PNG")
            print(f"wrote: {dst}")


if __name__ == "__main__":
    main()