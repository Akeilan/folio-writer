"""Folio Page's own vector icons, drawn with cairo on a 24x24 grid in the suite's style
(as Folio Draw's): dark ink outlines, white paper, Writer's hunter green as the accent.
Keyed by command name (the LibreOffice-style names the ribbon uses: 'bold', 'insertfootnote')."""
import math

INK = (0.22, 0.22, 0.24)
ACC = (0.18, 0.42, 0.25)        # hunter green
ACC_LIGHT = (0.80, 0.89, 0.82)
RED = (0.78, 0.16, 0.14)
GOLD = (0.93, 0.70, 0.16)
BLUE = (0.20, 0.45, 0.75)
PAPER = (1, 1, 1)
GREY = (0.62, 0.62, 0.64)
PALE = (0.90, 0.90, 0.91)


# ------------------------------------------------------------------ primitives
def _rgb(cr, c):
    cr.set_source_rgb(*c)


def page(cr, x=4.5, y=2.5, w=15, h=19, fold=4, fill=PAPER, ink=INK):
    cr.move_to(x, y)
    cr.line_to(x + w - fold, y)
    cr.line_to(x + w, y + fold)
    cr.line_to(x + w, y + h)
    cr.line_to(x, y + h)
    cr.close_path()
    _rgb(cr, fill)
    cr.fill_preserve()
    _rgb(cr, ink)
    cr.stroke()
    if fold:
        cr.move_to(x + w - fold, y)
        cr.line_to(x + w - fold, y + fold)
        cr.line_to(x + w, y + fold)
        cr.stroke()


def rect(cr, x, y, w, h, fill=PAPER, ink=INK):
    cr.rectangle(x, y, w, h)
    if fill is not None:
        _rgb(cr, fill)
        cr.fill_preserve()
    if ink is not None:
        _rgb(cr, ink)
        cr.stroke()
    else:
        cr.new_path()


def rrect(cr, x, y, w, h, r, fill=PAPER, ink=INK):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    cr.close_path()
    if fill is not None:
        _rgb(cr, fill)
        cr.fill_preserve()
    if ink is not None:
        _rgb(cr, ink)
        cr.stroke()
    else:
        cr.new_path()


def bar(cr, x, y, w, h=1.2, col=INK):
    cr.rectangle(x, y, w, h)
    _rgb(cr, col)
    cr.fill()


def lines(cr, x, y, widths, gap=3.0, col=INK, h=1.2):
    for i, w in enumerate(widths):
        if w:
            bar(cr, x, y + i * gap, w, h, col)


def text_lines(cr, x=7, y=7, w=10, n=4, gap=3, col=GREY, last=0.6):
    ws = [w] * (n - 1) + [w * last]
    lines(cr, x, y, ws, gap, col)


def line(cr, x0, y0, x1, y1, col=INK, w=None):
    if w:
        cr.save()
        cr.set_line_width(w)
    cr.move_to(x0, y0)
    cr.line_to(x1, y1)
    _rgb(cr, col)
    cr.stroke()
    if w:
        cr.restore()


def circle(cr, cx, cy, r, fill=None, ink=INK):
    cr.new_sub_path()
    cr.arc(cx, cy, r, 0, math.tau)
    if fill is not None:
        _rgb(cr, fill)
        cr.fill_preserve()
    if ink is not None:
        _rgb(cr, ink)
        cr.stroke()
    else:
        cr.new_path()


def letter(cr, ch, x, y, size, col=INK, bold=False, italic=False, family="Sans", underline=False):
    cr.save()
    cr.select_font_face(family, 1 if italic else 0, 1 if bold else 0)
    cr.set_font_size(size)
    cr.move_to(x, y)
    _rgb(cr, col)
    cr.show_text(ch)
    if underline:
        ext = cr.text_extents(ch)
        cr.rectangle(x, y + 1.2, ext.x_advance, 1.3)
        cr.fill()
    cr.restore()


def centred(cr, ch, cx, y, size, col=INK, bold=False, italic=False, family="Sans"):
    cr.save()
    cr.select_font_face(family, 1 if italic else 0, 1 if bold else 0)
    cr.set_font_size(size)
    ext = cr.text_extents(ch)
    cr.move_to(cx - ext.width / 2 - ext.x_bearing, y)
    _rgb(cr, col)
    cr.show_text(ch)
    cr.restore()


def badge_plus(cr, cx=18, cy=18, r=4.2, col=ACC):
    circle(cr, cx, cy, r, fill=col, ink=None)
    cr.save()
    cr.set_line_width(1.6)
    _rgb(cr, PAPER)
    cr.move_to(cx - 2.2, cy)
    cr.line_to(cx + 2.2, cy)
    cr.move_to(cx, cy - 2.2)
    cr.line_to(cx, cy + 2.2)
    cr.stroke()
    cr.restore()


def badge_minus(cr, cx=18, cy=18, r=4.2, col=RED):
    circle(cr, cx, cy, r, fill=col, ink=None)
    cr.save()
    cr.set_line_width(1.6)
    _rgb(cr, PAPER)
    cr.move_to(cx - 2.2, cy)
    cr.line_to(cx + 2.2, cy)
    cr.stroke()
    cr.restore()


def badge_x(cr, cx=18, cy=18, r=4.2, col=RED):
    circle(cr, cx, cy, r, fill=col, ink=None)
    cr.save()
    cr.set_line_width(1.5)
    _rgb(cr, PAPER)
    d = 1.8
    cr.move_to(cx - d, cy - d)
    cr.line_to(cx + d, cy + d)
    cr.move_to(cx + d, cy - d)
    cr.line_to(cx - d, cy + d)
    cr.stroke()
    cr.restore()


def badge_check(cr, cx=18, cy=18, r=4.2, col=ACC):
    circle(cr, cx, cy, r, fill=col, ink=None)
    cr.save()
    cr.set_line_width(1.5)
    _rgb(cr, PAPER)
    cr.move_to(cx - 2.2, cy)
    cr.line_to(cx - 0.6, cy + 1.8)
    cr.line_to(cx + 2.4, cy - 1.8)
    cr.stroke()
    cr.restore()


def check_mark(cr, x, y, s=6, col=ACC, w=2.0):
    cr.save()
    cr.set_line_width(w)
    _rgb(cr, col)
    cr.move_to(x, y)
    cr.line_to(x + s * 0.38, y + s * 0.38)
    cr.line_to(x + s, y - s * 0.5)
    cr.stroke()
    cr.restore()


def x_mark(cr, cx, cy, d=3, col=RED, w=2.0):
    cr.save()
    cr.set_line_width(w)
    _rgb(cr, col)
    cr.move_to(cx - d, cy - d)
    cr.line_to(cx + d, cy + d)
    cr.move_to(cx + d, cy - d)
    cr.line_to(cx - d, cy + d)
    cr.stroke()
    cr.restore()


def arrow(cr, x0, y0, x1, y1, col=ACC, head=3.0, w=1.6):
    cr.save()
    cr.set_line_width(w)
    _rgb(cr, col)
    cr.move_to(x0, y0)
    cr.line_to(x1, y1)
    cr.stroke()
    a = math.atan2(y1 - y0, x1 - x0)
    cr.move_to(x1, y1)
    cr.line_to(x1 - head * math.cos(a - 0.5), y1 - head * math.sin(a - 0.5))
    cr.line_to(x1 - head * math.cos(a + 0.5), y1 - head * math.sin(a + 0.5))
    cr.close_path()
    cr.fill()
    cr.restore()


def tri(cr, x, y, s, direction, col=ACC):
    """A small solid triangle pointing up/down/left/right."""
    _rgb(cr, col)
    if direction == "up":
        cr.move_to(x, y + s)
        cr.line_to(x + s, y + s)
        cr.line_to(x + s / 2, y)
    elif direction == "down":
        cr.move_to(x, y)
        cr.line_to(x + s, y)
        cr.line_to(x + s / 2, y + s)
    elif direction == "left":
        cr.move_to(x + s, y)
        cr.line_to(x + s, y + s)
        cr.line_to(x, y + s / 2)
    else:
        cr.move_to(x, y)
        cr.line_to(x, y + s)
        cr.line_to(x + s, y + s / 2)
    cr.close_path()
    cr.fill()


def table(cr, x, y, w, h, rows, cols, header=True, ink=INK):
    rect(cr, x, y, w, h, PAPER, ink)
    if header:
        cr.rectangle(x, y, w, h / rows)
        _rgb(cr, ACC_LIGHT)
        cr.fill()
        rect(cr, x, y, w, h, None, ink)
    _rgb(cr, ink)
    for r in range(1, rows):
        cr.move_to(x, y + h * r / rows)
        cr.line_to(x + w, y + h * r / rows)
    for c in range(1, cols):
        cr.move_to(x + w * c / cols, y)
        cr.line_to(x + w * c / cols, y + h)
    cr.stroke()


def picture(cr, x, y, w, h, ink=INK):
    rect(cr, x, y, w, h, PAPER, ink)
    cr.save()
    cr.rectangle(x + 0.6, y + 0.6, w - 1.2, h - 1.2)
    cr.clip()
    _rgb(cr, (0.55, 0.75, 0.55))
    cr.move_to(x, y + h)
    cr.line_to(x + w * 0.35, y + h * 0.45)
    cr.line_to(x + w * 0.6, y + h * 0.75)
    cr.line_to(x + w * 0.75, y + h * 0.6)
    cr.line_to(x + w, y + h * 0.9)
    cr.line_to(x + w, y + h)
    cr.close_path()
    cr.fill()
    cr.restore()
    circle(cr, x + w * 0.75, y + h * 0.3, min(w, h) * 0.12, fill=GOLD, ink=None)


def pencil(cr, x=13, y=19, length=10, col=GOLD):
    """A pencil from its tip at (x, y), pointing down-left."""
    cr.save()
    cr.translate(x, y)
    cr.rotate(-math.pi / 4)
    cr.rectangle(2.5, -1.6, length, 3.2)
    _rgb(cr, col)
    cr.fill_preserve()
    _rgb(cr, INK)
    cr.stroke()
    cr.move_to(0, 0)
    cr.line_to(2.5, -1.6)
    cr.line_to(2.5, 1.6)
    cr.close_path()
    _rgb(cr, (0.95, 0.85, 0.7))
    cr.fill_preserve()
    _rgb(cr, INK)
    cr.stroke()
    cr.restore()


def magnifier(cr, cx=10, cy=10, r=5, col=INK):
    circle(cr, cx, cy, r, fill=(0.93, 0.97, 1.0), ink=col)
    cr.save()
    cr.set_line_width(2.4)
    _rgb(cr, col)
    d = r * 0.72
    cr.move_to(cx + d, cy + d)
    cr.line_to(cx + d + 5, cy + d + 5)
    cr.stroke()
    cr.restore()


def envelope(cr, x, y, w, h, fill=PAPER):
    rect(cr, x, y, w, h, fill, INK)
    cr.move_to(x, y)
    cr.line_to(x + w / 2, y + h * 0.55)
    cr.line_to(x + w, y)
    _rgb(cr, INK)
    cr.stroke()


def bubble(cr, x, y, w, h, fill=GOLD):
    rrect(cr, x, y, w, h, 2, fill, INK)
    cr.move_to(x + 3, y + h)
    cr.line_to(x + 2.5, y + h + 3.5)
    cr.line_to(x + 6.5, y + h)
    _rgb(cr, fill)
    cr.fill_preserve()
    _rgb(cr, INK)
    cr.stroke()


def person(cr, cx, cy, s=1.0, col=ACC):
    circle(cr, cx, cy - 3.2 * s, 2.4 * s, fill=col, ink=None)
    cr.new_sub_path()
    cr.arc(cx, cy + 4.5 * s, 4.5 * s, math.pi, 0)
    cr.close_path()
    _rgb(cr, col)
    cr.fill()


def chain(cr, x, y):
    cr.save()
    cr.set_line_width(1.8)
    _rgb(cr, ACC)
    for dx in (0, 6):
        rrect(cr, x + dx, y, 8, 4.5, 2.2, None, ACC)
    cr.restore()


def brush(cr, x=4, y=4):
    rrect(cr, x, y, 13, 5, 1, GOLD, INK)
    rect(cr, x + 5.5, y + 5, 2.4, 3, INK, INK)
    rect(cr, x + 5, y + 8, 3.4, 9, (0.62, 0.42, 0.25), INK)


def bucket(cr, x=4, y=6):
    cr.move_to(x + 2, y + 2)
    cr.line_to(x + 11, y + 2)
    cr.line_to(x + 10, y + 12)
    cr.line_to(x + 3, y + 12)
    cr.close_path()
    _rgb(cr, PAPER)
    cr.fill_preserve()
    _rgb(cr, INK)
    cr.stroke()
    cr.move_to(x + 11, y + 4)
    cr.curve_to(x + 15, y + 5, x + 15, y + 9, x + 14, y + 11)
    _rgb(cr, BLUE)
    cr.stroke()


def color_bar(cr, col=RED, y=19.5, x=3, w=18, h=3):
    cr.rectangle(x, y, w, h)
    _rgb(cr, col)
    cr.fill()


def window(cr, x, y, w, h, title=ACC):
    rect(cr, x, y, w, h, PAPER, INK)
    cr.rectangle(x + 0.6, y + 0.6, w - 1.2, 2.4)
    _rgb(cr, title)
    cr.fill()


def disk(cr, x=4, y=4, w=16):
    rrect(cr, x, y, w, w, 1.5, ACC, INK)
    rect(cr, x + 3, y + 0.6, w - 6, 5, PAPER, None)
    rect(cr, x + 2.5, y + w - 6.5, w - 5, 6, PALE, None)


def folder(cr, x=3, y=6, w=18, h=13):
    cr.move_to(x, y)
    cr.line_to(x + 6, y)
    cr.line_to(x + 8, y + 2)
    cr.line_to(x + w, y + 2)
    cr.line_to(x + w, y + h)
    cr.line_to(x, y + h)
    cr.close_path()
    _rgb(cr, GOLD)
    cr.fill_preserve()
    _rgb(cr, INK)
    cr.stroke()


def printer(cr, x=3, y=7):
    rect(cr, x + 3, y - 4, 12, 5, PAPER, INK)
    rrect(cr, x, y, 18, 8, 1.5, PALE, INK)
    rect(cr, x + 3, y + 5, 12, 7, PAPER, INK)
    lines(cr, x + 5, y + 8, [8, 6], 2.0, GREY, 1)
    circle(cr, x + 15, y + 2.5, 0.9, fill=ACC, ink=None)


def lock(cr, x=7, y=11):
    cr.new_sub_path()
    cr.arc(x + 5, y, 3.5, math.pi, 0)
    _rgb(cr, INK)
    cr.stroke()
    rrect(cr, x, y, 10, 8, 1, GOLD, INK)
    circle(cr, x + 5, y + 4, 1.1, fill=INK, ink=None)


def gear(cr, cx, cy, r=5, col=GREY):
    cr.save()
    _rgb(cr, col)
    for i in range(8):
        a = i * math.tau / 8
        cr.save()
        cr.translate(cx, cy)
        cr.rotate(a)
        cr.rectangle(-1.2, -r - 1.6, 2.4, 2.4)
        cr.restore()
    cr.fill()
    circle(cr, cx, cy, r, fill=col, ink=None)
    circle(cr, cx, cy, r * 0.4, fill=PAPER, ink=None)
    cr.restore()


def clock(cr, cx, cy, r=5):
    circle(cr, cx, cy, r, fill=PAPER, ink=INK)
    cr.move_to(cx, cy - r * 0.6)
    cr.line_to(cx, cy)
    cr.line_to(cx + r * 0.5, cy + r * 0.2)
    _rgb(cr, ACC)
    cr.stroke()


def calendar(cr, x=4, y=4, w=16, h=16):
    rect(cr, x, y, w, h, PAPER, INK)
    cr.rectangle(x + 0.6, y + 0.6, w - 1.2, 3.5)
    _rgb(cr, ACC)
    cr.fill()
    _rgb(cr, GREY)
    for r in range(3):
        for c in range(4):
            cr.rectangle(x + 2 + c * 3.4, y + 6 + r * 3.2, 2, 2)
    cr.fill()


def globe(cr, cx, cy, r=6):
    circle(cr, cx, cy, r, fill=(0.85, 0.93, 0.98), ink=BLUE)
    _rgb(cr, BLUE)
    cr.save()
    cr.translate(cx, cy)
    cr.scale(0.45, 1)
    cr.arc(0, 0, r, 0, math.tau)
    cr.restore()
    cr.move_to(cx - r, cy)
    cr.line_to(cx + r, cy)
    cr.stroke()


def star(cr, cx, cy, r, col=GOLD):
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        (cr.move_to if i == 0 else cr.line_to)(cx + rr * math.cos(a), cy + rr * math.sin(a))
    cr.close_path()
    _rgb(cr, col)
    cr.fill_preserve()
    _rgb(cr, INK)
    cr.stroke()


def flag(cr, x, y, col=RED):
    line(cr, x, y, x, y + 14)
    cr.move_to(x, y)
    cr.line_to(x + 9, y + 2.5)
    cr.line_to(x, y + 6)
    cr.close_path()
    _rgb(cr, col)
    cr.fill()


def ribbon_mark(cr, x, y, w=6, h=10, col=ACC):
    cr.move_to(x, y)
    cr.line_to(x + w, y)
    cr.line_to(x + w, y + h)
    cr.line_to(x + w / 2, y + h - 2.5)
    cr.line_to(x, y + h)
    cr.close_path()
    _rgb(cr, col)
    cr.fill()


def eye(cr, cx, cy, r=7):
    cr.move_to(cx - r, cy)
    cr.curve_to(cx - r / 2, cy - r * 0.7, cx + r / 2, cy - r * 0.7, cx + r, cy)
    cr.curve_to(cx + r / 2, cy + r * 0.7, cx - r / 2, cy + r * 0.7, cx - r, cy)
    _rgb(cr, PAPER)
    cr.fill_preserve()
    _rgb(cr, INK)
    cr.stroke()
    circle(cr, cx, cy, r * 0.35, fill=ACC, ink=None)


def chart_bars(cr, x=4, y=4, w=16, h=16, cols=(ACC, BLUE, GOLD)):
    line(cr, x, y, x, y + h)
    line(cr, x, y + h, x + w, y + h)
    hs = (0.55, 0.85, 0.4)
    for i, (hh, c) in enumerate(zip(hs, cols)):
        cr.rectangle(x + 2 + i * 4.6, y + h - h * hh, 3.4, h * hh - 0.6)
        _rgb(cr, c)
        cr.fill()


# ------------------------------------------------------------------ the icons
ICONS = {}


def icon(*names):
    def deco(fn):
        for n in names:
            ICONS[n] = fn
        return fn
    return deco


# --- clipboard
@icon("paste")
def i_paste(cr):
    rrect(cr, 3.5, 4.5, 13, 17, 1.5, (0.85, 0.72, 0.55), INK)
    rrect(cr, 7, 2.5, 6, 4, 1, PALE, INK)
    page(cr, 10.5, 9.5, 11, 13, 3)
    lines(cr, 12.5, 14, [7, 7, 5], 2.6, ACC)


@icon("pastespecial")
def i_pastespecial(cr):
    i_paste(cr)
    star(cr, 17.5, 17.5, 3.2)


@icon("pasteunformatted")
def i_pasteunformatted(cr):
    rrect(cr, 3.5, 4.5, 13, 17, 1.5, (0.85, 0.72, 0.55), INK)
    rrect(cr, 7, 2.5, 6, 4, 1, PALE, INK)
    page(cr, 10.5, 9.5, 11, 13, 3)
    centred(cr, "A", 16, 20, 8, INK)


@icon("cut")
def i_cut(cr):
    line(cr, 8.5, 3, 15, 15)
    line(cr, 15.5, 3, 9, 15)
    cr.save()
    cr.set_line_width(1.6)
    circle(cr, 7, 18, 3, None, ACC)
    circle(cr, 17, 18, 3, None, ACC)
    cr.restore()


@icon("copy")
def i_copy(cr):
    page(cr, 3.5, 2.5, 11, 14, 3)
    page(cr, 9.5, 7.5, 11, 14, 3)
    lines(cr, 11.5, 12, [7, 7, 5], 2.8, ACC)


@icon("formatpaintbrush")
def i_formatpaintbrush(cr):
    brush(cr, 4, 3)


@icon("selectall", "selectobject", "drawselect")
def i_selectall(cr):
    cr.save()
    cr.set_dash([1.5, 1.5])
    rect(cr, 3.5, 3.5, 17, 17, None, INK)
    cr.restore()
    cr.move_to(8, 7)
    cr.line_to(8, 19)
    cr.line_to(11, 16)
    cr.line_to(13.5, 20.5)
    cr.line_to(15.5, 19.5)
    cr.line_to(13, 15)
    cr.line_to(17, 15)
    cr.close_path()
    _rgb(cr, PAPER)
    cr.fill_preserve()
    _rgb(cr, INK)
    cr.stroke()


# --- font
@icon("bold")
def i_bold(cr):
    centred(cr, "B", 12, 18, 16, INK, bold=True)


@icon("italic")
def i_italic(cr):
    centred(cr, "I", 12, 18, 16, INK, italic=True, family="Serif")


@icon("underline")
def i_underline(cr):
    centred(cr, "U", 12, 16.5, 14, INK)
    bar(cr, 6, 19.5, 12, 1.6, INK)


@icon("strikeout")
def i_strikeout(cr):
    centred(cr, "abc", 12, 16, 10, INK)
    bar(cr, 3.5, 12.4, 17, 1.4, RED)


@icon("subscript")
def i_subscript(cr):
    letter(cr, "x", 4, 15, 13, INK)
    letter(cr, "2", 13, 20, 8, ACC, bold=True)


@icon("superscript")
def i_superscript(cr):
    letter(cr, "x", 4, 19, 13, INK)
    letter(cr, "2", 13, 10, 8, ACC, bold=True)


@icon("grow")
def i_grow(cr):
    letter(cr, "A", 2.5, 19, 15, INK)
    tri(cr, 16, 4, 5, "up", ACC)


@icon("shrink")
def i_shrink(cr):
    letter(cr, "A", 2.5, 19, 12, INK)
    tri(cr, 15, 5, 5, "down", ACC)


@icon("fontcolor", "color")
def i_fontcolor(cr):
    centred(cr, "A", 12, 16, 14, INK)
    color_bar(cr, RED, 18.5, 4, 16, 3.5)


@icon("charbackcolor")
def i_charbackcolor(cr):
    cr.save()
    cr.translate(12, 11)
    cr.rotate(math.pi / 4)
    rect(cr, -2.5, -8, 5, 11, PAPER, INK)
    cr.move_to(-2.5, 3)
    cr.line_to(0, 6)
    cr.line_to(2.5, 3)
    _rgb(cr, INK)
    cr.stroke()
    cr.restore()
    color_bar(cr, (1.0, 0.95, 0.0), 18.5, 4, 16, 3.5)


@icon("fontdialog")
def i_fontdialog(cr):
    letter(cr, "A", 2, 16, 13, INK)
    letter(cr, "a", 12, 16, 11, ACC, italic=True, family="Serif")
    bar(cr, 3, 19, 18, 1.2, GREY)


@icon("resetattributes")
def i_resetattributes(cr):
    letter(cr, "A", 2, 16, 14, INK)
    cr.save()
    cr.translate(16, 15)
    cr.rotate(-math.pi / 4)
    rrect(cr, -2.5, -5, 5, 10, 1, (0.95, 0.6, 0.65), INK)
    rect(cr, -2.5, 1, 5, 4, PAPER, INK)
    cr.restore()


@icon("text", "insertfixedtext")
def i_text(cr):
    rect(cr, 3.5, 4.5, 17, 15, PAPER, INK)
    centred(cr, "A", 12, 16.5, 11, ACC, bold=True)


@icon("charmapcontrol", "insertsymbol")
def i_insertsymbol(cr):
    centred(cr, "Ω", 12, 19, 17, ACC)


@icon("fontworkgalleryfloater")
def i_wordart(cr):
    cr.save()
    cr.select_font_face("Sans", 1, 1)
    cr.set_font_size(15)
    cr.move_to(3.5, 18)
    cr.text_path("A")
    _rgb(cr, ACC_LIGHT)
    cr.fill_preserve()
    _rgb(cr, ACC)
    cr.set_line_width(1.2)
    cr.stroke()
    cr.restore()
    letter(cr, "a", 13, 18, 11, GOLD, bold=True)


# --- paragraph
def _align(cr, which):
    ws = [16, 11, 16, 9]
    for i, w in enumerate(ws):
        if which == "left":
            x = 4
        elif which == "right":
            x = 20 - w
        elif which == "center":
            x = 12 - w / 2
        else:
            x, w = 4, 16
        bar(cr, x, 5 + i * 4, w, 1.6, INK)


@icon("leftpara")
def i_leftpara(cr):
    _align(cr, "left")


@icon("rightpara")
def i_rightpara(cr):
    _align(cr, "right")


@icon("centerpara")
def i_centerpara(cr):
    _align(cr, "center")


@icon("justifypara")
def i_justifypara(cr):
    _align(cr, "justify")


@icon("defaultbullet", "outlinebullet")
def i_defaultbullet(cr):
    for i in range(3):
        circle(cr, 5.5, 6 + i * 6, 1.6, fill=ACC, ink=None)
        bar(cr, 9, 5.4 + i * 6, 11, 1.4, INK)


@icon("defaultnumbering")
def i_defaultnumbering(cr):
    for i in range(3):
        letter(cr, str(i + 1), 3, 8.5 + i * 6, 6.5, ACC, bold=True)
        bar(cr, 9, 6.0 + i * 6, 11, 1.4, INK)


@icon("setoutline")
def i_setoutline(cr):
    for i, ind in enumerate((0, 3, 6)):
        letter(cr, ("1", "a", "i")[i], 3 + ind, 8.5 + i * 6, 6.5, ACC, bold=True)
        bar(cr, 8.5 + ind, 6.0 + i * 6, 11.5 - ind, 1.4, INK)


def _indent(cr, direction):
    bar(cr, 4, 4, 16, 1.4)
    for i in range(3):
        bar(cr, 11, 8 + i * 3.5, 9, 1.4)
    bar(cr, 4, 19, 16, 1.4)
    if direction > 0:
        tri(cr, 4, 9, 5, "right", ACC)
    else:
        tri(cr, 4, 9, 5, "left", ACC)


@icon("incrementindent")
def i_incrementindent(cr):
    _indent(cr, 1)


@icon("decrementindent")
def i_decrementindent(cr):
    _indent(cr, -1)


@icon("linespacing", "spacepara15")
def i_linespacing(cr):
    for i in range(4):
        bar(cr, 10, 5 + i * 4.5, 10, 1.4)
    arrow(cr, 5, 12, 5, 3.5, ACC, 2.6, 1.2)
    arrow(cr, 5, 12, 5, 20.5, ACC, 2.6, 1.2)


@icon("paraspaceincrease")
def i_paraspaceincrease(cr):
    for y in (4, 7):
        bar(cr, 10, y, 10, 1.4)
    for y in (16, 19):
        bar(cr, 10, y, 10, 1.4)
    arrow(cr, 5, 12, 5, 4, ACC, 2.6, 1.2)
    arrow(cr, 5, 12, 5, 20, ACC, 2.6, 1.2)


@icon("controlcodes")
def i_controlcodes(cr):
    centred(cr, "¶", 12, 19, 17, ACC)


@icon("pararighttoleft")
def i_pararighttoleft(cr):
    centred(cr, "¶", 15, 19, 15, INK)
    arrow(cr, 10, 6, 3, 6, ACC, 2.6, 1.3)


@icon("paragraphdialog")
def i_paragraphdialog(cr):
    page(cr, 4.5, 2.5, 15, 19, 4)
    lines(cr, 7, 7, [10, 10, 6], 2.6, GREY)
    lines(cr, 7, 15, [10, 7], 2.6, GREY)
    centred(cr, "¶", 16.5, 20.5, 8, ACC)


@icon("sortascending", "sortdialog")
def i_sortascending(cr):
    letter(cr, "A", 3, 10, 8, INK, bold=True)
    letter(cr, "Z", 3, 20, 8, INK, bold=True)
    arrow(cr, 16, 3.5, 16, 20, ACC, 3, 1.5)


@icon("setborderstyle", "borderdialog")
def i_borders(cr):
    cr.save()
    cr.set_dash([1, 1.5])
    rect(cr, 3.5, 3.5, 17, 17, None, GREY)
    cr.move_to(12, 3.5)
    cr.line_to(12, 20.5)
    cr.move_to(3.5, 12)
    cr.line_to(20.5, 12)
    _rgb(cr, GREY)
    cr.stroke()
    cr.restore()
    line(cr, 3, 20.5, 21, 20.5, INK, 2.0)


@icon("backgroundcolor")
def i_backgroundcolor(cr):
    bucket(cr, 4, 3)
    color_bar(cr, (1.0, 0.95, 0.0), 18.5, 4, 16, 3.5)


@icon("xlinecolor")
def i_xlinecolor(cr):
    pencil(cr, 5, 16, 11, GOLD)
    color_bar(cr, ACC, 18.5, 4, 16, 3.5)


@icon("linewidth")
def i_linewidth(cr):
    for i, w in enumerate((0.8, 1.6, 2.6, 3.6)):
        bar(cr, 4, 4 + i * 4.5, 16, w, INK)


@icon("fillshadow")
def i_fillshadow(cr):
    rect(cr, 7, 7, 13, 13, GREY, None)
    rect(cr, 4, 4, 13, 13, ACC_LIGHT, INK)


# --- styles
@icon("editstyle")
def i_editstyle(cr):
    letter(cr, "A", 3, 15, 12, ACC)
    pencil(cr, 12, 21, 9, GOLD)


@icon("stylenewbyexample")
def i_stylenewbyexample(cr):
    letter(cr, "A", 3, 15, 12, ACC)
    badge_plus(cr, 17, 17)


@icon("styleupdatebyexample")
def i_styleupdatebyexample(cr):
    letter(cr, "A", 3, 15, 12, ACC)
    cr.save()
    cr.set_line_width(1.6)
    _rgb(cr, BLUE)
    cr.new_path()
    cr.arc(17, 17, 3.5, 0.3, 5.0)
    cr.stroke()
    cr.restore()
    tri(cr, 18.3, 12.2, 3, "right", BLUE)


@icon("setdefault")
def i_setdefault(cr):
    page(cr)
    text_lines(cr)
    badge_check(cr, 17, 17)


@icon("searchdialog", "recsearch")
def i_searchdialog(cr):
    magnifier(cr, 9.5, 9.5, 5.5)


@icon("languagemenu")
def i_languagemenu(cr):
    globe(cr, 10, 10, 6.5)
    bubble(cr, 12, 12, 9, 6, ACC_LIGHT)
    letter(cr, "a", 14.5, 17, 6, ACC)


# --- file
@icon("newdoc")
def i_newdoc(cr):
    page(cr)
    badge_plus(cr, 17, 18)


@icon("open")
def i_open(cr):
    folder(cr, 2.5, 5.5, 18, 14)
    cr.move_to(5, 11)
    cr.line_to(22, 11)
    cr.line_to(19.5, 19.5)
    cr.line_to(2.5, 19.5)
    cr.close_path()
    _rgb(cr, (0.98, 0.82, 0.38))
    cr.fill_preserve()
    _rgb(cr, INK)
    cr.stroke()


@icon("saveas")
def i_saveas(cr):
    disk(cr, 3, 3, 15)
    pencil(cr, 13, 21, 9, GOLD)


@icon("closedoc")
def i_closedoc(cr):
    page(cr)
    text_lines(cr)
    badge_x(cr, 17, 18)


@icon("reload")
def i_reload(cr):
    cr.save()
    cr.set_line_width(2.2)
    _rgb(cr, ACC)
    cr.new_path()
    cr.arc(12, 12, 7, 0.5, 5.4)
    cr.stroke()
    cr.restore()
    tri(cr, 15.5, 2.5, 5, "right", ACC)


@icon("recentfilelist")
def i_recentfilelist(cr):
    page(cr, 3.5, 2.5, 13, 17, 3)
    text_lines(cr, 6, 7, 8, 3)
    clock(cr, 16.5, 16.5, 5)


@icon("print")
def i_print(cr):
    printer(cr, 3, 8)


@icon("printpreview")
def i_printpreview(cr):
    page(cr, 3.5, 2.5, 13, 17, 3)
    text_lines(cr, 6, 7, 8, 4)
    magnifier(cr, 14, 14, 3.8)


@icon("exportdirecttopdf")
def i_exportpdf(cr):
    page(cr)
    rrect(cr, 2.5, 12, 14, 7, 1, RED, None)
    letter(cr, "PDF", 3.6, 17.8, 6, PAPER, bold=True)


@icon("sendmail")
def i_sendmail(cr):
    envelope(cr, 2.5, 6.5, 17, 12)
    arrow(cr, 14, 18, 22, 18, ACC, 3, 1.6)


@icon("protect")
def i_protect(cr):
    page(cr, 3.5, 2.5, 13, 17, 3)
    text_lines(cr, 6, 7, 8, 3)
    lock(cr, 11.5, 13)


@icon("versiondialog")
def i_versiondialog(cr):
    page(cr, 8.5, 2.5, 12, 15, 3)
    page(cr, 5.5, 4.5, 12, 15, 3)
    page(cr, 2.5, 6.5, 12, 15, 3)
    letter(cr, "v2", 4.5, 17, 7, ACC, bold=True)


@icon("comparedocuments")
def i_comparedocuments(cr):
    page(cr, 2.5, 3.5, 9, 13, 2.5)
    page(cr, 12.5, 7.5, 9, 13, 2.5)
    lines(cr, 4, 7, [6, 6, 4], 2.5, GREY)
    lines(cr, 14, 11, [6, 6, 4], 2.5, RED)


@icon("adddirect")
def i_adddirect(cr):
    page(cr)
    badge_plus(cr, 17, 18)


@icon("mailmergewizard", "addressbooksource")
def i_mailmergewizard(cr):
    envelope(cr, 2.5, 9.5, 14, 10)
    person(cr, 18, 8, 0.9, ACC)


@icon("mailmergecreatedocuments")
def i_mailmergecreate(cr):
    for i, x in enumerate((2.5, 6.5, 10.5)):
        page(cr, x, 2.5 + i * 2, 10, 15, 3)
    badge_check(cr, 18, 18)


@icon("insertenvelope")
def i_insertenvelope(cr):
    envelope(cr, 2.5, 5.5, 19, 13)
    rect(cr, 16, 7.5, 3.5, 4, RED, None)


@icon("label")
def i_label(cr):
    rect(cr, 3.5, 2.5, 17, 19, PAPER, INK)
    for r in range(3):
        for c in range(2):
            rrect(cr, 5 + c * 7.5, 4 + r * 5.8, 6.3, 4.6, 1, ACC_LIGHT, ACC)


# --- insert
@icon("inserttable")
def i_inserttable(cr):
    table(cr, 3.5, 4.5, 17, 15, 4, 3)


@icon("tabledialog")
def i_tabledialog(cr):
    table(cr, 2.5, 3.5, 15, 13, 3, 3)
    gear(cr, 18, 18, 3.6)


@icon("selecttable")
def i_selecttable(cr):
    cr.rectangle(3.5, 4.5, 17, 15)
    _rgb(cr, (0.75, 0.86, 0.95))
    cr.fill()
    table(cr, 3.5, 4.5, 17, 15, 3, 3, header=False, ink=BLUE)


@icon("deletetable")
def i_deletetable(cr):
    table(cr, 2.5, 3.5, 15, 13, 3, 3)
    badge_x(cr, 18, 18)


def _grid_rows(cr, hl=None, col=None, cols=3, rows=3):
    table(cr, 3.5, 3.5, 17, 17, rows, cols, header=False)
    if hl is not None:
        cr.rectangle(3.5, 3.5 + 17 * hl / rows, 17, 17 / rows)
    if col is not None:
        cr.rectangle(3.5 + 17 * col / cols, 3.5, 17 / cols, 17)
    _rgb(cr, ACC_LIGHT if hl is not None or col is not None else PAPER)
    cr.fill()
    table(cr, 3.5, 3.5, 17, 17, rows, cols, header=False)
    cr.new_path()


@icon("insertrowsbefore")
def i_insertrowsbefore(cr):
    table(cr, 3.5, 9.5, 17, 11, 2, 3, header=False)
    rect(cr, 3.5, 3.5, 17, 5, ACC_LIGHT, ACC)
    badge_plus(cr, 12, 6, 2.6)


@icon("insertrowsafter")
def i_insertrowsafter(cr):
    table(cr, 3.5, 3.5, 17, 11, 2, 3, header=False)
    rect(cr, 3.5, 15.5, 17, 5, ACC_LIGHT, ACC)
    badge_plus(cr, 12, 18, 2.6)


@icon("insertcolumnsbefore")
def i_insertcolumnsbefore(cr):
    table(cr, 9.5, 3.5, 11, 17, 3, 2, header=False)
    rect(cr, 3.5, 3.5, 5, 17, ACC_LIGHT, ACC)
    badge_plus(cr, 6, 12, 2.6)


@icon("insertcolumnsafter")
def i_insertcolumnsafter(cr):
    table(cr, 3.5, 3.5, 11, 17, 3, 2, header=False)
    rect(cr, 15.5, 3.5, 5, 17, ACC_LIGHT, ACC)
    badge_plus(cr, 18, 12, 2.6)


@icon("deleterows")
def i_deleterows(cr):
    table(cr, 3.5, 3.5, 17, 17, 3, 3, header=False)
    rect(cr, 3.5, 9.2, 17, 5.6, (0.98, 0.85, 0.85), RED)
    badge_minus(cr, 12, 12, 2.6)


@icon("deletecolumns")
def i_deletecolumns(cr):
    table(cr, 3.5, 3.5, 17, 17, 3, 3, header=False)
    rect(cr, 9.2, 3.5, 5.6, 17, (0.98, 0.85, 0.85), RED)
    badge_minus(cr, 12, 12, 2.6)


@icon("delete")
def i_delete(cr):
    x_mark(cr, 12, 12, 6, RED, 3)


@icon("mergecells", "merge")
def i_mergecells(cr):
    table(cr, 3.5, 3.5, 17, 17, 3, 1, header=False)
    rect(cr, 3.5, 9.2, 17, 5.6, ACC_LIGHT, ACC)
    arrow(cr, 5, 12, 10.5, 12, ACC, 2.5, 1.2)
    arrow(cr, 19, 12, 13.5, 12, ACC, 2.5, 1.2)


@icon("splitcell")
def i_splitcell(cr):
    table(cr, 3.5, 3.5, 17, 17, 3, 1, header=False)
    rect(cr, 3.5, 9.2, 17, 5.6, ACC_LIGHT, ACC)
    line(cr, 12, 9.2, 12, 14.8, ACC)
    arrow(cr, 10.5, 12, 5, 12, ACC, 2.5, 1.2)
    arrow(cr, 13.5, 12, 19, 12, ACC, 2.5, 1.2)


@icon("splittable")
def i_splittable(cr):
    table(cr, 3.5, 2.5, 17, 8, 2, 3, header=False)
    table(cr, 3.5, 13.5, 17, 8, 2, 3, header=False)
    cr.save()
    cr.set_dash([1.5, 1.5])
    line(cr, 2, 12, 22, 12, ACC)
    cr.restore()


@icon("setoptimalcolumnwidth", "distributecolumns")
def i_optimalwidth(cr):
    table(cr, 3.5, 6.5, 17, 11, 2, 3, header=False)
    arrow(cr, 12, 3, 4, 3, ACC, 2.4, 1.1)
    arrow(cr, 12, 3, 20, 3, ACC, 2.4, 1.1)


@icon("distributerows")
def i_distributerows(cr):
    table(cr, 7.5, 3.5, 13, 17, 3, 2, header=False)
    arrow(cr, 4, 12, 4, 4, ACC, 2.4, 1.1)
    arrow(cr, 4, 12, 4, 20, ACC, 2.4, 1.1)


def _cellalign(cr, where):
    rect(cr, 3.5, 3.5, 17, 17, PAPER, INK)
    y = {"up": 6, "middle": 10.5, "down": 15}[where]
    lines(cr, 7, y, [10, 7], 2.6, ACC, 1.4)


@icon("alignup")
def i_alignup(cr):
    _cellalign(cr, "up")


@icon("alignmiddle", "cellvertcenter")
def i_alignmiddle(cr):
    _cellalign(cr, "middle")


@icon("aligndown")
def i_aligndown(cr):
    _cellalign(cr, "down")


@icon("alignhorizontalcenter")
def i_alignhcenter(cr):
    rect(cr, 3.5, 3.5, 17, 17, PAPER, INK)
    lines(cr, 7.5, 9, [9], 3, ACC, 1.4)
    lines(cr, 9, 13, [6], 3, ACC, 1.4)


@icon("insertgraphic")
def i_insertgraphic(cr):
    picture(cr, 2.5, 4.5, 19, 15)


@icon("insertobjectchart", "diagramtype")
def i_chart(cr):
    chart_bars(cr, 3.5, 3.5, 17, 17)


@icon("diagramarea")
def i_diagramarea(cr):
    rect(cr, 2.5, 2.5, 19, 19, ACC_LIGHT, INK)
    chart_bars(cr, 5.5, 5.5, 13, 13)


@icon("diagramdata", "datainrows")
def i_diagramdata(cr):
    table(cr, 2.5, 3.5, 13, 13, 4, 3)
    chart_bars(cr, 13, 11, 9, 10)


@icon("insertobjectstarmath")
def i_formula(cr):
    centred(cr, "√", 8, 18, 15, INK)
    letter(cr, "x", 11, 16, 10, ACC, italic=True, family="Serif")
    bar(cr, 9.5, 5.5, 11, 1.2, INK)


@icon("insertobject")
def i_insertobject(cr):
    rect(cr, 3.5, 5.5, 13, 13, PAPER, INK)
    circle(cr, 9, 12, 3.5, ACC_LIGHT, ACC)
    badge_plus(cr, 18, 18)


@icon("basicshapes")
def i_basicshapes(cr):
    rect(cr, 3.5, 9.5, 9, 9, ACC_LIGHT, ACC)
    circle(cr, 15, 9, 5.5, (0.98, 0.9, 0.7), GOLD)


@icon("insertpage", "titlepagedialog")
def i_insertpage(cr):
    page(cr, 3.5, 2.5, 13, 17, 3)
    centred(cr, "T", 10, 11, 7, ACC, bold=True)
    lines(cr, 6, 14, [8, 6], 2.5, GREY)
    badge_plus(cr, 18, 18)


@icon("insertpagebreak", "insertbreak")
def i_pagebreak(cr):
    rect(cr, 5.5, 1.5, 13, 8, PAPER, INK)
    rect(cr, 5.5, 14.5, 13, 8, PAPER, INK)
    cr.save()
    cr.set_dash([1.5, 1.5])
    line(cr, 2, 12, 22, 12, ACC)
    cr.restore()


@icon("insertpageheader")
def i_header(cr):
    page(cr, 4.5, 2.5, 15, 19, 0)
    rect(cr, 5.1, 3.1, 13.8, 4.5, ACC_LIGHT, None)
    bar(cr, 7, 4.8, 9, 1.2, ACC)
    text_lines(cr, 7, 11, 10, 3)


@icon("insertpagefooter")
def i_footer(cr):
    page(cr, 4.5, 2.5, 15, 19, 0)
    rect(cr, 5.1, 16.4, 13.8, 4.5, ACC_LIGHT, None)
    bar(cr, 7, 18, 9, 1.2, ACC)
    text_lines(cr, 7, 6, 10, 3)


@icon("insertpagenumberfield", "gotopage")
def i_pagenumber(cr):
    page(cr, 4.5, 2.5, 15, 19, 4)
    text_lines(cr, 7, 6, 10, 3)
    centred(cr, "#", 12, 20, 7, ACC, bold=True)


@icon("insertdatefield")
def i_insertdate(cr):
    calendar(cr, 3.5, 3.5, 17, 17)


@icon("insertfieldctrl", "insertreferencefield", "convertmenu")
def i_insertfield(cr):
    rrect(cr, 2.5, 7.5, 19, 9, 2, (0.9, 0.9, 0.9), INK)
    centred(cr, "{ }", 12, 15, 8, ACC, bold=True)


@icon("hyperlinkdialog")
def i_hyperlink(cr):
    globe(cr, 8.5, 8.5, 6)
    chain(cr, 7.5, 15)


@icon("insertbookmark")
def i_bookmark(cr):
    page(cr, 3.5, 2.5, 15, 19, 4)
    ribbon_mark(cr, 12, 2.5, 5, 9, ACC)
    text_lines(cr, 6, 14, 10, 2)


@icon("insertfootnote", "footnotedialog")
def i_footnote(cr):
    page(cr, 4.5, 2.5, 15, 19, 0)
    text_lines(cr, 7, 5, 10, 3)
    letter(cr, "1", 15.5, 9, 5, ACC, bold=True)
    bar(cr, 7, 15, 5, 0.8, INK)
    letter(cr, "1", 7, 19.5, 4.5, ACC, bold=True)
    bar(cr, 9.5, 18, 7, 1.0, GREY)


@icon("insertendnote")
def i_endnote(cr):
    page(cr, 4.5, 2.5, 15, 19, 0)
    text_lines(cr, 7, 5, 10, 3)
    letter(cr, "i", 15.5, 9, 5, ACC, bold=True)
    bar(cr, 7, 14.5, 10, 0.8, INK)
    lines(cr, 7, 17, [10, 7], 2.4, ACC, 1.0)


@icon("insertcaptiondialog")
def i_caption(cr):
    picture(cr, 3.5, 2.5, 17, 12)
    bar(cr, 5, 17, 14, 1.4, ACC)
    bar(cr, 7, 20, 10, 1.2, GREY)


@icon("insertindexesentry", "insertauthoritiesentry")
def i_markentry(cr):
    page(cr, 4.5, 2.5, 15, 19, 4)
    text_lines(cr, 7, 7, 10, 4)
    rect(cr, 6.5, 12.3, 8, 2.6, (1.0, 0.95, 0.4), None)
    bar(cr, 7, 13, 7, 1.2, INK)


@icon("insertmultiindex")
def i_toc(cr):
    page(cr, 4.5, 2.5, 15, 19, 4)
    for i in range(4):
        ind = 0 if i % 2 == 0 else 2
        bar(cr, 7 + ind, 6.5 + i * 3.5, 7 - ind, 1.2, ACC if ind == 0 else INK)
        cr.save()
        cr.set_dash([0.6, 1.0])
        line(cr, 14.3, 7.1 + i * 3.5, 16.2, 7.1 + i * 3.5, GREY)
        cr.restore()
        bar(cr, 16.3, 6.5 + i * 3.5, 1.2, 1.2, INK)


@icon("updatecurindex")
def i_updateindex(cr):
    i_toc(cr)
    cr.save()
    cr.set_line_width(1.6)
    circle(cr, 17.5, 17.5, 4.2, PAPER, None)
    _rgb(cr, BLUE)
    cr.new_path()
    cr.arc(17.5, 17.5, 3, 0.3, 5.0)
    cr.stroke()
    cr.restore()


@icon("bibliographycomponent")
def i_bibliography(cr):
    for i, c in enumerate((ACC, BLUE, RED)):
        rect(cr, 4 + i * 5, 4, 4, 16, c, INK)
    cr.save()
    cr.translate(19, 5)
    cr.rotate(0.3)
    rect(cr, 0, 0, 3.5, 15.5, GOLD, INK)
    cr.restore()


@icon("signaturelinedialog")
def i_signature(cr):
    cr.save()
    cr.set_line_width(1.4)
    _rgb(cr, BLUE)
    cr.move_to(4, 14)
    cr.curve_to(6, 4, 9, 4, 8, 13)
    cr.curve_to(10, 8, 12, 8, 13, 13)
    cr.curve_to(15, 10, 17, 10, 20, 12)
    cr.stroke()
    cr.restore()
    x_mark(cr, 5, 18.5, 1.5, INK, 1.2)
    bar(cr, 8, 19.5, 13, 1.2, INK)


@icon("insertannotation")
def i_insertcomment(cr):
    bubble(cr, 2.5, 3.5, 16, 11, (1.0, 0.92, 0.6))
    badge_plus(cr, 18, 17)


@icon("deleteannotation")
def i_deletecomment(cr):
    bubble(cr, 2.5, 3.5, 16, 11, (1.0, 0.92, 0.6))
    badge_x(cr, 18, 17)


@icon("previousannotation")
def i_prevcomment(cr):
    bubble(cr, 7.5, 3.5, 14, 10, (1.0, 0.92, 0.6))
    arrow(cr, 12, 18, 3, 18, ACC, 3, 1.8)


@icon("nextannotation")
def i_nextcomment(cr):
    bubble(cr, 2.5, 3.5, 14, 10, (1.0, 0.92, 0.6))
    arrow(cr, 12, 18, 21, 18, ACC, 3, 1.8)


@icon("watermark")
def i_watermark(cr):
    page(cr)
    cr.save()
    cr.translate(12, 13)
    cr.rotate(-0.8)
    centred(cr, "DRAFT", 0, 2, 5.5, (0.72, 0.82, 0.74), bold=True)
    cr.restore()


@icon("textdirectiontoptobottom")
def i_textvertical(cr):
    rect(cr, 4.5, 2.5, 15, 19, PAPER, INK)
    for i, ch in enumerate("AB"):
        centred(cr, ch, 15 - i * 6, 9, 6, INK, bold=True)
    arrow(cr, 15, 11, 15, 20, ACC, 2.6, 1.2)
    arrow(cr, 9, 11, 9, 20, ACC, 2.6, 1.2)


@icon("insertfixedtext_box", "objecttitledescription")
def i_alttext(cr):
    picture(cr, 2.5, 2.5, 13, 10)
    bubble(cr, 9.5, 11.5, 12, 7, ACC_LIGHT)
    lines(cr, 11.5, 14, [8], 2, ACC, 1.2)


# --- layout
@icon("pagemargin")
def i_margins(cr):
    page(cr, 4.5, 2.5, 15, 19, 0)
    cr.save()
    cr.set_dash([1, 1])
    rect(cr, 7.5, 5.5, 9, 13, None, ACC)
    cr.restore()


@icon("orientation")
def i_orientation(cr):
    rect(cr, 3.5, 2.5, 10, 14, PAPER, INK)
    rect(cr, 7.5, 11.5, 14, 10, ACC_LIGHT, INK)
    cr.save()
    cr.set_line_width(1.3)
    _rgb(cr, ACC)
    cr.new_path()
    cr.arc(17, 6, 4, -math.pi / 2, 0.3)
    cr.stroke()
    cr.restore()


@icon("attributepagesize")
def i_pagesize(cr):
    page(cr, 7.5, 2.5, 13, 17, 3)
    arrow(cr, 14, 21.5, 7, 21.5, ACC, 2.2, 1.0)
    arrow(cr, 14, 21.5, 20.5, 21.5, ACC, 2.2, 1.0)
    arrow(cr, 4, 11, 4, 2.5, ACC, 2.2, 1.0)
    arrow(cr, 4, 11, 4, 19.5, ACC, 2.2, 1.0)


@icon("formatcolumns", "pagecolumntype")
def i_columns(cr):
    rect(cr, 3.5, 2.5, 17, 19, PAPER, INK)
    for x in (5.5, 12.5):
        lines(cr, x, 5, [6] * 5, 3, INK, 1.2)


@icon("linenumberingdialog")
def i_linenumbering(cr):
    for i in range(4):
        letter(cr, str(i + 1), 3, 7.5 + i * 4.5, 5, ACC, bold=True)
        bar(cr, 8, 5.4 + i * 4.5, 12, 1.3)


@icon("hyphenate")
def i_hyphenate(cr):
    letter(cr, "ab", 2.5, 11, 9, INK)
    bar(cr, 13, 7.5, 4, 1.6, ACC)
    letter(cr, "cd", 6, 20, 9, INK)


@icon("wrapon", "toggleanchortype")
def i_wrap(cr):
    rect(cr, 8.5, 7.5, 7, 7, ACC_LIGHT, ACC)
    for y in (3.5, 18.5):
        bar(cr, 3, y, 18, 1.3)
    for y in (8, 11.5):
        bar(cr, 3, y, 4, 1.3)
        bar(cr, 17, y, 4, 1.3)


@icon("bringtofront")
def i_bringtofront(cr):
    rect(cr, 9.5, 9.5, 11, 11, PALE, GREY)
    rect(cr, 3.5, 3.5, 11, 11, ACC_LIGHT, ACC)


@icon("sendtoback")
def i_sendtoback(cr):
    rect(cr, 3.5, 3.5, 11, 11, ACC_LIGHT, ACC)
    rect(cr, 9.5, 9.5, 11, 11, PALE, GREY)


@icon("objectalignleft")
def i_objalignleft(cr):
    line(cr, 3.5, 2, 3.5, 22, ACC, 1.6)
    rect(cr, 5.5, 4.5, 14, 6, ACC_LIGHT, INK)
    rect(cr, 5.5, 13.5, 9, 6, ACC_LIGHT, INK)


@icon("objectalignright")
def i_objalignright(cr):
    line(cr, 20.5, 2, 20.5, 22, ACC, 1.6)
    rect(cr, 4.5, 4.5, 14, 6, ACC_LIGHT, INK)
    rect(cr, 9.5, 13.5, 9, 6, ACC_LIGHT, INK)


@icon("distributehorzcenter")
def i_disthorz(cr):
    for x in (3.5, 10, 16.5):
        rect(cr, x, 7.5, 4, 9, ACC_LIGHT, INK)
        line(cr, x + 2, 4, x + 2, 20, ACC)


@icon("distributevertcenter")
def i_distvert(cr):
    for y in (3.5, 10, 16.5):
        rect(cr, 7.5, y, 9, 4, ACC_LIGHT, INK)
        line(cr, 4, y + 2, 20, y + 2, ACC)


@icon("formatgroup")
def i_group(cr):
    cr.save()
    cr.set_dash([1.5, 1.5])
    rect(cr, 2.5, 2.5, 19, 19, None, ACC)
    cr.restore()
    rect(cr, 5.5, 5.5, 7, 7, ACC_LIGHT, INK)
    circle(cr, 15, 15, 3.6, (0.98, 0.9, 0.7), INK)


@icon("formatungroup")
def i_ungroup(cr):
    rect(cr, 3.5, 3.5, 8, 8, ACC_LIGHT, INK)
    circle(cr, 16, 16, 4, (0.98, 0.9, 0.7), INK)
    cr.save()
    cr.set_dash([1.5, 1.5])
    line(cr, 4, 20, 20, 4, GREY)
    cr.restore()


@icon("toggleobjectrotatemode")
def i_rotate(cr):
    cr.save()
    cr.translate(12, 12)
    cr.rotate(0.35)
    rect(cr, -5, -5, 10, 10, ACC_LIGHT, INK)
    cr.restore()
    cr.save()
    cr.set_line_width(1.4)
    _rgb(cr, ACC)
    cr.new_path()
    cr.arc(12, 12, 9, -2.6, -0.7)
    cr.stroke()
    cr.restore()
    tri(cr, 17.5, 3, 3.5, "right", ACC)


@icon("toggleobjectbeziermode")
def i_points(cr):
    cr.save()
    cr.set_line_width(1.6)
    _rgb(cr, ACC)
    cr.move_to(3, 18)
    cr.curve_to(6, 3, 16, 22, 21, 6)
    cr.stroke()
    cr.restore()
    for x, y in ((3, 18), (12, 12), (21, 6)):
        rect(cr, x - 1.5, y - 1.5, 3, 3, PAPER, INK)


@icon("crop")
def i_crop(cr):
    cr.save()
    cr.set_line_width(2.2)
    _rgb(cr, INK)
    cr.move_to(7, 2)
    cr.line_to(7, 17)
    cr.line_to(22, 17)
    cr.move_to(2, 7)
    cr.line_to(17, 7)
    cr.line_to(17, 22)
    cr.stroke()
    cr.restore()
    rect(cr, 8, 8, 8, 8, ACC_LIGHT, None)


@icon("compressgraphic")
def i_compress(cr):
    picture(cr, 6.5, 6.5, 11, 11)
    arrow(cr, 2, 2, 6, 6, ACC, 2.4, 1.3)
    arrow(cr, 22, 22, 18, 18, ACC, 2.4, 1.3)


@icon("grafluminance")
def i_brightness(cr):
    circle(cr, 12, 12, 4.5, GOLD, INK)
    for i in range(8):
        a = i * math.tau / 8
        line(cr, 12 + 6.5 * math.cos(a), 12 + 6.5 * math.sin(a),
             12 + 9 * math.cos(a), 12 + 9 * math.sin(a), GOLD, 1.6)


@icon("grafmode")
def i_colormode(cr):
    for i, c in enumerate((RED, ACC, BLUE)):
        circle(cr, (8, 16, 12)[i], (9, 9, 15.5)[i], 5, c, None)


@icon("graftransparence")
def i_transparency(cr):
    for r in range(4):
        for c in range(4):
            if (r + c) % 2 == 0:
                rect(cr, 3 + c * 4.5, 3 + r * 4.5, 4.5, 4.5, PALE, None)
    rect(cr, 3.5, 3.5, 17, 17, None, INK)
    cr.rectangle(8, 8, 12, 12)
    cr.set_source_rgba(*ACC, 0.55)
    cr.fill()


@icon("graphicfilterpopart")
def i_artistic(cr):
    for i, c in enumerate((GOLD, RED, BLUE, ACC)):
        rect(cr, 3.5 + (i % 2) * 8.5, 3.5 + (i // 2) * 8.5, 8.5, 8.5, c, None)
    rect(cr, 3.5, 3.5, 17, 17, None, INK)
    circle(cr, 12, 12, 4, PAPER, INK)


@icon("chainframes")
def i_chainframes(cr):
    rect(cr, 2.5, 3.5, 8, 7, PAPER, INK)
    rect(cr, 13.5, 13.5, 8, 7, PAPER, INK)
    arrow(cr, 10.5, 9, 13.5, 15, ACC, 2.4, 1.3)


@icon("unhainframes")
def i_unchainframes(cr):
    rect(cr, 2.5, 3.5, 8, 7, PAPER, INK)
    rect(cr, 13.5, 13.5, 8, 7, PAPER, INK)
    x_mark(cr, 12, 12, 2.2, RED, 1.6)


@icon("controlproperties", "designerdialog", "inspectordeck")
def i_properties(cr):
    window(cr, 2.5, 3.5, 17, 16)
    for i in range(3):
        bar(cr, 5, 9 + i * 3.5, 5, 1.2, GREY)
        rect(cr, 11, 8.3 + i * 3.5, 6, 2.5, PAPER, INK)
    gear(cr, 18.5, 18.5, 3.2, ACC)


# --- review
@icon("spellingandgrammardialog")
def i_spelling(cr):
    letter(cr, "ABC", 2, 11, 8, INK, bold=True)
    check_mark(cr, 8, 17, 9, ACC, 2.2)


@icon("thesaurusdialog")
def i_thesaurus(cr):
    rect(cr, 3.5, 3.5, 7.5, 17, ACC, INK)
    rect(cr, 11, 3.5, 7.5, 17, ACC_LIGHT, INK)
    letter(cr, "A", 4.8, 14, 6, PAPER, bold=True)
    letter(cr, "A", 12.6, 14, 6, ACC, bold=True)


@icon("wordcountdialog")
def i_wordcount(cr):
    rect(cr, 3.5, 3.5, 17, 17, PAPER, INK)
    letter(cr, "123", 5, 11, 6.5, ACC, bold=True)
    lines(cr, 6, 15, [12, 8], 2.8, GREY)


@icon("trackchanges", "trackchangesbar")
def i_trackchanges(cr):
    page(cr, 3.5, 2.5, 15, 19, 4)
    text_lines(cr, 6, 7, 10, 4)
    pencil(cr, 13, 21, 9, GOLD)


@icon("showtrackedchanges")
def i_showchanges(cr):
    page(cr, 3.5, 2.5, 15, 19, 4)
    lines(cr, 6, 7, [10, 10], 3, GREY)
    bar(cr, 6, 13, 10, 1.2, RED)
    eye(cr, 15.5, 18, 5)


@icon("accepttrackedchange")
def i_accept(cr):
    page(cr, 3.5, 2.5, 15, 19, 4)
    text_lines(cr, 6, 7, 10, 3)
    badge_check(cr, 17, 17)


@icon("rejecttrackedchange")
def i_reject(cr):
    page(cr, 3.5, 2.5, 15, 19, 4)
    text_lines(cr, 6, 7, 10, 3)
    badge_x(cr, 17, 17)


@icon("previoustrackedchange")
def i_prevchange(cr):
    page(cr, 8.5, 2.5, 13, 17, 3)
    bar(cr, 11, 8, 8, 1.2, RED)
    arrow(cr, 12, 19, 2.5, 19, ACC, 3, 1.8)


@icon("nexttrackedchange")
def i_nextchange(cr):
    page(cr, 2.5, 2.5, 13, 17, 3)
    bar(cr, 5, 8, 8, 1.2, RED)
    arrow(cr, 12, 19, 21.5, 19, ACC, 3, 1.8)


@icon("viewvaluehighlighting")
def i_fieldshading(cr):
    rect(cr, 3, 8, 18, 8, (0.85, 0.85, 0.85), None)
    centred(cr, "ab", 12, 15, 8, INK)


@icon("ok")
def i_ok(cr):
    check_mark(cr, 4, 13, 16, ACC, 3)


# --- view
@icon("printlayout")
def i_printlayout(cr):
    rect(cr, 2.5, 2.5, 19, 19, PALE, INK)
    rect(cr, 6.5, 4.5, 11, 15, PAPER, INK)
    text_lines(cr, 8, 7, 8, 4)


@icon("browseview")
def i_webview(cr):
    window(cr, 2.5, 3.5, 19, 17)
    globe(cr, 12, 13, 4.5)


@icon("normalviewmode")
def i_draftview(cr):
    rect(cr, 2.5, 3.5, 19, 17, PAPER, INK)
    lines(cr, 5, 7, [14, 14, 14, 9], 3, INK)
    cr.save()
    cr.set_dash([1, 1])
    line(cr, 2.5, 18.5, 21.5, 18.5, GREY)
    cr.restore()


@icon("fullscreen")
def i_fullscreen(cr):
    for (x, y, dx, dy) in ((3, 3, 1, 1), (21, 3, -1, 1), (3, 21, 1, -1), (21, 21, -1, -1)):
        cr.move_to(x + 5 * dx, y)
        cr.line_to(x, y)
        cr.line_to(x, y + 5 * dy)
    cr.save()
    cr.set_line_width(2)
    _rgb(cr, ACC)
    cr.stroke()
    cr.restore()


@icon("navigator")
def i_navigator(cr):
    circle(cr, 12, 12, 9, PAPER, INK)
    cr.move_to(12, 4)
    cr.line_to(14.5, 12)
    cr.line_to(9.5, 12)
    cr.close_path()
    _rgb(cr, RED)
    cr.fill()
    cr.move_to(12, 20)
    cr.line_to(14.5, 12)
    cr.line_to(9.5, 12)
    cr.close_path()
    _rgb(cr, GREY)
    cr.fill()


@icon("zoom")
def i_zoom(cr):
    magnifier(cr, 10, 10, 6)


@icon("zoom100percent")
def i_zoom100(cr):
    magnifier(cr, 10, 10, 6.5)
    centred(cr, "1", 10, 13, 8, ACC, bold=True)


@icon("zoompage", "showtwopages_one")
def i_zoompage(cr):
    page(cr, 5.5, 2.5, 13, 19, 3)
    text_lines(cr, 8, 7, 8, 4)


@icon("zoompagewidth")
def i_zoompagewidth(cr):
    rect(cr, 5.5, 2.5, 13, 19, PAPER, INK)
    arrow(cr, 12, 12, 2.5, 12, ACC, 2.6, 1.3)
    arrow(cr, 12, 12, 21.5, 12, ACC, 2.6, 1.3)


@icon("showtwopages")
def i_twopages(cr):
    rect(cr, 2.5, 4.5, 9, 15, PAPER, INK)
    rect(cr, 12.5, 4.5, 9, 15, PAPER, INK)
    lines(cr, 4, 8, [6, 6, 4], 2.6, GREY)
    lines(cr, 14, 8, [6, 6, 4], 2.6, GREY)


@icon("showmultiplepages")
def i_multipages(cr):
    for r in range(2):
        for c in range(3):
            rect(cr, 2.5 + c * 6.6, 3.5 + r * 9, 5.6, 8, PAPER, INK)


@icon("newwindow")
def i_newwindow(cr):
    window(cr, 2.5, 3.5, 14, 12)
    window(cr, 7.5, 8.5, 14, 12)
    badge_plus(cr, 18.5, 18.5, 3.5)


@icon("stackwindow")
def i_arrange(cr):
    window(cr, 2.5, 2.5, 19, 9)
    window(cr, 2.5, 12.5, 19, 9)


@icon("splitwindow")
def i_split(cr):
    window(cr, 2.5, 3.5, 19, 17)
    line(cr, 3, 12.5, 21, 12.5, ACC, 1.6)


@icon("macrodialog")
def i_macro(cr):
    window(cr, 2.5, 3.5, 19, 17)
    tri(cr, 9, 9, 7, "right", ACC)


@icon("helpindex")
def i_help(cr):
    circle(cr, 12, 12, 9, ACC, None)
    centred(cr, "?", 12, 17, 13, PAPER, bold=True)


# --- outline / navigation
@icon("outlineleft", "decrementlevel")
def i_promote(cr):
    lines(cr, 10, 5, [10, 10, 10, 10], 4.5, INK, 1.4)
    arrow(cr, 8, 12, 2, 12, ACC, 3, 1.8)


@icon("outlineright", "incrementlevel")
def i_demote(cr):
    lines(cr, 10, 5, [10, 10, 10, 10], 4.5, INK, 1.4)
    arrow(cr, 2, 12, 8, 12, ACC, 3, 1.8)


@icon("decrementsublevels")
def i_promotesub(cr):
    bar(cr, 9, 5, 11, 1.4)
    lines(cr, 12, 10, [8, 8, 8], 3.5, GREY, 1.4)
    arrow(cr, 8, 13, 2, 13, ACC, 3, 1.8)


@icon("moveup")
def i_moveup(cr):
    arrow(cr, 12, 20, 12, 4, ACC, 5, 2.4)


@icon("movedown")
def i_movedown(cr):
    arrow(cr, 12, 4, 12, 20, ACC, 5, 2.4)


@icon("showdetail")
def i_expand(cr):
    rect(cr, 4.5, 4.5, 15, 15, PAPER, INK)
    line(cr, 8, 12, 16, 12, ACC, 2)
    line(cr, 12, 8, 12, 16, ACC, 2)


@icon("hidedetail")
def i_collapse(cr):
    rect(cr, 4.5, 4.5, 15, 15, PAPER, INK)
    line(cr, 8, 12, 16, 12, ACC, 2)


def _record(cr, kind):
    if kind in ("first", "prev"):
        tri(cr, 9, 6, 12, "left", ACC)
    else:
        tri(cr, 4, 6, 12, "right", ACC)
    if kind == "first":
        bar(cr, 5, 6, 2.4, 12, ACC)
    if kind == "last":
        bar(cr, 17, 6, 2.4, 12, ACC)


@icon("firstrecord")
def i_firstrec(cr):
    _record(cr, "first")


@icon("prevrecord")
def i_prevrec(cr):
    _record(cr, "prev")


@icon("nextrecord")
def i_nextrec(cr):
    _record(cr, "next")


@icon("lastrecord")
def i_lastrec(cr):
    _record(cr, "last")


@icon("datafilterautofilter")
def i_filter(cr):
    cr.move_to(3, 4)
    cr.line_to(21, 4)
    cr.line_to(14, 12)
    cr.line_to(14, 20)
    cr.line_to(10, 18)
    cr.line_to(10, 12)
    cr.close_path()
    _rgb(cr, ACC_LIGHT)
    cr.fill_preserve()
    _rgb(cr, ACC)
    cr.stroke()


@icon("dbviewtables")
def i_dbtables(cr):
    table(cr, 3.5, 4.5, 17, 15, 4, 3)


@icon("dbviewfunctions")
def i_dbfunctions(cr):
    rect(cr, 3.5, 3.5, 17, 17, PAPER, INK)
    centred(cr, "Σ", 12, 17, 12, ACC, bold=True)


# --- master documents (W3-07) and AutoFormat (W3-09)
def _subdoc(cr, x, y, w=11, h=13):
    """A small page with a corner tab: a subdocument."""
    page(cr, x, y, w, h, 3)
    text_lines(cr, x + 2, y + 5, w - 4, 2)


@icon("showmasterdocument")
def i_showmaster(cr):
    page(cr, 3.5, 2.5, 15, 19, 4)
    rect(cr, 6.5, 7.5, 9, 4, PALE, ACC)
    rect(cr, 6.5, 13.5, 9, 4, PALE, ACC)


@icon("collapsesubdocuments")
def i_collapsesub(cr):
    page(cr, 3.5, 2.5, 15, 19, 4)
    rect(cr, 6.5, 9.5, 9, 5, PALE, ACC)
    line(cr, 8.5, 12, 13.5, 12, ACC, 1.6)


@icon("createsubdocument")
def i_createsub(cr):
    _subdoc(cr, 4.5, 4.5)
    badge_plus(cr, 17, 18)


@icon("insertsubdocument")
def i_insertsub(cr):
    page(cr, 2.5, 2.5, 13, 17, 3)
    _subdoc(cr, 10.5, 9.5, 10, 12)
    arrow(cr, 3, 13, 9, 13, ACC, 2.5, 1.4)


@icon("unlinksubdocument")
def i_unlinksub(cr):
    _subdoc(cr, 4.5, 3.5)
    badge_x(cr, 17, 18)


@icon("mergesubdocuments")
def i_mergesub(cr):
    _subdoc(cr, 2.5, 3.5, 9, 11)
    _subdoc(cr, 12.5, 3.5, 9, 11)
    arrow(cr, 7, 16, 12, 20, ACC, 2.5, 1.4)
    arrow(cr, 17, 16, 12, 20, ACC, 2.5, 1.4)


@icon("splitsubdocument")
def i_splitsub(cr):
    _subdoc(cr, 6.5, 2.5, 10, 9)
    _subdoc(cr, 6.5, 13.5, 10, 9)
    cr.save()
    cr.set_dash([1.5, 1.5])
    line(cr, 3, 12, 21, 12, RED, 1.2)
    cr.restore()


@icon("lockdocument")
def i_lockdocument(cr):
    _subdoc(cr, 3.5, 2.5, 13, 16)
    lock(cr, 12.5, 13)


@icon("autoformat")
def i_autoformat(cr):
    page(cr, 3.5, 2.5, 14, 18, 4)
    bar(cr, 6, 7, 8, 2.2, ACC)
    text_lines(cr, 6, 12, 9, 3)
    star(cr, 18, 18, 3.4)
