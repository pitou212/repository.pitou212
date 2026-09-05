"""Generate add-on artwork.

Kodi renders these small, so everything is built from a few large high-contrast
shapes and drawn at 4x then downsampled for clean edges.

Three distinct surfaces, easy to confuse:
  * <id>/icon.png at the package root  -> the REPOSITORY listing tile
  * <assets><icon> in addon.xml        -> the INSTALLED add-on tile
  * addon_icons/minis/<same filename>  -> in-add-on header logo, matched to the
                                          main icon BY FILENAME (kodi_utils.py
                                          takes basename(addon_info('icon')))
The mini is white-on-transparent because it is composited over the skin's own
background; the icon is opaque because it is a tile.
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 4                       # supersample factor
FONT_BOLD = 'C:/Windows/Fonts/arialbd.ttf'

CYAN = (79, 216, 208)
SILVER = (232, 238, 242)


def font(px):
    return ImageFont.truetype(FONT_BOLD, int(px))


def fit_font(text, target_w):
    """Font sized so `text` renders at target_w. Stacked wordmarks look right
    only when each line is scaled to a common width, which is how the original
    FEN / LITE lockup is built - not by using one size for both lines."""
    lo, hi = 8, 4000
    while lo < hi:
        mid = (lo + hi + 1) // 2
        f = font(mid)
        if f.getbbox(text)[2] - f.getbbox(text)[0] <= target_w:
            lo = mid
        else:
            hi = mid - 1
    return font(lo)


def draw_line(d, text, cx, top, target_w, fill):
    """Draw one wordmark line scaled to target_w, centred on cx. Returns height."""
    f = fit_font(text, target_w)
    b = f.getbbox(text)
    d.text((cx - (b[2] - b[0]) / 2 - b[0], top - b[1]), text, font=f, fill=fill)
    return b[3] - b[1]


def backdrop(size, top, bottom, vignette=True):
    w = size * S
    img = Image.new('RGB', (w, w), top)
    d = ImageDraw.Draw(img)
    for y in range(w):
        t = y / (w - 1)
        d.line([(0, y), (w, y)],
               fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    if vignette:
        v = Image.new('L', (w, w), 0)
        ImageDraw.Draw(v).ellipse([-w // 4, -w // 4, w + w // 4, w + w // 4], fill=255)
        v = v.filter(ImageFilter.GaussianBlur(w // 12))
        img = Image.composite(img, Image.new('RGB', (w, w), (0, 0, 0)), v)
    return img


def wordmark(d, w, colours, target_w_ratio=0.74, top_ratio=0.30):
    """The stacked DEAD / LIGHT lockup, both lines scaled to the same width."""
    target = w * target_w_ratio
    cx = w / 2
    y = w * top_ratio
    h1 = draw_line(d, 'DEAD', cx, y, target, colours[0])
    draw_line(d, 'LIGHT', cx, y + h1 * 1.18, target, colours[1])


# --------------------------------------------------------------- repo listing tile
def deadlight_repo_icon():
    """Bulb mark + wordmark. Used for the repository listing, where it sits in a
    grid beside other add-ons and needs a distinct silhouette rather than text."""
    size, w = 512, 512 * S
    img = backdrop(size, (26, 30, 40), (8, 10, 14))

    layer = Image.new('L', (w, w), 0)
    ImageDraw.Draw(layer).ellipse([170 * S, 118 * S, 342 * S, 290 * S], fill=190)
    layer = layer.filter(ImageFilter.GaussianBlur(42 * S))
    img = Image.composite(Image.new('RGB', (w, w), (40, 150, 150)), img,
                          layer.point(lambda v: min(v, 120)))

    d = ImageDraw.Draw(img)
    lw = 11 * S
    d.ellipse([170 * S, 118 * S, 342 * S, 290 * S], outline=CYAN, width=lw)
    d.rectangle([222 * S, 286 * S, 290 * S, 322 * S], outline=CYAN, width=lw)
    for y in (330, 352):
        d.rounded_rectangle([220 * S, y * S, 292 * S, (y + 14) * S],
                            radius=6 * S, outline=CYAN, width=lw)
    d.line([(214 * S, 250 * S), (232 * S, 196 * S), (246 * S, 226 * S)],
           fill=CYAN, width=lw, joint='curve')
    d.line([(266 * S, 226 * S), (280 * S, 196 * S), (298 * S, 250 * S)],
           fill=CYAN, width=lw, joint='curve')

    f = fit_font('DEADLIGHT', w * 0.62)
    b = f.getbbox('DEADLIGHT')
    d.text((w / 2 - (b[2] - b[0]) / 2 - b[0], 400 * S - b[1]), 'DEADLIGHT', font=f, fill=SILVER)
    return img.resize((size, size), Image.LANCZOS)


# ------------------------------------------------------------- installed-addon tile
def deadlight_addon_icon():
    """Opaque tile, stacked wordmark - matches the FEN / LITE lockup it replaces."""
    size, w = 512, 512 * S
    img = backdrop(size, (22, 26, 34), (6, 8, 11))
    d = ImageDraw.Draw(img)
    wordmark(d, w, (SILVER, CYAN))
    return img.resize((size, size), Image.LANCZOS)


# ------------------------------------------------------------------ in-addon header
def deadlight_mini():
    """Pure white on TRANSPARENT: this is composited over the skin's background,
    so it must carry no tile of its own and no colour that could clash."""
    size, w = 512, 512 * S
    img = Image.new('RGBA', (w, w), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    wordmark(d, w, ((255, 255, 255, 255), (255, 255, 255, 255)))
    return img.resize((size, size), Image.LANCZOS)


# ------------------------------------------------------------------------- fanart
def deadlight_fanart():
    """1920x1200 background art. Deliberately low-contrast and off-centre: skins
    lay text and widgets over this, so it must not compete with them."""
    W, H = 1920 * 2, 1200 * 2
    img = Image.new('RGB', (W, H), (10, 12, 16))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(int(18 - 8 * t), int(22 - 10 * t), int(30 - 14 * t)))

    glow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(glow).ellipse([W * 0.60, H * 0.10, W * 0.94, H * 0.78], fill=90)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    img = Image.composite(Image.new('RGB', (W, H), (30, 110, 110)), img, glow)

    d = ImageDraw.Draw(img)
    cx, cy, r = W * 0.77, H * 0.40, H * 0.20
    lw = int(H * 0.012)
    dim = (44, 92, 96)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=dim, width=lw)
    d.rectangle([cx - r * 0.30, cy + r * 0.96, cx + r * 0.30, cy + r * 1.22], outline=dim, width=lw)
    for i in (1.30, 1.46):
        d.rounded_rectangle([cx - r * 0.32, cy + r * i, cx + r * 0.32, cy + r * (i + 0.11)],
                            radius=lw, outline=dim, width=lw)
    d.line([(cx - r * 0.48, cy + r * 0.32), (cx - r * 0.20, cy - r * 0.30), (cx + r * 0.02, cy + r * 0.06)],
           fill=dim, width=lw, joint='curve')
    d.line([(cx + r * 0.18, cy + r * 0.06), (cx + r * 0.34, cy - r * 0.30), (cx + r * 0.56, cy + r * 0.32)],
           fill=dim, width=lw, joint='curve')

    f = fit_font('DEADLIGHT', W * 0.34)
    b = f.getbbox('DEADLIGHT')
    d.text((W * 0.07, H * 0.44 - b[1]), 'DEADLIGHT', font=f, fill=(206, 216, 224))
    f2 = fit_font('KODI VIDEO ADD-ON', W * 0.20)
    d.text((W * 0.075, H * 0.60), 'KODI VIDEO ADD-ON', font=f2, fill=(96, 116, 130))
    return img.resize((1920, 1200), Image.LANCZOS)


# ------------------------------------------------------------------------- magneto
def magneto_repo_icon():
    size, w = 512, 512 * S
    RED, STEEL = (214, 58, 58), (208, 214, 222)
    img = backdrop(size, (30, 26, 30), (12, 9, 12))
    d = ImageDraw.Draw(img)
    for r in (110, 140, 170):
        d.arc([256 * S - r * S, 190 * S - r * S, 256 * S + r * S, 190 * S + r * S],
              start=238, end=302, fill=(74, 98, 128), width=4 * S)
    lw = 46 * S
    d.arc([150 * S, 108 * S, 362 * S, 320 * S], start=180, end=360, fill=RED, width=lw)
    for x in (150 * S + lw // 2, 362 * S - lw // 2):
        d.line([(x, 214 * S), (x, 300 * S)], fill=RED, width=lw)
        d.line([(x, 300 * S), (x, 352 * S)], fill=STEEL, width=lw)
    f = fit_font('MAGNETO', w * 0.60)
    b = f.getbbox('MAGNETO')
    d.text((w / 2 - (b[2] - b[0]) / 2 - b[0], 404 * S - b[1]), 'MAGNETO', font=f, fill=(236, 240, 244))
    return img.resize((size, size), Image.LANCZOS)


TARGETS = {
    'deadlight-repo-icon.png':  (deadlight_repo_icon, 'PNG'),
    'deadlight-addon-icon.png': (deadlight_addon_icon, 'PNG'),
    'deadlight-mini.png':       (deadlight_mini, 'PNG'),
    'deadlight-fanart.jpg':     (deadlight_fanart, 'JPEG'),
    'magneto-repo-icon.png':    (magneto_repo_icon, 'PNG'),
}



# ---------------------------------------------------------------- extra variants
# New FILENAMES, never redesigns of existing ones: Kodi caches textures by path,
# so changing an icon's content in place leaves the old image on screen.

def _bulb(d, w, cx, cy, r, colour, lw, filament=True):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=colour, width=lw)
    d.rectangle([cx - r * 0.40, cy + r * 0.98, cx + r * 0.40, cy + r * 1.20], outline=colour, width=lw)
    for i in (1.28, 1.44):
        d.rounded_rectangle([cx - r * 0.42, cy + r * i, cx + r * 0.42, cy + r * (i + 0.10)],
                            radius=lw, outline=colour, width=lw)
    if filament:
        d.line([(cx - r * 0.52, cy + r * 0.34), (cx - r * 0.22, cy - r * 0.32), (cx + r * 0.02, cy + r * 0.06)],
               fill=colour, width=lw, joint='curve')
        d.line([(cx + r * 0.18, cy + r * 0.06), (cx + r * 0.36, cy - r * 0.32), (cx + r * 0.60, cy + r * 0.34)],
               fill=colour, width=lw, joint='curve')


def _glowed(img, w, box, colour, radius, cap=120):
    layer = Image.new('L', (w, w), 0)
    ImageDraw.Draw(layer).ellipse(box, fill=200)
    layer = layer.filter(ImageFilter.GaussianBlur(radius))
    return Image.composite(Image.new('RGB', (w, w), colour), img, layer.point(lambda v: min(v, cap)))


def icon_bulb_only():
    """No text - reads best at the smallest tile sizes."""
    size, w = 512, 512 * S
    img = backdrop(size, (24, 28, 38), (7, 9, 13))
    img = _glowed(img, w, [130 * S, 110 * S, 382 * S, 362 * S], (36, 140, 140), 46 * S)
    _bulb(ImageDraw.Draw(img), w, 256 * S, 224 * S, 118 * S, CYAN, 13 * S)
    return img.resize((size, size), Image.LANCZOS)


def icon_monogram():
    size, w = 512, 512 * S
    img = backdrop(size, (24, 28, 38), (7, 9, 13))
    d = ImageDraw.Draw(img)
    f = fit_font('DL', w * 0.56)
    b = f.getbbox('DL')
    d.text((w / 2 - (b[2] - b[0]) / 2 - b[0], w / 2 - (b[3] - b[1]) / 2 - b[1]), 'DL', font=f, fill=CYAN)
    return img.resize((size, size), Image.LANCZOS)


def icon_inverted():
    """Cyan field, dark mark - stands out in a grid of dark tiles."""
    size, w = 512, 512 * S
    img = Image.new('RGB', (w, w), (64, 198, 190))
    d = ImageDraw.Draw(img)
    for y in range(w):
        t = y / (w - 1)
        d.line([(0, y), (w, y)], fill=(int(72 - 20 * t), int(206 - 46 * t), int(198 - 42 * t)))
    wordmark(d, w, ((10, 26, 30), (10, 26, 30)))
    return img.resize((size, size), Image.LANCZOS)


def icon_solid_bulb():
    size, w = 512, 512 * S
    img = backdrop(size, (20, 24, 32), (6, 8, 11))
    d = ImageDraw.Draw(img)
    cx, cy, r = 256 * S, 226 * S, 116 * S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CYAN)
    d.rectangle([cx - r * 0.40, cy + r * 0.96, cx + r * 0.40, cy + r * 1.20], fill=CYAN)
    for i in (1.28, 1.44):
        d.rounded_rectangle([cx - r * 0.42, cy + r * i, cx + r * 0.42, cy + r * (i + 0.10)],
                            radius=8 * S, fill=CYAN)
    d.line([(cx - r * 0.48, cy + r * 0.30), (cx - r * 0.20, cy - r * 0.30), (cx + r * 0.02, cy + r * 0.04)],
           fill=(12, 30, 34), width=12 * S, joint='curve')
    d.line([(cx + r * 0.18, cy + r * 0.04), (cx + r * 0.34, cy - r * 0.30), (cx + r * 0.56, cy + r * 0.30)],
           fill=(12, 30, 34), width=12 * S, joint='curve')
    return img.resize((size, size), Image.LANCZOS)


def icon_wordmark_plain():
    """All-white, no accent - neutral against any skin colour scheme."""
    size, w = 512, 512 * S
    img = backdrop(size, (18, 20, 26), (5, 6, 9), vignette=False)
    wordmark(ImageDraw.Draw(img), w, (SILVER, SILVER))
    return img.resize((size, size), Image.LANCZOS)


def icon_light():
    """Light tile, for pale skins where a dark square looks like a hole."""
    size, w = 512, 512 * S
    img = Image.new('RGB', (w, w), (238, 242, 245))
    d = ImageDraw.Draw(img)
    _bulb(d, w, 256 * S, 200 * S, 92 * S, (28, 150, 146), 11 * S)
    f = fit_font('DEADLIGHT', w * 0.62)
    b = f.getbbox('DEADLIGHT')
    d.text((w / 2 - (b[2] - b[0]) / 2 - b[0], 396 * S - b[1]), 'DEADLIGHT', font=f, fill=(24, 34, 42))
    return img.resize((size, size), Image.LANCZOS)


def _fanart_base(W, H, top, bottom):
    img = Image.new('RGB', (W, H), top)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)],
               fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


def fanart_left():
    W, H = 1920 * 2, 1200 * 2
    img = _fanart_base(W, H, (20, 24, 32), (8, 10, 14))
    glow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(glow).ellipse([W * 0.04, H * 0.10, W * 0.38, H * 0.78], fill=90)
    img = Image.composite(Image.new('RGB', (W, H), (28, 104, 104)), img,
                          glow.filter(ImageFilter.GaussianBlur(160)))
    d = ImageDraw.Draw(img)
    _bulb(d, W, W * 0.21, H * 0.40, H * 0.19, (44, 92, 96), int(H * 0.012))
    f = fit_font('DEADLIGHT', W * 0.30)
    b = f.getbbox('DEADLIGHT')
    d.text((W * 0.46, H * 0.46 - b[1]), 'DEADLIGHT', font=f, fill=(202, 213, 222))
    return img.resize((1920, 1200), Image.LANCZOS)


def fanart_minimal():
    """Almost empty - the safest background under dense widget layouts."""
    W, H = 1920 * 2, 1200 * 2
    img = _fanart_base(W, H, (16, 19, 25), (7, 8, 11))
    d = ImageDraw.Draw(img)
    f = fit_font('DEADLIGHT', W * 0.14)
    d.text((W * 0.05, H * 0.88), 'DEADLIGHT', font=f, fill=(58, 70, 80))
    return img.resize((1920, 1200), Image.LANCZOS)


def fanart_centre():
    """Large, very dim bulb - texture without competing with overlaid text."""
    W, H = 1920 * 2, 1200 * 2
    img = _fanart_base(W, H, (18, 22, 29), (6, 8, 11))
    glow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(glow).ellipse([W * 0.30, -H * 0.10, W * 0.70, H * 0.86], fill=70)
    img = Image.composite(Image.new('RGB', (W, H), (26, 92, 96)), img,
                          glow.filter(ImageFilter.GaussianBlur(220)))
    _bulb(ImageDraw.Draw(img), W, W * 0.50, H * 0.38, H * 0.24, (34, 68, 74), int(H * 0.010))
    return img.resize((1920, 1200), Image.LANCZOS)


TARGETS.update({
    'deadlight_icon_11.png': (icon_bulb_only, 'PNG'),
    'deadlight_icon_12.png': (icon_monogram, 'PNG'),
    'deadlight_icon_13.png': (icon_inverted, 'PNG'),
    'deadlight_icon_14.png': (icon_solid_bulb, 'PNG'),
    'deadlight_icon_15.png': (icon_wordmark_plain, 'PNG'),
    'deadlight_icon_16.png': (icon_light, 'PNG'),
    'deadlight_fanart_02.jpg': (fanart_left, 'JPEG'),
    'deadlight_fanart_03.jpg': (fanart_minimal, 'JPEG'),
    'deadlight_fanart_04.jpg': (fanart_centre, 'JPEG'),
})


if __name__ == '__main__':
    import sys, os
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    only = sys.argv[2:] if len(sys.argv) > 2 else None
    for name, (fn, fmt) in TARGETS.items():
        if only and name not in only:
            continue
        img = fn()
        p = os.path.join(out, name)
        if fmt == 'JPEG':
            img.save(p, quality=88, optimize=True)
        else:
            img.save(p)
        print('  %-26s %sx%s  %d bytes' % (name, img.width, img.height, os.path.getsize(p)))
