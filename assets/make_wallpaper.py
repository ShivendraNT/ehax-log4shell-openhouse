#!/usr/bin/env python3
"""Generate the EHAX Open House reveal wallpaper.

Outputs:
  assets/ehax-wallpaper.png  (1920x1080)
  assets/ehax-wallpaper.jpg  (1920x1080, quality 92)

No external assets are required. Uses macOS system fonts by default;
falls back to common Linux fonts if needed.
"""
from __future__ import annotations

import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

INK = (4, 8, 14)
NAVY = (6, 15, 22)
GREEN = (57, 255, 136)
GREEN_DIM = (30, 150, 90)
CYAN = (64, 224, 255)
MAGENTA = (255, 65, 160)
WHITE = (238, 246, 242)
GREY = (122, 148, 146)
DARK_GREEN = (7, 38, 28)


def find_font(candidates: list[str], fallback: str) -> str:
    for candidate in candidates:
        p = Path(candidate).expanduser()
        if p.exists():
            return str(p)
    return fallback


FONT_BLACK = find_font(
    [
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "DejaVuSans-Bold.ttf",
)
FONT_BOLD = find_font(
    [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "DejaVuSans-Bold.ttf",
)
FONT_MONO = find_font(
    [
        "~/Library/Fonts/JetBrainsMonoNLNerdFont-Regular.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ],
    "DejaVuSansMono.ttf",
)
FONT_MONO_BOLD = find_font(
    [
        "~/Library/Fonts/JetBrainsMonoNLNerdFont-Bold.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    ],
    "DejaVuSansMono-Bold.ttf",
)


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        # ease-out so the top stays dark longer
        t = t ** 1.6
        r = round(top[0] + (bottom[0] - top[0]) * t)
        g = round(top[1] + (bottom[1] - top[1]) * t)
        b = round(top[2] + (bottom[2] - top[2]) * t)
        for x in range(w):
            px[x, y] = (r, g, b)
    return img


def radial_glow(size: tuple[int, int], center: tuple[int, int], radius: int, color: tuple[int, int, int], strength: int) -> Image.Image:
    w, h = size
    glow = Image.new("L", size, 0)
    d = ImageDraw.Draw(glow)
    cx, cy = center
    steps = 48
    for i in range(steps, 0, -1):
        t = i / steps
        r = int(radius * t)
        alpha = int(strength * (1 - t) ** 2)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=alpha)
    glow = glow.filter(ImageFilter.GaussianBlur(radius // 4))
    overlay = Image.new("RGB", size, color)
    base = Image.new("RGB", size, (0, 0, 0))
    return Image.composite(overlay, base, glow)


def add_glow_layer(base: Image.Image, glow: Image.Image, opacity: float = 0.6) -> Image.Image:
    # Screen blend with adjustable opacity.
    blended = Image.blend(base, Image.new("RGB", base.size, (0, 0, 0)), 1 - opacity)
    screen = Image.blend(blended, Image.new("RGB", base.size, (255, 255, 255)), 0.0)
    # PIL has no screen blend; use numpy-free per-channel formula.
    b = base.load()
    g = glow.load()
    out = Image.new("RGB", base.size)
    o = out.load()
    for y in range(base.height):
        for x in range(base.width):
            br, bg, bb = b[x, y]
            gr, gg, gb = g[x, y]
            o[x, y] = (
                min(255, int(br + gr * opacity)),
                min(255, int(bg + gg * opacity)),
                min(255, int(bb + gb * opacity)),
            )
    return out


def draw_tracked(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fnt: ImageFont.FreeTypeFont, fill, tracking: int = 0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking
    return x


def tracked_width(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, tracking: int = 0) -> float:
    return sum(draw.textlength(ch, font=fnt) for ch in text) + tracking * max(len(text) - 1, 0)


def draw_grid(img: Image.Image):
    d = ImageDraw.Draw(img, "RGBA")
    step = 80
    for x in range(0, W, step):
        d.line([(x, 0), (x, H)], fill=(30, 90, 86, 18), width=1)
    for y in range(0, H, step):
        d.line([(0, y), (W, y)], fill=(30, 90, 86, 18), width=1)
    # stronger horizon lines
    for y in (400, 760):
        d.line([(0, y), (W, y)], fill=(57, 255, 136, 16), width=1)


def draw_isometric_cube(draw: ImageDraw.ImageDraw, x: int, y: int, s: int, top=(34, 90, 67), left=(10, 34, 29), right=(18, 58, 45), edge=(57, 255, 136, 150)):
    # isometric cube: top rhombus, left and right faces
    top_pts = [(x, y), (x + s, y - s // 2), (x + 2 * s, y), (x + s, y + s // 2)]
    left_pts = [(x, y), (x + s, y + s // 2), (x + s, y + s + s // 2), (x, y + s)]
    right_pts = [(x + 2 * s, y), (x + s, y + s // 2), (x + s, y + s + s // 2), (x + 2 * s, y + s)]
    draw.polygon(top_pts, fill=top)
    draw.polygon(left_pts, fill=left)
    draw.polygon(right_pts, fill=right)
    for pts in (top_pts, left_pts, right_pts):
        draw.line(pts + [pts[0]], fill=edge, width=2)


def rounded_rect(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def main() -> None:
    base = vertical_gradient((W, H), (2, 5, 9), (5, 18, 20))
    glow1 = radial_glow((W, H), (1380, 430), 760, (14, 110, 74), 110)
    glow2 = radial_glow((W, H), (360, 160), 620, (8, 70, 92), 70)
    base = add_glow_layer(base, glow1, 0.8)
    base = add_glow_layer(base, glow2, 0.55)
    draw_grid(base)
    d = ImageDraw.Draw(base, "RGBA")

    # deco: giant outlined shield behind the terminal
    shield = [
        (1570, 80), (1830, 170), (1810, 500), (1690, 680), (1570, 740),
        (1450, 680), (1330, 500), (1310, 170),
    ]
    d.line(shield + [shield[0]], fill=(57, 255, 136, 38), width=3)
    inner = [(x, y) for (x, y) in shield]
    # shift inward crudely
    cx, cy = 1570, 410
    inner = [(round(cx + (x - cx) * 0.86), round(cy + (y - cy) * 0.86)) for x, y in shield]
    d.line(inner + [inner[0]], fill=(57, 255, 136, 18), width=1)

    # terminal card
    tx, ty, tw, th = 1170, 276, 610, 396
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((tx + 14, ty + 18, tx + tw + 14, ty + th + 18), radius=20, fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    base = Image.alpha_composite(base.convert("RGBA"), shadow).convert("RGB")
    d = ImageDraw.Draw(base, "RGBA")
    rounded_rect(d, (tx, ty, tx + tw, ty + th), 18, (5, 13, 17, 232), (57, 255, 136, 105), 2)
    # terminal header
    d.rounded_rectangle((tx, ty, tx + tw, ty + 52), 18, fill=(9, 24, 24, 245))
    d.rectangle((tx, ty + 38, tx + tw, ty + 52), fill=(9, 24, 24, 245))
    for i, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((tx + 22 + i * 24, ty + 18, tx + 36 + i * 24, ty + 32), fill=col)
    d.text((tx + tw // 2 - 58, ty + 14), "ehax@dtu:~", font=font(FONT_MONO, 22), fill=(150, 190, 178))

    mono = font(FONT_MONO, 24)
    mono_bold = font(FONT_MONO_BOLD, 24)
    lines = [
        ("$ ", GREEN, "whoami", WHITE),
        ("", None, "ehax", GREY),
        ("", None, "", GREY),
        ("$ ", GREEN, "tail -n 3 demo.log", WHITE),
        ("", None, "[LOG] chat message received", GREY),
        ("", None, "[LOG] remote class loaded", GREY),
        ("", None, "[OK]  wallpaper changed", GREEN),
        ("", None, "", GREY),
        ("$ ", GREEN, "echo $LESSON", WHITE),
        ("", None, "patch. update. repeat.", GREEN),
    ]
    y = ty + 76
    for prompt, pcol, text, tcol in lines:
        if prompt:
            d.text((tx + 26, y), prompt, font=mono_bold, fill=pcol)
            d.text((tx + 26 + d.textlength(prompt, font=mono_bold), y), text, font=mono, fill=tcol)
        elif text:
            d.text((tx + 26, y), text, font=mono, fill=tcol)
        y += 30
    # cursor on the line after the last output
    cursor_y = y
    d.rectangle((tx + 26, cursor_y, tx + 39, cursor_y + 18), fill=GREEN)

    # top kicker
    d.line((128, 150, 260, 150), fill=GREEN, width=4)
    d.text((128, 116), "EHAX", font=font(FONT_BLACK, 34), fill=GREEN)
    d.text((128 + d.textlength("EHAX", font=font(FONT_BLACK, 34)) + 16, 122), "// DTU CYBERSECURITY SOCIETY", font=font(FONT_MONO_BOLD, 22), fill=(170, 205, 192))
    d.text((128, 174), "OPEN HOUSE  /  LOG4SHELL DEMO", font=font(FONT_MONO, 18), fill=(90, 125, 116))

    # big glitch title
    title_font = font(FONT_BLACK, 164)
    title_lines = [
        ("YOU'VE", 244, WHITE),
        ("BEEN", 402, WHITE),
        ("HACKED.", 560, GREEN),
    ]
    for text, yy, col in title_lines:
        x = 120
        # chromatic glitch ghosts
        d.text((x - 6, yy + 2), text, font=title_font, fill=(255, 65, 160, 80))
        d.text((x + 6, yy - 2), text, font=title_font, fill=(64, 224, 255, 80))
        d.text((x, yy), text, font=title_font, fill=col)
        # thin slice displacement
        if text == "HACKED.":
            slice_y = yy + 96
            strip = base.crop((100, slice_y, 1000, slice_y + 14))
            base.paste(strip, (114, slice_y))
            d = ImageDraw.Draw(base, "RGBA")
            d.rectangle((100, slice_y, 1000, slice_y + 3), fill=(4, 8, 14, 180))

    # subline
    sub_font = font(FONT_MONO_BOLD, 27)
    d.text((128, 796), "ETHICALLY.", font=font(FONT_BLACK, 50), fill=(220, 238, 229))
    # small divider dot and text
    d.text((128, 872), "ONE CHAT MESSAGE. ONE OLD LIBRARY. ZERO PASSWORDS.", font=sub_font, fill=(133, 166, 155))

    # bottom rule + footer
    d.line((128, 978, 1792, 978), fill=(57, 255, 136, 45), width=1)
    d.text((128, 1000), "CVE-2021-44228  /  PATCH. UPDATE. REPEAT.", font=font(FONT_MONO_BOLD, 19), fill=(121, 156, 145))
    right = "EHAX // DTU  •  OPEN AIR THEATRE"
    d.text((1792 - d.textlength(right, font=font(FONT_MONO, 19)), 1000), right, font=font(FONT_MONO, 19), fill=(121, 156, 145))

    # cubes bottom right
    draw_isometric_cube(d, 1510, 842, 52)
    draw_isometric_cube(d, 1642, 880, 64)
    draw_isometric_cube(d, 1750, 806, 40)

    # scanlines + vignette
    scan = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scan)
    for y in range(0, H, 4):
        sd.line([(0, y), (W, y)], fill=(0, 0, 0, 14), width=1)
    base = Image.alpha_composite(base.convert("RGBA"), scan).convert("RGB")

    vignette = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vignette)
    for i in range(160, 0, -1):
        alpha = int(120 * (i / 160) ** 2)
        vd.rectangle([-i, -i, W + i, H + i], outline=alpha, width=2)
    # cheaper radial vignette using a blurred ellipse mask
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((-300, -260, W + 300, H + 260), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(160))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    base = Image.composite(base, black, mask)

    # subtle film grain
    import random
    random.seed(44228)
    grain = Image.effect_noise((W, H), 18).convert("L")
    grain_rgb = Image.merge("RGB", (grain, grain, grain))
    base = Image.blend(base, grain_rgb, 0.018)

    out_png = HERE / "ehax-wallpaper.png"
    out_jpg = HERE / "ehax-wallpaper.jpg"
    base.save(out_png, "PNG", optimize=True)
    base.save(out_jpg, "JPEG", quality=93, optimize=True, progressive=True)
    print(f"wrote {out_png} ({out_png.stat().st_size/1024:.0f} KB)")
    print(f"wrote {out_jpg} ({out_jpg.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
