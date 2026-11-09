# Schaltung und Lochraster-Layout (1 Sensor)

Kein KiCad, nur diese Seite. Die Platine ist ein **Punktraster 60 × 40 mm** (20 Spalten A–T, 14 Reihen 1–14), alles wird mit Draht verbunden. **Nur ESP und ToF-Modul sind gesteckt** (Buchsenleisten), der Rest ist fest verlötet.

## Einbaulage (wichtig)

Die Platine hängt im Gehäuse **mit der Bestückungsseite nach unten**. Buchsenleisten und Bauteile sitzen unten, ESP und Sensor hängen darunter, die Lötseite liegt oben unter dem Deckel. So schaut der Sensor ohne Kabel durch das Fenster im Boden nach unten.

- Alle Spalten- und Reihenangaben unten gelten für die **Bestückungsseite** (Ansicht von unten): A links, T rechts, Reihe 1 vorne (unten im Bild), Reihe 14 hinten.
- Im Gehäuse ist links und rechts dann vertauscht: **Spalte T (ESP, USB-C) liegt an der linken Gehäusewand**, Spalte A rechts. Der Deckel schiebt von links ein.
- Beim Löten siehst du die Lötseite, also gespiegelt. Zuerst bestücken und prüfen, dann umdrehen.

## Pinout

### ESP32-C3 SuperMini (Buchsenleisten Reihe 9 und Reihe 3, Spalten M–T)

Der ESP steckt mit der Bauteilseite (USB-C) nach unten. Von unten gesehen liegt der USB-C rechts (Spalte T) und die Leisten laufen wie in der Tabelle. Reihenabstand 15,24 mm: 5 leere Reihen zwischen den beiden Leisten (gemessen am eigenen Modul).

| Loch | ESP-Pin | Verwendung |
|---|---|---|
| T9 | 5V | VBAT_SW (Akku über Schalter) |
| S9 | GND | GND |
| R9 | 3V3 | 3V3 (Sensor, Pullups) |
| Q9 | GPIO4 | ToF GPIO1/INT (nicht benutzt, Pullup `Rint`) |
| P9, O9 | GPIO3, GPIO2 | frei (GPIO2 ist Strapping-Pin) |
| N9 | GPIO1 | Akku-Spannungsteiler |
| M9 | GPIO0 | frei |
| T3 | GPIO5 | ToF XSHUT |
| S3 | GPIO6 | I2C SDA |
| R3 | GPIO7 | I2C SCL |
| Q3, P3 | GPIO8, GPIO9 | frei (Strapping-Pins, nicht belegen) |
| O3, N3, M3 | GPIO10, GPIO20, GPIO21 | frei |

### ToF-Modul TOF200C (Buchsenleiste 1×6 in Reihe 1, Spalten B–G)

Das Modul hängt flach unter der Platine, Sensor nach unten, Pinreihe vorne (Reihe 1), das Modul liegt nach hinten. Die Stiftleiste vom Sensor her einsetzen (Kunststoff auf der Sensorseite) und von der Rückseite verlöten, damit die langen Pins nach hinten stehen. Reihenfolge gemessen am eigenen Modul: VIN, GND, SDA, SCL, INT, XSHUT (von links nach rechts, Sensorseite oben, Pins unten).

| Loch | Modul-Pin | Anschluss | Bauteil am Pin |
|---|---|---|---|
| B1 | VIN | 3V3 (R9) | `Cs1` 10–47 µF und `Cs2` 100 nF nach GND |
| C1 | GND | GND (S9) | |
| D1 | SDA | GPIO6 (S3) | optional `Rsda` 4,7 kΩ nach 3V3 |
| E1 | SCL | GPIO7 (R3) | optional `Rscl` 4,7 kΩ nach 3V3 |
| F1 | GPIO1 (INT) | GPIO4 (Q9) | `Rint` 10 kΩ nach 3V3 (Open-Drain) |
| G1 | XSHUT | GPIO5 (T3) | `Rxs` 1 kΩ nach GND (Pulldown) |

Warum diese Bauteile:
- **XSHUT** = Enable. ESPHome setzt ihn beim Start auf high. Im Deep Sleep floatet der ESP-Pin, `Rxs` zieht ihn auf low: Sensor im Standby (Sparmodus). 1 kΩ, weil viele Module XSHUT per ca. 10 kΩ nach VIN hochziehen. Mit 100 kΩ bliebe der Pegel dann zu hoch. Sensor ohne XSHUT-Pullup am Modul: `Rxs` bleibt trotzdem drauf, schadet nicht (ca. 3 mA nur in der kurzen Wachphase).
- **INT** ist Open-Drain und braucht einen Pullup, sonst schwebt der Pin. Wird von der Firmware nicht benutzt.
- **SDA/SCL-Pullups** sind auf den TOF-Modulen normalerweise schon drauf. Dann `Rsda`/`Rscl` weglassen (Multimeter: SDA gegen VIN messen, ca. 4,7–10 kΩ). Fehlen sie, 4,7 kΩ ergänzen.
- `Cs1`/`Cs2` direkt am Modul fangen die ca. 19-mA-Pulse beim Messen ab.

## Schaltplan

```
 Akku 18650 --B+/B-- TP4056 (USB-C) --OUT+--[Kippschalter]--+--> VBAT_SW
                                      OUT- ------------------+--> GND

 VBAT_SW --+--- ESP 5V (T9)                 3V3 (ESP R9) --+-- Sensor VIN (B1)  --- Cs1 10-47u, Cs2 100n --- GND
           +--- Cbat 10-47u --- GND                        +-- Rint 10k --+-- Sensor INT (F1) --- ESP GPIO4 (Q9)
           +--- Ra 1M --+--- ESP GPIO1 (N9)                +-- Rsda/Rscl 4k7 (nur falls Modul keine hat)
                        +--- Cadc 100n --- GND
                        +--- Rb 1M --- GND
 ESP GPIO6 (S3) ---- SDA ---- Sensor SDA (D1)
 ESP GPIO7 (R3) ---- SCL ---- Sensor SCL (E1)
 ESP GPIO5 (T3) ---- XSHUT --+-- Sensor XSHUT (G1)
                             +-- Rxs 1k --- GND
 ESP GND (S9) ----- GND ----- Sensor GND (C1)
```

Akku-Messung: `Ra`/`Rb` teilen VBAT_SW 1:2 auf GPIO1 (ca. 2 µA), `Cadc` glättet.

## Bauteile auf dem Lochraster

| Teil | Wert | Anzahl |
|---|---|---|
| Lochraster Punktraster | 60 × 40 mm, 4 Montagelöcher Ø 1,8 | 1 |
| Buchsenleiste 1×8 (ESP) | 8,5 mm hoch | 2 |
| Buchsenleiste 1×6 (ToF) | 8,5 mm hoch | 1 |
| Stiftleisten für ESP und ToF-Modul | liegen meist bei | je Modul |
| `Ra`, `Rb` | 1 MΩ | 2 |
| `Rxs` | 1 kΩ | 1 |
| `Rint` | 10 kΩ | 1 |
| `Rsda`, `Rscl` (optional) | 4,7 kΩ | 0–2 |
| `Cadc` | 100 nF | 1 |
| `Cs2` | 100 nF | 1 |
| `Cbat`, `Cs1` | Elko 10–47 µF, Ø ≤ 5 mm, liegend | 2 |

## Layout grob

Ansicht auf die **Bestückungsseite** (A links, T rechts, Reihe 1 unten). `E` = Buchsenleisten des ESP, `S` = Buchsenleiste des ToF-Moduls, `.` = frei. Der ESP (USB-C rechts) und das ToF-Modul hängen bis ca. 12 mm unter der Platine. Zwischen Platine und ESP/Modul ist ca. 8–11 mm Platz für liegende Widerstände und Kondensatoren.

```
       A B C D E F G H I J K L M N O P Q R S T
  14   . . . . . . . . . . . . . . . . . . . .
  13   . . . . . . . . . . . . . . . . . . . .   <- GND-Schiene (Draht)
  12   . . . . . . . . . . . . . . . . . . . .   <- 3V3-Schiene
  11   . . . . . . . . . . . . . . . . . . . .   <- VBAT_SW-Schiene
  10   . . . . . . . . . . . . . . . . . . . .   Anschluss von TP4056/Schalter rechts (Spalte A)
   9   . . . . . . . . . . . . E E E E E E E E   ESP: 5V GND 3V3 G4 G3 G2 G1 G0  (T..M)
   8   . . . . . . . . . . . . . . . . . . . .
   7   . . . . . . . . . . . . . . . . . . . .   ESP-Mitte, Platz fuer Ra/Rb/Cadc/Cbat
   6   . . . . . . . . . . . . . . . . . . . .
   5   . . . . . . . . . . . . . . . . . . . .
   4   . . . . . . . . . . . . . . . . . . . .
   3   . . . . . . . . . . . . E E E E E E E E   ESP: G5 G6 G7 G8 G9 G10 G20 G21  (T..M)
   2   . . . . . . . . . . . . . . . . . . . .   Cs1/Cs2 zwischen B2 und C2
   1   . S S S S S S . . . . . . . . . . . . .   ToF: VIN GND SDA SCL INT XSHUT (B..G)
```

Vorschlag für die Verdrahtung:
1. Buchsenleisten stecken, einlöten, **bevor** irgendetwas anderes kommt (ESP und Modul dabei aufstecken, damit der Abstand stimmt).
2. Schienen als Draht: GND in Reihe 13 (mit S9 und C1 verbinden), 3V3 in Reihe 12 (mit R9, B1, Rint, Rsda/Rscl), VBAT_SW in Reihe 11 (mit T9, Ra, Cbat).
3. Signale: S3 → D1 (SDA), R3 → E1 (SCL), T3 → G1 (XSHUT) mit `Rxs` nach GND, Q9 → F1 (INT) mit `Rint` nach 3V3, N9 → Mitte Ra/Rb mit `Cadc`.
4. Externe Drähte an die Schienen: OUT− des TP4056 an GND, Schalterausgang an VBAT_SW (Draht rechts bei Spalte A, ca. 5–8 cm).
5. Mit dem Multimeter prüfen: zwischen 3V3, GND und VBAT_SW darf kein Kurzschluss sein. Erst dann ESP und Modul stecken.

Maße des Rasters: Reihen mittig (3,5 mm Rand), **Loch T 5,5 mm von der Plattenkante** (gemessen). Das Gehäuse (`case/gen_case.py`, `COL_RIM`) rechnet damit, wo der ESP-USB-C liegt.

## Externe Verdrahtung

- Akku → TP4056 B+/B−
- TP4056 OUT+ → Kippschalter → VBAT_SW
- **TP4056 OUT− → GND** (nicht B−)
- Kein weiteres Kabel: Sensor und ESP sitzen direkt auf der Platine.

## Spannung und Strom

- **USB am ESP nur mit Kippschalter AUS**, sonst geht USB-5V auf den Akku. Geladen wird über den TP4056.
- Die ToF-Module haben einen Spannungsregler, VIN = 3V3 vom ESP reicht. Messen/Wachphase ca. 19 mA, im Deep Sleep Standby durch `Rxs`.
- Ruhestrom und Laufzeit: noch nicht gemessen. Multimeter in Reihe zum Kippschalter.
