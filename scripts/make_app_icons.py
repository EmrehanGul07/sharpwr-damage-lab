"""Draw the SharpWR app icon and splash screens for the Android app.

The mark is a gold arrow through a crosshair ring on SharpWR's dark navy, drawn in the 108-unit
grid of an Android adaptive icon (everything inside the 66-unit safe circle). Writes:

- mipmap-*/ic_launcher_foreground.png: the mark on a transparent layer (adaptive icon);
- mipmap-*/ic_launcher.png and ic_launcher_round.png: mark and background, for Android 7;
- drawable*/splash.png: the mark centred on the app background, for Android 7-11
  (Android 12+ draws its own splash from the launcher icon and values/splash.xml);
- mobile/resources/icon-512.png: a 512 px copy for store listings.

Run after changing the design, then update mobile/native.json (the Android shell changed).
Needs Pillow, which Streamlit already installs.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "mobile" / "android" / "app" / "src" / "main" / "res"
GOLD = (216, 180, 93, 255)
LIGHT_GOLD = (240, 212, 138, 255)
BACKGROUND = (13, 22, 36, 255)
SPLASH_BACKGROUND = (7, 11, 17, 255)
DENSITIES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
SPLASH_SIZES = {
    "mdpi": (320, 480),
    "hdpi": (480, 800),
    "xhdpi": (720, 1280),
    "xxhdpi": (960, 1600),
    "xxxhdpi": (1280, 1920),
}
SUPERSAMPLE = 4


def mark(size):
    """The mark on a transparent square of `size` px covering the 108-unit grid."""
    big = size * SUPERSAMPLE
    unit = big / 108
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    def point(x, y):
        return (x * unit, y * unit)

    def line(a, b, width, color):
        draw.line([point(*a), point(*b)], fill=color, width=round(width * unit))
        for x, y in (a, b):
            r = width / 2
            draw.ellipse([point(x - r, y - r), point(x + r, y + r)], fill=color)

    centre = 54
    # Crosshair ring with four ticks.
    ring, stroke = 21, 3.4
    draw.ellipse(
        [point(centre - ring, centre - ring), point(centre + ring, centre + ring)],
        outline=GOLD,
        width=round(stroke * unit),
    )
    for angle in (0, 90, 180, 270):
        dx, dy = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        line(
            (centre + dx * 24.5, centre + dy * 24.5),
            (centre + dx * 30.5, centre + dy * 30.5),
            stroke,
            GOLD,
        )
    # Arrow from bottom left to top right, tip and tail 31 units from the centre.
    axis = (math.cos(math.radians(-45)), math.sin(math.radians(-45)))
    normal = (-axis[1], axis[0])

    def along(distance, side=0.0):
        return (
            centre + axis[0] * distance + normal[0] * side,
            centre + axis[1] * distance + normal[1] * side,
        )

    shaft = [along(-24, 2.1), along(20, 2.1), along(20, -2.1), along(-24, -2.1)]
    draw.polygon([point(*p) for p in shaft], fill=LIGHT_GOLD)
    head = [along(31), along(16, 7), along(19.5), along(16, -7)]
    draw.polygon([point(*p) for p in head], fill=LIGHT_GOLD)
    # Fletching: one swept-back vane on each side of the shaft's end.
    for side in (1, -1):
        vane = [along(-17, 1.4 * side), along(-24, 1.4 * side), along(-30, 7 * side), along(-23, 7 * side)]
        draw.polygon([point(*p) for p in vane], fill=LIGHT_GOLD)
    return image.resize((size, size), Image.LANCZOS)


def full_icon(size, round_mask):
    """Mark on the background, masked to a circle or a rounded square."""
    big = size * SUPERSAMPLE
    mask = Image.new("L", (big, big), 0)
    draw = ImageDraw.Draw(mask)
    if round_mask:
        draw.ellipse([0, 0, big - 1, big - 1], fill=255)
    else:
        draw.rounded_rectangle([0, 0, big - 1, big - 1], radius=big * 0.22, fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    # Legacy icons have no adaptive zoom: draw the 108-unit grid so the mark fills the icon.
    layer = mark(round(size * 108 / 76))
    offset = (size - layer.width) // 2
    icon = Image.new("RGBA", (size, size), BACKGROUND)
    icon.alpha_composite(layer, (offset, offset))
    icon.putalpha(mask)
    return icon


def splash(width, height):
    image = Image.new("RGBA", (width, height), SPLASH_BACKGROUND)
    layer = mark(round(min(width, height) * 0.6))
    image.alpha_composite(layer, ((width - layer.width) // 2, (height - layer.height) // 2))
    return image.convert("RGB")


def main():
    for density, scale in DENSITIES.items():
        folder = RES / f"mipmap-{density}"
        mark(round(108 * scale)).save(folder / "ic_launcher_foreground.png", optimize=True)
        full_icon(round(48 * scale), False).save(folder / "ic_launcher.png", optimize=True)
        full_icon(round(48 * scale), True).save(folder / "ic_launcher_round.png", optimize=True)
        portrait = SPLASH_SIZES[density]
        splash(*portrait).save(RES / f"drawable-port-{density}" / "splash.png", optimize=True)
        splash(*reversed(portrait)).save(RES / f"drawable-land-{density}" / "splash.png", optimize=True)
    splash(480, 320).save(RES / "drawable" / "splash.png", optimize=True)
    resources = ROOT / "mobile" / "resources"
    resources.mkdir(exist_ok=True)
    full_icon(512, False).save(resources / "icon-512.png", optimize=True)


if __name__ == "__main__":
    main()
