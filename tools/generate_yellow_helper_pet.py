#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw


DEFAULT_OUT_DIR = Path("dist") / "yellow-helper"
CELL_W = 192
CELL_H = 208
ROWS = {
    "idle": 6,
    "running-right": 8,
    "running-left": 8,
    "waving": 4,
    "jumping": 5,
    "failed": 8,
    "waiting": 6,
    "running": 6,
    "review": 6,
}
ROW_ORDER = list(ROWS)


BLACK = (34, 28, 22, 255)
YELLOW = (248, 214, 48, 255)
YELLOW_DARK = (219, 178, 32, 255)
BLUE = (42, 104, 188, 255)
BLUE_DARK = (22, 66, 138, 255)
SILVER = (184, 190, 194, 255)
WHITE = (250, 250, 235, 255)
BROWN = (95, 62, 36, 255)
TRANSPARENT = (0, 0, 0, 0)


def ellipse(draw: ImageDraw.ImageDraw, box, fill, outline=BLACK, width=4) -> None:
    draw.ellipse(box, fill=fill, outline=outline, width=width)


def rounded(draw: ImageDraw.ImageDraw, box, radius, fill, outline=BLACK, width=4) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_limb(draw: ImageDraw.ImageDraw, p0, p1, width=11, fill=BLACK) -> None:
    draw.line([p0, p1], fill=fill, width=width)
    r = width // 2
    draw.ellipse((p0[0] - r, p0[1] - r, p0[0] + r, p0[1] + r), fill=fill)
    draw.ellipse((p1[0] - r, p1[1] - r, p1[0] + r, p1[1] + r), fill=fill)


def draw_banana(draw: ImageDraw.ImageDraw, x: int, y: int, flip: bool = False) -> None:
    sign = -1 if flip else 1
    outer = [
        (x - 2 * sign, y + 12),
        (x + 13 * sign, y + 8),
        (x + 20 * sign, y - 6),
        (x + 15 * sign, y - 11),
        (x + 5 * sign, y + 2),
        (x - 5 * sign, y + 4),
    ]
    inner = [
        (x + 4 * sign, y + 7),
        (x + 12 * sign, y + 4),
        (x + 16 * sign, y - 4),
    ]
    draw.line(outer[:4], fill=BLACK, width=8, joint="curve")
    draw.line(outer[:4], fill=(255, 224, 69, 255), width=5, joint="curve")
    draw.line(inner, fill=(255, 247, 145, 255), width=2)
    draw.ellipse((x + 14 * sign - 3, y - 13, x + 14 * sign + 3, y - 7), fill=BLACK)


def draw_wrench(draw: ImageDraw.ImageDraw, x: int, y: int, angle_up: bool = True) -> None:
    end = (x + 24, y - 27 if angle_up else y - 15)
    draw.line((x, y, end[0], end[1]), fill=BLACK, width=7)
    draw.line((x, y, end[0], end[1]), fill=SILVER, width=4)
    draw.ellipse((end[0] - 8, end[1] - 8, end[0] + 8, end[1] + 8), fill=SILVER, outline=BLACK, width=3)
    draw.pieslice((end[0] - 8, end[1] - 8, end[0] + 8, end[1] + 8), 300, 60, fill=TRANSPARENT)
    draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=BLACK)


def draw_magnifier(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.line((x + 8, y + 11, x + 25, y + 28), fill=BLACK, width=7)
    draw.line((x + 8, y + 11, x + 25, y + 28), fill=(104, 72, 38, 255), width=4)
    draw.ellipse((x - 15, y - 15, x + 15, y + 15), fill=(170, 222, 255, 180), outline=BLACK, width=5)
    draw.arc((x - 9, y - 9, x + 9, y + 9), 210, 310, fill=WHITE, width=2)


def draw_attached_smoke(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    colors = [(210, 210, 205, 255), (235, 235, 230, 255)]
    bubbles = [(-7, 1, 9), (2, -7, 11), (13, 0, 8)]
    for index, (dx, dy, radius) in enumerate(bubbles):
        draw.ellipse(
            (x + dx - radius, y + dy - radius, x + dx + radius, y + dy + radius),
            fill=colors[index % 2],
            outline=BLACK,
            width=2,
        )


def draw_helper(
    *,
    pose: str,
    phase: int,
    frame_count: int,
    face: str = "smile",
    facing: int = 1,
) -> Image.Image:
    img = Image.new("RGBA", (CELL_W, CELL_H), TRANSPARENT)
    draw = ImageDraw.Draw(img)

    t = phase / max(1, frame_count - 1)
    wave = math.sin(t * math.tau)
    cx = 96
    base_y = 95
    squash = 0
    tilt = 0
    bounce = 0
    prop = ""

    arm_l = ((61, 99), (42, 124))
    arm_r = ((131, 99), (150, 124))
    leg_l = ((78, 153), (70, 178))
    leg_r = ((114, 153), (122, 178))

    if pose == "idle":
        bounce = [0, -2, -3, -2, 0, 1][phase]
        squash = [0, 0, 1, 0, 0, -1][phase]
        face = "blink" if phase in {2, 3} else "smile"
    elif pose == "running-right":
        cx += 2
        tilt = 5
        bounce = [-1, -5, -2, 1, -1, -5, -2, 1][phase]
        stride = math.sin(t * math.tau * 2)
        arm_l = ((61, 100), (45, 116 + int(stride * 13)))
        arm_r = ((131, 100), (158, 113 - int(stride * 15)))
        leg_l = ((78, 153), (62 + int(stride * 15), 178))
        leg_r = ((114, 153), (131 - int(stride * 15), 178))
        face = "grin"
    elif pose == "waving":
        arm_l = ((61, 99), (42, 123))
        raise_y = [111, 76, 54, 78][phase]
        arm_r = ((132, 98), (156, raise_y))
        face = "grin"
        bounce = [-1, -3, -3, -1][phase]
        prop = "wrench"
    elif pose == "jumping":
        bounce = [4, -14, -34, -17, 3][phase]
        squash = [3, -1, -2, -1, 2][phase]
        arm_l = ((61, 99), (34, 78 + phase * 2))
        arm_r = ((131, 99), (158, 78 + phase * 2))
        leg_l = ((78, 153), (66, 165 + min(phase, 2) * 2))
        leg_r = ((114, 153), (126, 165 + min(phase, 2) * 2))
        face = "open"
    elif pose == "failed":
        bounce = [0, 3, 5, 6, 5, 4, 5, 6][phase]
        tilt = [-5, -8, -10, -7, -8, -11, -9, -8][phase]
        arm_l = ((61, 103), (47, 137))
        arm_r = ((131, 103), (145, 137))
        leg_l = ((78, 153), (75, 176))
        leg_r = ((114, 153), (117, 176))
        face = "sad"
        prop = "smoke" if phase in {1, 3, 5, 7} else "tear"
    elif pose == "waiting":
        glance = ["left", "left", "center", "right", "right", "center"][phase]
        bounce = [0, -1, -2, -1, 0, 1][phase]
        face = glance
        arm_l = ((61, 100), (45, 116))
        arm_r = ((131, 100), (146, 124))
        prop = "banana"
    elif pose == "running":
        bounce = [-1, -5, -2, -1, -5, -2][phase]
        stride = math.sin(t * math.tau * 2)
        arm_l = ((61, 100), (39, 120 + int(stride * 14)))
        arm_r = ((131, 100), (153, 120 - int(stride * 14)))
        leg_l = ((78, 153), (66 + int(stride * 13), 178))
        leg_r = ((114, 153), (126 - int(stride * 13), 178))
        face = "grin"
    elif pose == "review":
        tilt = [-2, -3, -5, -3, -1, -2][phase]
        bounce = [0, 0, -1, -2, -1, 0][phase]
        face = "focus" if phase not in {2} else "blink"
        arm_l = ((60, 101), (51, 128))
        arm_r = ((132, 101), (148, 122))
        prop = "magnifier"

    def tx(point):
        x, y = point
        x = cx + (x - 96) * facing
        return (int(x), int(y + bounce))

    body = (cx - 47, base_y - 70 + bounce, cx + 47, base_y + 74 + bounce + squash)
    # Body outline and fill: capsule top/bottom joined by a rectangle.
    rounded(draw, body, 40, YELLOW, width=5)
    draw.rectangle((body[0] + 5, body[1] + 48, body[2] - 5, body[3] - 42), fill=YELLOW)
    draw.arc((body[0], body[1], body[2], body[1] + 84), 190, 350, fill=YELLOW_DARK, width=3)

    # Hair tufts.
    hair_y = body[1] + 6
    for dx, dy in [(-11, -15), (0, -18), (10, -14)]:
        draw.line((cx, hair_y, cx + dx, hair_y + dy), fill=BLACK, width=4)

    # Arms behind overalls.
    draw_limb(draw, tx(arm_l[0]), tx(arm_l[1]), width=10)
    draw_limb(draw, tx(arm_r[0]), tx(arm_r[1]), width=10)
    for hand in [tx(arm_l[1]), tx(arm_r[1])]:
        ellipse(draw, (hand[0] - 8, hand[1] - 7, hand[0] + 8, hand[1] + 8), BLACK, outline=BLACK, width=1)

    if prop == "wrench":
        hand = tx(arm_r[1])
        draw_wrench(draw, hand[0] + 2, hand[1] - 3, angle_up=phase in {1, 2})
    elif prop == "banana":
        hand = tx(arm_l[1])
        draw_banana(draw, hand[0] - 6, hand[1] - 6, flip=False)
    elif prop == "magnifier":
        hand = tx(arm_r[1])
        draw_magnifier(draw, hand[0] + 12, hand[1] - 4)

    # Goggle strap.
    strap_y = body[1] + 57
    draw.line((body[0] + 2, strap_y, body[2] - 2, strap_y), fill=BLACK, width=10)
    # Single goggle with expressive eye.
    gx, gy = cx, strap_y
    ellipse(draw, (gx - 35, gy - 31, gx + 35, gy + 31), SILVER, width=6)
    ellipse(draw, (gx - 25, gy - 22, gx + 25, gy + 22), WHITE, outline=BLACK, width=4)
    pupil_dx = 0
    if face == "left":
        pupil_dx = -5
    elif face == "right":
        pupil_dx = 5
    if face == "blink":
        draw.line((gx - 18, gy, gx + 18, gy), fill=BLACK, width=5)
    else:
        ellipse(draw, (gx - 9 + pupil_dx, gy - 9, gx + 10 + pupil_dx, gy + 11), BROWN, outline=BLACK, width=2)
        draw.ellipse((gx - 2 + pupil_dx, gy - 6, gx + 4 + pupil_dx, gy), fill=WHITE)
        draw.ellipse((gx + 3 + pupil_dx, gy + 2, gx + 6 + pupil_dx, gy + 5), fill=(45, 30, 20, 255))

    # Overalls.
    bib = (cx - 30, body[1] + 98, cx + 30, body[1] + 133)
    draw.rectangle((body[0] + 13, body[1] + 126, body[2] - 13, body[3] - 16), fill=BLUE, outline=BLACK, width=4)
    rounded(draw, bib, 9, BLUE, width=4)
    draw.line((cx - 32, body[1] + 101, cx - 45, body[1] + 70), fill=BLUE_DARK, width=7)
    draw.line((cx + 32, body[1] + 101, cx + 45, body[1] + 70), fill=BLUE_DARK, width=7)
    draw.rectangle((cx - 13, body[1] + 115, cx + 13, body[1] + 128), fill=BLUE_DARK, outline=BLACK, width=2)
    for bx in (cx - 20, cx + 20):
        draw.ellipse((bx - 4, body[1] + 101, bx + 4, body[1] + 109), fill=(245, 201, 68, 255), outline=BLACK, width=1)

    # Mouth and state details.
    my = body[1] + 88
    draw.ellipse((cx - 31, my - 3, cx - 23, my + 5), fill=(255, 225, 88, 255))
    draw.ellipse((cx + 23, my - 3, cx + 31, my + 5), fill=(255, 225, 88, 255))
    if face == "sad":
        draw.arc((cx - 15, my + 2, cx + 15, my + 24), 200, 340, fill=BLACK, width=3)
        draw.ellipse((cx + 12, gy + 16, cx + 18, gy + 28), fill=(94, 164, 226, 255), outline=BLACK, width=1)
        if prop == "tear":
            draw.ellipse((cx - 20, gy + 14, cx - 11, gy + 28), fill=(94, 164, 226, 255), outline=BLACK, width=1)
    elif face == "open":
        ellipse(draw, (cx - 9, my, cx + 9, my + 15), (82, 36, 28, 255), width=2)
    elif face == "focus":
        draw.line((cx - 10, my + 7, cx + 11, my + 5), fill=BLACK, width=3)
    else:
        draw.arc((cx - 15, my - 2, cx + 15, my + 14), 20, 160, fill=BLACK, width=3)

    # Legs and boots on top so they read clearly.
    draw_limb(draw, tx(leg_l[0]), tx(leg_l[1]), width=10)
    draw_limb(draw, tx(leg_r[0]), tx(leg_r[1]), width=10)
    for foot in [tx(leg_l[1]), tx(leg_r[1])]:
        draw.rounded_rectangle((foot[0] - 12, foot[1] - 3, foot[0] + 14, foot[1] + 9), radius=4, fill=BLACK)

    if prop == "smoke":
        draw_attached_smoke(draw, int(cx + 31), int(body[1] + 31))

    if tilt:
        rotated = img.rotate(tilt * facing, resample=Image.Resampling.NEAREST, center=(cx, 106), fillcolor=TRANSPARENT)
        img = rotated

    # Clip to a generous centered sprite box and paste back to avoid rotation expanding outside.
    return img


def row_strip(state: str, count: int) -> Image.Image:
    strip = Image.new("RGBA", (CELL_W * count, CELL_H), TRANSPARENT)
    if state == "running-left":
        right = row_strip("running-right", count)
        return right.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    for i in range(count):
        pose = state
        if state == "running-right":
            frame = draw_helper(pose=pose, phase=i, frame_count=count, facing=1)
        else:
            frame = draw_helper(pose=pose, phase=i, frame_count=count)
        strip.alpha_composite(frame, (i * CELL_W, 0))
    return strip


def compose_atlas() -> Image.Image:
    atlas = Image.new("RGBA", (CELL_W * 8, CELL_H * 9), TRANSPARENT)
    for row_index, state in enumerate(ROW_ORDER):
        strip = row_strip(state, ROWS[state])
        atlas.alpha_composite(strip, (0, row_index * CELL_H))
    return atlas


def write_pet_manifest(out_dir: Path) -> None:
    manifest = {
        "id": "yellow-helper",
        "displayName": "Yellow Helper",
        "description": "A tiny yellow goggle-wearing helper in blue overalls for Codex.",
        "spritesheetPath": "spritesheet.webp",
    }
    (out_dir / "pet.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def write_package(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    atlas = compose_atlas()
    atlas.save(out_dir / "spritesheet.webp", format="WEBP", lossless=True, quality=100, method=6)
    write_pet_manifest(out_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Yellow Helper Codex pet package.")
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT_DIR),
        help="Output directory containing pet.json and spritesheet.webp.",
    )
    args = parser.parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    write_package(out_dir)
    print(json.dumps({"ok": True, "package": str(out_dir)}, indent=2))


if __name__ == "__main__":
    main()
