#!/usr/bin/env python3
"""Streifenraster-Layout fuer den Prototyp: prueft die Verbindungen und zeichnet stripboard.svg.

Sensoren dauerhaft an 3V3, JSN-SR04T im Low-Power-Modus 4 (360k auf dem Mode-Loetfeld).
Raster: 10 Spalten (c0..c9) x 14 Zeilen (r0..r13), 2.54 mm, Platine 25.4 x 35.56 mm.
Die Kupferstreifen laufen SENKRECHT (eine Spalte = ein Streifen).
Ansicht im SVG links: Bestueckungsseite, rechts: Kupferseite (gespiegelt) mit Trennstellen.
Aufruf: python gen_stripboard.py   (bricht mit Fehler ab, wenn eine Verbindung nicht stimmt)
"""
import os, sys
from collections import defaultdict

COLS, ROWS = 10, 14
P = 2.54

# ---------------- Layout ----------------
# Spalte 0 = GND-Bus, Spalten 1-8 = ESP, Spalte 9 = 3V3-Bus. Keine Befestigungsloecher:
# die Platine wird im Gehaeuse eingeklipst (Auflagen an den Ecken, Rastnasen rechts, Leiste links).
# Trennstellen (Streifen am Loch aufbohren, ca. 3 mm Bohrer von Hand)
CUTS = [(c, 4) for c in (1, 4, 5, 8)] + [(c, 7) for c in range(1, 9)]
MOUNT = []

# Bauteile: name -> (Beschriftung, [(pin, spalte, zeile, netz)], art)
ESP_TOP = ["GPIO5", "GPIO6", "GPIO7", "GPIO8", "GPIO9", "GPIO10", "GPIO20", "GPIO21"]
ESP_BOT = ["5V", "GND", "3V3", "GPIO4", "GPIO3", "GPIO2", "GPIO1", "GPIO0"]
NET_OF_ESP = {"GPIO6": "TRIG1", "GPIO7": "ECHO1", "GPIO10": "ECHO2", "GPIO20": "TRIG2",
              "5V": "VBAT_SW", "GND": "GND", "3V3": "3V3", "GPIO1": "VBDIV"}
PARTS = {
    "U1": ("ESP32-C3 SuperMini", [(n, 1 + i, 5, NET_OF_ESP.get(n)) for i, n in enumerate(ESP_TOP)] +
           [(n, 1 + i, 11, NET_OF_ESP.get(n)) for i, n in enumerate(ESP_BOT)], "esp"),
    # Pulldowns: TRIG im Deep Sleep (ESP-Pins hochohmig) sicher LOW, Sensoren sind immer versorgt
    "R5": ("120k", [("1", 2, 0, "TRIG1"), ("2", 4, 0, "GND")], "r"),
    "R6": ("120k", [("1", 5, 0, "GND"), ("2", 7, 0, "TRIG2")], "r"),
    "J1": ("JSN #1", [("VCC", 1, 1, "3V3"), ("TRIG", 2, 1, "TRIG1"), ("ECHO", 3, 1, "ECHO1"), ("GND", 4, 1, "GND")], "hdr"),
    "J2": ("JSN #2", [("GND", 5, 1, "GND"), ("ECHO", 6, 1, "ECHO2"), ("TRIG", 7, 1, "TRIG2"), ("VCC", 8, 1, "3V3")], "hdr"),
    # Akku-Teiler liegend unter dem ESP (der sitzt ca. 11 mm ueber der Platine)
    "R1": ("1M", [("1", 1, 8, "VBAT_SW"), ("2", 7, 8, "VBDIV")], "r"),
    "R2": ("1M", [("1", 2, 9, "GND"), ("2", 7, 9, "VBDIV")], "r"),
    "C1": ("100nF", [("1", 2, 10, "GND"), ("2", 7, 10, "VBDIV")], "c"),
    "J3": ("Akku/Schalter", [("GND", 0, 13, "GND"), ("VBAT", 1, 13, "VBAT_SW")], "hdr"),
    "C2": ("1µF+", [("-", 2, 13, "GND"), ("+", 3, 13, "3V3")], "c"),
}
# Drahtbruecken auf der Bestueckungsseite: (netz, zeile, [spalten, an denen geloetet wird])
WIRES = [
    ("3V3", 2, [1, 8, 9]),
    ("GND", 3, [0, 4, 5]),
    ("GND", 12, [0, 2]),
    ("3V3", 12, [3, 9]),
]

# Erwartete Netze laut Schaltplan (docs/schema_prototyp.svg)
EXPECTED = {
    "TRIG1": {"J1.TRIG", "U1.GPIO6", "R5.1"}, "ECHO1": {"J1.ECHO", "U1.GPIO7"},
    "TRIG2": {"J2.TRIG", "U1.GPIO20", "R6.2"}, "ECHO2": {"J2.ECHO", "U1.GPIO10"},
    "GND": {"J1.GND", "J2.GND", "U1.GND", "C2.-", "C1.1", "R2.1", "J3.GND", "R5.2", "R6.1"},
    "3V3": {"U1.3V3", "C2.+", "J1.VCC", "J2.VCC"},
    "VBAT_SW": {"U1.5V", "R1.1", "J3.VBAT"},
    "VBDIV": {"U1.GPIO1", "R1.2", "R2.2", "C1.2"},
}


# ---------------- Pruefung ----------------
def check():
    err = []
    used = {}
    blocked = set(CUTS) | set(MOUNT)

    def take(h, who):
        if not (0 <= h[0] < COLS and 0 <= h[1] < ROWS):
            err.append(f"{who}: Loch {h} ausserhalb der Platine")
        if h in blocked:
            err.append(f"{who}: Loch {h} ist Trennstelle/Befestigungsloch")
        if h in used:
            err.append(f"{who}: Loch {h} schon belegt von {used[h]}")
        used[h] = who

    for ref, (_, pins, _) in PARTS.items():
        for name, c, r, _ in pins:
            take((c, r), f"{ref}.{name}")
    for i, (net, r, cols) in enumerate(WIRES):
        for c in cols:
            take((c, r), f"Draht{i}({net})")

    # Lotstellen muessen ausserhalb des Gehaeuse-Doms (Durchmesser 4.5 mm) samt Lotpunkt liegen
    for h, who in used.items():
        for m in MOUNT:
            dist = P * ((h[0] - m[0]) ** 2 + (h[1] - m[1]) ** 2) ** 0.5
            if dist < 3.5:
                err.append(f"{who}: Loch {h} nur {dist:.1f} mm neben Befestigungsloch {m} (min. 3,5 mm)")

    # Union-Find ueber Loecher: Streifen (senkrecht) + Draehte
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        parent[find(a)] = find(b)

    for c in range(COLS):
        for r in range(ROWS - 1):
            if (c, r) not in blocked and (c, r + 1) not in blocked:
                union((c, r), (c, r + 1))
    for net, r, cols in WIRES:
        for c in cols[1:]:
            union((cols[0], r), (c, r))

    groups = defaultdict(set)
    pin_net = {}
    for ref, (_, pins, _) in PARTS.items():
        for name, c, r, net in pins:
            groups[find((c, r))].add(f"{ref}.{name}")
            pin_net[f"{ref}.{name}"] = net
    # Draehte muessen auf dem Netz liegen, fuer das sie gedacht sind
    for i, (net, r, cols) in enumerate(WIRES):
        g = groups.get(find((cols[0], r)), set())
        wrong = [p for p in g if pin_net[p] not in (net, None)]
        if wrong:
            err.append(f"Draht{i}({net}) verbindet fremde Pins: {sorted(wrong)}")
    found = {}
    for g in groups.values():
        nets = {pin_net[p] for p in g} - {None}
        if len(nets) > 1:
            err.append(f"KURZSCHLUSS zwischen {sorted(nets)}: {sorted(g)}")
        if not nets and len(g) > 1:
            err.append(f"unbenutzte Pins verbunden: {sorted(g)}")
        for n in nets:
            found.setdefault(n, set()).update(g)
        unused = [p for p in g if pin_net[p] is None]
        if unused and nets:
            err.append(f"unbenutzter Pin haengt an {sorted(nets)}: {unused}")
    for net, pins in EXPECTED.items():
        got = {p for p in found.get(net, set()) if pin_net[p] is not None}
        if got != pins:
            err.append(f"Netz {net}: erwartet {sorted(pins)}, gefunden {sorted(got)}")
        else:
            # zusammenhaengend?
            roots = set()
            for ref, (_, ps, _) in PARTS.items():
                for name, c, r, n in ps:
                    if n == net:
                        roots.add(find((c, r)))
            if len(roots) > 1:
                err.append(f"Netz {net} ist unterbrochen ({len(roots)} Teile)")
    extra = {pin_net[p] for p in pin_net if pin_net[p]} - set(EXPECTED)
    if extra:
        err.append(f"Netze ohne Erwartung: {extra}")
    return err


# ---------------- Zeichnung ----------------
NET_COL = {"GND": "#222222", "3V3": "#c0392b", "VBAT_SW": "#8e44ad", "VBDIV": "#27ae60",
           "TRIG1": "#1f5fae", "ECHO1": "#1f5fae", "TRIG2": "#1f5fae", "ECHO2": "#1f5fae"}
S = 34                      # Pixel pro Rastermass
M = 46                      # Rand


def svg_board(ox, oy, mirror, out):
    def X(c):
        return ox + M + ((COLS - 1 - c) if mirror else c) * S

    def Y(r):
        return oy + M + r * S

    w, h = (COLS - 1) * S + 2 * M, (ROWS - 1) * S + 2 * M
    out.append(f'<rect x="{ox + 16}" y="{oy + 16}" width="{w - 32}" height="{h - 32}" rx="6" fill="#f3e3c3" stroke="#b08850"/>')
    for c in range(COLS):  # Streifen
        out.append(f'<rect x="{X(c) - S * 0.38}" y="{Y(0) - S * 0.42}" width="{S * 0.76}" '
                   f'height="{(ROWS - 1) * S + S * 0.84}" rx="3" fill="{"#d9a066" if mirror else "#ead2a8"}" '
                   f'stroke="#c4935a" stroke-width="0.8"/>')
    for c in range(COLS):
        for r in range(ROWS):
            out.append(f'<circle cx="{X(c)}" cy="{Y(r)}" r="3" fill="#fff" stroke="#b08850" stroke-width="0.8"/>')
    for c in range(COLS):  # Spalten-/Zeilennummern
        out.append(f'<text x="{X(c)}" y="{Y(0) - 22}" font-size="10" text-anchor="middle" fill="#666">{c}</text>')
    for r in range(ROWS):
        lx = X(0) + 22 if mirror else X(0) - 22
        out.append(f'<text x="{lx}" y="{Y(r) + 4}" font-size="10" text-anchor="middle" fill="#666">{r}</text>')
    for (c, r) in MOUNT:
        out.append(f'<circle cx="{X(c)}" cy="{Y(r)}" r="9" fill="#555" stroke="#000"/>')
    for (c, r) in CUTS:
        col = "#d00000"
        out.append(f'<circle cx="{X(c)}" cy="{Y(r)}" r="9" fill="{"#fff" if mirror else "none"}" stroke="{col}" stroke-width="{2.5 if mirror else 1.2}"'
                   f'{"" if mirror else " stroke-dasharray=\"3,2\""}/>')
        if mirror:
            out.append(f'<path d="M{X(c) - 6},{Y(r) - 6} L{X(c) + 6},{Y(r) + 6} M{X(c) - 6},{Y(r) + 6} L{X(c) + 6},{Y(r) - 6}" stroke="{col}" stroke-width="2.5"/>')
    if mirror:
        return
    # Drahtbruecken
    for net, r, cols in WIRES:
        a, b = min(cols), max(cols)
        out.append(f'<line x1="{X(a)}" y1="{Y(r)}" x2="{X(b)}" y2="{Y(r)}" stroke="{NET_COL[net]}" stroke-width="5" stroke-linecap="round" opacity="0.85"/>')
        for c in cols:
            out.append(f'<circle cx="{X(c)}" cy="{Y(r)}" r="5" fill="{NET_COL[net]}" stroke="#fff" stroke-width="1.5"/>')
    # Bauteile
    for ref, (val, pins, kind) in PARTS.items():
        xs = [X(c) for _, c, _, _ in pins]
        ys = [Y(r) for _, _, r, _ in pins]
        if kind == "esp":
            rt = min(r for _, _, r, _ in pins)
            rb = max(r for _, _, r, _ in pins)
            x0 = X(0) - 0.38 * S                       # USB-Seite ca. 0,3 mm innerhalb der Platinenkante
            x1 = x0 + 22.5 / P * S                     # SuperMini 22,5 x 18 mm
            ym = (Y(rt) + Y(rb)) / 2
            y0, y1 = ym - 9 / P * S, ym + 9 / P * S
            out.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="5" fill="#2b2b2b" opacity="0.15" stroke="#000" stroke-width="1.5" stroke-dasharray="6,3"/>')
            out.append(f'<rect x="{x0 - 12}" y="{ym - 22}" width="18" height="44" rx="3" fill="#999" stroke="#000"/>')
            out.append(f'<text x="{x0 - 1}" y="{ym + 4}" font-size="10" fill="#000" transform="rotate(-90 {x0 - 1},{ym})" text-anchor="middle">USB-C</text>')
            out.append(f'<text x="{(X(1) + X(8)) / 2}" y="{Y(rt + 1) + 5}" font-size="13" font-weight="bold" text-anchor="middle">U1 ESP32-C3 (gestrichelt, auf Buchsenleisten)</text>')
            for name, c, r, net in pins:
                fill = NET_COL.get(net, "#bbb")
                out.append(f'<rect x="{X(c) - 6}" y="{Y(r) - 6}" width="12" height="12" fill="{fill}" stroke="#000"/>')
                ty = Y(r) - 10 if r == rt else Y(r) + 20
                out.append(f'<text x="{X(c)}" y="{ty}" font-size="9" text-anchor="middle" fill="#000">{name.replace("GPIO", "")}</text>')
            continue
        if kind == "hdr":
            x0, x1 = min(xs) - 12, max(xs) + 12
            out.append(f'<rect x="{x0}" y="{ys[0] - 12}" width="{x1 - x0}" height="24" rx="3" fill="#333" opacity="0.85"/>')
            for name, c, r, net in pins:
                out.append(f'<rect x="{X(c) - 4}" y="{Y(r) - 4}" width="8" height="8" fill="#e8c34a"/>')
                below = r > ROWS / 2
                out.append(f'<text x="{X(c)}" y="{Y(r) + (24 if below else 22)}" font-size="9" text-anchor="middle" fill="{NET_COL.get(net, "#000")}" font-weight="bold">{name}</text>')
            ly = ys[0] + 40 if ys[0] > Y(ROWS // 2) else Y(0) - 34
            out.append(f'<text x="{(x0 + x1) / 2}" y="{ly}" font-size="12" font-weight="bold" text-anchor="middle">{ref} {val}</text>')
            continue
        (xa, ya), (xb, yb) = (xs[0], ys[0]), (xs[1], ys[1])
        color = {"r": "#c9a26b", "c": "#e8b04b", "elko": "#3a5fa0"}[kind]
        out.append(f'<line x1="{xa}" y1="{ya}" x2="{xb}" y2="{yb}" stroke="#777" stroke-width="2"/>')
        mx = (xa + xb) / 2
        if kind == "elko":
            out.append(f'<circle cx="{mx}" cy="{ya}" r="{S * 0.95}" fill="{color}" stroke="#000" opacity="0.9"/>')
            out.append(f'<text x="{xa + 2}" y="{ya - 8}" font-size="13" font-weight="bold" fill="#fff">+</text>')
        else:
            bw = min(abs(xb - xa) - 8, 34) if kind == "r" else 16
            out.append(f'<rect x="{mx - bw / 2}" y="{ya - 6}" width="{bw}" height="12" rx="5" fill="{color}" stroke="#000"/>')
        for x, y in ((xa, ya), (xb, yb)):
            out.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#888" stroke="#000"/>')
        out.append(f'<text x="{mx}" y="{ya - (S if kind == "elko" else 10)}" font-size="11" font-weight="bold" text-anchor="middle">{ref} {val}</text>')


TITLE = "Tankmonitor: Streifenraster 10 × 14 Löcher (25,4 × 35,6 mm), Streifen senkrecht"


def render(path):
    out = []
    bw = (COLS - 1) * S + 2 * M
    bh = (ROWS - 1) * S + 2 * M
    W, H = 2 * bw + 380, max(bh + 150, 700)
    out.append(f'<rect width="{W}" height="{H}" fill="#fff"/>')
    out.append(f'<text x="20" y="32" font-size="20" font-weight="bold">{TITLE}</text>')
    out.append(f'<text x="{20 + bw / 2}" y="70" font-size="15" font-weight="bold" text-anchor="middle">Bestückungsseite (von oben)</text>')
    out.append(f'<text x="{40 + bw * 1.5}" y="70" font-size="15" font-weight="bold" text-anchor="middle">Kupferseite (von unten, gespiegelt)</text>')
    svg_board(20, 80, False, out)
    svg_board(40 + bw, 80, True, out)
    # Legende
    lx, ly = 2 * bw + 70, 110
    leg = [("Draht", None)] + [(n, NET_COL[n]) for n in ("GND", "3V3", "VBAT_SW", "VBDIV")]
    out.append(f'<text x="{lx}" y="{ly}" font-size="14" font-weight="bold">Netze / Drahtbrücken</text>')
    for i, (n, col) in enumerate(leg[1:]):
        y = ly + 24 + i * 22
        out.append(f'<line x1="{lx}" y1="{y}" x2="{lx + 30}" y2="{y}" stroke="{col}" stroke-width="5" stroke-linecap="round"/>')
        out.append(f'<text x="{lx + 40}" y="{y + 5}" font-size="13">{n}</text>')
    y = ly + 24 + len(leg) * 22 + 10
    items = [
        ('<circle cx="{x}" cy="{y}" r="9" fill="#fff" stroke="#d00000" stroke-width="2.5"/>', "Streifen trennen (12×)"),
        ('<rect x="{x0}" y="{y0}" width="12" height="12" fill="#bbb" stroke="#000"/>', "ESP-Pin unbenutzt"),
    ]
    for i, (shape, txt) in enumerate(items):
        yy = y + i * 28
        out.append(shape.format(x=lx + 15, y=yy, x0=lx + 9, y0=yy - 6))
        out.append(f'<text x="{lx + 40}" y="{yy + 5}" font-size="13">{txt}</text>')
    y += 2 * 28 + 10
    notes = [
        "Reihenfolge: 1. Platine zuschneiden",
        f"2. Trennstellen bohren ({len(CUTS)}×)",
        f"3. Drahtbrücken ({len(WIRES)}×)",
        "4. R1, R2, C1 liegend (unter dem ESP)",
        "5. R5, R6 stehend, nach oben gebogen",
        "6. C2 Elko (+ an Spalte 3), Stift-/Buchsenleisten",
        "7. Durchgang messen, dann ESP stecken",
        "",
        "Keine Befestigungslöcher: die Platine",
        "wird im Gehäuse eingeklipst.",
        "J2 ist gespiegelt belegt:",
        "GND-ECHO-TRIG-VCC (JSN-Pin 4-3-2-1)",
        "JSN: 3×120k in Reihe (=360k) auf 'Mode'",
        "ESP-Pins vor dem Löten am Modul prüfen!",
    ]
    for i, n in enumerate(notes):
        out.append(f'<text x="{lx}" y="{y + i * 19}" font-size="12">{n}</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="Segoe UI, Helvetica, Arial, sans-serif">\n' + "\n".join(out) + "\n</svg>\n")
    open(path, "w", encoding="utf-8").write(svg)


if __name__ == "__main__":
    errors = check()
    if errors:
        print("FEHLER:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print(f"Verbindungen OK: {len(EXPECTED)} Netze, {sum(len(p[1]) for p in PARTS.values())} Pins, "
          f"{len(CUTS)} Trennstellen, {len(WIRES)} Drahtbruecken")
    name = "stripboard.svg"
    render(os.path.join(os.path.dirname(os.path.abspath(__file__)), name))
    print(name, "geschrieben")
