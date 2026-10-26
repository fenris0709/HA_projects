"""Gehaeuse fuer ESP32-C3 + 2x TOF200C (VL53L0X) + 18650 als SolidCraft-Skript.

Alle Platinen werden mit Heissleim eingeklebt (keine Schnappmechanismen). Positionierhilfen:
Stifte durch die Befestigungsloecher der ToF-Boards, niedrige Rahmen, Eckauflagen.

Erzeugt (im Ordner dieses Skripts):
  gehaeuse.json            SolidCraft-Befehlsskript (Unterteil + Deckel + Passprobe)
  Gehaeuse.solidcraft      Design zum Oeffnen/Weiterbearbeiten in SolidCraft
  Gehaeuse_Unterteil.stl   Druckteil, Boden unten
  Gehaeuse_Deckel.stl      Druckteil, Aussenseite unten (Druckorientierung)
  Gehaeuse_Passprobe.stl   kleines Probestueck (ToF-Fenster + TP4056 mit USB-Loch) zum Pruefen der Masse
  preview_*.png            Vorschau, mit Platzhaltern fuer die Bauteile
Aufruf: python gen_case.py            (Pfad zur CLI unten in SC_CLI)
        python gen_case.py --no-run   (nur JSON schreiben)

Koordinaten: X = Breite, Y = Laenge, Z = Hoehe. u/v/z = Innenmass ab der inneren Ecke links vorne
auf dem Boden. Layout (Draufsicht, Y nach oben):

   +-------------------------------+
   | [Streifenraster]   [18650-    |
   |  ESP USB-C links    Halter,   |
   | [ToF #1  Fenster ]  quer zur  |
   | [ToF #2  Fenster ]  Wand      |
   | [TP4056]  [Schalter]          |
   +--USB-C---Schalter (Wand vorne)
Die ToF-Boards liegen mit dem Sensor nach unten auf dem Boden, Messrichtung durch die Fenster im Boden.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SC_CLI = r"C:\Program Files\SolidCraft\solidcraft-cli.exe"

# ---------------- Parameter (mm) ----------------
T = 2.0            # Wandstaerke (Schalter Einbaustaerke beachten)
FL = 2.0           # Bodenstaerke
HI = 30.0          # Innenhoehe
# Gewindeeinsaetze zum Einschmelzen (True) oder selbstschneidende Schrauben (False).
USE_INSERTS = True
if USE_INSERTS:
    POST = 8.0                          # Eckpfosten fuer Deckelschrauben (Kantenlaenge)
    POST_PILOT, POST_DEPTH = 4.0, 7.0   # M3-Einsatz (z. B. M3 x 5.7, Bohrung 4.0)
else:
    POST = 7.0
    POST_PILOT, POST_DEPTH = 2.5, 14.0  # M3 selbstschneidend

# TOF200C / TOF050C Breakout (datasheets/tof200c_dimensions.md): 20 x 11, Loecher d2 im Abstand 14.4,
# Fenster 9.6 x 5. Sensor- und Lochmitte ca. 3.3 vom Rand (aus dem Bild geschaetzt) - NACHMESSEN.
TOF_W, TOF_H = 20.0, 11.0
TOF_HX, TOF_HY = 14.4, 3.3         # Lochabstand, Abstand Loch-/Fenstermitte von der Fensterkante
TOF_WIN_L, TOF_WIN_W = 10.6, 5.8   # Fensterdurchbruch (Sensor 9.6 x 5 plus Spiel)
TOF_PCB = 1.2                      # Platinenstaerke (geschaetzt)
TOF_PEG_D, TOF_PEG_H = 1.8, 2.0    # Positionierstift durch das Befestigungsloch
TOF_RIM, TOF_RIM_H, TOF_C = 1.0, 1.6, 0.3   # Rahmen: Wandstaerke, Hoehe, Spiel

# Streifenraster 10 x 14 Raster = 25.4 x 35.56 (Layout: ../docs/stripboard.svg), ohne Befestigungsloecher:
# liegt auf 4 Eckauflagen (Platz fuer Loetstellen), Anschlaege aussen herum, mit Heissleim fixiert.
PB_W, PB_L = 10 * 2.54, 14 * 2.54
PB_BOSS_H = 5.0    # Hoehe der Auflagen
PB_T = 1.6         # Platinenstaerke
PB_GAP = 0.3       # Spiel rund um die Platine
ESP_USB_ROW = 8    # Rasterzeile der ESP-Mitte (Zeile 0 = Kante Richtung ToF-Boards, vorne)

# ESP32-C3 SuperMini USB-C (Lochraster links an der Wand, ESP in Buchsenleiste)
ESP_HDR_SPACER, ESP_PCB = 2.5, 1.0                # Kunststoffsteg der Stiftleiste am ESP, Platinenstaerke
ESP_USB_Z = PB_BOSS_H + 1.6 + 8.5 + ESP_HDR_SPACER + ESP_PCB + 1.6   # Mitte USB-C ueber Innenboden
ESP_USB_W, ESP_USB_H = 13.0, 11.0

# 18650 Halter (1 Zelle) - wird aufgeklebt, an den Enden Platz fuer Loetfahnen/Draehte
BAT_W, BAT_L, BAT_H = 21.0, 78.0, 20.0
BAT_WIRE = 5.0
BAT_RIM = 2.0      # Hoehe Positionierrahmen

# TP4056 USB-C Lader (Verkaeuferfoto: ca. 17.9 x 14.1) - VOR DEM DRUCK NACHMESSEN
# Lange Seite (TP_L) laeuft in Y, USB-C zeigt durch die Vorderwand, Loetseite nach hinten offen.
TP_L, TP_W = 17.9, 14.1
TP_PLAT = 3.0      # Sockel, damit die Buchse hoch genug in der Wand sitzt
TP_RIM, TP_RIM_H = 1.0, 1.5
TP_USB_Z = TP_PLAT + 1.0 + 1.6
TP_USB_W, TP_USB_H = 13.0, 7.5
TP_WIRE = 6.0      # Platz hinter dem TP4056 fuer die Loetdraehte (B+/B-/OUT+/OUT-)

# Schalter rund 20 mm (Wand vorne)
SW_HOLE = 20.2
SW_BODY_D, SW_DEPTH = 21.0, 25.0
SW_Z = 15.0

# Sensorkappe = Blindkappe (3D-gedruckt), 1 Sensor pro Tank (2x drucken). Sie wird ueber den Gewindestutzen des
# Tanks gestuelpt (Stutzen aussen 100 mm, innen ca. 80 mm) und hat in der Mitte ein Sichtloch. Das ToF-Board sitzt
# AUSSEN auf der Kappe in einem separaten Sensorhalter (2x drucken, mit Heissleim ueber das Sichtloch geklebt),
# so muss das Kabel nirgends durch die Kappe. Gedruckt wird die Kappe mit der Platte unten auf dem Bett.
CAP_ID, CAP_H, CAP_T = 102.0, 30.0, 3.0    # Innendurchmesser (Stutzen 100 + 1 mm Spiel je Seite), Tiefe ueber der Platte, Wand
CAP_VIEW_D = 24.0                          # Sichtloch in der Kappenplatte (grosszuegig, das Fenster im Halter begrenzt den Strahl)
HOLDER_MARGIN, HOLDER_TAIL = 3.0, 8.0      # Rand um das Board, Platz auf der Pinseite fuer die Kabeladern

# Sensorkabel (je Sensor 1, z. B. Cat5/6, 1-2 m): U-Schlitz von oben in die Wand, Stecker muss nicht durch
CABLE_W, CABLE_DEPTH = 10.0, 12.0
CABLE_U = POST + 1.0 + CABLE_W / 2         # Schlitz hinten im Hauptgehaeuse neben dem Eckpfosten

# Deckel
LID_T, LIP_T, LIP_H, LIP_GAP = 2.0, 1.5, 4.0, 0.3
LID_HOLE = 3.4
EAR_W, EAR_L, EAR_T, EAR_HOLE = 16.0, 10.0, 3.0, 4.5   # Laschen zur Wandmontage
C = 0.5            # allgemeines Spiel

# ---------------- Layout Hauptgehaeuse ----------------
# Spalte A (links): Schalter in der Vorderwand, TP4056 (USB-C links), Streifenraster (hinten, Kabelschlitz hinten)
# Spalte B (rechts): Akkuhalter
END = POST + 1.0                        # Abstand Bauteile <-> Stirnwand (Eckpfosten)
PB_U = PB_GAP                           # Platine links an der Wand (USB-C des ESP)

SW_U = POST + 0.5 + SW_BODY_D / 2       # Schalter neben dem Eckpfosten
TP_U = 0.5                              # TP4056 an der linken Wand, USB-C zeigt nach links
TP_V = SW_DEPTH + 2.0
PB_V = TP_V + TP_W + 2 * (C + TP_RIM) + 3.0
BAT_RIMW = 1.2
B_U0 = max(SW_U + SW_BODY_D / 2, PB_U + PB_W + 1.5) + 3.0
BAT_U = B_U0 + C + BAT_RIMW
BAT_V = BAT_WIRE + C + BAT_RIMW
WI = round(BAT_U + BAT_W + C + BAT_RIMW + POST + 0.3, 1)
LI = round(max(PB_V + PB_L + END, BAT_V + BAT_L + C + BAT_RIMW + BAT_WIRE), 1)

WO, LO, HO = WI + 2 * T, LI + 2 * T, HI + FL


def P(u, v, z=0.0, org=None):
    ox, oy = org or (T, T)
    return [round(ox + u, 3), round(oy + v, 3), round(FL + z, 3)]


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


def slot_x(x0, v, z, w, h, target="Unterteil"):
    """Langloch (Breite w entlang Y, Hoehe h, Mitte v/z absolut) durch eine Wand in X-Richtung ab x0."""
    r = h / 2
    box(None, [x0, v - (w - h) / 2, z - r], [T + 2, w - h, h], "cut", target)
    for dv in (-(w - h) / 2, (w - h) / 2):
        cyl([x0, v + dv, z], h, T + 2, "X", target=target)


def u_slot(x, y0, ztop, w, depth, target):
    """U-Schlitz von oben in eine Wand in Y-Richtung (Kabel muss nicht durchgefaedelt werden)."""
    zc = ztop - depth + w / 2
    box(None, [x - w / 2, y0, zc], [w, T + 4, depth - w / 2 + 1], "cut", target)
    cyl([x, y0, zc], w - 0.02, T + 4, "Y", target=target)   # minimal schmaler: Tangente an der Boxkante schlaegt sonst fehl


# ---- Montagestrukturen (fuer Unterteil, Sensorgehaeuse und Passprobe gleich; org = absoluter Ursprung) ----
def tof_cut(uc, v, org, target):
    """Fensterdurchbruch in der Platte. v = Kante des Boards auf der Fensterseite, uc = Mitte."""
    x, y = org[0] + uc, org[1] + v + TOF_HY
    r = TOF_WIN_W / 2
    box(None, [x - (TOF_WIN_L - TOF_WIN_W) / 2, y - r, -1], [TOF_WIN_L - TOF_WIN_W, TOF_WIN_W, FL + 2], "cut", target)
    for dx in (-(TOF_WIN_L - TOF_WIN_W) / 2, (TOF_WIN_L - TOF_WIN_W) / 2):
        cyl([x + dx, y, -1], TOF_WIN_W - 0.02, FL + 2, "Z", target=target)   # minimal schmaler: Tangente schlaegt sonst fehl


def tof_join(uc, v, org, target):
    """Stifte durch die Befestigungsloecher und Rahmen an der Fensterseite und links/rechts (Pinseite offen)."""
    for du in (-TOF_HX / 2, TOF_HX / 2):
        cyl(P(uc + du, v + TOF_HY, -0.5, org), TOF_PEG_D, TOF_PEG_H + 0.5, op="join", target=target)
    u0, u1 = uc - TOF_W / 2 - TOF_C - TOF_RIM, uc + TOF_W / 2 + TOF_C
    box(None, P(u0, v - TOF_C - TOF_RIM, -0.5, org), [u1 - u0 + TOF_RIM, TOF_RIM, TOF_RIM_H + 0.5], "join", target)
    for ux in (u0, u1):
        box(None, P(ux, v - TOF_C - TOF_RIM, -0.5, org), [TOF_RIM, TOF_H * 0.6 + TOF_C + TOF_RIM, TOF_RIM_H + 0.5],
            "join", target)


def tp_join(u0, v0, org, target):
    """TP4056 (USB-C links an der Wand): Sockel mit Rahmen vorne/hinten, Loetseite nach rechts offen."""
    ul = u0 + TP_L
    pv0 = v0 - C - TP_RIM
    pw = TP_W + 2 * C + 2 * TP_RIM
    box(None, P(0, pv0, 0, org), [ul, pw, TP_PLAT], "join", target)
    for vy in (pv0, pv0 + pw - TP_RIM):
        box(None, P(0, vy, TP_PLAT, org), [ul, TP_RIM, TP_RIM_H], "join", target)


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

# Wanddurchbrueche (vor den Aufbauten schneiden: SolidCraft-Kern ist reihenfolgeempfindlich)
ESP_V = PB_V + PB_L - (ESP_USB_ROW * 2.54 + 1.27)                         # Zeile 0 liegt hinten (Kabel)
slot_x(-1, T + ESP_V, FL + ESP_USB_Z, ESP_USB_W, ESP_USB_H)                # ESP USB-C links
slot_x(-1, T + TP_V + TP_W / 2, FL + TP_USB_Z, TP_USB_W, TP_USB_H)         # TP4056 USB-C links
cyl([round(T + SW_U, 3), -1, round(FL + SW_Z, 3)], SW_HOLE, T + 2, "Y")    # Schalter vorne
u_slot(T + CABLE_U, LO - T - 1, HO, CABLE_W, CABLE_DEPTH, "Unterteil")     # Sensorkabel hinten

# Streifenraster: Eckauflagen (Loetstellen frei), Anschlaege aussen herum, links die Wand
PB_TOP = PB_BOSS_H + PB_T
for (u, v) in ((PB_U + 11.6, PB_V), (PB_U + PB_W - 2.2, PB_V),
               (PB_U, PB_V + PB_L - 2.2), (PB_U + PB_W - 2.2, PB_V + PB_L - 2.2)):
    box(None, P(u, v), [2.2, 2.2, PB_BOSS_H], "join")
for v in (PB_V - PB_GAP - 1.2, PB_V + PB_L + PB_GAP):          # vorne/hinten
    for u in (PB_U, PB_U + PB_W - 4.0):
        box(None, P(u, v), [4.0, 1.2, PB_TOP + 1.0], "join")
for v in (PB_V, PB_V + PB_L - 4.0):                              # rechts
    box(None, P(PB_U + PB_W + PB_GAP, v), [1.2, 4.0, PB_TOP + 1.0], "join")

# Positionierrahmen 18650-Halter (Enden offen fuer Draehte)
rim = BAT_RIMW
bx0, by0 = BAT_U - C - rim, BAT_V - C - rim
bw, bl = BAT_W + 2 * C + 2 * rim, BAT_L + 2 * C + 2 * rim
box(None, P(bx0, by0), [bw, bl, BAT_RIM], "join")
box(None, P(bx0 + rim, by0 + rim, 0), [bw - 2 * rim, bl - 2 * rim, BAT_RIM + 1], "cut")
for v in (by0 - 0.5, by0 + bl - rim - 0.5):
    box(None, P(BAT_U + BAT_W / 2 - 5, v, 0), [10, rim + 1, BAT_RIM + 1], "cut")

# TP4056-Sockel
tp_join(TP_U, TP_V, (T, T), "Unterteil")

# Laschen zur Wandmontage: vorne unter dem Schalter, hinten mittig
for (xc, y0, yh) in ((T + SW_U, -EAR_L, 0 - EAR_L / 2), (WO / 2, LO, LO + EAR_L / 2)):
    box(None, [xc - EAR_W / 2, y0, 0], [EAR_W, EAR_L + 1, EAR_T], "join")
    cyl([xc, yh, -1], EAR_HOLE, EAR_T + 2)

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
box(None, [mx(T + CABLE_U + CABLE_W / 2 + 1), T + LI - 3, LID_T], [CABLE_W + 2, 4, LIP_H + 1], "cut", "Deckel")  # Lippe am Kabelschlitz offen

# ---------------- Sensorkappe: Blindkappe ueber den Tankstutzen mit Sichtloch in der Mitte ----------------
# Becher: Platte FL dick (im Einsatz oben), darauf eine Wand mit CAP_ID Innendurchmesser und CAP_H Hoehe (im Einsatz nach unten offen).
CAP_R = CAP_ID / 2 + CAP_T
CAPCX, CAPCY = LX + WO + 15.0 + CAP_R, CAP_R
cmd("solid.cylinder", diameter=2 * CAP_R, height=FL + CAP_H, base=[CAPCX, CAPCY, 0], axis="Z", body_name="Sensorgehaeuse")
cyl([CAPCX, CAPCY, FL], CAP_ID, CAP_H + 1, target="Sensorgehaeuse")
cyl([CAPCX, CAPCY, -1], CAP_VIEW_D, FL + 2, target="Sensorgehaeuse")

# ---------------- Sensorhalter: kleine Platte mit Fenster, Stiften und Rahmen fuer das ToF-Board ----------------
# Wird mit dem Fenster ueber das Sichtloch auf die Aussenseite der Kappe geklebt. Das Board liegt mit der Sensorseite
# nach unten auf der Platte, Pinseite zeigt nach +Y (dort die Adern anloeten).
TOF_V0 = -TOF_HY
HW = TOF_W + 2 * (TOF_C + TOF_RIM + HOLDER_MARGIN)
HY_FRONT = TOF_C + TOF_RIM + HOLDER_MARGIN                 # Plattenkante bis Board-Vorderkante
HL = HY_FRONT + TOF_H + HOLDER_TAIL
HX = CAPCX + CAP_R + 15.0
HOLDER_ORG = (HX + HW / 2, HY_FRONT + TOF_HY)             # Sensormitte
cmd("solid.box", length=round(HW, 3), width=round(HL, 3), height=FL, corner=[HX, 0, 0], body_name="Sensorhalter")
tof_cut(0.0, TOF_V0, HOLDER_ORG, "Sensorhalter")
tof_join(0.0, TOF_V0, HOLDER_ORG, "Sensorhalter")

# ---------------- Passprobe: Probedruck zum Pruefen der Masse, bevor das ganze Gehaeuse gedruckt wird ----------------
# Enthaelt den TP4056-Sockel mit USB-C-Loch in der Wand und ein ToF-Fenster mit Stiften/Rahmen wie im Sensorhalter.
CX = HX + HW + 15.0
PP_V = 3.0 + TP_RIM + C                  # TP4056 ab hier in Y
PP_UC = TP_U + TP_L + 4.0 + TOF_W / 2 + TOF_C + TOF_RIM
PP_W = T + PP_UC + TOF_W / 2 + 4.0
PP_L = PP_V + TP_W + C + TP_RIM + 3.0
PP_ORG = (CX + T, 0)                     # Innenecke an der Wand
cmd("solid.box", length=round(PP_W, 3), width=round(PP_L, 3), height=FL, corner=[CX, 0, 0], body_name="Passprobe")
box(None, [CX, 0, FL], [T, PP_L, 14.0], "join", "Passprobe")
slot_x(CX - 1, PP_V + TP_W / 2, FL + TP_USB_Z, TP_USB_W, TP_USB_H, "Passprobe")
tp_join(TP_U, PP_V, PP_ORG, "Passprobe")
tof_cut(PP_UC, 4.0, PP_ORG, "Passprobe")
tof_join(PP_UC, 4.0, PP_ORG, "Passprobe")

cmd("appearance.assign", bodies=["Unterteil", "Deckel", "Sensorgehaeuse", "Sensorhalter", "Passprobe"], color="#d9d9d9")

UNTER_CMDS = len(cmds)

# ---------------- Platzhalter (nur fuer Vorschau / Kollisionspruefung) ----------------
PH = []


def ph(name, corner, size, color):
    cmd("solid.box", length=round(size[0], 3), width=round(size[1], 3), height=round(size[2], 3),
        corner=corner, body_name=name)
    cmd("appearance.assign", bodies=[name], color=color, opacity=0.85)
    PH.append(name)


ph("Streifenraster", P(PB_U, PB_V, PB_BOSS_H), (PB_W, PB_L, PB_T), "#b07a3c")
ph("ESP32C3", P(PB_U + 0.3, ESP_V - 9, PB_BOSS_H + PB_T + 8.5 + ESP_HDR_SPACER), (22.5, 18, 4.5), "#333333")
ph("Akkuhalter", P(BAT_U, BAT_V, 0), (BAT_W, BAT_L, BAT_H), "#202020")
ph("TP4056", P(TP_U, TP_V, TP_PLAT), (TP_L, TP_W, 4.2), "#1a1a1a")
cmd("solid.cylinder", diameter=SW_BODY_D, height=SW_DEPTH, base=P(SW_U, 0, SW_Z), axis="Y", body_name="Schalter")
cmd("appearance.assign", bodies=["Schalter"], color="#aa2222", opacity=0.85)
PH.append("Schalter")
ph("ToF", P(-TOF_W / 2, TOF_V0, 0, HOLDER_ORG), (TOF_W, TOF_H, TOF_PCB), "#2a5db0")


def write_and_run():
    unter = {"commands": cmds[:UNTER_CMDS]}
    full = {"commands": cmds + [{"command": "inspect.interference", "params": {}}]}
    js = os.path.join(HERE, "gehaeuse.json")
    jsa = os.path.join(HERE, "gehaeuse_mit_bauteilen.json")
    json.dump(unter, open(js, "w"), indent=1)
    json.dump(full, open(jsa, "w"), indent=1)
    print(f"Hauptgehaeuse innen {WI} x {LI} x {HI} mm, aussen {WO} x {LO} x {HO + LID_T} mm (mit Deckel)")
    print(f"Sensorkappe (2x drucken) innen d{CAP_ID} x {CAP_H} mm tief, aussen d{2 * CAP_R} x {FL + CAP_H} mm; Sensorhalter (2x) {round(HW, 1)} x {round(HL, 1)} mm")
    if "--no-run" in sys.argv:
        return
    def run(*a):
        r = subprocess.run([SC_CLI, *a], capture_output=True, text=True)
        if r.returncode:
            sys.exit("SolidCraft-Fehler (" + " ".join(a[:2]) + "): " + r.stdout + " " + r.stderr)
        return r
    run("run", js, "--save", os.path.join(HERE, "Gehaeuse.solidcraft"), "--quiet")
    for body, fn in (("Unterteil", "Gehaeuse_Unterteil.stl"), ("Deckel", "Gehaeuse_Deckel.stl"),
                     ("Sensorgehaeuse", "Sensorkappe.stl"), ("Sensorhalter", "Sensorhalter.stl"),
                     ("Passprobe", "Gehaeuse_Passprobe.stl")):
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
            "--width", "1800", "--height", "1000", "--no-grid", "--no-axes")


if __name__ == "__main__":
    write_and_run()
