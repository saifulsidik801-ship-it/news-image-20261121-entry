#!/usr/bin/env python3
"""News image for make.fun competition news-image-20261121.

Draws a newspaper front page summing up Saturday 21 November 2026
with pure Python 3.13 standard library only (no network, no fonts on
disk).  The image is rendered with an embedded 5x7 bitmap font and a
small PNG encoder, so the program is fully deterministic: two runs
write byte-identical files.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- font
# 5x7 bitmap font.  Each glyph is 7 rows of 5 characters ('#' = ink).
FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "J": ["..###", "....#", "....#", "....#", "....#", "#...#", ".###."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "a": [".....", ".....", ".###.", "....#", ".####", "#...#", ".###."],
    "b": ["#....", "#....", "####.", "#...#", "#...#", "#...#", "####."],
    "c": [".....", ".....", ".####", "#....", "#....", "#....", ".####"],
    "d": ["....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"],
    "e": [".....", ".....", ".###.", "#...#", "#####", "#....", ".###."],
    "f": ["..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."],
    "g": [".....", ".###.", "#...#", "#...#", ".####", "....#", ".###."],
    "h": ["#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"],
    "i": [".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."],
    "j": ["....#", ".....", "...##", "....#", "....#", "#...#", ".###."],
    "k": ["#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."],
    "l": [".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "m": [".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"],
    "n": [".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"],
    "o": [".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."],
    "p": [".....", ".....", "####.", "#...#", "#...#", "####.", "#...."],
    "q": [".....", ".....", ".####", "#...#", "#...#", ".####", "....#"],
    "r": [".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."],
    "s": [".....", ".....", ".####", "#....", ".###.", "....#", "####."],
    "t": [".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."],
    "u": [".....", ".....", "#...#", "#...#", "#...#", "#...#", ".###."],
    "v": [".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "w": [".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "x": [".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"],
    "y": [".....", ".....", "#...#", "#...#", "#...#", ".####", "....#"],
    "z": [".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"],
    "0": [".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    ".": [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    ",": [".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."],
    ":": [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    ";": [".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "/": ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    "'": ["..#..", "..#..", ".....", ".....", ".....", ".....", "....."],
    '"': [".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."],
    "(": ["...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."],
    ")": [".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."],
    "%": ["##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    "=": [".....", ".....", "#####", ".....", "#####", ".....", "....."],
    "&": [".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"],
    "$": ["..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."],
    "#": [".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."],
    "@": [".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."],
    "*": [".....", "#...#", ".#.#.", "#####", ".#.#.", "#...#", "....."],
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
}
# Aliases for typographic characters used in the copy.
FONT["\u2019"] = FONT["'"]
FONT["\u201c"] = FONT['"']
FONT["\u201d"] = FONT['"']
FONT["\u2013"] = FONT["-"]
FONT["\u2014"] = FONT["-"]
FONT["\u2022"] = [".....", ".....", ".##..", ".##..", ".##..", ".....", "....."]

for _ch, _g in FONT.items():
    assert len(_g) == 7, _ch
    for _row in _g:
        assert len(_row) == 5, (_ch, _row)

# ---------------------------------------------------------------- canvas
PAPER = (247, 243, 232)
INK = (20, 20, 20)
NAVY = (20, 33, 61)
NAVY2 = (28, 48, 88)
RED = (185, 28, 28)
RED2 = (220, 38, 38)
BLUE = (29, 78, 216)
TEAL = (13, 116, 128)
GOLD = (180, 130, 20)
WHITE = (255, 255, 255)
GREY = (90, 90, 90)
LIGHT = (238, 232, 216)
MIDGREY = (200, 194, 178)


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c, t=1):
        self.fill(x, y, w, t, c)
        self.fill(x, y + h - t, w, t, c)
        self.fill(x, y, t, h, c)
        self.fill(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=1):
        self.fill(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        for s in range(steps + 1):
            x = x0 + dx * s // steps
            y = y0 + dy * s // steps
            self.fill(x - t // 2, y - t // 2, t, t, c)

    def circle(self, cx, cy, r, c, filled=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if filled:
                    if d <= r * r:
                        self.set(xx, yy, c)
                else:
                    if r * r - 2 * r <= d <= r * r:
                        self.set(xx, yy, c)

    def poly(self, pts, c):
        # Scanline fill of a simple polygon.
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) // (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(xs[k], xs[k + 1] + 1):
                    self.set(x, y, c)


# ---------------------------------------------------------------- text
def text_w(s, scale):
    return len(s) * 6 * scale


def draw_text(cv, x, y, s, scale, color):
    cx = x
    for ch in s:
        g = FONT.get(ch)
        if g is None:
            g = FONT["?"]
        for r in range(7):
            row = g[r]
            for col in range(5):
                if row[col] == "#":
                    cv.fill(cx + col * scale, y + r * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def draw_text_centered(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, color)


def wrap(s, max_w, scale):
    words = s.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, s, max_w, scale, color, leading=None):
    if leading is None:
        leading = 7 * scale + 4
    lines = wrap(s, max_w, scale)
    for ln in lines:
        draw_text(cv, x, y, ln, scale, color)
        y += leading
    return y


# ---------------------------------------------------------------- png
def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", comp)
        + chunk(b"IEND", b"")
    )

# ---------------------------------------------------------------- icons
def icon_chart(cv, x, y, w, h):
    # Falling market chart: axes + red descending line + bars.
    cv.hline(x, y + h - 8, w, INK, 2)
    cv.vline(x, y, h - 8, INK, 2)
    pts = [(x + 6, y + 10), (x + 20, y + 22), (x + 34, y + 18),
           (x + 48, y + 38), (x + 62, y + 52), (x + w - 6, y + h - 16)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], RED2, 3)
    for px, py in pts:
        cv.circle(px, py, 3, RED2)
    cv.line(x + 6, y + 6, x + w - 6, y + 6, GREY, 1)


def icon_tent(cv, x, y, w, h):
    # Aid tent in the rain + supply box.
    cv.poly([(x + 8, y + h - 10), (x + w // 2, y + 14), (x + w - 8, y + h - 10)], TEAL)
    cv.poly([(x + w // 2 - 8, y + h - 10), (x + w // 2, y + h - 26),
             (x + w // 2 + 8, y + h - 10)], INK)
    for dx in (4, 16, 28):
        cv.line(x + dx, y + 4, x + dx - 3, y + 12, BLUE, 2)
    cv.fill(x + w - 22, y + h - 22, 16, 12, GOLD)
    cv.hline(x + w - 22, y + h - 16, 16, INK, 2)


def icon_crowd(cv, x, y, w, h):
    # Marchers with a placard.
    for i, dx in enumerate((6, 22, 38)):
        cv.circle(x + dx + 6, y + 16, 6, NAVY2)
        cv.fill(x + dx, y + 24, 12, h - 32, NAVY2 if i != 1 else RED)
    cv.vline(x + w - 16, y + 6, h - 14, INK, 2)
    cv.fill(x + w - 34, y + 6, 34, 18, WHITE)
    cv.rect(x + w - 34, y + 6, 34, 18, RED, 2)
    cv.fill(x + w - 30, y + 12, 12, 3, RED)
    cv.fill(x + w - 30, y + 17, 20, 3, INK)


def icon_globe(cv, x, y, w, h):
    # Globe with a leaf: climate talks.
    cx, cy, r = x + w // 2 - 6, y + h // 2, min(w, h) // 2 - 6
    cv.circle(cx, cy, r, BLUE, filled=False)
    cv.circle(cx, cy, r, BLUE, filled=False)
    for rr in (r // 2,):
        for yy in range(cy - rr, cy + rr + 1):
            dx = int((rr * rr - (yy - cy) ** 2) ** 0.5)
            cv.set(cx - dx, yy, BLUE)
            cv.set(cx + dx, yy, BLUE)
    cv.hline(cx - r, cy, 2 * r, BLUE, 1)
    # Leaf: diamond blade + stem, sitting on the globe's edge.
    cv.poly([(cx + 8, cy + 4), (cx + 24, cy - 14), (cx + 30, cy + 2),
             (cx + 16, cy + 12)], (34, 139, 34))
    cv.line(cx + 8, cy + 4, cx + 2, cy + 12, (34, 139, 34), 2)


def lead_art(cv, x, y, w, h):
    # Night map panel: graticule, missile streaks, blast marker, NATO star.
    import math
    cv.fill(x, y, w, h, NAVY)
    for gx in range(x + 28, x + w, 56):
        cv.vline(gx, y, h, (38, 60, 100), 1)
    for gy in range(y + 28, y + h, 56):
        cv.hline(x, gy, w, (38, 60, 100), 1)
    # Abstract landmass.
    cv.poly([(x + 30, y + h - 40), (x + 90, y + 70), (x + 180, y + 40),
             (x + 250, y + 90), (x + 300, y + 160), (x + 260, y + h - 30),
             (x + 120, y + h - 16)], (52, 78, 128))
    # Missile streaks coming in from the top right.
    for i, (sx, sy, ex, ey) in enumerate((
            (x + w - 30, y + 18, x + 190, y + 150),
            (x + w - 70, y + 8, x + 150, y + 132),
            (x + w - 10, y + 70, x + 210, y + 168))):
        cv.line(sx, sy, ex, ey, RED2, 3)
        cv.line(sx, sy, ex, ey, (255, 120, 120), 1)
        cv.circle(ex, ey, 5, (255, 200, 80))
    # Blast marker.
    bx, by = x + 178, y + 148
    for r, c in ((26, (255, 90, 90)), (18, RED2), (10, (255, 200, 80))):
        cv.circle(bx, by, r, c)
    for k in range(8):
        ang = k * math.pi / 4
        ex = bx + int(34 * math.cos(ang))
        ey = by + int(34 * math.sin(ang))
        cv.line(bx, by, ex, ey, (255, 200, 80), 2)
    # NATO compass star, top left.
    sx, sy = x + 44, y + 44
    cv.circle(sx, sy, 26, WHITE, filled=False)
    cv.poly([(sx, sy - 24), (sx + 6, sy - 6), (sx + 24, sy), (sx + 6, sy + 6),
             (sx, sy + 24), (sx - 6, sy + 6), (sx - 24, sy), (sx - 6, sy - 6)], WHITE)
    draw_text(cv, sx + 34, sy - 8, "NATO", 2, WHITE)
    draw_text(cv, x + 24, y + h - 34, "POLAND", 2, WHITE)
    draw_text(cv, x + 24, y + h - 58, "MISSILES CROSS", 2, (255, 150, 150))


# ---------------------------------------------------------------- layout
def build_image():
    cv = Canvas(W, H, PAPER)
    M = 24
    RW = W - 2 * M

    # Masthead.
    cv.fill(M, M, RW, 118, NAVY)
    cv.fill(M, M + 118, RW, 6, RED)
    draw_text_centered(cv, W // 2, M + 16, "THE WORLD IN ONE DAY", 6, WHITE)
    draw_text_centered(cv, W // 2, M + 70, "SATURDAY 21 NOVEMBER 2026", 3, (255, 210, 90))
    draw_text_centered(cv, W // 2, M + 96, "THE DAY'S NEWS IN ONE IMAGE", 2, (200, 210, 230))

    # Lead story.
    ly = M + 142
    lh = 300
    tx = M
    tw = 560
    draw_text(cv, tx, ly + 6, "POLAND  •  NATO", 2, RED)
    cv.hline(tx, ly + 28, tw, INK, 2)
    hy = ly + 44
    draw_text(cv, tx, hy, "RUSSIAN", 5, INK)
    draw_text(cv, tx, hy + 42, "MISSILES HIT", 5, INK)
    draw_text(cv, tx, hy + 84, "POLAND", 5, RED)
    sy = hy + 138
    draw_para(cv, tx, sy, "Two Russian missiles and a suspected drone came down in Poland. Warsaw calls it a deliberate provocation; NATO calls it a grave violation of its airspace.", tw, 2, INK)
    ax = M + 584
    aw = RW - 584
    lead_art(cv, ax, ly, aw, lh)

    # Secondary stories, 2 x 2.
    gy = ly + lh + 22
    gh = 148
    gw = (RW - 24) // 2
    panels = [
        ("MARKETS", "WALL STREET SLUMPS INTO CORRECTION",
         "S&P 500 falls 3.7% as AI shares sell off; Nasdaq down over 5%.", icon_chart, RED),
        ("MIDDLE EAST", "AID PLEA FOR FLOODED GAZA",
         "Australia, Canada, Italy and the UK urge Israel to let in 150,000 tents stuck at the border.", icon_tent, TEAL),
        ("EUROPE", "FRANCE MARCHES FOR 4TH WEEKEND",
         "146,000 protest living costs across France; 46,000 in Paris.", icon_crowd, NAVY2),
        ("CLIMATE", "COP31 ENTERS FINAL STRETCH",
         "Fossil fuels and climate finance top the agenda in Turkey.", icon_globe, (34, 139, 34)),
    ]
    for i, (kick, head, summ, icon, col) in enumerate(panels):
        px = M + (i % 2) * (gw + 24)
        py = gy + (i // 2) * (gh + 18)
        cv.fill(px, py, gw, gh, WHITE)
        cv.rect(px, py, gw, gh, INK, 2)
        cv.fill(px, py, 8, gh, col)
        ix = px + gw - 92
        iy = py + 12
        icon(cv, ix, iy, 76, 56)
        draw_text(cv, px + 20, py + 10, kick, 2, col)
        draw_para(cv, px + 20, py + 32, head, gw - 116, 3, INK, leading=26)
        n_head_lines = len(wrap(head, gw - 116, 3))
        draw_para(cv, px + 20, py + 32 + n_head_lines * 26 + 4, summ, gw - 40, 2, (60, 60, 60))

    # Also today, 3 x 2.
    ay = gy + 2 * gh + 18 + 18
    draw_text(cv, M, ay, "ALSO TODAY", 2, RED)
    cv.hline(M, ay + 20, RW, INK, 2)
    items = [
        ("CYCLONE AKVAN", "crosses India's Odisha coast"),
        ("ISRAEL", "Eisenkot tapped to form government"),
        ("EVEREST", "two helicopters collide; one dead"),
        ("SCIENCE", "pancreatic-cancer pill hailed a breakthrough"),
        ("NIGERIA", "states to run their own police"),
        ("CULTURE", "Robert Pattinson is the next James Bond"),
    ]
    cw = (RW - 48) // 3
    for i, (lead, rest) in enumerate(items):
        cx = M + (i % 3) * (cw + 24)
        cy = ay + 32 + (i // 3) * 64
        draw_text(cv, cx, cy, lead, 2, INK)
        draw_para(cv, cx, cy + 20, rest, cw, 2, (60, 60, 60))

    # Footer.
    fy = ay + 32 + 2 * 64 + 16
    cv.hline(M, fy, RW, INK, 2)
    draw_text_centered(cv, W // 2, fy + 12, "UK and EU sign landmark food, carbon and youth deals in Brussels", 2, INK)
    return png_bytes(cv)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    data = build_image()
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
