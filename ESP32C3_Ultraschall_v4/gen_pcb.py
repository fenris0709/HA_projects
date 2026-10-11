#!/usr/bin/env python3
"""Erzeugt ESP32C3_Ultraschall_v4.kicad_pcb (4 Lagen: F.Cu Signal / In1 GND-Plane / In2 Supply-Plane / B.Cu Signal).
Platzierung kompakt, Netze mit Direktverbindungen, A*-Router fuer Signalnetze, Plane-Vias fuer SMD-Pads,
eigener Clearance-Check und PNG-Vorschau."""
import heapq, json, math, sys, uuid
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "ESP32C3_Ultraschall_v4.kicad_pcb"
PNG = OUT.replace(".kicad_pcb", "_preview.png")
UU = json.load(open("/tmp/uuids.json"))

W, H = 51.5, 99.5
RES = 0.1
CLR = 0.25
CHECK_CLR = 0.2
VIA_D, VIA_DRILL = 0.8, 0.4
W_SIG, W_PWR, W_DOG = 0.25, 0.4, 0.3
EDGE = 0.8

ZONES = {"VBAT_SW": [(0.5, 0.5, W - 0.5, H - 0.5)]}   # Supply-Plane In2 ueber die ganze Platine
PLANE_NETS = {"GND", "VBAT_SW"}

def uid():
    return str(uuid.uuid4())

# ---------------- Footprints ----------------
def hdr(n):
    return [(str(i + 1), 0.0, 2.54 * i, 1.7, 1.7, "rect" if i == 0 else "circle", True, 1.0) for i in range(n)]

def esp():
    pads = [(str(i + 1), 0.0, 2.54 * i, 1.8, 1.8, "rect" if i == 0 else "circle", True, 1.0) for i in range(8)]
    pads += [(str(i + 9), 15.24, 2.54 * i, 1.8, 1.8, "circle", True, 1.0) for i in range(8)]
    return pads

def two(dx, w, h):
    return [("1", -dx, 0.0, w, h, "roundrect", False, 0), ("2", dx, 0.0, w, h, "roundrect", False, 0)]

FP = {
    "HDR2": ("Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", hdr(2), (-1.4, -1.2, 1.4, 2.54 + 1.2)),
    "HDR4": ("Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", hdr(4), (-1.4, -1.2, 1.4, 7.62 + 1.2)),
    "ESP": ("proj_modules:ESP32C3_SuperMini_THT", esp(), (-1.5, -2.0, 16.8, 17.78 + 2.0)),
    "R0805": ("Resistor_SMD:R_0805_2012Metric", two(0.9125, 1.025, 1.4), (-1.7, -0.95, 1.7, 0.95)),
    "C0805": ("Capacitor_SMD:C_0805_2012Metric", two(0.95, 1.0, 1.45), (-1.7, -0.95, 1.7, 0.95)),
    "C1206": ("Capacitor_SMD:C_1206_3216Metric", two(1.475, 1.15, 1.8), (-2.3, -1.15, 2.3, 1.15)),
    "SOT23": ("Package_TO_SOT_SMD:SOT-23-3",
              [("1", -1.1375, -0.95, 1.475, 0.6, "rect", False, 0),
               ("2", -1.1375, 0.95, 1.475, 0.6, "rect", False, 0),
               ("3", 1.1375, 0.0, 1.475, 0.6, "rect", False, 0)], (-2.0, -1.6, 2.0, 1.6)),
    "MH2": ("MountingHole:MountingHole_2.2mm_M2", [("", 0.0, 0.0, 2.4, 2.4, "circle", "np", 2.4)], (-2.2, -2.2, 2.2, 2.2)),
    "MH": ("MountingHole:MountingHole_3.2mm_M3", [("", 0.0, 0.0, 3.2, 3.2, "circle", "np", 3.2)], (-1.7, -1.7, 1.7, 1.7)),
}

# ref -> (typ, x, y, rot, wert)
# Modul 1 oben (Stiftleiste unten), Modul 2 unten (180 Grad, Stiftleiste oben); Module werden direkt auf die
# Pins gesteckt/geloetet (Pinspitzen 3 mm ausserhalb der Modulkante) und mit 4x M2 verschraubt.
MW, MH_ = 41.3, 28.5
JX0 = (W - 36) / 2
M1Y = 1.0                      # Oberkante Modul 1
PAD1Y = M1Y + MH_ + 3.0        # Pinreihe Modul 1
M2Y = H - 1.0 - MH_            # Oberkante Modul 2
PAD2Y = M2Y - 3.0              # Pinreihe Modul 2
PL = {
    # Eingangsblock oben links: U2 <-> BT1 / SW1 auf gleicher Zeile (Direktverbindung)
    "U2": ("HDR4", 6.0, 40, 0, "TP4056 Modul"),
    "BT1": ("HDR2", 12.0, 40, 0, "18650"),
    "SW1": ("HDR2", 12.0, 45.08, 0, "Ein/Aus"),
    "C1": ("C1206", 12.0, 50.4, 0, "22uF"),
    # Boost-Schalter darunter: Q1.D -> U3.1 gerade
    "Q1": ("SOT23", 10.5, 53.5, 180, "AO3401"),
    "R9": ("R0805", 14.4125, 54.45, 180, "100k"),
    "U3": ("HDR4", 6.0, 53.5, 0, "MT3608"),
    "C2": ("C1206", 10.5, 59.5, 0, "22uF"),
    "C3": ("C1206", 10.5, 62.5, 0, "22uF"),
    # ESP32-C3 SuperMini
    "U1": ("ESP", 23.0, 40, 0, "ESP32-C3 SuperMini"),
    # Logik links vom ESP
    "Q2": ("SOT23", 17.5, 49.21, 180, "2N7002"),
    "R8": ("R0805", 18.6, 53, 180, "100k"),
    "R2": ("R0805", 19.5875, 55.24, 180, "1M"),
    "R1": ("R0805", 19.5875, 57.24, 0, "1M"),
    "C4": ("C0805", 19.55, 59.24, 180, "100nF"),
    # Sensoren: ESP-Pad -> Teiler -> Sensorpin in einer Linie
    "R3": ("R0805", 43.1125, 42.54, 180, "10k"),
    "R4": ("R0805", 43.1125, 44.54, 0, "20k"),
    "R5": ("R0805", 43.1125, 55.24, 180, "10k"),
    "R6": ("R0805", 43.1125, 57.24, 0, "20k"),
    "H1": ("MH", 2.5, 2.5, 0, ""),
    "H2": ("MH", W - 2.5, H - 2.5, 0, ""),
    "H3": ("MH", 2.5, H - 2.5, 0, ""),
    "U4": ("HDR4", W / 2 - 3.81, PAD1Y, 90, "JSN-SR04T #1"),
    "U5": ("HDR4", W / 2 + 3.81, PAD2Y, 270, "JSN-SR04T #2"),
    "H4": ("MH", W - 2.5, 2.5, 0, ""),
    "M1": ("MH2", JX0 + 0, M1Y + 2.25 + 0, 0, ""),
    "M5": ("MH2", JX0 + 0, M2Y + 2.25 + 0, 0, ""),
    "M2": ("MH2", JX0 + 36, M1Y + 2.25 + 0, 0, ""),
    "M6": ("MH2", JX0 + 36, M2Y + 2.25 + 0, 0, ""),
    "M3": ("MH2", JX0 + 0, M1Y + 2.25 + 24, 0, ""),
    "M7": ("MH2", JX0 + 0, M2Y + 2.25 + 24, 0, ""),
    "M4": ("MH2", JX0 + 36, M1Y + 2.25 + 24, 0, ""),
    "M8": ("MH2", JX0 + 36, M2Y + 2.25 + 24, 0, ""),
}

NETS_DEF = {
    "BT1": {"1": "BAT+", "2": "BAT-"},
    "U2": {"1": "BAT+", "2": "BAT-", "3": "VBAT_PROT", "4": "GND"},
    "SW1": {"1": "VBAT_PROT", "2": "VBAT_SW"},
    "C1": {"1": "VBAT_SW", "2": "GND"},
    "R1": {"1": "VBAT_SW", "2": "VBDIV"},
    "R2": {"1": "VBDIV", "2": "GND"},
    "C4": {"1": "VBDIV", "2": "GND"},
    "R9": {"1": "VBAT_SW", "2": "GATE_P"},
    "Q1": {"1": "GATE_P", "2": "VBAT_SW", "3": "VBOOST_IN"},
    "Q2": {"1": "SEN_EN", "2": "GND", "3": "GATE_P"},
    "R8": {"1": "SEN_EN", "2": "GND"},
    "U3": {"1": "VBOOST_IN", "2": "GND", "3": "5V_SENS", "4": "GND"},
    "C2": {"1": "5V_SENS", "2": "GND"},
    "C3": {"1": "5V_SENS", "2": "GND"},
    "U1": {"1": "VBAT_SW", "2": "GND", "5": "SEN_EN", "7": "VBDIV", "9": "TRIG1", "10": "ECHO1",
           "14": "TRIG2", "15": "ECHO2"},
    "U4": {"1": "5V_SENS", "2": "TRIG1", "3": "ECHO1_5V", "4": "GND"},
    "U5": {"1": "5V_SENS", "2": "TRIG2", "3": "ECHO2_5V", "4": "GND"},
    "R3": {"1": "ECHO1_5V", "2": "ECHO1"},
    "R4": {"1": "ECHO1", "2": "GND"},
    "R5": {"1": "ECHO2_5V", "2": "ECHO2"},
    "R6": {"1": "ECHO2", "2": "GND"},
}
POWER = {"BAT+", "BAT-", "VBAT_PROT", "VBOOST_IN", "5V_SENS"}
net_names = sorted({n for d in NETS_DEF.values() for n in d.values()})
NET_ID = {n: i + 1 for i, n in enumerate(net_names)}

def rot(px, py, th):
    t = math.radians(th)
    c, s = round(math.cos(t), 6), round(math.sin(t), 6)
    return px * c + py * s, -px * s + py * c      # KiCad: CCW auf dem Bildschirm, y nach unten

pads = []
for ref, (typ, x, y, th, val) in PL.items():
    fpname, plist, _ = FP[typ]
    for (num, px, py, w, h, shape, tht, drill) in plist:
        rx, ry = rot(px, py, th)
        if th in (90, 270):
            w, h = h, w
        pads.append(dict(ref=ref, num=num, x=round(x + rx, 4), y=round(y + ry, 4), w=w, h=h, shape=shape,
                         tht=tht, net=NETS_DEF.get(ref, {}).get(num), drill=drill))

nx, ny = int(W / RES) + 1, int(H / RES) + 1
cu = np.full((2, ny, nx), -1, dtype=np.int32)
for i, p in enumerate(pads):
    p["id"] = NET_ID[p["net"]] if p["net"] else 1000 + i

def cells_rect(x0, y0, x1, y1):
    ix0, ix1 = max(0, math.ceil(x0 / RES - 1e-9)), min(nx - 1, math.floor(x1 / RES + 1e-9))
    iy0, iy1 = max(0, math.ceil(y0 / RES - 1e-9)), min(ny - 1, math.floor(y1 / RES + 1e-9))
    return iy0, iy1 + 1, ix0, ix1 + 1

for p in pads:
    ex = 0.6 if p["tht"] == "np" else 0.0
    y0, y1, x0, x1 = cells_rect(p["x"] - p["w"] / 2 - ex, p["y"] - p["h"] / 2 - ex, p["x"] + p["w"] / 2 + ex, p["y"] + p["h"] / 2 + ex)
    for l in ([0, 1] if p["tht"] else [0]):
        cu[l, y0:y1, x0:x1] = p["id"]
    p["cells"] = (y0, y1, x0, x1)
m = int(EDGE / RES)
for l in (0, 1):
    cu[l, :m, :] = -2; cu[l, -m:, :] = -2; cu[l, :, :m] = -2; cu[l, :, -m:] = -2

def zone_mask(net, inset=0.9):
    mk = np.zeros((ny, nx), bool)
    for (x0, y0, x1, x1_) in ZONES[net]:
        yy0, yy1, xx0, xx1 = cells_rect(x0 + inset, y0 + inset, x1 - inset, x1_ - inset)
        mk[yy0:yy1, xx0:xx1] = True
    return mk
ZM = {n: zone_mask(n) for n in ZONES}

def dilate(mask, r):
    R = int(math.ceil(r))
    out = np.zeros_like(mask)
    cache = {}
    ny_, nx_ = mask.shape
    for dy in range(-R, R + 1):
        if abs(dy) > r:
            continue
        half = int(math.floor(math.sqrt(max(r * r - dy * dy, 0))))
        if half not in cache:
            cs = np.cumsum(np.pad(mask.astype(np.int32), ((0, 0), (half + 1, half)), mode="constant"), axis=1)
            cache[half] = (cs[:, 2 * half + 1:] - cs[:, :nx_]) > 0
        hd = cache[half]
        if dy >= 0:
            out[dy:, :] |= hd[:ny_ - dy, :]
        else:
            out[:dy, :] |= hd[-dy:, :]
    return out

segments, vias = [], []

def mark_capsule(l, pts, w, net):
    r = w / 2.0
    for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
        steps = max(1, int(math.hypot(xb - xa, yb - ya) / (RES / 2)))
        for s in range(steps + 1):
            t = s / steps
            cx, cy = xa + (xb - xa) * t, ya + (yb - ya) * t
            y0, y1, x0, x1 = cells_rect(cx - r, cy - r, cx + r, cy + r)
            sub = cu[l, y0:y1, x0:x1]
            sub[sub == -1] = net

def mark_via(x, y, net):
    r = VIA_D / 2
    y0, y1, x0, x1 = cells_rect(x - r, y - r, x + r, y + r)
    for l in (0, 1):
        sub = cu[l, y0:y1, x0:x1]
        sub[sub == -1] = net

DIRS = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]

def finish_path(path, N, w):
    cur_layer, pts, out_segs = None, [], []
    for node in path:
        if node[0] == "V":
            vias.append((N, node[2] * RES, node[1] * RES)); continue
        l, yy, xx = node
        pt = (round(xx * RES, 3), round(yy * RES, 3))
        if cur_layer is None:
            cur_layer, pts = l, [pt]
        elif l != cur_layer:
            out_segs.append((cur_layer, pts)); cur_layer, pts = l, [pts[-1]]
            if pts[-1] != pt: pts.append(pt)
        else:
            pts.append(pt)
    out_segs.append((cur_layer, pts))
    for l, pts in out_segs:
        simp = [pts[0]]
        for i in range(1, len(pts) - 1):
            a, b, c = simp[-1], pts[i], pts[i + 1]
            if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-6:
                simp.append(b)
        simp.append(pts[-1])
        if len(simp) >= 2 and simp[0] != simp[-1]:
            segments.append((N, l, simp, w)); mark_capsule(l, simp, w, N)
    for (n2, vx, vy) in vias:
        if n2 == N: mark_via(vx, vy, N)

def astar(srcmask, goal, blocked, own, viablock, hx, hy, allow_via=True):
    INF = 1e18
    g = np.full((2, ny, nx), INF)
    prev, pq = {}, []
    h = lambda xx, yy: max(abs(xx - hx), abs(yy - hy)) + 0.41 * min(abs(xx - hx), abs(yy - hy))
    for l in (0, 1):
        ys, xs = np.nonzero(srcmask[l])
        for yy, xx in zip(ys, xs):
            if blocked[l][yy, xx] and not own[l][yy, xx]:
                continue
            g[l, yy, xx] = 0
            heapq.heappush(pq, (h(xx, yy), 0.0, l, yy, xx))
    found = None
    while pq:
        f, gc, l, yy, xx = heapq.heappop(pq)
        if gc > g[l, yy, xx] + 1e-9: continue
        if goal[l][yy, xx]:
            found = (l, yy, xx); break
        for dx, dy, c in DIRS:
            nx_, ny_ = xx + dx, yy + dy
            if not (0 <= nx_ < nx and 0 <= ny_ < ny): continue
            if blocked[l][ny_, nx_] and not own[l][ny_, nx_]: continue
            if dx and dy:
                if blocked[l][yy, nx_] and not own[l][yy, nx_]: continue
                if blocked[l][ny_, xx] and not own[l][ny_, xx]: continue
            ng = gc + c * (1.0 if l == 0 else 1.3)
            if ng < g[l, ny_, nx_]:
                g[l, ny_, nx_] = ng; prev[(l, ny_, nx_)] = (l, yy, xx)
                heapq.heappush(pq, (ng + h(nx_, ny_), ng, l, ny_, nx_))
        if allow_via:
            ol = 1 - l
            if not viablock[yy, xx] and not (cu[l, yy, xx] >= 0 and cu[l, yy, xx] != -1 and not own[l][yy, xx]):
                ng = gc + 15.0
                if ng < g[ol, yy, xx] and (not blocked[ol][yy, xx] or own[ol][yy, xx]):
                    g[ol, yy, xx] = ng; prev[(ol, yy, xx)] = ("via", l, yy, xx)
                    heapq.heappush(pq, (ng + h(xx, yy), ng, ol, yy, xx))
    if not found: return None
    path, cur = [found], found
    while cur in prev:
        pv = prev[cur]
        if pv[0] == "via":
            path.append(("V", pv[2], pv[3])); cur = (pv[1], pv[2], pv[3]); path.append(cur)
        else:
            cur = pv; path.append(cur)
    path.reverse()
    return path

def masks(N, w):
    r_tr = (CLR + w / 2 + 0.12) / RES
    r_via = (CLR + VIA_D / 2 + 0.12) / RES
    foreign = [(cu[l] != N) & (cu[l] != -1) for l in (0, 1)]
    blocked = [dilate(foreign[l], r_tr) for l in (0, 1)]
    anycu = (cu[0] != -1) | (cu[1] != -1)
    viablock = dilate(foreign[0] | foreign[1], r_via) | dilate(anycu, 0.55 / RES) | blocked[0] | blocked[1]
    own = [(cu[l] == N) for l in (0, 1)]
    return blocked, viablock, own

def srcmask_of(p):
    sm = [np.zeros((ny, nx), bool), np.zeros((ny, nx), bool)]
    y0, y1, x0, x1 = p["cells"]
    for l in ([0, 1] if p["tht"] else [0]):
        sm[l][y0:y1, x0:x1] = True
    return sm

def route_net(name):
    N = NET_ID[name]
    w = (0.6 if name == "5V_SENS" else W_PWR) if name in POWER else W_SIG
    nm = [p for p in pads if p["net"] == name]
    connected, rest, ok = [nm[0]], nm[1:], True
    while rest:
        best = min(rest, key=lambda q: min(math.hypot(q["x"] - c["x"], q["y"] - c["y"]) for c in connected))
        rest.remove(best)
        blocked, viablock, own = masks(N, w)
        sm = srcmask_of(best)
        goal = [own[l] & ~sm[l] for l in (0, 1)]
        near = min(connected, key=lambda c: math.hypot(c["x"] - best["x"], c["y"] - best["y"]))
        path = astar(sm, goal, blocked, own, viablock, near["x"] / RES, near["y"] / RES)
        if path is None:
            print("KEIN WEG:", name, best["ref"], best["num"]); ok = False; break
        finish_path(path, N, w)
        connected.append(best)
    return ok

def plane_via(p):
    """SMD-Pad eines Plane-Netzes: kurze Leiterbahn zu freier Via-Position in der passenden Zone."""
    N = NET_ID[p["net"]]
    blocked, viablock, own = masks(N, W_DOG)
    zm = ZM[p["net"]] if p["net"] in ZM else np.ones((ny, nx), bool)
    sm = srcmask_of(p)
    goal = [(~viablock) & zm, np.zeros((ny, nx), bool)]
    # Via-Mitte darf nicht im eigenen Pad liegen
    goal[0] &= ~sm[0]
    path = astar(sm, goal, blocked, own, viablock, p["x"] / RES, p["y"] / RES, allow_via=False)
    if path is None:
        print("KEIN PLANE-VIA:", p["ref"], p["num"], p["net"]); return False
    l, yy, xx = path[-1]
    vias.append((N, xx * RES, yy * RES))
    finish_path(path, N, W_DOG)
    mark_via(xx * RES, yy * RES, N)
    return True

ORDER1 = ["TRIG1", "ECHO1", "ECHO1_5V", "TRIG2", "ECHO2", "ECHO2_5V", "SEN_EN", "VBDIV", "BAT+", "BAT-", "VBAT_PROT", "VBOOST_IN"]
fails = [n for n in ORDER1 if not route_net(n)]
for p in pads:
    if p["net"] in PLANE_NETS and not p["tht"]:
        if not plane_via(p):
            fails.append(f'{p["ref"]}.{p["num"]}')
fails += [n for n in ["5V_SENS", "GATE_P"] if not route_net(n)]
print("Nicht geroutet:", fails)

# Trace-Enden auf Pad-Mitte
for (n, l, pts, w) in segments:
    for end in (0, -1):
        P = pts[end]
        for p in pads:
            if p["net"] and NET_ID[p["net"]] == n and (p["tht"] or l == 0) and p["tht"] != "np":
                if abs(P[0] - p["x"]) <= p["w"] / 2 and abs(P[1] - p["y"]) <= p["h"] / 2 and (P[0], P[1]) != (p["x"], p["y"]):
                    c = (round(p["x"], 3), round(p["y"], 3))
                    pts.insert(0, c) if end == 0 else pts.append(c)
                    break

# ---------------- exakter Clearance-Check ----------------
def dseg(a, b, c, d):
    def pseg(p, s0, s1):
        dx, dy = s1[0] - s0[0], s1[1] - s0[1]
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((p[0] - s0[0]) * dx + (p[1] - s0[1]) * dy) / L))
        return math.hypot(p[0] - (s0[0] + t * dx), p[1] - (s0[1] + t * dy))
    def o(a_, b_, c_): return (b_[0] - a_[0]) * (c_[1] - a_[1]) - (b_[1] - a_[1]) * (c_[0] - a_[0])
    if o(a, b, c) * o(a, b, d) < 0 and o(c, d, a) * o(c, d, b) < 0: return 0.0
    return min(pseg(a, c, d), pseg(b, c, d), pseg(c, a, b), pseg(d, a, b))

def shape_pad(p):
    if p["shape"] == "circle" and p["w"] == p["h"]:
        return ("circ", p["x"], p["y"], p["w"] / 2)
    return ("rect", p["x"] - p["w"] / 2, p["y"] - p["h"] / 2, p["x"] + p["w"] / 2, p["y"] + p["h"] / 2)

def dist(s1, s2):
    if s1[0] > s2[0]: s1, s2 = s2, s1
    t1, t2 = s1[0], s2[0]
    if t1 == "circ" and t2 == "circ": return math.hypot(s1[1] - s2[1], s1[2] - s2[2]) - s1[3] - s2[3]
    if t1 == "circ" and t2 == "rect":
        dx = max(s2[1] - s1[1], 0, s1[1] - s2[3]); dy = max(s2[2] - s1[2], 0, s1[2] - s2[4])
        return math.hypot(dx, dy) - s1[3]
    if t1 == "circ" and t2 == "seg":
        return dseg((s1[1], s1[2]), (s1[1], s1[2]), s2[1], s2[2]) - s1[3] - s2[3] / 2
    if t1 == "rect" and t2 == "rect":
        dx = max(s1[1] - s2[3], 0, s2[1] - s1[3]); dy = max(s1[2] - s2[4], 0, s2[2] - s1[4])
        return math.hypot(dx, dy)
    if t1 == "rect" and t2 == "seg":
        x0, y0, x1, y1 = s1[1:]
        for pt in (s2[1], s2[2]):
            if x0 <= pt[0] <= x1 and y0 <= pt[1] <= y1: return -1.0
        cs = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        return min(dseg(s2[1], s2[2], cs[i], cs[(i + 1) % 4]) for i in range(4)) - s2[3] / 2
    return dseg(s1[1], s1[2], s2[1], s2[2]) - s1[3] / 2 - s2[3] / 2

objs = []
for p in pads:
    if p["tht"] == "np": continue
    objs.append((NET_ID[p["net"]] if p["net"] else -p["id"], [0, 1] if p["tht"] else [0], shape_pad(p), f'{p["ref"]}.{p["num"]}'))
for (n, l, pts, w) in segments:
    for a, b in zip(pts[:-1], pts[1:]):
        objs.append((n, [l], ("seg", a, b, w), f"trace{n}"))
for (n, x, y) in vias:
    objs.append((n, [0, 1], ("circ", x, y, VIA_D / 2), f"via{n}"))
viol, worst = 0, 9
for i in range(len(objs)):
    for j in range(i + 1, len(objs)):
        a, b = objs[i], objs[j]
        if a[0] == b[0] or not (set(a[1]) & set(b[1])): continue
        d = dist(a[2], b[2]); worst = min(worst, d)
        if d < CHECK_CLR - 1e-6:
            viol += 1; print("CLEARANCE", round(d, 3), a[3], b[3])
for o in objs:
    s = o[2]
    pts = [(s[1], s[2])] if s[0] == "circ" else ([s[1], s[2]] if s[0] == "seg" else [(s[1], s[2]), (s[3], s[4])])
    for (x, y) in pts:
        if x < 0.5 or y < 0.5 or x > W - 0.5 or y > H - 0.5:
            print("RAND", o[3], x, y); viol += 1
tl = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for (_, _, pts, _) in segments for a, b in zip(pts[:-1], pts[1:]))
print(f"Eigenpruefung: Verstoesse={viol}, kleinster Abstand={worst:.3f} mm, Trace-Laenge={tl:.0f} mm, Vias={len(vias)}")

# ---------------- Datei ----------------
L = []; a = L.append
a('(kicad_pcb (version 20240108) (generator "pcbnew") (generator_version "8.0")')
a('  (general (thickness 1.6) (legacy_teardrops no))')
a('  (paper "A4")')
a('  (layers (0 "F.Cu" signal) (4 "In1.Cu" signal) (6 "In2.Cu" signal) (2 "B.Cu" signal) (9 "F.Adhes" user "F.Adhesive")'
  ' (11 "B.Adhes" user "B.Adhesive") (13 "F.Paste" user) (15 "B.Paste" user) (5 "F.SilkS" user "F.Silkscreen")'
  ' (7 "B.SilkS" user "B.Silkscreen") (1 "F.Mask" user) (3 "B.Mask" user) (17 "Dwgs.User" user "User.Drawings")'
  ' (19 "Cmts.User" user "User.Comments") (21 "Eco1.User" user "User.Eco1") (23 "Eco2.User" user "User.Eco2")'
  ' (25 "Edge.Cuts" user) (27 "Margin" user) (31 "F.CrtYd" user "F.Courtyard") (29 "B.CrtYd" user "B.Courtyard")'
  ' (35 "F.Fab" user) (33 "B.Fab" user))')
a('  (setup (pad_to_mask_clearance 0.05)'
  ' (stackup (layer "F.SilkS" (type "Top Silk Screen")) (layer "F.Paste" (type "Top Solder Paste")) (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))'
  ' (layer "F.Cu" (type "copper") (thickness 0.035)) (layer "dielectric 1" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))'
  ' (layer "In1.Cu" (type "copper") (thickness 0.035)) (layer "dielectric 2" (type "core") (thickness 1.0) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))'
  ' (layer "In2.Cu" (type "copper") (thickness 0.035)) (layer "dielectric 3" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))'
  ' (layer "B.Cu" (type "copper") (thickness 0.035)) (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))'
  ' (layer "B.Paste" (type "Bottom Solder Paste")) (layer "B.SilkS" (type "Bottom Silk Screen")) (copper_finish "None") (dielectric_constraints no)))')
a('  (net 0 "")')
for n, i in NET_ID.items():
    a(f'  (net {i} "{n}")')
for ref, (typ, x, y, th, val) in PL.items():
    fpname, plist, cy = FP[typ]
    tht = any(pp[6] for pp in plist)
    pth = f'    (path "/{UU[ref]}")' if ref in UU else None
    a(f'  (footprint "{fpname}" (layer "F.Cu") (uuid "{uid()}") (at {x} {y}{(" " + str(th)) if th else ""})')
    rl = "F.Fab" if ref.startswith("H") else "F.SilkS"
    a(f'    (property "Reference" "{ref}" (at 0 {cy[1]-1.0:.2f} {th}) (layer "{rl}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    a(f'    (property "Value" "{val}" (at 0 {cy[3]+1.0:.2f} {th}) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    if pth: a(pth)
    a(f'    (attr {"through_hole" if tht else "smd"})')
    a(f'    (fp_rect (start {cy[0]} {cy[1]}) (end {cy[2]} {cy[3]}) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd") (uuid "{uid()}"))')
    for (num, px, py, w, h, shape, t, drill) in plist:
        net = NETS_DEF.get(ref, {}).get(num)
        ns = f' (net {NET_ID[net]} "{net}")' if net else ""
        ang = f" {th}" if th else ""
        if t == "np":
            a(f'    (pad "{num}" np_thru_hole circle (at {px} {py}) (size {w} {h}) (drill {drill}) (layers "*.Cu" "*.Mask") (uuid "{uid()}"))')
        elif t:
            a(f'    (pad "{num}" thru_hole {shape} (at {px} {py}{ang}) (size {w} {h}) (drill {drill}) (layers "*.Cu" "*.Mask"){ns} (uuid "{uid()}"))')
        else:
            ex = " (roundrect_rratio 0.25)" if shape == "roundrect" else ""
            a(f'    (pad "{num}" smd {shape} (at {px} {py}{ang}) (size {w} {h}) (layers "F.Cu" "F.Paste" "F.Mask"){ex}{ns} (uuid "{uid()}"))')
    a('  )')
for (n, l, pts, w) in segments:
    layer = "F.Cu" if l == 0 else "B.Cu"
    for p0, p1 in zip(pts[:-1], pts[1:]):
        a(f'  (segment (start {p0[0]} {p0[1]}) (end {p1[0]} {p1[1]}) (width {w}) (layer "{layer}") (net {n}) (uuid "{uid()}"))')
for (n, x, y) in vias:
    a(f'  (via (at {x:.3f} {y:.3f}) (size {VIA_D}) (drill {VIA_DRILL}) (layers "F.Cu" "B.Cu") (net {n}) (uuid "{uid()}"))')
a(f'  (gr_rect (start 0 0) (end {W} {H}) (stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{uid()}"))')
MX0 = (W - MW) / 2
for (yy, lay, txt) in ((M1Y, "F.SilkS", "JSN-SR04T #1 (4x M2, Stifte unten)"), (M2Y, "F.SilkS", "JSN-SR04T #2 (4x M2, Stifte oben)")):
    a(f'  (gr_rect (start {MX0:.2f} {yy:.2f}) (end {MX0+MW:.2f} {yy+MH_:.2f}) (stroke (width 0.15) (type dash)) (fill none) (layer "{lay}") (uuid "{uid()}"))')
    a(f'  (gr_text "{txt}" (at {W/2} {yy+MH_/2:.2f} 0) (layer "{lay}") (uuid "{uid()}") (effects (font (size 0.9 0.9) (thickness 0.15))))')
a(f'  (gr_text "ESP32-C3 Ultraschall v4" (at 28 {H-1.8} 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 1 1) (thickness 0.16))))')
def zone(net, layer, pts):
    ps = " ".join(f"(xy {x} {y})" for x, y in pts)
    a(f'  (zone (net {NET_ID[net]}) (net_name "{net}") (layer "{layer}") (uuid "{uid()}") (hatch edge 0.5)'
      f' (connect_pads (clearance 0.25)) (min_thickness 0.25) (filled_areas_thickness no)'
      f' (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.4)) (polygon (pts {ps})))')
zone("GND", "In1.Cu", [(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)])
zone("VBAT_SW", "In2.Cu", [(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)])
a(')')
open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
print("geschrieben:", OUT)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
fig, ax = plt.subplots(figsize=(8, 14), dpi=140)
ax.set_xlim(-1, W + 1); ax.set_ylim(H + 1, -1); ax.set_aspect("equal"); ax.set_facecolor("#0c2a14")
ax.add_patch(Rectangle((0, 0), W, H, fill=False, ec="#e6e63c", lw=1.2))
for yy, t in ((M1Y, "JSN #1"), (M2Y, "JSN #2")):
    ax.add_patch(Rectangle((MX0, yy), MW, MH_, fill=False, ec="#9bd", lw=0.8, ls="--"))
    ax.text(W / 2, yy + MH_ / 2, t, color="#9bd", fontsize=8, ha="center", va="center")
for (n, l, pts, w) in segments:
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color="#d33" if l == 0 else "#38d", lw=w * 140 / 25.4 * 0.72, solid_capstyle="round", zorder=3 if l == 0 else 2)
for (n, x, y) in vias:
    ax.add_patch(Circle((x, y), VIA_D / 2, fc="#cfcfcf", ec="k", lw=0.3, zorder=5))
for p in pads:
    if p["tht"] == "np":
        ax.add_patch(Circle((p["x"], p["y"]), p["drill"] / 2, fc="k", ec="#aaa", zorder=6)); continue
    colr = "#d4a017" if p["tht"] else "#d33"
    if p["shape"] == "circle" and p["w"] == p["h"]:
        ax.add_patch(Circle((p["x"], p["y"]), p["w"] / 2, fc=colr, ec="k", lw=0.3, zorder=6))
    else:
        ax.add_patch(Rectangle((p["x"] - p["w"] / 2, p["y"] - p["h"] / 2), p["w"], p["h"], fc=colr, ec="k", lw=0.3, zorder=6))
    if p["tht"]:
        ax.add_patch(Circle((p["x"], p["y"]), p["drill"] / 2, fc="#0c2a14", zorder=7))
for ref, (typ, x, y, th, val) in PL.items():
    if ref.startswith("H") or ref.startswith("M"): continue
    xs_ = [p["x"] for p in pads if p["ref"] == ref]; ys_ = [p["y"] for p in pads if p["ref"] == ref]
    ax.text(sum(xs_) / len(xs_), min(ys_) - 1.3, ref, color="#fff", fontsize=6, ha="center", va="bottom", zorder=9)
ax.set_title(f"ESP32-C3 Ultraschall v4 - 4 Lagen, {W:.0f} x {H:.0f} mm (rot F.Cu, blau B.Cu; In1 = GND-Plane, In2 = VBAT_SW-Plane)", color="w", fontsize=8)
fig.patch.set_facecolor("#111"); ax.tick_params(colors="#888")
fig.savefig(PNG, bbox_inches="tight")
print("Vorschau:", PNG)
