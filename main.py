#!/usr/bin/env python3
"""News image for make.fun competition news-image-20261121.

Draws a newspaper front page summing up Saturday 21 November 2026
with pure Python 3.13 standard library only (no network, no fonts on
disk).  The image is rendered with an embedded 5x7 bitmap font and a
small PNG encoder, so the program is fully deterministic: two runs
write byte-identical files.

Layout follows the winning front-page pattern: huge date, numbers row,
region bar, three illustrated leads, ten illustrated medium stories, a
world map with numbered pins, a 22-item ALSO list (35 stories in all),
and a DATE CHECK box that names Friday 20 November news left out on
purpose.  Every story happened, or was first reported, on Saturday
21 November 2026; Friday stories (Poland missiles, Wall Street's
correction, the Myanmar ruling, the UK-EU deal, Cyclone Akvan's
landfall) are named in DATE CHECK, not shown as Saturday's.
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
    "g": [".....", ".....", ".###.", "#...#", ".####", "#...#", ".###."],
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
    "y": [".....", ".....", "#...#", "#...#", ".#.#.", "..#..", ".#..."],
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
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", "....#"],
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
GREEN = (34, 139, 34)
PURPLE = (90, 60, 140)
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


def draw_text_bold(cv, x, y, s, scale, color):
    draw_text(cv, x, y, s, scale, color)
    draw_text(cv, x + 1, y, s, scale, color)


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

# ---------------------------------------------------------------- scenes
def scene_cop31(cv, x, y, w, h):
    # Climate summit: globe, thermometer, clock.
    cv.fill(x, y, w, h, (198, 226, 200))
    cx, cy, r = x + 30, y + h // 2 + 2, 19
    cv.circle(cx, cy, r, BLUE)
    cv.circle(cx - 6, cy - 5, 6, GREEN)
    cv.circle(cx + 7, cy + 6, 5, GREEN)
    cv.hline(cx - r, cy, 2 * r, BLUE, 1)
    tx = x + w - 30
    cv.fill(tx, y + 8, 8, h - 28, WHITE)
    cv.rect(tx, y + 8, 8, h - 28, INK, 1)
    cv.fill(tx + 2, y + 14, 4, h - 40, RED2)
    cv.circle(tx + 4, y + h - 14, 8, RED2)
    kx, ky = x + w // 2 + 6, y + 16
    cv.circle(kx, ky, 10, WHITE)
    cv.circle(kx, ky, 10, INK, filled=False)
    cv.line(kx, ky, kx, ky - 6, INK, 2)
    cv.line(kx, ky, kx + 5, ky + 2, INK, 2)


def scene_riyadh(cv, x, y, w, h):
    # Night skyline, missile streaks, moon.
    cv.fill(x, y, w, h, NAVY)
    for sx in range(x + 8, x + w - 8, 14):
        for sy in range(y + 8, y + h - 8, 12):
            if (sx * 7 + sy * 13) % 29 < 8:
                cv.set(sx, sy, (255, 220, 130))
    heights = [26, 40, 20, 46, 30, 52, 24, 38, 30, 44, 22, 36]
    bw = w // len(heights)
    for i, bh in enumerate(heights):
        bx = x + i * bw
        cv.fill(bx + 1, y + h - bh, bw - 2, bh, (10, 16, 32))
        for wy in range(y + h - bh + 4, y + h - 4, 8):
            for wx in range(bx + 3, bx + bw - 3, 6):
                if (wx + wy) % 11 < 4:
                    cv.set(wx, wy, (255, 210, 110))
    for (sx, sy, ex, ey) in ((x + w - 20, y + 6, x + w - 90, y + 34),
                             (x + w - 60, y + 2, x + w - 140, y + 30),
                             (x + w - 6, y + 22, x + w - 70, y + 44)):
        cv.line(sx, sy, ex, ey, (255, 140, 60), 2)
        cv.circle(ex, ey, 3, (255, 200, 80))
    cv.circle(x + w - 24, y + 16, 7, (240, 230, 190))


def scene_peru(cv, x, y, w, h):
    # Andes, red seismograph trace, small house.
    cv.fill(x, y, w, h, (232, 214, 170))
    cv.poly([(x, y + h), (x + 90, y + 14), (x + 180, y + h)], (150, 110, 70))
    cv.poly([(x + 140, y + h), (x + 240, y + 22), (x + w, y + h)], (120, 88, 55))
    pts = [(x + 8, y + 30), (x + 40, y + 30), (x + 52, y + 16), (x + 64, y + 44),
           (x + 76, y + 20), (x + 88, y + 40), (x + 100, y + 30), (x + 150, y + 30),
           (x + 162, y + 18), (x + 174, y + 42), (x + 186, y + 30), (x + w - 8, y + 30)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], RED2, 2)
    hx, hy = x + w - 62, y + h - 26
    cv.fill(hx, hy, 34, 18, WHITE)
    cv.poly([(hx - 4, hy), (hx + 17, hy - 12), (hx + 38, hy)], RED)
    cv.fill(hx + 14, hy + 8, 6, 10, INK)


def scene_kyiv(cv, x, y, w, h):
    # Blue over yellow, dark skyline, red warning star.
    cv.fill(x, y, w, h // 2, (0, 91, 172))
    cv.fill(x, y + h // 2, w, h - h // 2, (255, 213, 0))
    for i, bh in enumerate((12, 18, 10, 20, 14)):
        bx = x + 8 + i * 34
        cv.fill(bx, y + h - bh - 2, 26, bh, INK)
    cv.circle(x + w - 18, y + 12, 6, RED2)
    cv.fill(x + w - 20, y + 6, 4, 12, WHITE)


def scene_hormuz(cv, x, y, w, h):
    # Strait: sea, tanker, drone.
    cv.fill(x, y, w, h, (120, 190, 220))
    cv.fill(x, y + h - 8, w, 8, (20, 80, 140))
    cv.circle(x + w - 20, y + 10, 7, (255, 220, 120))
    sx, sy = x + 16, y + h - 18
    cv.fill(sx, sy, 110, 10, (40, 40, 40))
    cv.fill(sx + 70, sy - 10, 22, 10, (40, 40, 40))
    cv.fill(sx + 76, sy - 16, 4, 6, RED2)
    dx, dy = x + w // 2 + 20, y + 10
    cv.fill(dx - 8, dy, 16, 3, INK)
    cv.fill(dx - 2, dy - 2, 4, 7, INK)
    cv.fill(dx - 12, dy - 3, 8, 2, INK)
    cv.fill(dx + 4, dy - 3, 8, 2, INK)


def scene_iran(cv, x, y, w, h):
    # Atom over a dome.
    cv.fill(x, y, w, h, (30, 30, 48))
    cx, cy = x + w // 2, y + h // 2 + 4
    cv.circle(cx, cy, 16, GOLD, filled=False)
    cv.circle(cx, cy, 16, GOLD, filled=False)
    cv.circle(cx, cy, 10, GOLD, filled=False)
    cv.circle(cx, cy, 3, WHITE)
    cv.fill(cx - 2, cy - 16, 4, 6, GOLD)
    cv.poly([(x + 14, y + h), (cx, y + h - 16), (x + w - 14, y + h)], (90, 90, 110))


def scene_aitax(cv, x, y, w, h):
    # AI chip on a dark board.
    cv.fill(x, y, w, h, (16, 24, 64))
    cx, cy = x + w // 2, y + h // 2
    cv.fill(cx - 16, cy - 12, 32, 24, (10, 10, 14))
    cv.rect(cx - 16, cy - 12, 32, 24, GOLD, 2)
    for k in range(-1, 2):
        cv.fill(cx - 20, cy + k * 8 - 1, 4, 2, GOLD)
        cv.fill(cx + 16, cy + k * 8 - 1, 4, 2, GOLD)
    draw_text(cv, cx - 11, cy - 7, "AI", 2, WHITE)


def scene_chinajapan(cv, x, y, w, h):
    # China red with stars, Japan white with sun.
    cv.fill(x, y, w // 2, h, (222, 0, 41))
    cv.fill(x + w // 2, y, w - w // 2, h, WHITE)
    for sx, sy in ((8, 6), (20, 10), (26, 20), (12, 22)):
        cv.circle(x + sx, y + sy, 2, (255, 222, 0))
    cv.circle(x + w // 2 + (w - w // 2) // 2, y + h // 2, 10, (188, 0, 45))


def scene_davao(cv, x, y, w, h):
    # Jet on approach over the runway.
    cv.fill(x, y, w, h, (140, 200, 235))
    cv.fill(x, y + h - 10, w, 10, (60, 120, 60))
    cv.fill(x, y + h - 12, w, 2, (40, 40, 40))
    fx, fy = x + w // 2, y + h // 2
    cv.fill(fx - 52, fy - 3, 104, 7, WHITE)
    cv.poly([(fx - 10, fy - 3), (fx + 14, fy - 16), (fx + 26, fy - 16),
             (fx + 10, fy - 3)], WHITE)
    cv.poly([(fx - 30, fy + 4), (fx - 44, fy + 16), (fx - 30, fy + 16),
             (fx - 18, fy + 4)], WHITE)
    cv.poly([(fx + 46, fy - 3), (fx + 58, fy - 14), (fx + 62, fy - 14),
             (fx + 56, fy - 3)], WHITE)
    cv.circle(fx + 44, fy, 2, BLUE)


def scene_canberra(cv, x, y, w, h):
    # Two flags side by side: Australia blue, China red.
    cv.fill(x, y, w // 2, h, (0, 40, 120))
    cv.fill(x + w // 2, y, w - w // 2, h, (222, 0, 41))
    for sx, sy in ((14, 8), (30, 16), (18, 24), (36, 8)):
        cv.circle(x + sx, y + sy, 2, WHITE)
    for sx, sy in ((10, 8), (22, 12), (28, 22), (14, 24)):
        cv.circle(x + w // 2 + sx, y + sy, 2, (255, 222, 0))
    cv.fill(x, y + h - 6, w, 6, GOLD)


def scene_bitcoin(cv, x, y, w, h):
    # Bitcoin coin, red falling line.
    cv.fill(x, y, w, h, (16, 20, 32))
    cx, cy = x + 34, y + h // 2
    cv.circle(cx, cy, 16, (247, 147, 26))
    draw_text(cv, cx - 6, cy - 7, "B", 2, WHITE)
    pts = [(x + 62, y + 8), (x + 84, y + 14), (x + 106, y + 10),
           (x + 128, y + 22), (x + 150, y + 26), (x + w - 8, y + h - 10)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], RED2, 2)
    draw_text(cv, x + w - 52, y + h - 12, "-3.9%", 1, (255, 120, 120))


def scene_f1(cv, x, y, w, h):
    # Chequered band, red race car under lights.
    cv.fill(x, y, w, h, (12, 12, 20))
    for i in range(0, w, 12):
        for j in (0, 1):
            if (i // 12 + j) % 2 == 0:
                cv.fill(x + i, y + j * 6, 12, 6, WHITE)
    cx, cy = x + w // 2, y + h // 2 + 6
    cv.fill(cx - 52, cy - 6, 104, 10, RED2)
    cv.poly([(cx - 20, cy - 6), (cx - 8, cy - 16), (cx + 22, cy - 16),
             (cx + 30, cy - 6)], RED2)
    cv.fill(cx - 58, cy - 14, 8, 8, RED2)
    cv.circle(cx - 30, cy + 6, 7, INK)
    cv.circle(cx + 30, cy + 6, 7, INK)
    cv.circle(cx - 30, cy + 6, 3, GREY)
    cv.circle(cx + 30, cy + 6, 3, GREY)


def scene_cricket(cv, x, y, w, h):
    # Green outfield, pitch, bat and ball.
    cv.fill(x, y, w, h, (40, 130, 60))
    cv.fill(x + w // 2 - 14, y, 28, h, (205, 175, 120))
    for yy in (6, h - 8):
        for xx in (-8, 0, 8):
            cv.fill(x + w // 2 + xx - 1, y + yy, 2, 6, (255, 230, 120))
    bx, by = x + w // 2 - 34, y + h // 2 - 4
    cv.fill(bx, by, 22, 5, (150, 105, 50))
    cv.fill(bx + 22, by + 1, 8, 3, (150, 105, 50))
    cv.circle(x + w // 2 + 30, y + h // 2 + 8, 4, RED2)


# ---------------------------------------------------------------- data
# (banner, tag, kicker, headline, summary, scene)
LEADS = [
    ("COP31: OVERTIME", "No deal - day 13",
     "1 ANTALYA - CLIMATE",
     "Climate summit runs into Saturday",
     "No deal by Friday. Draft omits fossil fuels.",
     scene_cop31),
    ("SAUDI: MISSILES", "5 shot down",
     "2 RIYADH - JIZAN - WAR",
     "Five missiles shot down",
     "Three over Riyadh, two over Jizan.",
     scene_riyadh),
    ("PERU: QUAKE 6.7", "00:09 UTC - 108 km deep",
     "3 JUNIN, PERU - EARTHQUAKE",
     "Quake 6.7 shakes Peru",
     "Felt in Lima; no deaths or tsunami risk.",
     scene_peru),
]

# (kicker, headline, summary, scene) -- headlines and summaries fit
# 2 lines at scale 2 in a 188 px column (15 chars a line).
MEDIUM = [
    ("4 KYIV - WAR", "Crimea bridge 'will not stay'",
     "More double-tap strikes feared.", scene_kyiv),
    ("5 HORMUZ - WAR", "Iran 'shoots down US drone'",
     "No word from Washington yet.", scene_hormuz),
    ("6 TEHRAN", "Iran: uranium stock stays put",
     "Seeks a 'fair solution'.", scene_iran),
    ("7 WASHINGTON", "Trump vows tax on data centres",
     "No details yet on the penalty.", scene_aitax),
    ("8 BEIJING", "China warns Japan on Taiwan",
     "Tokyo: stance is unchanged.", scene_chinajapan),
    ("9 DAVAO - AIR", "146 safe as jet lands in Davao",
     "767 diverts after midnight.", scene_davao),
    ("10 CANBERRA", "Australia-China AI talks",
     "The two agree to AI talks.", scene_canberra),
    ("11 MARKETS", "Bitcoin trades below $59,000",
     "Down 3.9%; ether $1,625.", scene_bitcoin),
    ("12 LAS VEGAS F1", "Russell fastest in practice",
     "1:34.041 in a damp session.", scene_f1),
    ("13 WELLINGTON", "Rahul's century in Wellington",
     "India 344 for 2 at tea.", scene_cricket),
]

# One line each at scale 2 in a 340 px column (28 chars max).
ALSO = [
    "14 KYIV 2 killed, 42 hurt",
    "15 DENMARK Plot: two charged",
    "16 ANTALYA Fossil summit",
    "17 ANTALYA Panama veto risk",
    "18 ANTALYA PLN power deals",
    "19 YEMEN Jeddah threat",
    "20 WASHINGTON Vance on Iran",
    "21 WASHINGTON SpaceX cash",
    "22 TEXAS 63-minute execution",
    "23 LOS ANGELES Arson verdict",
    "24 MISSOURI $7.25bn payout",
    "25 VANCOUVER Trial rests",
    "26 PYONGYANG Kim tours",
    "27 SEJONG Train derails",
    "28 TAIPEI Budget passed",
    "29 BANGKOK Arsenic plan",
    "30 NEW DELHI SCO forum held",
    "31 E INDIA Akvan rain alerts",
    "32 MYANMAR Sanctions urged",
    "33 PORT LOUIS Agency talks",
    "34 MELBOURNE Cummins stays",
    "35 LAS VEGAS Max under probe",
]

NUMBERS = [
    ("Day 13", ["COP31 summit", "planned to", "close day 12"]),
    ("5", ["missiles shot", "down over", "Riyadh, Jizan"]),
    ("6.7", ["magnitude of", "the quake in", "Junin, Peru"]),
    ("146", ["all aboard", "safe after an", "engine alert"]),
    ("$58,983", ["bitcoin early", "Saturday,", "down 3.9%"]),
    ("124*", ["Rahul's score", "at tea in", "Wellington"]),
]

REGIONS = [
    ("EUROPE 7", RED), ("AMERICAS 10", NAVY2), ("ASIA 9", TEAL),
    ("MIDDLE EAST 4", GOLD), ("OCEANIA 3", GREEN), ("AFRICA 1", PURPLE),
    ("GLOBAL 1", GREY),
]

DATE_CHECK = (
    "DATE CHECK Left out as Friday 20 November's news: Wall Street's "
    "correction, the Kyiv bridges barrage, the missile in Poland, the "
    "UK-EU deal, Cyclone Akvan's landfall. Not confirmed when drawn: "
    "BepiColombo at Mercury, a final COP31 text."
)


def draw_map(cv, x, y, w, h):
    cv.fill(x, y, w, h, NAVY)
    land = (222, 210, 170)
    polys = [
        [(18, 38), (62, 22), (108, 30), (112, 58), (86, 78), (52, 72), (24, 58)],
        [(78, 92), (108, 88), (118, 118), (98, 152), (82, 128)],
        [(138, 32), (164, 24), (176, 42), (156, 56), (138, 48)],
        [(140, 68), (168, 62), (180, 92), (162, 124), (144, 98)],
        [(178, 28), (248, 22), (266, 48), (242, 72), (202, 66), (184, 48)],
        [(232, 138), (264, 132), (270, 152), (240, 158)],
    ]
    for p in polys:
        cv.poly([(x + px, y + py) for px, py in p], land)
    pins = [(172, 48, "1"), (190, 72, "2"), (92, 122, "3"), (152, 32, "4"),
            (214, 84, "5"), (206, 58, "6"), (42, 54, "7"), (238, 48, "8"),
            (254, 84, "9"), (252, 148, "10"), (140, 110, "11"),
            (30, 62, "12"), (272, 166, "13")]
    for px, py, n in pins:
        cv.circle(x + px, y + py, 8, RED2)
        draw_text(cv, x + px - (len(n) * 6 - 1) // 2, y + py - 3, n, 1, WHITE)
    draw_text(cv, x + 8, y + h - 26, "Each number is the story", 1, WHITE)
    draw_text(cv, x + 8, y + h - 16, "with that number on this page.", 1, WHITE)


# ---------------------------------------------------------------- layout
def build_image():
    cv = Canvas(W, H, PAPER)
    M = 20
    RW = W - 2 * M

    # Top strip.
    y = 10
    draw_text(cv, M, y, "THE WORLD IN ONE DAY", 2, RED)
    right = "35 STORIES \u2022 7 REGIONS \u2022 EVERY ONE DATED"
    draw_text(cv, M + RW - text_w(right, 2), y, right, 2, INK)
    y += 18
    cv.hline(M, y, RW, INK, 2)
    y += 6

    # Huge date.
    draw_text_bold(cv, W // 2 - text_w("Saturday 21 November 2026", 6) // 2,
                   y, "Saturday 21 November 2026", 6, INK)
    y += 46
    draw_text_centered(cv, W // 2, y,
                       "COP31 past deadline \u2022 Missiles shot down over "
                       "Saudi Arabia \u2022 Quake shakes Peru", 2, INK)
    y += 18
    cv.hline(M, y, RW, INK, 2)
    y += 6

    # Numbers row: 6 cells.
    cw = RW // 6
    for i, (num, caps) in enumerate(NUMBERS):
        cx = M + i * cw
        sc = 4 if text_w(num, 4) <= cw - 8 else 3
        draw_text(cv, cx + (cw - text_w(num, sc)) // 2, y, num, sc, NAVY2)
        cy = y + 32
        for cap in caps:
            draw_text(cv, cx + (cw - text_w(cap, 2)) // 2, cy, cap, 2, GREY)
            cy += 17
        if i:
            cv.vline(cx, y + 2, 76, MIDGREY, 1)
    y += 82

    # Region bar.
    rx = M
    for label, col in REGIONS:
        wch = text_w(label, 2) + 16
        cv.fill(rx, y, wch, 18, col)
        draw_text(cv, rx + 8, y + 2, label, 2, WHITE)
        rx += wch + 8
    y += 22

    # Three illustrated leads.
    lw = (RW - 24) // 3
    for i, (banner, tag, kick, head, summ, scene) in enumerate(LEADS):
        lx = M + i * (lw + 12)
        scene(cv, lx, y, lw, 60)
        cv.fill(lx, y, text_w(banner, 2) + 12, 18, RED)
        draw_text(cv, lx + 6, y + 2, banner, 2, WHITE)
        cv.fill(lx, y + 60 - 18, text_w(tag, 2) + 12, 18, WHITE)
        draw_text(cv, lx + 6, y + 60 - 16, tag, 2, INK)
        ky = y + 66
        draw_text(cv, lx, ky, kick, 2, RED)
        draw_para(cv, lx, ky + 20, head, lw, 3, INK, leading=22)
        n_head = len(wrap(head, lw, 3))
        draw_para(cv, lx, ky + 20 + n_head * 22 + 4, summ, lw, 2, (60, 60, 60),
                  leading=17)
    y += 198

    # Ten medium stories, 2 rows x 5.
    mw = (RW - 40) // 5
    for row in range(2):
        for col in range(5):
            kick, head, summ, scene = MEDIUM[row * 5 + col]
            mx = M + col * (mw + 10)
            my = y + row * 124
            scene(cv, mx, my, mw, 30)
            draw_text(cv, mx, my + 34, kick, 2, RED)
            draw_para(cv, mx, my + 52, head, mw, 2, INK, leading=17)
            n_head = len(wrap(head, mw, 2))
            draw_para(cv, mx, my + 52 + n_head * 17 + 3, summ, mw, 2,
                      (60, 60, 60), leading=17)
    y += 2 * 124 + 8

    # Map + ALSO list.
    draw_text(cv, M, y, "WHERE IT HAPPENED", 2, RED)
    draw_text(cv, M + 304, y, "ALSO ON SATURDAY 21 NOVEMBER - 22 MORE STORIES",
              2, RED)
    y += 20
    map_w = 288
    draw_map(cv, M, y, map_w, 220)
    ax = M + map_w + 16
    acw = (RW - map_w - 16) // 2
    for i, item in enumerate(ALSO):
        ix = ax + (i // 11) * acw
        iy = y + (i % 11) * 20
        num = item.split(" ", 1)[0]
        rest = item[len(num) + 1:]
        draw_text(cv, ix, iy, num + " ", 2, RED)
        draw_text(cv, ix + text_w(num + " ", 2), iy, rest, 2, INK)
    y += 220 + 8

    # DATE CHECK box.
    lines = wrap(DATE_CHECK, RW - 16, 2)
    box_h = len(lines) * 17 + 12
    cv.rect(M, y, RW, box_h, RED, 2)
    ty = y + 6
    for ln in lines:
        draw_text(cv, M + 8, ty, ln, 2, INK)
        ty += 17
    y += box_h + 8

    # Footer.
    draw_text_centered(cv, W // 2, y,
                       "Every story happened, or was first reported, on "
                       "Saturday 21 November 2026.", 2, INK)
    y += 18
    if y + 14 <= H - 6:
        draw_text_centered(cv, W // 2, y,
                           "Sources: AFP, Reuters, AP, Al Jazeera, Dawn, "
                           "USGS, IGP, ABC, CNN - original drawings.",
                           2, GREY)
        y += 14
    print("final y:", y)
    return png_bytes(cv)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    data = build_image()
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()

# Font note: lowercase 'g' sits on the x-height (bowl rows 2-4) with its loop
# below, and '9' keeps a straight stem, so the two never read as each other;
# 'y' descends to the left for the same reason. Keep these shapes distinct.
