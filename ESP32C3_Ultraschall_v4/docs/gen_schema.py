#!/usr/bin/env python3
"""Erzeugt schema_prototyp.svg (Schaltplan Lochraster-Prototyp). Aufruf: python gen_schema.py"""
import os

W, H = 1400, 880
out = []
INK, PWR, SIG, GNDC = "#222", "#c0392b", "#1f5fae", "#222"


def e(s):
    out.append(s)


def line(*pts, c=INK, w=2):
    p = " ".join(f"{x},{y}" for x, y in pts)
    e(f'<polyline points="{p}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linejoin="round"/>')


def text(x, y, s, size=14, anchor="start", c=INK, weight="normal", style="normal"):
    s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    e(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{c}" '
      f'font-weight="{weight}" font-style="{style}">{s}</text>')


def dot(x, y):
    e(f'<circle cx="{x}" cy="{y}" r="4" fill="{INK}"/>')


def gnd(x, y):
    """GND-Symbol, Anschluss oben bei (x, y)."""
    line((x, y), (x, y + 12))
    for i, hw in enumerate((12, 8, 4)):
        line((x - hw, y + 12 + i * 4), (x + hw, y + 12 + i * 4))


def res_v(x, y1, y2, name, val):
    """Widerstand senkrecht zwischen y1 und y2."""
    m = (y1 + y2) / 2
    line((x, y1), (x, m - 20))
    line((x, m + 20), (x, y2))
    e(f'<rect x="{x - 7}" y="{m - 20}" width="14" height="40" fill="#fff" stroke="{INK}" stroke-width="2"/>')
    text(x + 12, m - 2, name, 13)
    text(x + 12, m + 14, val, 13, weight="bold")


def res_h(x1, x2, y, name, val):
    m = (x1 + x2) / 2
    line((x1, y), (m - 20, y))
    line((m + 20, y), (x2, y))
    e(f'<rect x="{m - 20}" y="{y - 7}" width="40" height="14" fill="#fff" stroke="{INK}" stroke-width="2"/>')
    text(m, y - 12, f"{name} {val}", 13, "middle")


def cap_v(x, y1, y2, name, val, polar=False):
    m = (y1 + y2) / 2
    line((x, y1), (x, m - 4))
    line((x, m + 4), (x, y2))
    line((x - 12, m - 4), (x + 12, m - 4), w=2.5)
    if polar:
        e(f'<path d="M{x - 12},{m + 8} Q{x},{m + 2} {x + 12},{m + 8}" fill="none" stroke="{INK}" stroke-width="2.5"/>')
        text(x - 22, m - 6, "+", 14)
    else:
        line((x - 12, m + 4), (x + 12, m + 4), w=2.5)
    text(x + 16, m - 2, name, 13)
    text(x + 16, m + 14, val, 13, weight="bold")


def label(x, y, s, side="left", c=SIG):
    """Netzlabel am Leitungsende (x, y)."""
    a = "end" if side == "left" else "start"
    dx = -6 if side == "left" else 6
    text(x + dx, y + 5, s, 14, a, c, "bold")


def box(x, y, w, h, title, sub=None):
    e(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#f6f8fb" stroke="{INK}" stroke-width="2"/>')
    text(x + w / 2, y + 22, title, 15, "middle", weight="bold")
    if sub:
        text(x + w / 2, y + 40, sub, 12, "middle", "#555")


def pin(x, y, name, side, length=20):
    """Pin an der Boxkante; side = Seite der Box ('left'/'right'). Gibt Leitungsende zurueck."""
    if side == "left":
        line((x, y), (x - length, y))
        text(x + 8, y + 5, name, 13)
        return x - length, y
    line((x, y), (x + length, y))
    text(x - 8, y + 5, name, 13, "end")
    return x + length, y


# ---------------- Hintergrund + Titel ----------------
e(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
text(30, 40, "Tankmonitor Prototyp (Streifenraster): ESP32-C3 SuperMini + 2x TOF200C (I2C) + 18650", 20, weight="bold")

# ---------------- Akku + Lader ----------------
bx = 80
line((bx, 160), (bx, 186))
line((bx - 16, 186), (bx + 16, 186), w=3)
line((bx - 9, 194), (bx + 9, 194), w=3)
line((bx - 16, 202), (bx + 16, 202), w=3)
line((bx - 9, 210), (bx + 9, 210), w=3)
line((bx, 210), (bx, 240))
text(bx - 30, 190, "+", 16, weight="bold")
text(bx + 24, 194, "BT1", 13)
text(bx + 24, 210, "18650", 13, weight="bold")
text(bx - 40, 270, "Akkuhalter", 12, c="#555")

box(190, 120, 160, 160, "TP4056")
text(270, 200, "Lader mit", 12, "middle", "#555")
text(270, 214, "DW01-Schutz", 12, "middle", "#555")
text(270, 268, "USB-C = Laden", 12, "middle", "#555")
l_bp = pin(190, 160, "B+", "left", 20)
l_bm = pin(190, 240, "B−", "left", 20)
r_op = pin(350, 160, "OUT+", "right", 20)
r_om = pin(350, 240, "OUT−", "right", 20)
line((bx, 160), l_bp)
line((bx, 240), l_bm)
line(r_om, (395, 240))
gnd(395, 240)
text(408, 236, "GND = OUT−", 12, c="#555")
text(408, 250, "(nicht B−!)", 12, c="#555")

# Schalter SW1
sx1, sx2 = 410, 460
line(r_op, (sx1, 160))
e(f'<circle cx="{sx1}" cy="160" r="4" fill="#fff" stroke="{INK}" stroke-width="2"/>')
e(f'<circle cx="{sx2}" cy="160" r="4" fill="#fff" stroke="{INK}" stroke-width="2"/>')
line((sx1 + 3, 158), (sx2 - 4, 140))
text((sx1 + sx2) / 2, 128, "SW1 Kippschalter", 13, "middle")

# VBAT_SW -> ESP 5V
ESP_X, ESP_Y, ESP_W, ESP_H = 640, 120, 200, 560
line((sx2 + 4, 160), (ESP_X - 20, 160), c=PWR, w=2.5)
text(540, 152, "VBAT_SW (3,0–4,2 V)", 13, "middle", PWR, "bold")
dot(500, 160)

# Batteriemessung
line((500, 160), (500, 330))
text(430, 300, "Akkumessung", 13, "middle", SIG, "bold")
text(430, 316, "(hochohmig, 1:2)", 12, "middle", "#555")
res_v(500, 330, 410, "R1", "1M")
line((500, 410), (500, 440))
dot(500, 440)
line((500, 440), (ESP_X - 20, 440))
text(560, 432, "VBDIV", 13, "middle", SIG, "bold")
res_v(500, 440, 520, "R2", "1M")
gnd(500, 520)
dot(580, 440)
cap_v(580, 440, 520, "C1", "100nF")
gnd(580, 520)

# ---------------- ESP32-C3 ----------------
box(ESP_X, ESP_Y, ESP_W, ESP_H, "ESP32-C3", "SuperMini (USB-C)")
pin(ESP_X, 160, "5V", "left")
p = pin(ESP_X, 220, "GND", "left")
line(p, (ESP_X - 40, 220))
gnd(ESP_X - 40, 220)
p = pin(ESP_X, 300, "3V3", "left")
line(p, (ESP_X - 40, 300), c=PWR)
label(ESP_X - 40, 300, "3V3", "left", PWR)
pin(ESP_X, 440, "GPIO1 (ADC)", "left")
text(ESP_X + ESP_W / 2, ESP_Y + ESP_H - 36, "USB-C am ESP:", 12, "middle", PWR, "bold")
text(ESP_X + ESP_W / 2, ESP_Y + ESP_H - 20, "nur mit SW1 AUS!", 12, "middle", PWR, "bold")

# ---------------- Stuetzkondensator ----------------
RAIL_Y = 150
line((900, RAIL_Y), (960, RAIL_Y), c=PWR)
label(900, RAIL_Y, "3V3", "left", PWR)
cap_v(960, RAIL_Y, 250, "C2", "1µF", polar=True)
gnd(960, 250)

# ---------------- ESP-Pins zu den Sensoren (Netzlabels) ----------------
for y, gp, net in ((300, "GPIO6", "SDA"), (330, "GPIO7", "SCL"), (360, "GPIO5", "XSHUT1"), (390, "GPIO10", "XSHUT2")):
    ex, _ = pin(ESP_X + ESP_W, y, gp, "right")
    label(ex, y, net, "right")

# ---------------- TOF200C (VL53L0X) ----------------
JX, JW = 1080, 200


def tof(y, n, xshut):
    box(JX, y, JW, 150, f"TOF200C #{n}", "VL53L0X, 2 m, I2C")
    for i, (name, net, c) in enumerate((("VIN", "3V3", PWR), ("SDA", "SDA", SIG), ("SCL", "SCL", SIG),
                                         ("XSHUT", xshut, SIG))):
        py = y + 60 + i * 22
        p = pin(JX, py, name, "left", 20)
        label(p[0], py, net, "left", c)
    py = y + 60 + 4 * 22
    p = pin(JX, py, "GND", "left", 20)
    line(p, (JX - 40, py))
    gnd(JX - 40, py)
    text(JX + JW + 10, y + 100, "Adresse nach", 12, c="#555")
    text(JX + JW + 10, y + 114, f"Start: 0x{0x2f + n:02x}", 12, c="#555")


tof(300, 1, "XSHUT1")
tof(500, 2, "XSHUT2")

# ---------------- Hinweise ----------------
notes = [
    "Netzlabels mit gleichem Namen sind verbunden (3V3, SDA, SCL, XSHUT1/2).",
    "Beide ToF-Module hängen dauerhaft an 3,3 V und teilen sich den I2C-Bus.",
    "XSHUT = Enable je Board: beide starten mit 0x29, ESPHome weckt sie einzeln und stellt 0x30/0x31 ein.",
    "SDA/SCL-Pull-ups sind auf den Modulen (sonst 4,7 kΩ nach 3V3 ergänzen).",
    "Kein Boost-Wandler, keine Pegelteiler, keine Abschaltung nötig.",
    "R1/R2/C1 Akkumessung 1:2: 3,0–4,2 V → 1,5–2,1 V an GPIO1, ca. 2 µA Dauerstrom.",
]
e(f'<rect x="30" y="705" width="1000" height="{30 + 22 * len(notes)}" rx="6" fill="#fffbea" stroke="#d4b106"/>')
for i, n in enumerate(notes):
    text(44, 730 + 22 * i, "• " + n, 13)

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'font-family="Segoe UI, Helvetica, Arial, sans-serif">\n' + "\n".join(out) + "\n</svg>\n")
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema_prototyp.svg"), "w", encoding="utf-8").write(svg)
print("schema_prototyp.svg geschrieben")
