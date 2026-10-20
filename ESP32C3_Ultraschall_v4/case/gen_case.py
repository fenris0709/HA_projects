#!/usr/bin/env python3
"""Gehaeuse fuer ESP32-C3 + 2x JSN-SR04T + 18650 als SolidCraft-Skript.

Erzeugt (im Ordner dieses Skripts):
  gehaeuse.json            SolidCraft-Befehlsskript (Unterteil + Deckel)
  Gehaeuse.solidcraft      Design zum Oeffnen/Weiterbearbeiten in SolidCraft
  Gehaeuse_Unterteil.stl   Druckteil, Boden unten
  Gehaeuse_Deckel.stl      Druckteil, Aussenseite unten (Druckorientierung)
  preview_*.png            Vorschau, mit Platzhaltern fuer die Bauteile
Aufruf: python gen_case.py            (Pfad zur CLI unten in SC_CLI)
        python gen_case.py --no-run   (nur JSON schreiben)

Koordinaten: X = Breite, Y = Laenge, Z = Hoehe. u/v/z = Innenmass ab der inneren Ecke links vorne
auf dem Boden. Layout (Draufsicht, Y nach oben):

   +-----------------------------+
   | [JSN #1, Stifte unten] [TP4056]=USB-C rechts
   |                        [     ]
   | [Lochraster/PCB]       [18650]
   |  ESP USB-C links       [halter]
   |                        [     ]
   | [JSN #2, Stifte oben]  [Schalter]
   +--Kabel #2-------------Schalter (Wand vorne)
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SC_CLI = r"C:\Program Files\SolidCraft\solidcraft-cli.exe"

# ---------------- Parameter (mm) ----------------
T = 2.0            # Wandstaerke (Schalter Einbaustaerke beachten)
FL = 2.0           # Bodenstaerke
HI = 30.0          # Innenhoehe
# Gewindeeinsaetze zum Einschmelzen (True) oder selbstschneidende Schrauben (False).
# Bohrung/Tiefe an die vorhandenen Einsaetze anpassen (Werte unten: gaengige Ruthex-Masse).
USE_INSERTS = True
if USE_INSERTS:
    POST = 8.0                          # Eckpfosten fuer Deckelschrauben (Kantenlaenge)
    POST_PILOT, POST_DEPTH = 4.0, 7.0   # M3-Einsatz (z. B. M3 x 5.7, Bohrung 4.0)
    BOSS_D, BOSS_PILOT = 6.0, 3.2       # M2-Einsatz (z. B. M2 x 3, Bohrung 3.2), Dom-Durchmesser
else:
    POST = 7.0
    POST_PILOT, POST_DEPTH = 2.5, 14.0  # M3 selbstschneidend
    BOSS_D, BOSS_PILOT = 5.0, 1.7       # M2 selbstschneidend

# JSN-SR04T V3.0 Steuerplatine (Datenblatt: 41.3 x 28.5, Loecher 4x d2 im Raster 36 x 24)
JSN_W, JSN_L = 41.3, 28.5
JSN_HX, JSN_HY = 36.0, 24.0
JSN_PINS = 5.8     # Stifte ragen in der Platinenebene ueber die Kante (34.3 - 28.5)
JSN_BOSS_H = 5.0

# Streifenraster 10 x 14 Raster = 25.4 x 35.56 (Layout: ../docs/stripboard.svg), ohne Befestigungsloecher:
# liegt auf 4 Eckauflagen, links unter zwei Leisten an der Gehaeusewand, rechts von 2 Rastzungen gehalten.
PB_W, PB_L = 10 * 2.54, 14 * 2.54
PB_BOSS_H = 5.0    # Hoehe der Auflagen (Platz fuer Loetstellen unter der Platine)
PB_T = 1.6         # Platinenstaerke
PB_GAP = 0.3       # Spiel rund um die Platine
CLIP_W, CLIP_T, CLIP_HOOK = 5.0, 1.2, 1.1   # Rastzunge: Breite, Dicke, Ueberstand der Nase ab Zunge
GAP_JSN_PB = 22.0  # Dupont-Stecker (14 mm) + Kabelbogen zwischen JSN-Kante und Platine
ESP_USB_ROW = 8    # Rasterzeile der ESP-Mitte (Zeile 0 = Kante Richtung JSN #1)

# ESP32-C3 SuperMini USB-C (Lochraster links an der Wand, ESP in Buchsenleiste)
ESP_HDR_SPACER, ESP_PCB = 2.5, 1.0                # Kunststoffsteg der Stiftleiste am ESP, Platinenstaerke
ESP_USB_Z = PB_BOSS_H + 1.6 + 8.5 + ESP_HDR_SPACER + ESP_PCB + 1.6   # Mitte USB-C ueber Innenboden
ESP_USB_W, ESP_USB_H = 13.0, 11.0

# 18650 Halter (1 Zelle) - wird aufgeklebt, an den Enden Platz fuer Loetfahnen/Draehte
BAT_W, BAT_L, BAT_H = 21.0, 78.0, 20.0
BAT_WIRE = 5.0
BAT_RIM = 2.0      # Hoehe Positionierrahmen

# TP4056 USB-C Lader (Verkaeuferfoto: ca. 17.9 x 14.1) - VOR DEM DRUCK NACHMESSEN
TP_L, TP_W = 17.9, 14.1
TP_PLAT = 3.0      # Sockel, damit die Buchse hoch genug in der Wand sitzt
TP_USB_Z = TP_PLAT + 1.0 + 1.6
TP_USB_W, TP_USB_H = 13.0, 7.5

# Schalter rund 20 mm (Wand vorne)
SW_HOLE = 20.2
SW_BODY_D, SW_DEPTH = 21.0, 25.0
SW_Z = 15.0

# Sensorkabel: U-Schlitz von oben in die Stirnwand (Stecker muss nicht durch)
CABLE_W, CABLE_DEPTH = 6.0, 12.0

# Deckel
LID_T, LIP_T, LIP_H, LIP_GAP = 2.0, 1.5, 4.0, 0.3
LID_HOLE = 3.4
EAR_W, EAR_L, EAR_T, EAR_HOLE = 16.0, 10.0, 3.0, 4.5   # Laschen zur Wandmontage
C = 0.5            # allgemeines Spiel

# ---------------- Layout ----------------
COL_A_W = max(JSN_W, PB_W) + 0.8
A_U0 = 1.0
B_U0 = A_U0 + COL_A_W + 3.0
END = POST + 1.0                        # Abstand Bauteile <-> Stirnwand (Eckpfosten)

JSN2_V = END
PB_V = JSN2_V + JSN_L + GAP_JSN_PB
JSN1_V = PB_V + PB_L + GAP_JSN_PB
LI = round(JSN1_V + JSN_L + END, 1)

SW_U = B_U0 + SW_BODY_D / 2 + 0.5
WI = round(max(SW_U + SW_BODY_D / 2 + POST + 0.5, B_U0 + BAT_W + 2 * 1.2 + 2 * C + 2.0), 1)
BAT_U = SW_U - BAT_W / 2
BAT_V = SW_DEPTH + 1.0 + BAT_WIRE
TP_U = WI - 1.0 - TP_L
TP_V = LI - END - TP_W - 1.0
A_UC = A_U0 + COL_A_W / 2
JSN_U = A_UC - JSN_W / 2
PB_U = PB_GAP                           # Platine links an der Wand (USB-C des ESP)

WO, LO, HO = WI + 2 * T, LI + 2 * T, HI + FL


def P(u, v, z=0.0):
    return [round(T + u, 3), round(T + v, 3), round(FL + z, 3)]


cmds = []


def cmd(c, **p):
    cmds.append({"command": c, "params": p})


def box(name, corner, size, op=None, target="Unterteil"):
    p = dict(length=round(size[0], 3), width=round(size[1], 3), height=round(size[2], 3), corner=corner)
    if op:
        p.update(operation=op, targets=[target])
    else:
        p.update(body_name=name)
    cmd("solid.box", **p)


def cyl(base, d, h, axis="Z", op="cut", target="Unterteil"):
    cmd("solid.cylinder", diameter=d, height=round(h, 3), base=base, axis=axis, operation=op, targets=[target])


def slot_x(side, v, z, w, h):
    """Langloch (Breite w entlang Y, Hoehe h, Mitte v/z absolut) durch die linke (side=0) oder rechte Wand."""
    x0 = -1 if side == 0 else WO - T - 1
    r = h / 2
    box(None, [x0, v - (w - h) / 2, z - r], [T + 2, w - h, h], "cut")
    for dv in (-(w - h) / 2, (w - h) / 2):
        cyl([x0, v + dv, z], h, T + 2, "X")


# ---------------- Unterteil ----------------
cmd("solid.box", length=WO, width=LO, height=HO, corner=[0, 0, 0], body_name="Unterteil")
cmd("solid.fillet", body="Unterteil", radius=3,
    edges=[[0, 0, HO / 2], [WO, 0, HO / 2], [0, LO, HO / 2], [WO, LO, HO / 2]])
box(None, P(0, 0), [WI, LI, HI + 1], "cut")

# Eckpfosten mit Kernloch fuer Deckelschrauben
POSTS = [(0, 0), (WI - POST, 0), (0, LI - POST), (WI - POST, LI - POST)]
for (u, v) in POSTS:
    box(None, P(u, v), [POST, POST, HI], "join")
    cyl(P(u + POST / 2, v + POST / 2, HI - POST_DEPTH), POST_PILOT, POST_DEPTH + 1)


def bosses(u0, v0, dx, dy, h, d=None, pilot=None):
    for du in (0, dx):
        for dv in (0, dy):
            cyl(P(u0 + du, v0 + dv), d or BOSS_D, h, op="join")
            cyl(P(u0 + du, v0 + dv, 0.5), pilot or BOSS_PILOT, h)


# Wanddurchbrueche (vor den Domen schneiden: SolidCraft-Kern ist reihenfolgeempfindlich)
ESP_V = PB_V + PB_L - (ESP_USB_ROW * 2.54 + 1.27)                   # Zeile 0 liegt oben (JSN #1)
slot_x(0, T + ESP_V, FL + ESP_USB_Z, ESP_USB_W, ESP_USB_H)            # ESP USB-C links
cyl([round(T + SW_U, 3), -1, round(FL + SW_Z, 3)], SW_HOLE, T + 2, "Y")  # Schalter vorne
for vwall in (-1, LO - T - 1):                                         # Kabelschlitze vorne/hinten
    box(None, [T + A_UC - CABLE_W / 2, vwall, HO - CABLE_DEPTH + CABLE_W / 2], [CABLE_W, T + 2, CABLE_DEPTH], "cut")
    cyl([T + A_UC, vwall, HO - CABLE_DEPTH + CABLE_W / 2], CABLE_W, T + 2, "Y")


# JSN-Dome (Lochbild symmetrisch, Drehung egal)
for v in (JSN2_V, JSN1_V):
    bosses(JSN_U + (JSN_W - JSN_HX) / 2, v + (JSN_L - JSN_HY) / 2, JSN_HX, JSN_HY, JSN_BOSS_H)
# Lochraster / spaeteres PCB
# Streifenraster: Eckauflagen, Anschlaege oben/unten, Leisten links, Rastzungen rechts
PB_TOP = PB_BOSS_H + PB_T
for (u, v) in ((PB_U + 11.6, PB_V), (PB_U + PB_W - 2.2, PB_V), (PB_U, PB_V + PB_L - 2.2), (PB_U + PB_W - 2.2, PB_V + PB_L - 2.2)):
    box(None, P(u, v), [2.2, 2.2, PB_BOSS_H], "join")
for col in (0.5, 9):                    # Anschlaege an freien Randloechern (oben: Spalte 0/1 und 9, unten: 6/7 und 9)
    box(None, P(PB_U + col * 2.54 - 0.4, PB_V + PB_L + PB_GAP), [3, 1.2, PB_TOP + 1.0], "join")
for col in (6.5, 9):
    box(None, P(PB_U + col * 2.54 - 0.4, PB_V - PB_GAP - 1.2), [3, 1.2, PB_TOP + 1.0], "join")
for (v0, v1) in ((PB_V + PB_L - 6.5, PB_V + PB_L - 1.0), (PB_V + 8.0, PB_V + 12.5)):   # Leisten links (frei von J3/Draehten)
    box(None, P(-0.3, v0, PB_TOP + 0.15), [PB_U + 1.0, v1 - v0, 1.4], "join")   # 0,3 mm in die Wand
for v in (PB_V + PB_L * 0.3, PB_V + PB_L * 0.7):                                 # Rastzungen rechts
    ux = PB_U + PB_W + PB_GAP
    box(None, P(ux, v - CLIP_W / 2), [CLIP_T, CLIP_W, PB_TOP + 0.15 + 1.6], "join")
    for k in range(3):   # Nase: unten volle Ueberdeckung, oben schraeg (Einfuehrschraege in 3 Stufen)
        o = CLIP_HOOK * (3 - k) / 3
        box(None, P(ux - o, v - CLIP_W / 2, PB_TOP + 0.15 + 0.4 * k), [o + 0.3, CLIP_W, 0.4], "join")

# Positionierrahmen 18650-Halter (Enden offen fuer Draehte)
rim = 1.2
bx0, by0 = BAT_U - C - rim, BAT_V - C - rim
bw, bl = BAT_W + 2 * C + 2 * rim, BAT_L + 2 * C + 2 * rim
box(None, P(bx0, by0), [bw, bl, BAT_RIM], "join")
box(None, P(bx0 + rim, by0 + rim, 0), [bw - 2 * rim, bl - 2 * rim, BAT_RIM + 1], "cut")
for v in (by0 - 0.5, by0 + bl - rim - 0.5):
    box(None, P(BAT_U + BAT_W / 2 - 5, v, 0), [10, rim + 1, BAT_RIM + 1], "cut")

# TP4056-Sockel mit Tasche, offen zur Wand rechts
tpx0, tpy0 = TP_U - C - rim, TP_V - C - rim
box(None, P(tpx0, tpy0), [WI - tpx0, TP_W + 2 * C + 2 * rim, TP_PLAT + 1.5], "join")
box(None, P(TP_U - C, TP_V - C, TP_PLAT), [WI - TP_U + C + 1, TP_W + 2 * C, 5], "cut")
slot_x(1, T + TP_V + TP_W / 2, FL + TP_USB_Z, TP_USB_W, TP_USB_H)     # TP4056 USB-C rechts

# Laschen zur Wandmontage
for (y0, yh) in ((-EAR_L, 0 - EAR_L / 2), (LO, LO + EAR_L / 2)):
    box(None, [WO / 2 - EAR_W / 2, y0, 0], [EAR_W, EAR_L + 1, EAR_T], "join")
    cyl([WO / 2, yh, -1], EAR_HOLE, EAR_T + 2)

# ---------------- Deckel (Druckorientierung: Aussenseite unten, neben dem Unterteil) ----------------
LX = WO + 15.0


def mx(x):
    """Deckel ist gedreht (um Y): Box-x -> Deckel-x."""
    return LX + (WO - x)


cmd("solid.box", length=WO, width=LO, height=LID_T, corner=[LX, 0, 0], body_name="Deckel")
cmd("solid.fillet", body="Deckel", radius=3,
    edges=[[LX, 0, LID_T / 2], [LX + WO, 0, LID_T / 2], [LX, LO, LID_T / 2], [LX + WO, LO, LID_T / 2]])
lo_u, hi_u = T + LIP_GAP, T + WI - LIP_GAP
lo_v, hi_v = T + LIP_GAP, T + LI - LIP_GAP
box(None, [mx(hi_u), lo_v, LID_T], [hi_u - lo_u, hi_v - lo_v, LIP_H], "join", "Deckel")
box(None, [mx(hi_u) + LIP_T, lo_v + LIP_T, LID_T], [hi_u - lo_u - 2 * LIP_T, hi_v - lo_v - 2 * LIP_T, LIP_H + 1],
    "cut", "Deckel")
for (u, v) in POSTS:   # Ausschnitte fuer Eckpfosten
    box(None, [mx(T + u + POST + 0.5), T + v - 0.5, LID_T], [POST + 1, POST + 1, LIP_H + 1], "cut", "Deckel")
    cyl([mx(T + u + POST / 2), T + v + POST / 2, -1], LID_HOLE, LID_T + 2, op="cut", target="Deckel")
for v in (T - 1, T + LI - 3):   # Lippe an den Kabelschlitzen offen
    box(None, [mx(T + A_UC + CABLE_W / 2 + 1), v, LID_T], [CABLE_W + 2, 4, LIP_H + 1], "cut", "Deckel")

cmd("appearance.assign", bodies=["Unterteil", "Deckel"], color="#d9d9d9")
UNTER_CMDS = len(cmds)

# ---------------- Platzhalter (nur fuer Vorschau / Kollisionspruefung) ----------------
PH = []


def ph(name, uvz, size, color):
    cmd("solid.box", length=round(size[0], 3), width=round(size[1], 3), height=round(size[2], 3),
        corner=P(*uvz), body_name=name)
    cmd("appearance.assign", bodies=[name], color=color, opacity=0.85)
    PH.append(name)


ph("JSN2", (JSN_U, JSN2_V, JSN_BOSS_H), (JSN_W, JSN_L, 12), "#2a5db0")
ph("JSN2_Stifte", (A_UC - 5, JSN2_V + JSN_L, JSN_BOSS_H + 1.6), (10, JSN_PINS, 2.5), "#c9a227")
ph("JSN1", (JSN_U, JSN1_V, JSN_BOSS_H), (JSN_W, JSN_L, 12), "#2a5db0")
ph("JSN1_Stifte", (A_UC - 5, JSN1_V - JSN_PINS, JSN_BOSS_H + 1.6), (10, JSN_PINS, 2.5), "#c9a227")
ph("Streifenraster", (PB_U, PB_V, PB_BOSS_H), (PB_W, PB_L, PB_T), "#b07a3c")
ph("ESP32C3", (PB_U + 0.3, ESP_V - 9, PB_BOSS_H + PB_T + 8.5 + ESP_HDR_SPACER), (22.5, 18, 4.5), "#333333")
ph("Akkuhalter", (BAT_U, BAT_V, 0), (BAT_W, BAT_L, BAT_H), "#202020")
ph("TP4056", (TP_U, TP_V, TP_PLAT), (TP_L, TP_W, 4.2), "#1a1a1a")
cmd("solid.cylinder", diameter=SW_BODY_D, height=SW_DEPTH, base=P(SW_U, 0, SW_Z), axis="Y", body_name="Schalter")
cmd("appearance.assign", bodies=["Schalter"], color="#aa2222", opacity=0.85)
PH.append("Schalter")


def write_and_run():
    unter = {"commands": cmds[:UNTER_CMDS]}
    full = {"commands": cmds + [{"command": "inspect.interference", "params": {}}]}
    js = os.path.join(HERE, "gehaeuse.json")
    jsa = os.path.join(HERE, "gehaeuse_mit_bauteilen.json")
    json.dump(unter, open(js, "w"), indent=1)
    json.dump(full, open(jsa, "w"), indent=1)
    print(f"Innen {WI} x {LI} x {HI} mm, aussen {WO} x {LO} x {HO + LID_T} mm (mit Deckel)")
    if "--no-run" in sys.argv:
        return
    run = lambda *a: subprocess.run([SC_CLI, *a], check=True, capture_output=True, text=True)
    run("run", js, "--save", os.path.join(HERE, "Gehaeuse.solidcraft"), "--quiet")
    for body, fn in (("Unterteil", "Gehaeuse_Unterteil.stl"), ("Deckel", "Gehaeuse_Deckel.stl")):
        exp = {"commands": cmds[:UNTER_CMDS] + [{"command": "file.export",
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
            "--width", "1400", "--height", "1000", "--no-grid", "--no-axes")


if __name__ == "__main__":
    write_and_run()
