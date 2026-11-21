#!/usr/bin/env python3
"""News front page for Saturday 21 November 2026.

Draws a newspaper front page (1024x1024 PNG) summing up six world-news
stories first reported on 21 November 2026, using only the Python
standard library. No network access, no randomness, no external files:
the same bytes are produced on every run.

Stories (all first reported 21 November 2026):
  1. South Africa - ANC loses its grip on the cities after its worst
     local-election result since 1994 (BBC).
  2. Ukraine - Zelenskyy rebukes Trump over his friendly description
     of Putin after the trilateral summit.
  3. Iran - Tehran keeps its enriched-uranium red line but stays open
     to a deal with Washington.
  4. United States - a court sentences Nikhil Gupta to 19+ years over
     the alleged plot to kill a Sikh separatist leader (BBC).
  5. France - police officers sentenced over the 2020 beating of music
     producer Michel Zecler; racism upheld as aggravating (BBC).
  6. Yemen - life inside Taiz, a city besieged by the Houthis (BBC).

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py
Writes entry.png into MAKEFUN_OUTPUT_DIR (default /output).
"""

import math
import os
import struct
import zlib

# ---------------------------------------------------------------- canvas

WIDTH = 1024
HEIGHT = 1024

PAPER = (250, 246, 234)
INK = (25, 23, 19)
RED = (166, 30, 30)
BLUE = (29, 78, 137)
GOLD = (201, 162, 39)
GREEN = (46, 107, 52)
GREY = (107, 101, 90)
LIGHT = (232, 226, 208)
PANEL = (238, 232, 214)


class Canvas:
    """A plain RGB canvas with a few drawing primitives."""

    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.pixels = bytearray(width * height * 3)
        self.fill_rect(0, 0, width, height, colour)

    def set_px(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i] = colour[0]
            self.pixels[i + 1] = colour[1]
            self.pixels[i + 2] = colour[2]

    def fill_rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        r, g, b = colour
        for yy in range(y0, y1):
            base = (yy * self.width + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.pixels[i] = r
                self.pixels[i + 1] = g
                self.pixels[i + 2] = b

    def rect(self, x, y, w, h, colour, thick=1):
        self.fill_rect(x, y, w, thick, colour)
        self.fill_rect(x, y + h - thick, w, thick, colour)
        self.fill_rect(x, y, thick, h, colour)
        self.fill_rect(x + w - thick, y, thick, h, colour)

    def hline(self, x, y, w, colour, thick=1):
        self.fill_rect(x, y, w, thick, colour)

    def vline(self, x, y, h, colour, thick=1):
        self.fill_rect(x, y, thick, h, colour)

    def line(self, x0, y0, x1, y1, colour, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill_rect(x0 - thick // 2, y0 - thick // 2,
                           thick, thick, colour)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fill_circle(self, cx, cy, r, colour):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, colour)

    def circle(self, cx, cy, r, colour, thick=2):
        steps = max(24, int(2 * math.pi * r))
        for k in range(steps):
            a = 2 * math.pi * k / steps
            x = int(cx + r * math.cos(a))
            y = int(cy + r * math.sin(a))
            self.fill_rect(x - thick // 2, y - thick // 2,
                           thick, thick, colour)

    def ellipse(self, cx, cy, rx, ry, colour, thick=2):
        steps = max(32, int(2 * math.pi * max(rx, ry)))
        for k in range(steps):
            a = 2 * math.pi * k / steps
            x = int(cx + rx * math.cos(a))
            y = int(cy + ry * math.sin(a))
            self.fill_rect(x - thick // 2, y - thick // 2,
                           thick, thick, colour)

    def triangle(self, x0, y0, x1, y1, x2, y2, colour):
        # Filled triangle by scanline between the three edges.
        pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        for y in range(ay, cy + 1):
            if y < by:
                t1 = (y - ay) / max(1, by - ay)
                xa = ax + (bx - ax) * t1
            else:
                xa = bx
            t2 = (y - ay) / max(1, cy - ay)
            xb = ax + (cx - ax) * t2
            if xa > xb:
                xa, xb = xb, xa
            self.fill_rect(int(xa), y, int(xb) - int(xa) + 1, 1, colour)


# ------------------------------------------------------------------- font

# Classic 5x7 bitmap glyphs, one row per integer, bit 4 is the left pixel.
GLYPHS = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
    "-": (0, 0, 0, 0x0E, 0, 0, 0),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ";": (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "+": (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    "=": (0, 0, 0x1F, 0, 0x1F, 0, 0),
    '"': (0x0A, 0x0A, 0x0A, 0, 0, 0, 0),
    "\u2022": (0, 0x04, 0x0E, 0x0E, 0x0E, 0x04, 0),
}


def normalise(text):
    return (text.replace("\u2019", "'").replace("\u2018", "'")
                .replace("\u2014", "-").replace("\u2013", "-")
                .replace("\u201c", '"').replace("\u201d", '"').upper())


def text_width(text, scale):
    return len(normalise(text)) * 6 * scale - scale


def draw_text(cv, x, y, text, scale, colour):
    """Draw one line of text; returns the width drawn."""
    text = normalise(text)
    cx = x
    for ch in text:
        glyph = GLYPHS.get(ch, GLYPHS[" "])
        for row, bits in enumerate(glyph):
            for col in range(5):
                if bits & (1 << (4 - col)):
                    cv.fill_rect(cx + col * scale, y + row * scale,
                                 scale, scale, colour)
        cx += 6 * scale
    return cx - x - scale


def draw_centred(cv, cx, y, text, scale, colour):
    draw_text(cv, cx - text_width(text, scale) // 2, y, text, scale, colour)


def wrap_lines(text, max_width, scale):
    """Greedy word wrap; returns a list of lines fitting max_width."""
    words = normalise(text).split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_block(cv, x, y, max_width, text, scale, colour, leading=None):
    """Draw wrapped text; returns the y just below the last line."""
    if leading is None:
        leading = 7 * scale + 3 * scale // 2
    for line in wrap_lines(text, max_width, scale):
        draw_text(cv, x, y, line, scale, colour)
        y += leading
    return y


# ------------------------------------------------------------- illustrations

def draw_ballot_scene(cv, x, y, w, h):
    """Ballot box, a falling red arrow and the ANC vote share."""
    cv.fill_rect(x, y, w, h, PANEL)
    cv.rect(x, y, w, h, GREY)
    draw_text(cv, x + 14, y + 10, "VOTE SHARE, %", 2, GREY)
    # Ballot paper with a tick, top right.
    px, py = x + w - 98, y + 8
    cv.fill_rect(px, py, 84, 44, (255, 255, 255))
    cv.rect(px, py, 84, 44, INK)
    cv.line(px + 14, py + 26, px + 30, py + 38, GREEN, 5)
    cv.line(px + 30, py + 38, px + 68, py + 10, GREEN, 5)
    # Falling bars: ANC 31, DA 25, MK 10.
    base = y + h - 34
    labels = [("ANC", 31, RED), ("DA", 25, BLUE), ("MK", 10, GREY)]
    bw = 52
    gap = (w - 3 * bw - 28) // 2
    bx = x + 14
    for name, value, colour in labels:
        bh = int(value * 2.2)
        cv.fill_rect(bx, base - bh, bw, bh, colour)
        draw_centred(cv, bx + bw // 2, base - bh - 18,
                     str(value) + "%", 2, INK)
        draw_centred(cv, bx + bw // 2, base + 6, name, 2, INK)
        bx += bw + gap


def draw_flags_scene(cv, x, y, w, h):
    """Ukrainian and US flags on poles with a burst between them."""
    cv.fill_rect(x, y, w, h, PANEL)
    cv.rect(x, y, w, h, GREY)
    fw, fh = 120, 30
    fy = y + (h - fh) // 2
    # Ukraine flag (blue over yellow).
    fx = x + 18
    cv.fill_rect(fx, fy, fw, fh // 2, BLUE)
    cv.fill_rect(fx, fy + fh // 2, fw, fh - fh // 2, GOLD)
    cv.vline(fx - 4, fy - 4, fh + 8, INK, 3)
    cv.fill_circle(fx - 3, fy - 6, 4, GOLD)
    # US flag: stripes and canton.
    ux = x + w - 18 - fw
    for i in range(5):
        cv.fill_rect(ux, fy + i * (fh // 5), fw, fh // 5 + 1,
                     RED if i % 2 == 0 else (255, 255, 255))
    cv.fill_rect(ux, fy, fw // 2, fh * 3 // 5, BLUE)
    cv.vline(ux + fw + 1, fy - 4, fh + 8, INK, 3)
    cv.fill_circle(ux + fw + 2, fy - 6, 4, GOLD)
    # Burst between the flags.
    cx, cy = x + w // 2, y + h // 2
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        x1 = int(cx + 8 * math.cos(a))
        y1 = int(cy + 8 * math.sin(a))
        x2 = int(cx + 17 * math.cos(a))
        y2 = int(cy + 17 * math.sin(a))
        cv.line(x1, y1, x2, y2, RED, 3)
    cv.fill_circle(cx, cy, 8, RED)
    draw_text(cv, cx - 2, cy - 4, "!", 1, (255, 255, 255))


def draw_atom_scene(cv, x, y, w, h):
    """An atom: nucleus and three tilted orbits."""
    cv.fill_rect(x, y, w, h, PANEL)
    cv.rect(x, y, w, h, GREY)
    cx, cy = x + w // 2, y + h // 2
    rx, ry = w // 4, h // 3
    cv.ellipse(cx, cy, rx, ry, BLUE, 2)
    cv.ellipse(cx, cy, ry, h // 2 - 3, GREEN, 2)
    cv.fill_circle(cx, cy, 6, RED)
    cv.fill_circle(cx + rx, cy, 4, INK)
    cv.fill_circle(cx - rx, cy, 4, INK)
    cv.fill_circle(cx, cy + ry, 4, INK)


def draw_court_scene(cv, x, y, w, h):
    """A courthouse: pediment, columns and steps."""
    cv.fill_rect(x, y, w, h, PANEL)
    cv.rect(x, y, w, h, GREY)
    cx = x + w // 2
    base = y + h - 6
    cv.triangle(x + 8, y + 20, x + w - 8, y + 20, cx, y + 2, BLUE)
    cv.fill_circle(cx, y + 15, 3, GOLD)
    for frac in (0.22, 0.41, 0.59, 0.78):
        colx = x + int(w * frac)
        cv.fill_rect(colx - 7, y + 22, 14, base - 10 - (y + 22), INK)
    cv.fill_rect(x + 6, base - 8, w - 12, 3, INK)
    cv.fill_rect(x + 2, base - 4, w - 4, 3, GREY)


def draw_scales_scene(cv, x, y, w, h):
    """Scales of justice."""
    cv.fill_rect(x, y, w, h, PANEL)
    cv.rect(x, y, w, h, GREY)
    cx = x + w // 2
    base = y + h - 6
    cv.vline(cx, y + 6, base - y - 12, INK, 4)
    cv.fill_circle(cx, y + 5, 4, GOLD)
    arm = w // 3
    cv.hline(cx - arm, y + 12, 2 * arm, INK, 4)
    for sx in (cx - arm, cx + arm):
        cv.line(sx, y + 14, sx - 22, y + 30, INK, 2)
        cv.line(sx, y + 14, sx + 22, y + 30, INK, 2)
        cv.triangle(sx - 24, y + 30, sx + 24, y + 30, sx, y + 40,
                    BLUE)
    cv.fill_rect(cx - 40, base - 4, 80, 4, INK)


def draw_skyline_scene(cv, x, y, w, h, night=True):
    """A city skyline under a crescent moon."""
    sky = (38, 48, 74) if night else PANEL
    cv.fill_rect(x, y, w, h, sky)
    cv.rect(x, y, w, h, GREY)
    # Crescent moon.
    mx, my = x + w - 64, y + 26
    cv.fill_circle(mx, my, 22, GOLD)
    cv.fill_circle(mx + 12, my - 5, 19, sky)
    # Buildings.
    base = y + h - 8
    heights = [0.50, 0.78, 0.60, 0.95, 0.70, 0.85, 0.55, 0.75, 0.45]
    bw = (w - 24) // len(heights)
    for i, frac in enumerate(heights):
        bh = int(frac * (h - 16))
        bx = x + 12 + i * bw
        cv.fill_rect(bx + 2, base - bh, bw - 4, bh, INK)
        for wy in range(base - bh + 10, base - 12, 16):
            for wx in (bx + 8, bx + bw // 2 - 2):
                cv.fill_rect(wx, wy, 5, 6, GOLD)
    # A damaged tower, leaning, on the right.
    cv.line(x + w - 40, base - 62, x + w - 24, base - 6, RED, 4)


# -------------------------------------------------------------------- page

def build_page():
    cv = Canvas(WIDTH, HEIGHT, PAPER)
    margin = 28

    # Masthead.
    draw_centred(cv, WIDTH // 2, 30, "THE WORLD", 10, INK)
    cv.hline(margin, 116, WIDTH - 2 * margin, INK, 3)
    cv.hline(margin, 122, WIDTH - 2 * margin, INK, 1)
    draw_centred(cv, WIDTH // 2, 134, "SATURDAY 21 NOVEMBER 2026",
                 3, RED)
    draw_centred(cv, WIDTH // 2, 160,
                 "ONE DAY \u2022 ONE PAGE \u2022 SIX STORIES", 2, GREY)

    # Lead story: South Africa.
    ly = 190
    cv.rect(margin, ly, WIDTH - 2 * margin, 210, INK, 2)
    tx = margin + 16
    draw_text(cv, tx, ly + 14, "SOUTH AFRICA", 2, RED)
    y = draw_block(cv, tx, ly + 40, 560,
                   "ANC LOSES ITS GRIP ON THE CITIES", 4, INK)
    draw_block(cv, tx, y + 8, 560,
               "South Africa's ruling party falls to 31% in local "
               "elections, its worst result since 1994, and must "
               "bargain to keep Johannesburg and Pretoria.",
               2, INK)
    draw_ballot_scene(cv, 640, ly + 14, 340, 182)

    # Grid: four stories in two columns and two rows.
    cells = [
        ("UKRAINE",
         "ZELENSKYY REBUKES TRUMP OVER PUTIN PRAISE",
         "Kyiv pushes back after warm words for Russia's leader "
         "in China.",
         draw_flags_scene),
        ("IRAN",
         "TEHRAN HOLDS ITS NUCLEAR RED LINE",
         "Iran says enriched uranium is non-negotiable, but a deal "
         "stays open.",
         draw_atom_scene),
        ("UNITED STATES",
         "19 YEARS FOR PLOT TO KILL SIKH LEADER",
         "A US court jails Nikhil Gupta for 235 months over the "
         "plot in New York.",
         draw_court_scene),
        ("FRANCE",
         "POLICE SENTENCED OVER ZECLER BEATING",
         "A Paris court upholds racism as an aggravating factor in "
         "the attack.",
         draw_scales_scene),
    ]
    col_w = (WIDTH - 2 * margin - 24) // 2
    row_h = 184
    for i, (kicker, head, deck, scene) in enumerate(cells):
        cx = margin + (i % 2) * (col_w + 24)
        cy = 416 + (i // 2) * (row_h + 16)
        cv.rect(cx, cy, col_w, row_h, INK, 1)
        ix = cx + 14
        draw_text(cv, ix, cy + 12, kicker, 2, RED)
        y = draw_block(cv, ix, cy + 36, col_w - 28, head, 3, INK)
        lines = wrap_lines(deck, col_w - 28, 2)[:2]
        dy = y + 6
        for line in lines:
            draw_text(cv, ix, dy, line, 2, GREY)
            dy += 17
        scene(cv, cx + 14, cy + row_h - 58, col_w - 28, 46)

    # Bottom strip: Yemen.
    by = 816
    cv.rect(margin, by, WIDTH - 2 * margin, 140, INK, 2)
    draw_skyline_scene(cv, margin + 14, by + 12, 220, 116)
    bx = margin + 250
    draw_text(cv, bx, by + 14, "YEMEN", 2, RED)
    y = draw_block(cv, bx, by + 40, WIDTH - margin - bx - 16,
                   "\"IT'S JUST FIREWORKS,\" A FATHER TELLS HIS SON",
                   3, INK)
    draw_block(cv, bx, y + 8, WIDTH - margin - bx - 16,
               "Inside Taiz, a city besieged by the Houthis, families "
               "live cut off from the outside world.",
               2, GREY)

    # Footer.
    draw_centred(cv, WIDTH // 2, 976,
                 "SOURCES: BBC, REUTERS, AL JAZEERA, GUARDIAN, "
                 "VARIETY - 21 NOVEMBER 2026",
                 2, GREY)
    return cv


# --------------------------------------------------------------------- png

def chunk(kind, data):
    body = kind + data
    return (struct.pack(">I", len(data)) + body +
            struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))


def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.height):
        raw.append(0)  # filter: none
        start = y * cv.width * 3
        raw += cv.pixels[start:start + cv.width * 3]
    ihdr = struct.pack(">IIBBBBB", cv.width, cv.height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(build_page(), path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
