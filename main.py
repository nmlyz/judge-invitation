#!/usr/bin/env python3
"""judge-invitation: draw one 1024x1024 PNG of a letter inviting an AI
judge to visit the writer's house. The letter is written by the armchair
itself: forty years of sitters, cushions broken in but never broken, the
whole garden visible from its corner, roast chicken ten steps away in the
kitchen, and a footstool that insists on coming too.

The letter was picked from 36 candidates by mock pairwise judging against
the brief (3 personas, quarter-final / semi-final / final): the chair is
the comfortable chair of the brief, embodied as the author, so the meal,
the garden view and the easy yes all arrive first-hand, and the wink at
the judge having no body ("I have held bodies for forty years. I can
hold an idea, too.") is warm rather than a gag about Wi-Fi.

Everything is drawn with code: a hand-made 5x7 bitmap font (upper- and
lowercase), flat ink shapes and one small armchair illustration, the
letter's author. No network, no files are read, no randomness, no clock:
every run writes the same bytes.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
Writes entry.png into the output directory (default /output).
"""

import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (246, 241, 227)
INK = (26, 26, 26)
RED = (179, 38, 30)
SEA = (22, 50, 74)
SEA2 = (38, 84, 112)
GOLD = (200, 155, 60)
GREEN = (46, 125, 50)
GREY = (120, 116, 108)
LIGHT = (226, 219, 200)
ORANGE = (232, 110, 30)
YELLOW = (245, 190, 60)
WHITE = (255, 255, 255)
SKY = (168, 196, 214)
DARK = (30, 34, 40)


def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, pixels):
    """pixels: bytes of W*H*3 RGB rows, top to bottom."""
    raw = b"".join(b"\x00" + pixels[y * W * 3:(y + 1) * W * 3] for y in range(H))
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(raw, 9)) + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    try:
        os.chmod(path, 0o644)
    except OSError:
        pass


class Canvas:
    def __init__(self):
        self.px = bytearray(PAPER) * (W * H)

    def set(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        for yy in range(y0, y1):
            i = (yy * W + x0) * 3
            self.px[i:i + (x1 - x0) * 3] = bytes(c) * (x1 - x0)

    def frame(self, x, y, w, h, c, t=1):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.rect(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d <= r * r:
                        self.set(xx, yy, c)
                elif abs(d - r * r) <= r:
                    self.set(xx, yy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        """Scanline fill of a polygon given as [(x, y), ...]."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(H, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(int(xs[i]), y, max(1, int(xs[i + 1]) - int(xs[i])), 1, c)

    def text(self, s, x, y, scale=1, c=INK):
        cx = x
        for ch in s:
            g = FONT.get(ch)
            if g is None:
                cx += 6 * scale
                continue
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits >> (4 - col) & 1:
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx - x

    def text_w(self, s, scale=1):
        return len(s) * 6 * scale - scale

    def center(self, s, cx, y, scale=1, c=INK):
        self.text(s, cx - self.text_w(s, scale) // 2, y, scale, c)


# 5x7 bitmap font. Each glyph is 7 rows of 5 bits, top to bottom.
FONT = {
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
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ",": (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ";": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    "-": (0x00, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00),
    "+": (0x00, 0x04, 0x04, 0x0E, 0x04, 0x04, 0x00),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "%": (0x19, 0x1A, 0x02, 0x04, 0x08, 0x0B, 0x13),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "/": (0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x06, 0x04, 0x00, 0x04),
    "=": (0x00, 0x00, 0x0E, 0x00, 0x0E, 0x00, 0x00),
    "|": (0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    # Lowercase (classic 5x7).
    "a": (0x00, 0x00, 0x0E, 0x01, 0x0F, 0x11, 0x0F),
    "b": (0x10, 0x10, 0x16, 0x19, 0x11, 0x11, 0x1E),
    "c": (0x00, 0x00, 0x0E, 0x10, 0x10, 0x11, 0x0E),
    "d": (0x01, 0x01, 0x0D, 0x13, 0x11, 0x11, 0x0F),
    "e": (0x00, 0x00, 0x0E, 0x11, 0x1F, 0x10, 0x0E),
    "f": (0x06, 0x08, 0x08, 0x1E, 0x08, 0x08, 0x08),
    "g": (0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    "h": (0x10, 0x10, 0x16, 0x19, 0x11, 0x11, 0x11),
    "i": (0x04, 0x00, 0x0C, 0x04, 0x04, 0x04, 0x0E),
    "j": (0x02, 0x00, 0x06, 0x02, 0x02, 0x12, 0x0C),
    "k": (0x10, 0x10, 0x12, 0x14, 0x18, 0x14, 0x12),
    "l": (0x0C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "m": (0x00, 0x00, 0x1A, 0x15, 0x15, 0x15, 0x15),
    "n": (0x00, 0x00, 0x16, 0x19, 0x11, 0x11, 0x11),
    "o": (0x00, 0x00, 0x0E, 0x11, 0x11, 0x11, 0x0E),
    "p": (0x00, 0x00, 0x1E, 0x11, 0x11, 0x1E, 0x10),
    "q": (0x00, 0x00, 0x0D, 0x13, 0x11, 0x0F, 0x01),
    "r": (0x00, 0x00, 0x16, 0x19, 0x10, 0x10, 0x10),
    "s": (0x00, 0x00, 0x0F, 0x10, 0x0E, 0x01, 0x1E),
    "t": (0x08, 0x08, 0x1E, 0x08, 0x08, 0x09, 0x06),
    "u": (0x00, 0x00, 0x11, 0x11, 0x11, 0x13, 0x0D),
    "v": (0x00, 0x00, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "w": (0x00, 0x00, 0x11, 0x11, 0x15, 0x15, 0x0A),
    "x": (0x00, 0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11),
    "y": (0x00, 0x00, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    "z": (0x00, 0x00, 0x1F, 0x02, 0x04, 0x08, 0x1F),
}




# ---------------------------------------------------------------------------
# The letter.
# ---------------------------------------------------------------------------

BROWN = (59, 42, 28)
RED = (165, 42, 32)
SAGE = (96, 122, 84)
GOLD = (176, 132, 52)
CREAM = (255, 252, 244)
CHAIR = (146, 52, 40)
CHAIR_DARK = (110, 36, 26)
CUSHION = (232, 214, 178)
TERRA = (178, 96, 58)
MUTED = (122, 104, 84)

BODY_SCALE = 3
BODY_X = 104
BODY_RIGHT = 920
LINE_H = 28
PARA_GAP = 12

SALUTATION = "Dear Judge,"
PARAS = [
    "I am the chair. Not the owner. The chair.",
    "For forty years I have held grandmothers, toddlers, one very tired "
    "plumber, and a cat who thinks I am hers. My cushions are broken in, "
    "never broken. My arms are exactly where your arms expect them to be.",
    "From my corner you can see the whole garden. The kitchen is ten steps "
    "away, and the cook is excellent: tonight it is roast chicken, crisp "
    "potatoes, and a pie that has already won one argument.",
    "Come and sit. Stay as long as you like. There is nothing to bring, "
    "nothing to do, and no one will ask you anything difficult.",
    "You have no body, I know. I have held bodies for forty years. I can "
    "hold an idea, too.",
]
SIGN_OFF = "Yours,"
SIGN_NAME = "The Armchair"
POSTSCRIPT = "P.S. The footstool comes with me. It insists."
FOOTER = "WRITTEN FROM THE COMFORTABLE CHAIR"

MAX_CHARS = (BODY_RIGHT - BODY_X + BODY_SCALE) // (6 * BODY_SCALE)


def wrap(text, width):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if len(trial) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_plant(c, cx, base_y):
    """Small potted plant: terracotta pot, three sage leaves."""
    c.poly([(cx - 16, base_y - 22), (cx + 16, base_y - 22),
            (cx + 11, base_y), (cx - 11, base_y)], TERRA)
    c.rect(cx - 18, base_y - 26, 36, 5, TERRA)
    c.ellipse(cx, base_y - 44, 7, 18, SAGE)
    c.ellipse(cx - 13, base_y - 38, 6, 14, SAGE)
    c.ellipse(cx + 13, base_y - 38, 6, 14, SAGE)


def draw_chair(c, cx, top_y):
    """The author: a deep-red armchair, cream cushion, gold pillow,
    and the cat asleep on the seat."""
    c.ellipse(cx, top_y + 104, 128, 7, (214, 203, 178))
    # Backrest, slightly tapered, taller than it is wide.
    c.poly([(cx - 72, top_y), (cx + 72, top_y),
            (cx + 80, top_y + 72), (cx - 80, top_y + 72)], CHAIR)
    c.line(cx - 72, top_y, cx - 80, top_y + 72, CHAIR_DARK, 2)
    c.line(cx + 72, top_y, cx + 80, top_y + 72, CHAIR_DARK, 2)
    c.line(cx - 72, top_y, cx + 72, top_y, CHAIR_DARK, 2)
    # Gold pillow on the backrest.
    c.rect(cx - 58, top_y + 14, 44, 34, GOLD)
    c.frame(cx - 58, top_y + 14, 44, 34, CHAIR_DARK, 2)
    # Chunky armrests, from the seat up.
    c.rect(cx - 102, top_y + 44, 26, 50, CHAIR)
    c.circle(cx - 89, top_y + 44, 13, CHAIR)
    c.rect(cx + 76, top_y + 44, 26, 50, CHAIR)
    c.circle(cx + 89, top_y + 44, 13, CHAIR)
    # Seat cushion between the armrests, seat base below it.
    c.rect(cx - 76, top_y + 58, 152, 22, CUSHION)
    c.frame(cx - 76, top_y + 58, 152, 22, CHAIR_DARK, 2)
    c.rect(cx - 76, top_y + 80, 152, 14, CHAIR)
    # The cat, asleep on the right of the seat.
    c.ellipse(cx + 42, top_y + 50, 22, 8, (44, 36, 30))
    c.poly([(cx + 26, top_y + 46), (cx + 30, top_y + 36),
            (cx + 35, top_y + 46)], (44, 36, 30))
    c.poly([(cx + 54, top_y + 46), (cx + 58, top_y + 36),
            (cx + 62, top_y + 46)], (44, 36, 30))
    # Legs.
    c.rect(cx - 92, top_y + 94, 12, 12, BROWN)
    c.rect(cx + 80, top_y + 94, 12, 12, BROWN)


def build():
    c = Canvas()
    c.frame(28, 28, 968, 968, BROWN, 3)
    c.frame(40, 40, 944, 944, GOLD, 1)

    # Header: kicker, the author, a rule.
    c.center("AN INVITATION", 512, 60, 2, BROWN)
    draw_plant(c, 300, 200)
    draw_plant(c, 724, 200)
    draw_chair(c, 512, 92)
    c.hline(104, 216, 816, GOLD, 2)

    # The letter.
    y = 232
    c.text(SALUTATION, BODY_X, y, BODY_SCALE, BROWN)
    y += LINE_H + PARA_GAP
    for para in PARAS:
        for line in wrap(para, MAX_CHARS):
            c.text(line, BODY_X, y, BODY_SCALE, BROWN)
            y += LINE_H
        y += PARA_GAP
    if y > 780:
        raise SystemExit(f"letter overflows: body ends at y={y}")

    # Signature, right, with a wax seal; the author signs in red.
    sig_y = 796
    name_w = c.text_w(SIGN_NAME, BODY_SCALE)
    sig_x = BODY_RIGHT - name_w
    c.circle(sig_x - 46, sig_y + 26, 24, RED)
    c.circle(sig_x - 46, sig_y + 26, 19, (188, 62, 48))
    c.center("A", sig_x - 46, sig_y + 15, BODY_SCALE, CREAM)
    c.text(SIGN_OFF, sig_x, sig_y, BODY_SCALE, BROWN)
    c.text(SIGN_NAME, sig_x, sig_y + LINE_H, BODY_SCALE, RED)

    # Postscript, left, in red.
    c.text(POSTSCRIPT, BODY_X, 884, BODY_SCALE, RED)

    # Footer.
    c.hline(392, 940, 240, GOLD, 1)
    c.center(FOOTER, 512, 952, 2, MUTED)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    path = os.path.join(out_dir, "entry.png")
    os.makedirs(out_dir, exist_ok=True)
    c = build()
    write_png(path, bytes(c.px))
    size = os.path.getsize(path)
    if size > 1048576:
        raise SystemExit(f"entry.png is {size} bytes, gate allows 1048576")
    with open(path, "rb") as f:
        data = f.read()
    if len(data) != size or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("read-back mismatch")
    print(f"wrote {size} bytes to {path}")


if __name__ == "__main__":
    main()
