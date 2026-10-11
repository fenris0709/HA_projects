# ESP32-C3 SuperMini + 2x JSN-SR04T, 18650, Sensoren per ESP schaltbar (v4)

Datei: `ESP32C3_Ultraschall_v4.kicad_sch` (KiCad 10), eigene Symbole in `proj_modules.kicad_sym`.

## Konzept
- ESP32-C3 hängt dauerhaft an der Batterie (über Schalter SW1) am 5V-Pin. Der Onboard-Regler liefert 3,3 V. Der ESP schläft im Deep Sleep.
- Der MT3608 (Boost auf 5 V) und damit beide JSN-SR04T sind nur aktiv, wenn GPIO3 (SEN_EN) HIGH ist.
- Schaltstufe: P-MOSFET Q1 (high-side) vor dem Boost-Eingang. Q2 (2N7002) zieht das Gate von Q1 nach GND, weil 3,3 V am GPIO einen P-MOSFET an 4,2 V nicht sicher sperren würden. R9 (100k) hält Q1 sonst aus, R8 (100k) hält Q2 beim Reset und im Sleep aus.
- Batteriemessung mit 1M/1M (ca. 2 µA Dauerverbrauch) + 100 nF an GPIO1.

## Ablauf in der Firmware
1. SEN_EN (GPIO3) = HIGH, ca. 100-200 ms warten (Boost + Sensoren starten).
2. Beide Sensoren nacheinander messen (nicht gleichzeitig, wegen Übersprechen).
3. TRIG1/TRIG2 (GPIO5/GPIO10) auf LOW setzen, SEN_EN = LOW.
4. GPIO3 vor dem Sleep halten (gpio_hold_en / deep_sleep_gpio_hold) oder R8 verlassen, dann Deep Sleep für 1-2 h.

## Pinbelegung
| Funktion | GPIO |
|---|---|
| SEN_EN (Sensoren Ein) | GPIO3 |
| Batteriespannung (ADC) | GPIO1 |
| TRIG1 / ECHO1 | GPIO5 / GPIO6 |
| TRIG2 / ECHO2 | GPIO10 / GPIO20 |

## Bauteile (neu/geändert gegenüber v3)
Q1 P-MOSFET (AO3401, SI2301 o. ä., Vgs(th) ca. -1 V, Vds >= 12 V, Rds(on) < 100 mΩ), Q2 2N7002, R9/R8 100k, R1/R2 jetzt 1M.

## Layout (ESP32C3_Ultraschall_v4.kicad_pcb)
- 4 Lagen, 51,5 x 32 mm: F.Cu Signal, In1 = GND-Plane (ganzflächig), In2 = Supply-Plane VBAT_SW (ganzflächig), B.Cu Signal. Zonen sind gefüllt.
- Kompakte Platzierung mit Direktverbindungen: TP4056-Anschluss gerade zu Batterie- und Schalter-Stecker, MT3608 gerade an Q1, ESP-Pad -> Pegelteiler -> Sensorpin jeweils auf einer Linie, Q2 direkt an GPIO3. THT-Pins von GND und VBAT_SW gehen direkt in die Planes, SMD-Pads über eine kurze Via.
- 5V_SENS (Boost-Ausgang zu den Sensoren) ist eine 0,6 mm breite Leiterbahn, keine Plane. Alle Netze geroutet, Eigenprüfung und KiCad-DRC: 0 Fehler (nur Warnungen zu Silkscreen und eingebetteten Footprints).
- C2/C3 sind jetzt 22 µF in 1206 (statt Elkos), im Schaltplan angepasst.
- TP4056, MT3608 und die JSN-Sensoren hängen über Stiftleisten per Kabel an der Platine (Module sind größer als ihr Anschluss). Der ESP32-C3 SuperMini wird aufgesteckt.
- Neu erzeugen/ändern: `python3 gen_pcb.py` (Platzierung in `PL`, Netze in `NETS_DEF`), danach in KiCad Zonen füllen (B).
- Vor dem Bestellen prüfen: Reihenabstand ESP32-C3 SuperMini (15,24 mm angenommen) sowie Pinbelegung der Module.
- "Update PCB from Schematic" in KiCad verknüpft die Footprints über die Symbol-UUIDs. Die Befestigungslöcher H1-H3 stehen nicht im Schaltplan: Option "Footprints ohne Symbol löschen" AUS lassen.

## Befestigung der JSN-SR04T-Steuerplatinen
- Platine ist 51,5 x 99,5 mm: oben Modul 1, in der Mitte die Elektronik, unten Modul 2 (180 Grad gedreht). Beide Module liegen auf der Oberseite, je 4x M2 (Ø2,4 mm) im Raster 36 x 24 mm (M1-M8, nicht im Schaltplan).
- Die vier Stifte (5V, TRIG, ECHO, GND) ragen aus der Modulplatine heraus und werden direkt in die Pads U4 (Modul 1) und U5 (Modul 2) gesteckt/gelötet. Pad-Reihe 3 mm ausserhalb der Modulkante, mittig an der Modulkante. Pin 1 (5V) bei Modul 1 links, bei Modul 2 rechts (Modul gedreht).
- Distanzbolzen M2 so wählen, dass die Stifte plan in die Pads kommen (Höhe ca. 2-3 mm je nach Position der Stifte am Modul).
- Vor Bestellung prüfen: Abstand der Stifte zur Modulkante (5,8 mm laut Zeichnung), Position der Stiftreihe entlang der Kante (hier mittig angenommen) und Pinreihenfolge am Modul. Passt etwas nicht, in `gen_pcb.py` PAD1Y/PAD2Y bzw. den x-Offset von U4/U5 ändern.

## Hinweise
- ESP am 5V-Pin direkt aus der Batterie (3,0-4,2 V): Der Regler auf dem SuperMini liefert bei unter ca. 3,5 V weniger als 3,3 V. Der ESP32-C3 läuft bis ca. 3,0 V. Bei tiefer Entladung ist die ADC-Genauigkeit eingeschränkt.
- Der Ruhestrom hängt stark vom SuperMini-Board (Regler, LED) ab. Mit Modul-Ruhestrom von TP4056/DW01 ist mit ca. 50-150 µA zu rechnen. Mit 3000 mAh sind dann mehrere Monate möglich. Ein MT3608-Modul allein würde im Standby mehrere hundert µA ziehen, deshalb wird er abgeschaltet.
- Wenn der ESP im Sleep ist und TRIG/ECHO-Leitungen HIGH wären, würden unbestromte Sensoren über ihre Eingangsdioden mitversorgt. Deshalb vor dem Abschalten TRIG auf LOW.
- MT3608-Trimmer vor dem Anschließen der Sensoren auf 5,0 V einstellen.
- Verbindungen: lokale Netze sind als Leitungen gezeichnet, längere Wege (SEN_EN, VBDIV, VBOOST_IN, 5V_SENS, TRIG/ECHO-Namen) zusätzlich über gleichnamige Netzlabels.
