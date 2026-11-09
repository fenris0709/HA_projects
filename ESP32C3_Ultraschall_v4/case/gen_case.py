"""Gehaeuse fuer EINEN Tank: ESP32-C3 SuperMini + 1x TOF200C (VL53L0X) + 18650, direkt auf dem Tankverschluss.

Ziele: wenig Filament, schnell druckbar (dünne Waende, keine Stuetzen, flach auf dem Bett), Deckel ohne Schrauben.
Das Gehaeuse sitzt auf der flachen Oberseite des Tankverschlusses (Ø ca. 110 mm). Der Sensor schaut durch ein
Fenster im Boden und das gebohrte Loch im Verschluss in den Tank. Das Gehaeuse darf etwas ueberstehen, 2 Laschen
(vorne/hinten) erlauben bei Bedarf zusaetzlich 2 Schrauben durch den Verschluss.

Die Lochrasterplatine (60 x 40 mm) haengt MIT DER BESTUECKUNGSSEITE NACH UNTEN auf 4 Pfosten: Die Zapfen (Ø 1.6)
stecken durch die Montagelocher. Unter der Platine haengen ESP (in Buchsenleisten) und ToF-Modul (in Buchsenleiste),
oben liegt die Loetseite. So schaut der Sensor ohne Kabel nach unten durch das Fenster.

Erzeugt (im Ordner dieses Skripts):
  gehaeuse.json              SolidCraft-Befehlsskript (Gehaeuse + Deckel)
  gehaeuse_mit_bauteilen.json  dasselbe mit Platzhaltern fuer Vorschau und Kollisionspruefung
  Gehaeuse.solidcraft        Design zum Oeffnen/Weiterbearbeiten in SolidCraft
  Gehaeuse.stl               Druckteil, Boden unten
  Deckel.stl                 Druckteil, flach
  preview_*.png              Vorschau
Aufruf: python gen_case.py            (SolidCraft-CLI muss auf dem PATH liegen)
        python gen_case.py --no-run   (nur JSON schreiben)

Koordinaten: X = Breite (u), Y = Laenge (v), Z = Hoehe. u/v/z = Innenmass ab der inneren Ecke links vorne auf dem
Innenboden. Layout (Draufsicht auf die Loetseite, Deckel ab; links ist die Einschubseite des Deckels):

   +--------------------------------------------------+
   |  [ESP USB-C links]   [Fenster]   |  [Schalter    |
   |   ToF-Modul unter der Platine    |   rechts]     |
   |  Lochraster 60 x 40 (oben)       |  [TP4056]     |
   |  [18650-Halter, quer, ganze Breite]              |
   +--------------------------------------------------+
"""
import json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SC_CLI = shutil.which("solidcraft-cli") or r"C:\Program Files\SolidCraft\solidcraft-cli.exe"

# ---------------- Parameter (mm) ----------------
T = 1.2            # Wandstaerke (3 Linien bei 0.4 mm Duese)
FL = 1.2           # Bodenstaerke
HI = 23.0          # Innenhoehe bis Unterkante Deckel (Schalter Ø 21 braucht ca. 22)
C = 0.4            # allgemeines Spiel

# Deckel schiebt von links in zwei Nuten an den Laengswaenden ein, rechts ist die Wand der Anschlag
LID_T, LID_SLOT, LIP_H = 1.6, 2.0, 1.2   # Deckeldicke, Nuthoehe, Rest der Rippe ueber der Nut
RIB, GD, LID_C = 2.4, 1.6, 0.15          # Rippe nach innen, Nuttiefe, Spiel Deckel <-> Nut

# Lochrasterplatine (Punktraster) 60 x 40, Montagelocher Ø 1.8 mit 2.5 mm Randabstand
PCB_W, PCB_L, PCB_T = 60.0, 40.0, 1.6
PCB_HOLE_IN = 2.5
POST_D = 5.0                     # Pfosten unter der Platine
PEG_D, PEG_H = 1.6, 4.0          # Zapfen durch das Montageloch
PITCH = 2.54
COL_RIM = 5.5                    # Abstand Loch T zur Plattenkante (gemessen), Spalten A..T = 20
ROW_RIM = round((PCB_L - 13 * PITCH) / 2, 2)   # 14 Reihen mittig

# ESP32-C3 SuperMini haengt unter der Platine in Buchsenleisten (Reihenabstand 6 Raster = 15.24)
ESP_L, ESP_W = 22.5, 18.0
ESP_PIN_IN = 2.2                 # Abstand erster Pin <-> USB-C-Kante
ESP_ROWS = (3, 9)                # Reihen der beiden Buchsenleisten
SOCKET_H, SPACER_H, ESP_PCB, USB_H = 8.5, 2.5, 1.0, 3.2
ESP_DROP = SOCKET_H + SPACER_H + ESP_PCB + USB_H           # Platinenunterseite -> tiefster Punkt des ESP
BOARD_Z = round(ESP_DROP + 2.3, 1)                         # Platinenunterseite ueber dem Innenboden
ESP_USB_Z = BOARD_Z - (SOCKET_H + SPACER_H + ESP_PCB + USB_H / 2)
ESP_USB_W, ESP_USB_H = 13.0, 7.0                           # Durchbruch fuer den Stecker

# TOF200C (20 x 11 mm), 6 Pins in Buchsenleiste auf Reihe 1, Spalten B..G. Modul haengt flach unter der Platine,
# Sensor nach unten. Pins 1.5 mm vom Modulrand, Sensormitte 6.2 mm von der Pinreihe (siehe datasheets/).
TOF_W, TOF_H = 20.0, 11.0
TOF_PIN_Y, TOF_SENS_Y = 1.5, 6.2
TOF_COLS = (1, 2, 3, 4, 5, 6)    # B..G (A = 0)
TOF_ROW = 1
TOF_BODY_H = 1.2 + 1.8           # Platine + Sensor
WIN_D = 12.0                     # Fenster im Boden = Bohrschablone fuer das Loch im Verschluss

# 18650-Halter (1 Zelle) quer in der vorderen Reihe, an einem Ende Platz fuer die Draehte
BAT_W, BAT_L, BAT_H = 21.0, 78.0, 20.0
BAT_WIRE, RAIL, RAIL_H = 5.0, 1.2, 2.0

# TP4056 USB-C Lader (ca. 17.9 x 14.1), USB-C zeigt durch die rechte Wand - VOR DEM DRUCK NACHMESSEN
TP_L, TP_W = 17.9, 14.1
TP_PLAT, TP_PAD_W, TP_RIM, TP_RIM_H = 2.0, 2.0, 0.8, 1.5
TP_USB_Z = TP_PLAT + 1.0 + 1.6
TP_USB_W, TP_USB_H = 13.0, 7.5

# Schalter rund 20 mm in der rechten Wand
SW_HOLE, SW_BODY_D, SW_DEPTH = 20.2, 21.0, 25.0
SW_Z = HI / 2

# Laschen vorne/hinten fuer 2 Schrauben durch den Tankverschluss (Option)
EAR_W, EAR_L, EAR_T, EAR_HOLE = 10.0, 9.0, 2.0, 3.4

# ---------------- Layout ----------------
BAT_STRIP = BAT_W + 2 * (C + RAIL)                 # vorne: Akkuhalter mit Schienen
PCB_U0 = 0.5                                       # Platine ab dieser Stelle (links), knapp an der Wand: USB-C-Stecker muss bis zum ESP reichen
PCB_V0 = round(BAT_STRIP + 1.0, 2)                 # dahinter
BAT_U = 2.4
RIGHT_U0 = PCB_U0 + PCB_W + 1.2                    # rechter Streifen: TP4056 + Schalter
WI = round(max(RIGHT_U0 + SW_DEPTH + 0.5, BAT_U + BAT_L + BAT_WIRE + 0.5), 1)
LI = round(PCB_V0 + PCB_L + 1.0, 1)
WO, LO, HO = WI + 2 * T, LI + 2 * T, FL + HI + LID_SLOT + LIP_H


def col_u(c):
    """u der Rasterspalte c (0 = A ... 19 = T). T liegt links (ESP-Seite), A rechts (Bestueckungsseite gespiegelt)."""
    return PCB_U0 + COL_RIM + (19 - c) * PITCH


def row_v(r):
    return PCB_V0 + ROW_RIM + (r - 1) * PITCH


ESP_U0 = col_u(19) - ESP_PIN_IN                    # USB-C-Kante des ESP
ESP_VC = (row_v(ESP_ROWS[0]) + row_v(ESP_ROWS[1])) / 2
TOF_UC = sum(col_u(c) for c in TOF_COLS) / len(TOF_COLS)
TOF_PIN_V = row_v(TOF_ROW)
WIN_U, WIN_V = TOF_UC, TOF_PIN_V + TOF_SENS_Y      # Fenstermitte = Sensormitte

TP_U0 = WI - 0.3 - TP_L
TP_V0 = 27.0
SW_V = LI - 0.5 - SW_BODY_D / 2
HOLES = [(PCB_U0 + PCB_HOLE_IN, PCB_V0 + PCB_HOLE_IN), (PCB_U0 + PCB_W - PCB_HOLE_IN, PCB_V0 + PCB_HOLE_IN),
         (PCB_U0 + PCB_HOLE_IN, PCB_V0 + PCB_L - PCB_HOLE_IN),
         (PCB_U0 + PCB_W - PCB_HOLE_IN, PCB_V0 + PCB_L - PCB_HOLE_IN)]


def P(u, v, z=0.0):
    return [round(T + u, 3), round(T + v, 3), round(FL + z, 3)]


cmds = []


def cmd(c, **p):
    cmds.append({"command": c, "params": p})


def box(name, corner, size, op=None, target="Gehaeuse"):
    p = dict(length=round(size[0], 3), width=round(size[1], 3), height=round(size[2], 3), corner=corner)
    if op:
        p.update(operation=op, targets=[target])
    else:
        p.update(body_name=name)
    cmd("solid.box", **p)


def cyl(base, d, h, axis="Z", op="cut", target="Gehaeuse"):
    cmd("solid.cylinder", diameter=d, height=round(h, 3), base=base, axis=axis, operation=op, targets=[target])


def slot_x(x0, v, z, w, h, target="Gehaeuse"):
    """Langloch (Breite w entlang Y, Hoehe h, Mitte v/z absolut) durch eine Wand in X-Richtung ab x0."""
    r = h / 2
    box(None, [x0, v - (w - h) / 2, z - r], [T + 2, w - h, h], "cut", target)
    for dv in (-(w - h) / 2, (w - h) / 2):
        cyl([x0, v + dv, z], h, T + 2, "X", target=target)


# ---------------- Gehaeuse ----------------
cmd("solid.box", length=WO, width=LO, height=HO, corner=[0, 0, 0], body_name="Gehaeuse")
cmd("solid.fillet", body="Gehaeuse", radius=3,
    edges=[[0, 0, HO / 2], [WO, 0, HO / 2], [0, LO, HO / 2], [WO, LO, HO / 2]])
box(None, P(0, 0), [WI, LI, HO], "cut")

# Wanddurchbrueche (vor den Aufbauten schneiden: SolidCraft-Kern ist reihenfolgeempfindlich)
slot_x(-1, T + ESP_VC, FL + ESP_USB_Z, ESP_USB_W, ESP_USB_H)                    # ESP USB-C, linke Wand
slot_x(T + WI - 1, T + TP_V0 + TP_W / 2, FL + TP_USB_Z, TP_USB_W, TP_USB_H)      # TP4056 USB-C, rechte Wand
cyl([round(T + WI - 1, 3), round(T + SW_V, 3), round(FL + SW_Z, 3)], SW_HOLE, T + 2, "X")   # Schalter, rechte Wand
cyl([round(T + WIN_U, 3), round(T + WIN_V, 3), -1], WIN_D, FL + 2)               # Sensorfenster im Boden
# Einschubseite: linke Wand oberhalb des Deckels weg (Deckel gleitet darueber)
RV0 = RIB - GD
box(None, [-1, T + RV0, FL + HI], [T + 1, LI - 2 * RV0, LID_SLOT + LIP_H + 1], "cut")

# Rippen fuer die Deckelnut an den Laengswaenden, nach unten mit 45-Grad-Stufen (ohne Stuetzen druckbar)
RIB_H = 2.0 + LID_SLOT + LIP_H
for front in (True, False):
    if front:
        v_in, v_s2, v_s1, v_cut = -0.2, -0.2, -0.2, RIB - GD
    else:
        v_in, v_s2, v_s1, v_cut = LI - RIB, LI - 1.6, LI - 0.8, LI - RIB - 0.2
    box(None, P(0, v_in, HI - 2.0), [WI + 0.2, RIB + 0.2, RIB_H], "join")
    # Stufen leicht versetzt und ueberlappend (deckungsgleiche Flaechen lassen die Boole-Operation scheitern)
    box(None, P(0.3, v_s2, HI - 2.8), [WI - 0.1, 1.7, 0.9], "join")
    box(None, P(0.6, v_s1, HI - 3.6), [WI - 0.4, 0.9, 0.9], "join")
for v_cut in (RIB - GD, LI - RIB - 0.2):   # Nuten (Deckel gleitet bis zur rechten Wand)
    box(None, P(-1, v_cut, HI), [WI + 1, GD + 0.2, LID_SLOT], "cut")

# Pfosten mit Zapfen fuer die Lochrasterplatine
for (u, v) in HOLES:
    cyl(P(u, v, -0.3), POST_D, BOARD_Z + 0.3, op="join")
    cyl(P(u, v, BOARD_Z - 0.3), PEG_D, PEG_H + 0.3, op="join")

# Akkuhalter: zwei Schienen und links ein Anschlag (rechts Platz fuer die Draehte)
bu0 = BAT_U - C - RAIL
for v in (-0.2, BAT_STRIP - RAIL):
    box(None, P(bu0, v, -0.3), [BAT_L + C + RAIL + 0.8, RAIL + 0.2, RAIL_H + 0.3], "join")
box(None, P(bu0, RAIL, -0.3), [RAIL, BAT_STRIP - 2 * RAIL, RAIL_H + 0.3], "join")

# TP4056: zwei Auflagen unter den Laengskanten, aussen je eine Fuehrung
for vy in (TP_V0, TP_V0 + TP_W - TP_PAD_W):
    box(None, P(TP_U0, vy, -0.3), [TP_L, TP_PAD_W, TP_PLAT + 0.3], "join")
for vy in (TP_V0 - C - TP_RIM, TP_V0 + TP_W + C):
    box(None, P(TP_U0, vy, -0.3), [TP_L, TP_RIM, TP_PLAT + TP_RIM_H + 0.3], "join")

# Laschen fuer 2 Schrauben durch den Tankverschluss (vorne/hinten, auf Hoehe des Fensters)
for (y0, yh) in ((-EAR_L + 0.5, -EAR_L / 2 - 0.5), (LO - 0.5, LO + EAR_L / 2 + 0.5)):
    box(None, [round(T + WIN_U - EAR_W / 2, 3), round(y0, 3), 0], [EAR_W, EAR_L, EAR_T], "join")
    cyl([round(T + WIN_U, 3), round(yh, 3), -1], EAR_HOLE, EAR_T + 2)

# ---------------- Deckel (liegt flach neben dem Gehaeuse) ----------------
LX = WO + 15.0
LID_L = WI + T - 0.3                      # buendig mit der linken Aussenkante, rechts bis zur Innenwand
LID_WD = LI - 2 * RV0 - 2 * LID_C
cmd("solid.box", length=round(LID_L, 3), width=round(LID_WD, 3), height=LID_T,
    corner=[LX, round(T + RV0 + LID_C, 3), 0], body_name="Deckel")
cyl([LX, round(T + LI / 2, 3), -1], 14.0, LID_T + 2, target="Deckel")      # Griffmulde am Einschubende

cmd("appearance.assign", bodies=["Gehaeuse", "Deckel"], color="#d9d9d9")
CASE_CMDS = len(cmds)

# ---------------- Platzhalter (nur fuer Vorschau / Kollisionspruefung) ----------------


def ph(name, corner, size, color):
    cmd("solid.box", length=round(size[0], 3), width=round(size[1], 3), height=round(size[2], 3),
        corner=corner, body_name=name)
    cmd("appearance.assign", bodies=[name], color=color, opacity=0.85)


ph("Leiterplatte", P(PCB_U0, PCB_V0, BOARD_Z), (PCB_W, PCB_L, PCB_T), "#b07a3c")
for (u, v) in HOLES:
    cyl([round(T + u, 3), round(T + v, 3), round(FL + BOARD_Z - 1, 3)], 1.8, PCB_T + 2, target="Leiterplatte")
ph("ESP32C3", P(ESP_U0, ESP_VC - ESP_W / 2, BOARD_Z - ESP_DROP), (ESP_L, ESP_W, ESP_DROP - SOCKET_H - SPACER_H), "#333333")
ph("ToF", P(TOF_UC - TOF_W / 2, TOF_PIN_V - TOF_PIN_Y, BOARD_Z - SOCKET_H - TOF_BODY_H), (TOF_W, TOF_H, TOF_BODY_H), "#2a5db0")
ph("Akkuhalter", P(BAT_U, RAIL + C, 0), (BAT_L, BAT_W, BAT_H), "#202020")
ph("TP4056", P(TP_U0, TP_V0, TP_PLAT), (TP_L, TP_W, 4.2), "#1a1a1a")
cmd("solid.cylinder", diameter=SW_BODY_D, height=SW_DEPTH, base=P(WI - SW_DEPTH, SW_V, SW_Z), axis="X", body_name="Schalter")
cmd("appearance.assign", bodies=["Schalter"], color="#aa2222", opacity=0.85)


def write_and_run():
    case = {"commands": cmds[:CASE_CMDS]}
    full = {"commands": cmds + [{"command": "inspect.interference", "params": {}}]}
    js = os.path.join(HERE, "gehaeuse.json")
    jsa = os.path.join(HERE, "gehaeuse_mit_bauteilen.json")
    json.dump(case, open(js, "w"), indent=1)
    json.dump(full, open(jsa, "w"), indent=1)
    print(f"Gehaeuse innen {WI} x {LI} x {HI} mm, aussen {WO:.1f} x {LO:.1f} x {HO:.1f} mm, Deckel {LID_L:.1f} x {LID_WD:.1f} x {LID_T} mm")
    print(f"Sensorfenster Ø{WIN_D} bei u={WIN_U:.2f} v={WIN_V:.2f} (innen), Platinenunterseite {BOARD_Z} mm ueber dem Boden")
    print(f"ESP-USB-C bei v={ESP_VC:.2f}, z={ESP_USB_Z:.2f}; TP4056-USB-C bei v={TP_V0 + TP_W / 2:.2f}; Schalter bei v={SW_V:.2f}")
    if "--no-run" in sys.argv:
        return

    def run(*a):
        r = subprocess.run([SC_CLI, *a], capture_output=True, text=True)
        if r.returncode:
            sys.exit("SolidCraft-Fehler (" + " ".join(a[:2]) + "): " + r.stdout + " " + r.stderr)
        return r
    run("run", js, "--save", os.path.join(HERE, "Gehaeuse.solidcraft"), "--quiet")
    for body, fn in (("Gehaeuse", "Gehaeuse.stl"), ("Deckel", "Deckel.stl")):
        exp = {"commands": cmds[:CASE_CMDS] + [{"command": "file.export",
                                                 "params": {"path": os.path.join(HERE, fn), "bodies": [body]}}]}
        tmp = os.path.join(HERE, "_export.json")
        json.dump(exp, open(tmp, "w"))
        run("run", tmp, "--quiet")
        os.remove(tmp)
    res = run("run", jsa, "--results", "--json-out", os.path.join(HERE, "_results.json"))
    results = json.load(open(os.path.join(HERE, "_results.json"), encoding="utf-8"))
    os.remove(os.path.join(HERE, "_results.json"))
    last = results[-1] if isinstance(results, list) else results
    hits = [i for i in last.get("result", last).get("interferences", [])
            if {i.get("a"), i.get("b")} != {None} and i.get("volume", 0) > 0.01]
    print("Kollisionen:", json.dumps(hits, indent=1) if hits else "keine")
    for view in ("iso", "top"):
        run("snapshot", jsa, "--out", os.path.join(HERE, f"preview_{view}.png"), "--view", view,
            "--width", "1800", "--height", "1000", "--no-grid", "--no-axes")


if __name__ == "__main__":
    write_and_run()
