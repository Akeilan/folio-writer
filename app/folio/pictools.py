"""Picture and shape tools: Remove Background, Artistic Effects, Compress
Pictures, WordArt Transform and Merge Shapes."""
import math
import os
import tempfile

from gi.repository import GdkPixbuf, GLib, Gtk

from ._lazy import Lazy, bridge, docapi
from .native import values


def _pil():
    try:
        from PIL import Image  # noqa: F401
        return True
    except Exception:
        return False


# ------------------------------------------------------------ remove background
def background_mask(img, keep=(), remove=(), tolerance=38):
    """A mask (L) of the foreground: background is flood-filled from the image
    edges (and from 'remove' marks) over similar colours; 'keep' marks stay."""
    from PIL import Image
    small = img.convert("RGB")
    w, h = small.size
    scale = 1.0
    if max(w, h) > 400:
        scale = 400.0 / max(w, h)
        small = small.resize((max(1, int(w * scale)), max(1, int(h * scale))))
    sw, sh = small.size
    px = small.load()
    bg = bytearray(sw * sh)
    seeds = []
    for x in range(sw):
        seeds += [(x, 0), (x, sh - 1)]
    for y in range(sh):
        seeds += [(0, y), (sw - 1, y)]
    seeds += [(int(x * sw), int(y * sh)) for x, y in remove]
    keep_px = {(int(x * sw), int(y * sh)) for x, y in keep}
    keep_zone = set()
    for kx, ky in keep_px:
        for dx in range(-8, 9):
            for dy in range(-8, 9):
                keep_zone.add((kx + dx, ky + dy))
    tol2 = tolerance * tolerance
    stack = []
    for sx, sy in seeds:
        if 0 <= sx < sw and 0 <= sy < sh:
            stack.append((sx, sy, px[sx, sy]))
    while stack:
        x, y, ref = stack.pop()
        i = y * sw + x
        if bg[i] or (x, y) in keep_zone:
            continue
        c = px[x, y]
        if (c[0] - ref[0]) ** 2 + (c[1] - ref[1]) ** 2 + (c[2] - ref[2]) ** 2 > tol2:
            continue
        bg[i] = 1
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < sw and 0 <= ny < sh and not bg[ny * sw + nx]:
                stack.append((nx, ny, c))
    mask = Image.frombytes("L", (sw, sh), bytes(0 if b else 255 for b in bg))
    from PIL import ImageFilter
    mask = mask.filter(ImageFilter.MedianFilter(3))
    return mask.resize((w, h), Image.BILINEAR).filter(ImageFilter.GaussianBlur(1))


# ------------------------------------------------------------ artistic effects
EFFECTS = ["None", "Pencil Grayscale", "Pencil Sketch", "Line Drawing", "Blur",
           "Paint Strokes", "Glow Edges", "Mosaic Bubbles", "Cutout", "Emboss",
           "Watercolor Sponge", "Film Grain"]


def apply_effect_image(img, name):
    from PIL import Image, ImageFilter, ImageOps, ImageChops
    rgb = img.convert("RGB")
    alpha = img.getchannel("A") if img.mode == "RGBA" else None
    if name == "Pencil Grayscale":
        g = ImageOps.grayscale(rgb)
        inv = ImageOps.invert(g).filter(ImageFilter.GaussianBlur(6))
        out = ImageChops.add(g, inv, scale=1.0)
        out = ImageOps.autocontrast(Image.blend(g, ImageChops.lighter(g, inv), 0.6))
        out = out.convert("RGB")
    elif name == "Pencil Sketch":
        g = ImageOps.grayscale(rgb)
        blur = ImageOps.invert(g).filter(ImageFilter.GaussianBlur(8))
        out = Image.composite(Image.new("L", g.size, 255), g,
                              ImageOps.invert(blur).point(lambda v: 255 if v > 200 else 0))
        out = ImageOps.grayscale(rgb).filter(ImageFilter.CONTOUR).convert("RGB")
    elif name == "Line Drawing":
        out = ImageOps.invert(ImageOps.grayscale(rgb).filter(ImageFilter.FIND_EDGES))
        out = out.point(lambda v: 255 if v > 210 else 0).convert("RGB")
    elif name == "Blur":
        out = rgb.filter(ImageFilter.GaussianBlur(max(2, rgb.width // 120)))
    elif name == "Paint Strokes":
        out = rgb.filter(ImageFilter.ModeFilter(7)).filter(ImageFilter.SMOOTH_MORE)
    elif name == "Glow Edges":
        out = ImageOps.autocontrast(rgb.filter(ImageFilter.FIND_EDGES)).filter(
            ImageFilter.MaxFilter(3))
    elif name == "Mosaic Bubbles":
        k = max(4, rgb.width // 60)
        out = rgb.resize((max(1, rgb.width // k), max(1, rgb.height // k)),
                         Image.BILINEAR).resize(rgb.size, Image.NEAREST)
    elif name == "Cutout":
        out = ImageOps.posterize(rgb.filter(ImageFilter.ModeFilter(5)), 2)
    elif name == "Emboss":
        out = ImageOps.grayscale(rgb).filter(ImageFilter.EMBOSS).convert("RGB")
    elif name == "Watercolor Sponge":
        out = rgb.filter(ImageFilter.MedianFilter(7)).filter(ImageFilter.SMOOTH_MORE)
        out = ImageOps.posterize(out, 4)
    elif name == "Film Grain":
        import random
        noise = Image.effect_noise(rgb.size, 40).convert("RGB")
        out = Image.blend(rgb, ImageChops.multiply(rgb, noise), 0.25)
        _ = random
    else:
        out = rgb
    out = out.convert("RGBA")
    if alpha is not None:
        out.putalpha(alpha)
    return out


# ------------------------------------------------------------ compress
RESOLUTIONS = [("High fidelity: preserves quality of the original picture", 0),
               ("HD (330 ppi): good quality for high-definition displays", 330),
               ("Print (220 ppi): excellent quality on most printers and screens", 220),
               ("Web (150 ppi): good for web pages and projectors", 150),
               ("E-mail (96 ppi): minimize document size for sharing", 96)]


