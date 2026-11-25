"""Loetplan fuer das Lochraster: prueft die Platzierung und zeichnet loetplan.svg.

Aufruf: python gen_loetplan.py   (nur Standardbibliothek)

Alle Lochangaben gelten fuer die Bestueckungsseite: Spalten A..T von links, Reihen 1..14 von unten.
Geprueft wird: kein Loch doppelt belegt, alle Netze wie im Schaltplan und ohne Verbindung untereinander,
Bauteilkoerper ohne Ueberschneidung mit anderen Teilen, Buchsenleisten, Pfosten und Plattenrand.
Die Koerpermasse sind Annahmen (1/4-W-Widerstand, Elko 5 x 11 mm), siehe BODY-Werte unten.
"""
import os

COLS = "ABCDEFGHIJKLMNOPQRST"
PITCH, W, H = 2.54, 60.0, 40.0
X_A, Y_1 = W - 5.5 - 19 * PITCH, (H - 13 * PITCH) / 2        # wie case/gen_case.py
POSTS = [(2.5, 2.5), (57.5, 2.5), (2.5, 37.5), (57.5, 37.5)]  # Pfosten d=5 auf der Bestueckungsseite

SOCKETS = {  # Name: (erstes Loch, letztes Loch)
    "ToF-Buchse 1x6": ("B1", "G1"),
    "ESP-Buchse unten 1x8": ("M3", "T3"),
    "ESP-Buchse oben 1x8": ("M9", "T9"),
}

# Name: (Loch 1, Loch 2, Beschriftung, Koerper als (x0, y0, x1, y1) in mm oder None = zwischen den Beinen)
R_LEN, R_DIA = 6.3, 2.3


def xy(hole):
    return X_A + COLS.index(hole[0]) * PITCH, Y_1 + (int(hole[1:]) - 1) * PITCH


def resistor_body(a, b):
    (x1, y1), (x2, y2) = xy(a), xy(b)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = (R_LEN, R_DIA) if y1 == y2 else (R_DIA, R_LEN)
    return (cx - dx / 2, cy - dy / 2, cx + dx / 2, cy + dy / 2)


def ceramic_body(a, b):
    (x1, y1), (x2, _) = xy(a), xy(b)
    cx = (x1 + x2) / 2
    return (cx - 2.2, y1 - 1.2, cx + 2.2, y1 + 1.2)


PARTS = {
    "Rint": ("E12", "E8", "10k", resistor_body("E12", "E8")),
    "Rsda": ("G12", "G8", "4k7*", resistor_body("G12", "G8")),
    "Rscl": ("I12", "I8", "4k7*", resistor_body("I12", "I8")),
    "Rxs": ("C13", "C9", "1k", resistor_body("C13", "C9")),
    "Ra": ("J10", "N10", "1M", resistor_body("J10", "N10")),
    "Rb": ("J14", "N14", "1M", resistor_body("J14", "N14")),
    "Cadc": ("O14", "P14", "100n", ceramic_body("O14", "P14")),
    "Cs2": ("B2", "C2", "100n", ceramic_body("B2", "C2")),
    # Elkos liegend: erstes Loch = Plus. Cs1 liegt Richtung Reihe 8, Cbat Richtung Spalte T.
    "Cs1": ("B3", "C3", "Elko", (xy("B3")[0] + 1.27 - 2.5, xy("B3")[1] + 1.4, xy("B3")[0] + 1.27 + 2.5, xy("B3")[1] + 12.4)),
    "Cbat": ("Q11", "Q13", "Elko", (xy("Q12")[0] + 1.2, xy("Q12")[1] - 2.5, xy("Q12")[0] + 12.2, xy("Q12")[1] + 2.5)),
}

RAILS = {"VBAT": ("A11", "T11"), "3V3": ("B12", "R12"), "GND": ("A13", "S13")}
BRIDGES = [("B1", "B2"), ("B2", "B3"), ("C1", "C2"), ("C2", "C3"),
           ("J10", "J11"), ("J14", "J13"), ("N9", "N10"), ("N14", "O14"), ("P14", "P13")]
WIRES = [  # isolierte Draehte auf der Loetseite: (Nummer, von, nach, Netz)
    (1, "T9", "T11", "VBAT"), (2, "R9", "R12", "3V3"), (3, "S9", "S13", "GND"),
    (4, "B1", "B12", "3V3"), (5, "C1", "B13", "GND"), (6, "N10", "N14", "ADC"),
    (7, "S3", "D1", "SDA"), (8, "R3", "E1", "SCL"), (9, "T3", "G1", "XSHUT"), (10, "Q9", "F1", "INT"),
    (11, "F1", "E8", "INT"), (12, "G1", "C9", "XSHUT"), (13, "D1", "G8", "SDA"), (14, "E1", "I8", "SCL"),
]
EXTERNAL = {"A11": "Schalter", "A13": "TP4056 OUT-"}

NETS = {  # Soll laut docs/schaltung.md
    "VBAT": "T9 A11 J10 Q11",
    "3V3": "R9 B1 B3 B2 E12 G12 I12",
    "GND": "S9 C1 C2 C3 C13 J14 P14 Q13 A13",
    "ADC": "N9 N10 N14 O14",
    "SDA": "S3 D1 G8",
    "SCL": "R3 E1 I8",
    "XSHUT": "T3 G1 C9",
    "INT": "Q9 F1 E8",
}
COLORS = {"VBAT": "#d62828", "3V3": "#f77f00", "GND": "#222222", "ADC": "#7b2cbf",
          "SDA": "#1d6fd1", "SCL": "#118a55", "XSHUT": "#b5179e", "INT": "#6c757d"}


def span(a, b):
    c0, c1 = sorted((COLS.index(a[0]), COLS.index(b[0])))
    r0, r1 = sorted((int(a[1:]), int(b[1:])))
    return [f"{COLS[c]}{r}" for c in range(c0, c1 + 1) for r in range(r0, r1 + 1)]


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def check():
    parent = {}

    def find(h):
        parent.setdefault(h, h)
        while parent[h] != h:
            h = parent[h]
        return h

    def join(a, b):
        parent[find(a)] = find(b)

    for a, b in RAILS.values():
        for h in span(a, b)[1:]:
            join(a, h)
    for a, b in BRIDGES:
        (x1, y1), (x2, y2) = xy(a), xy(b)
        assert abs(abs(x1 - x2) + abs(y1 - y2) - PITCH) < 0.01, f"Bruecke {a}-{b} nicht benachbart"
        join(a, b)
    for _, a, b, _net in WIRES:
        join(a, b)

    roots = {}
    for net, holes in NETS.items():
        found = {find(h) for h in holes.split()}
        assert len(found) == 1, f"Netz {net} ist unterbrochen"
        root = found.pop()
        assert root not in roots, f"Kurzschluss zwischen {net} und {roots[root]}"
        roots[root] = net
    for num, a, b, net in WIRES:
        assert roots[find(a)] == net, f"Draht {num} falsch bezeichnet"

    def net_of(h):
        return roots[find(h)]

    expected = {"Rint": ("3V3", "INT"), "Rsda": ("3V3", "SDA"), "Rscl": ("3V3", "SCL"), "Rxs": ("GND", "XSHUT"),
                "Ra": ("VBAT", "ADC"), "Rb": ("GND", "ADC"), "Cadc": ("ADC", "GND"), "Cs2": ("3V3", "GND"),
                "Cs1": ("3V3", "GND"), "Cbat": ("VBAT", "GND")}
    for name, (a, b, _label, _body) in PARTS.items():
        assert (net_of(a), net_of(b)) == expected[name], f"{name}: {net_of(a)}/{net_of(b)}"

    used = [h for a, b in SOCKETS.values() for h in span(a, b)]
    used += [h for p in PARTS.values() for h in p[:2]]
    assert len(used) == len(set(used)), "Loch doppelt belegt"

    bodies = {n: p[3] for n, p in PARTS.items()}
    for n, (a, b) in SOCKETS.items():
        (x1, y1), (x2, _) = xy(a), xy(b)
        bodies[n] = (x1 - 1.27, y1 - 1.27, x2 + 1.27, y1 + 1.27)
    names = list(bodies)
    for i, n in enumerate(names):
        x0, y0, x1, y1 = bodies[n]
        assert x0 >= 0 and y0 >= 0 and x1 <= W and y1 <= H, f"{n} ragt ueber den Plattenrand"
        for px, py in POSTS:
            dx, dy = px - min(max(px, x0), x1), py - min(max(py, y0), y1)
            assert dx * dx + dy * dy >= 2.5 ** 2, f"{n} stoesst an einen Pfosten"
        for m in names[i + 1:]:
            assert not overlap(bodies[n], bodies[m]), f"{n} ueberschneidet {m}"


S = 15  # Pixel pro mm


def view(out, top, title, mirrored):
    def X(x):
        return 30 + ((W - x) if mirrored else x) * S

    def Y(y):
        return top + (H - y) * S

    def text(x, y, s, size=13, color="#111", anchor="middle", bold=False):
        weight = ' font-weight="bold"' if bold else ""
        out.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" text-anchor="{anchor}"{weight}>{s}</text>')

    def rect(box, fill, stroke="#444", opacity=1.0):
        x0, x1 = sorted((X(box[0]), X(box[2])))
        out.append(f'<rect x="{x0:.1f}" y="{Y(box[3]):.1f}" width="{x1 - x0:.1f}" height="{(box[3] - box[1]) * S:.1f}" '
                   f'rx="4" fill="{fill}" stroke="{stroke}" opacity="{opacity}"/>')

    def line(a, b, color, width, dash=""):
        (x1, y1), (x2, y2) = xy(a), xy(b)
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        out.append(f'<line x1="{X(x1):.1f}" y1="{Y(y1):.1f}" x2="{X(x2):.1f}" y2="{Y(y2):.1f}" stroke="{color}" '
                   f'stroke-width="{width}" stroke-linecap="round"{extra}/>')

    text(30, top - 34, title, 20, anchor="start", bold=True)
    rect((0, 0, W, H), "#f1dfb8", "#8a6d3b")
    for px, py in POSTS:
        out.append(f'<circle cx="{X(px):.1f}" cy="{Y(py):.1f}" r="{0.9 * S}" fill="#fff" stroke="#8a6d3b"/>')
    for c in COLS:
        text(X(xy(c + "1")[0]), top - 8, c, 14, bold=True)
        text(X(xy(c + "1")[0]), Y(0) + 18, c, 14, bold=True)
    for r in range(1, 15):
        y = Y(xy(f"A{r}")[1]) + 5
        text(14, y, r, 13, bold=True)
        text(30 + W * S + 16, y, r, 13, bold=True)
    for c in COLS:
        for r in range(1, 15):
            x, y = xy(f"{c}{r}")
            out.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="4" fill="#c9a45c"/>')

    if mirrored:  # Loetseite: Schienen, Bruecken, Draehte
        for net, (a, b) in RAILS.items():
            line(a, b, COLORS[net], 9)
        for a, b in BRIDGES:
            line(a, b, "#8d99a6", 13)
        for num, a, b, net in WIRES:
            line(a, b, COLORS[net], 4, "10 5" if num in (13, 14) else "")
        for num, a, b, net in WIRES:
            (x1, y1), (x2, y2) = xy(a), xy(b)
            t = {5: 0.7, 7: 0.7, 8: 0.5, 9: 0.3, 10: 0.45, 11: 0.5, 13: 0.75, 14: 0.8}.get(num, 0.5)
            cx, cy = X(x1 + (x2 - x1) * t), Y(y1 + (y2 - y1) * t)
            out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="10" fill="#fff" stroke="{COLORS[net]}" stroke-width="2"/>')
            text(cx, cy + 4.5, num, 12, bold=True)
        used = {h for p in PARTS.values() for h in p[:2]} | {h for a, b in SOCKETS.values() for h in span(a, b)}
        for h in used | set(EXTERNAL):
            x, y = xy(h)
            out.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="5" fill="#fff" stroke="#111" stroke-width="2"/>')
    else:  # Bestueckungsseite: Buchsen und Bauteile
        for name, (a, b) in SOCKETS.items():
            (x1, y1), (x2, _) = xy(a), xy(b)
            rect((x1 - 1.27, y1 - 1.27, x2 + 1.27, y1 + 1.27), "#2b2b2b")
        text(X(xy("D1")[0] + 1.27), Y(xy("D1")[1]) + 5, "ToF-Buchse", 12, "#fff")
        text(X(xy("P3")[0] + 1.27), Y(xy("P3")[1]) + 5, "ESP-Buchse", 12, "#fff")
        text(X(xy("P9")[0] + 1.27), Y(xy("P9")[1]) + 5, "ESP-Buchse  (USB-C &#8594;)", 12, "#fff")
        for name, (a, b, label, body) in PARTS.items():
            fill = "#9ecbf0" if name.startswith("C") else "#e8c48c"
            line(a, b, "#777", 3)
            rect(body, fill, opacity=0.95)
            cx, cy = X((body[0] + body[2]) / 2), Y((body[1] + body[3]) / 2)
            if body[3] - body[1] > body[2] - body[0]:
                out.append(f'<text transform="translate({cx + 4:.1f},{cy:.1f}) rotate(-90)" font-size="12" '
                           f'text-anchor="middle" fill="#111">{name} {label}</text>')
            elif name in ("Cadc", "Cs2"):  # zu klein fuer Text: rechts daneben
                text(X(body[2]) + 6, cy + 4, f"{name} {label}", 12, anchor="start")
            else:
                text(cx, cy + 4, f"{name} {label}", 12)
            for h in (a, b):
                x, y = xy(h)
                out.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="5" fill="#fff" stroke="#111" stroke-width="2"/>')
        for h in ("B3", "Q11"):
            x, y = xy(h)
            text(X(x) - 12, Y(y) + 5, "+", 20, "#d62828", bold=True)
        for h, label in EXTERNAL.items():
            x, y = xy(h)
            out.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="6" fill="#d62828"/>')
            text(X(x) + 10, Y(y) + 4, label, 12, anchor="start", bold=True)


def draw(path):
    width, height = int(W * S + 62), 1470
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
           'font-family="Segoe UI, Arial, sans-serif">', f'<rect width="{width}" height="{height}" fill="#fff"/>']
    view(out, 70, "1. Bestückungsseite (A links): hier stecken die Teile", False)
    view(out, 770, "2. Lötseite, Platine umgedreht (A rechts): hier wird verdrahtet", True)
    y = 770 + H * S + 52
    for i, (net, color) in enumerate(COLORS.items()):
        x = 30 + i * 112
        out.append(f'<line x1="{x}" y1="{y}" x2="{x + 28}" y2="{y}" stroke="{color}" stroke-width="7"/>')
        out.append(f'<text x="{x + 34}" y="{y + 5}" font-size="14">{net}</text>')
    out.append(f'<text x="30" y="{y + 28}" font-size="14">Dicke Linie = blanke Schiene, grau = Lötbrücke, '
               'dünn mit Nummer = isolierter Draht, gestrichelt/* = nur falls das Modul keine Pullups hat</text>')
    out.append("</svg>")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    check()
    target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "loetplan.svg")
    draw(target)
    print("Pruefung ok, geschrieben:", target)
