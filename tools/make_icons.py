"""Generate add-on icons.

Kodi renders icons small (a grid tile is often ~120px), so these are built from a
few large high-contrast shapes rather than fine detail, and drawn at 4x then
downsampled for clean edges. Output is 512x512 PNG, which is what Kodi's add-on
browser expects.
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 4                      # supersample factor
W = 512 * S
FONT_BOLD = 'C:/Windows/Fonts/arialbd.ttf'


def font(px):
    return ImageFont.truetype(FONT_BOLD, px * S)


def backdrop(top, bottom, vignette=True):
    """Vertical gradient with an optional darkened rim, so the icon reads as a
    tile even against a light skin background."""
    img = Image.new('RGB', (W, W), top)
    d = ImageDraw.Draw(img)
    for y in range(W):
        t = y / (W - 1)
        d.line([(0, y), (W, y)],
               fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    if vignette:
        v = Image.new('L', (W, W), 0)
        ImageDraw.Draw(v).ellipse([-W // 4, -W // 4, W + W // 4, W + W // 4], fill=255)
        v = v.filter(ImageFilter.GaussianBlur(W // 12))
        img = Image.composite(img, Image.new('RGB', (W, W), (0, 0, 0)), v)
    return img


def glow(size, draw_fn, colour, radius):
    """Soft coloured glow behind a shape."""
    layer = Image.new('L', (size, size), 0)
    draw_fn(ImageDraw.Draw(layer))
    layer = layer.filter(ImageFilter.GaussianBlur(radius))
    tint = Image.new('RGB', (size, size), colour)
    return tint, layer


def centre_text(d, cy, text, f, fill, spacing=0):
    """Draw letter-spaced text centred horizontally."""
    widths = [d.textlength(ch, font=f) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = (W - total) / 2
    for ch, wd in zip(text, widths):
        d.text((x, cy), ch, font=f, fill=fill, anchor='lm')
        x += wd + spacing


def deadlight():
    """A bulb whose filament is broken - the light is dead."""
    CYAN = (79, 216, 208)
    img = backdrop((26, 30, 40), (8, 10, 14))

    # glow behind the bulb
    def g(d):
        d.ellipse([170 * S, 118 * S, 342 * S, 290 * S], fill=190)
    tint, mask = glow(W, g, (40, 150, 150), 42 * S)
    img = Image.composite(tint, img, mask.point(lambda v: min(v, 120)))

    d = ImageDraw.Draw(img)
    lw = 11 * S

    # bulb envelope + neck + screw base
    d.ellipse([170 * S, 118 * S, 342 * S, 290 * S], outline=CYAN, width=lw)
    d.rectangle([222 * S, 286 * S, 290 * S, 322 * S], outline=CYAN, width=lw)
    for i, y in enumerate((330, 352)):
        d.rounded_rectangle([220 * S, y * S, 292 * S, (y + 14) * S],
                            radius=6 * S, outline=CYAN, width=lw)

    # broken filament: two stubs with a conspicuous gap in the middle
    d.line([(214 * S, 250 * S), (232 * S, 196 * S), (246 * S, 226 * S)],
           fill=CYAN, width=lw, joint='curve')
    d.line([(266 * S, 226 * S), (280 * S, 196 * S), (298 * S, 250 * S)],
           fill=CYAN, width=lw, joint='curve')

    centre_text(d, 424 * S, 'DEADLIGHT', font(46), (238, 245, 248), spacing=3 * S)
    return img.resize((512, 512), Image.LANCZOS)


def magneto():
    """A horseshoe magnet - instantly readable at tile size."""
    RED = (214, 58, 58)
    STEEL = (208, 214, 222)
    img = backdrop((30, 26, 30), (12, 9, 12))
    d = ImageDraw.Draw(img)

    # Field lines arc entirely above the magnet. Radii and angular span are chosen
    # so no arc reaches the canvas edge or crosses the poles - a clipped arc reads
    # as a rendering fault rather than as a field line.
    for r in (110, 140, 170):
        d.arc([256 * S - r * S, 190 * S - r * S, 256 * S + r * S, 190 * S + r * S],
              start=238, end=302, fill=(74, 98, 128), width=4 * S)

    lw = 46 * S
    box = [150 * S, 108 * S, 362 * S, 320 * S]
    d.arc(box, start=180, end=360, fill=RED, width=lw)          # the arch
    d.line([(150 * S + lw // 2, 214 * S), (150 * S + lw // 2, 300 * S)], fill=RED, width=lw)
    d.line([(362 * S - lw // 2, 214 * S), (362 * S - lw // 2, 300 * S)], fill=RED, width=lw)
    # steel pole tips
    d.line([(150 * S + lw // 2, 300 * S), (150 * S + lw // 2, 352 * S)], fill=STEEL, width=lw)
    d.line([(362 * S - lw // 2, 300 * S), (362 * S - lw // 2, 352 * S)], fill=STEEL, width=lw)

    centre_text(d, 428 * S, 'MAGNETO', font(44), (236, 240, 244), spacing=3 * S)
    return img.resize((512, 512), Image.LANCZOS)


if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    deadlight().save(out + '/deadlight-icon.png')
    magneto().save(out + '/magneto-icon.png')
    print('  wrote deadlight-icon.png and magneto-icon.png to', out)
