# Prototyp ohne PCB: Lochraster + 3D-Druck-Gehäuse

Ziel: Aufbauen und im Tankraum testen. Das Gehäuse ist so ausgelegt, dass das Lochraster später 1:1 gegen ein bestelltes PCB getauscht werden kann (gleiche 4 Dome, gleiche Lage der ESP-USB-Buchse).

## Vereinfachte Schaltung (gegenüber v4)

Der **JSN-SR04T V3.0** läuft laut Datenblatt mit **3,0–5,5 V**. Daraus folgt:

| v4 (KiCad) | Prototyp | Grund |
|---|---|---|
| MT3608 Boost auf 5 V | **entfällt** | Sensoren laufen am 3V3-Pin des ESP |
| Pegelteiler R3/R4, R5/R6 | **entfällt** | ECHO hat bei 3,3 V Versorgung 3,3-V-Pegel |
| Q1 + Q2 (P- und N-MOSFET) | **nur Q1** | Source liegt jetzt auf 3,3 V, das GPIO kann das Gate direkt schalten |
| C2/C3 22 µF am Boost | **entfällt** | |
| TP4056, 18650, Schalter, Batteriemessung | bleibt | |

```
18650 ── B+/B- [TP4056 USB-C] OUT+ ── Schalter ── VBAT_SW ──┬── ESP 5V-Pin
                              OUT- ────────────────── GND   └── 1M ─┬─ 1M ── GND
                                                                    ├─ 100nF ─ GND
                                                                    └─ GPIO1 (ADC)
ESP 3V3 ──┬── Q1 Source (AO3401)
          └── 100k ──┐
GPIO3 ───────────────┴── Q1 Gate          Q1 Drain ── SENS_3V3 ── JSN1 Pin1, JSN2 Pin1
```

**Achtung, Logik invertiert:** GPIO3 **LOW = Sensoren EIN**, HIGH oder hochohmig = AUS. Der 100k hält Q1 im Reset und im Deep Sleep aus.

## Einkaufsliste (vorhanden: 18650, Halter, 2× JSN, ESP32-C3 SuperMini, Schalter)

| Teil | Menge | Bemerkung |
|---|---|---|
| TP4056 USB-C Modul **mit Schutz** (IN±, B±, OUT±) | 1 | das Modul vom Verkäuferfoto passt; 6 Pads = mit DW01-Schutz |
| AO3401 (oder SI2301) + SOT-23-Adapterplatine | 1 | Ersatz in THT: BC327 + 1k in die Basis (ca. 0,1–0,2 V Verlust) |
| Widerstand 100k | 1 | Gate-Pull-up |
| Widerstand 1M | 2 | Batteriemessung (optional für die ersten Tests) |
| Kondensator 100 nF | 1 | Batteriemessung |
| Lochraster, mind. 17 × 13 Löcher | 1 | auf 43,2 × 33,0 mm zuschneiden |
| Buchsenleiste 1×8 | 2 | ESP gesteckt, damit er später ins PCB umziehen kann |
| Stiftleiste 1×4 (2×), 1×2 (1×) | | JSN1, JSN2, Versorgung |
| Dupont-Kabel Buchse–Buchse | 8 | JSN-Stifte ↔ Stiftleisten |
| Schrauben M2 × 6 selbstschneidend | 12 | 8× JSN, 4× Lochraster |
| Schrauben M3 × 8 selbstschneidend | 4 | Deckel |

## Verdrahtung

| Von | Nach | Netz |
|---|---|---|
| Akkuhalter + / − | TP4056 B+ / B− | BAT |
| TP4056 OUT+ | Schalter Kontakt 1 | |
| Schalter Kontakt 2 | ESP Pin 1 (5V), R1 1M | VBAT_SW |
| TP4056 **OUT−** (nicht B−!) | ESP Pin 2 (GND), alle GND | GND |
| ESP Pin 3 (3V3) | Q1 Source, 100k | 3V3 |
| ESP Pin 5 (GPIO3) | Q1 Gate, anderes Ende 100k | SEN_EN (aktiv LOW) |
| Q1 Drain | JSN1 Pin 1, JSN2 Pin 1 | SENS_3V3 |
| ESP Pin 9 (GPIO5) / Pin 10 (GPIO6) | JSN1 Pin 2 TRIG / Pin 3 ECHO | |
| ESP Pin 14 (GPIO10) / Pin 15 (GPIO20) | JSN2 Pin 2 TRIG / Pin 3 ECHO | |
| JSN1/JSN2 Pin 4 | GND | |
| R1 1M / R2 1M Mittelpunkt + 100 nF | ESP Pin 7 (GPIO1) | VBDIV |

AO3401 im SOT-23: Pin 1 = Gate, Pin 2 = Source, Pin 3 = Drain.

**Lochraster-Anordnung** (passend zum Gehäuse): ESP mit USB-C an die linke Kante, mittig in der Höhe, damit die Buchse vor dem Wanddurchbruch sitzt. Die 4-Pin-Stiftleiste für JSN1 an die obere Kante, für JSN2 an die untere (Richtung der Module). Versorgung (VBAT_SW, GND) an die rechte Kante (Richtung Akku). Q1, 100k und den Messteiler rechts neben den ESP. Für die 4 Befestigungslöcher die Rasterlöcher (1,1), (15,1), (1,11), (15,11) auf 2,2 mm aufbohren (Abstand 35,56 × 25,4 mm).

## Testablauf

1. **Nur USB am ESP, ohne Akku:** JSN VCC direkt an 3V3, TRIG/ECHO verbinden, Firmware und Messung testen.
2. **Schaltstufe:** Q1 + 100k einbauen. Prüfen, dass bei GPIO3 = HIGH/hochohmig an SENS_3V3 ≈ 0 V anliegt.
3. **Akkubetrieb:** TP4056, Schalter, 18650. Ruhestrom im Deep Sleep messen (Multimeter in Reihe zum Schalter).
4. **Im Gehäuse:** Langzeittest im Tankraum.

## Firmware-Hinweise

- Messung: GPIO3 LOW, ca. 200 ms warten, Sensoren **nacheinander** auslösen (≥ 60 ms Abstand), dann GPIO3 HIGH.
- Vor dem Deep Sleep: TRIG1/TRIG2 LOW (oder als Eingang), GPIO3 als Eingang (der 100k hält aus) oder per `gpio_hold_en` auf HIGH. Liegt TRIG HIGH an einem unversorgten Sensor, versorgt er sich über die Eingangsdiode mit.
- Batterieteiler 1:2 → bei 4,2 V liegen 2,1 V an GPIO1 (ADC-Dämpfung 11/12 dB).
- Ab ca. 3,3 V Akkuspannung dauerhaft schlafen. Der DW01-Schutz schaltet erst bei ca. 2,4 V ab, das schadet der Zelle. Unter ca. 3,3 V liefert der Regler des SuperMini zudem keine 3,0 V mehr für die Sensoren.
- Blindzone 21 cm: Sensor mindestens 25 cm über dem maximalen Füllstand montieren.

## Wichtig

- **Bei USB am ESP den Schalter AUS.** Je nach Board-Revision liegt die USB-5V direkt am 5V-Pin, und bei eingeschaltetem Schalter ginge sie über OUT+ ungeregelt auf den Akku. Laden nur über die USB-C-Buchse des TP4056. Firmware-Updates später besser per OTA.
- Schaltet das Einschalten der Sensoren den ESP zurück (Spannungseinbruch durch die Eingangskondensatoren der Module), hilft ein 47–100 µF Elko zwischen 3V3 und GND auf dem Lochraster.
- Tankraum: bei Heizöl unkritisch. Bei Benzin, Gas oder einer ausgewiesenen Ex-Zone ist dieser Aufbau nicht zulässig.

## Gehäuse

`case/gen_case.py` erzeugt per SolidCraft-CLI `case/Gehaeuse.solidcraft`, `Gehaeuse_Unterteil.stl`, `Gehaeuse_Deckel.stl` und Vorschaubilder. Alle Maße stehen oben im Skript.

- Innen 77 × 142 × 30 mm, außen 81 × 146 × 34 mm mit Deckel, 2 Laschen zur Wandmontage.
- Dome: 8× M2 für die JSN-Module (36 × 24 mm laut Datenblatt), 4× M2 für das Lochraster bzw. später das PCB.
- Wand vorne: Schalter Ø 20,2 mm und Kabelschlitz JSN2. Wand hinten: Kabelschlitz JSN1. Links: ESP USB-C. Rechts: TP4056 USB-C.
- 18650-Halter: flacher Rahmen zum Einkleben, Enden für die Drähte offen. TP4056: Sockel mit Tasche.

**Vor dem Druck nachmessen** (Werte in `gen_case.py`): TP4056 Länge/Breite und Höhe der USB-Buchse (`TP_L`, `TP_W`, `TP_USB_Z`), Akkuhalter (`BAT_*`), Schalter Einbauloch und Tiefe (`SW_*`), Höhe des ESP auf der Buchsenleiste (`ESP_USB_Z`), Lochbild der JSN-Platine (`JSN_HX`, `JSN_HY`).

## Späteres PCB

Die Schaltung oben ersetzt die v4-Schaltung (kein MT3608, kein Q2, keine Pegelteiler), damit reicht ein 2-Lagen-PCB. Das PCB übernimmt das Lochraster-Lochbild (35,56 × 25,4 mm, M2). Die JSN-Stifte liegen laut Zeichnung **in der Platinenebene** (34,3 − 28,5 = 5,8 mm über die Kante). Zum direkten Aufstecken braucht das PCB deshalb gewinkelte Buchsenleisten an der Kante, keine stehenden Pads wie in v4. Beim Prototyp nachprüfen.
