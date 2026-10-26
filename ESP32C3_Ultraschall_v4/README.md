# Tankmonitor Prototyp: ToF-Sensoren + Streifenraster + 3D-Druck-Gehäuse

ESP32-C3 SuperMini, 2× TOF200C (VL53L0X, 2 m) an einem I2C-Bus, 18650 mit TP4056-Lader. Misst stündlich und sendet per MQTT.

Ersetzt die JSN-SR04T-Variante: Ultraschall sah die Tankwände. Der ToF-Strahl ist mit ca. 25° deutlich enger.

`firmware/` ESPHome ([Anleitung](firmware/README.md)) · `docs/` Schaltplan und Streifenraster (Generatoren) · `case/` Gehäuse (SolidCraft, STL) · `datasheets/` ([ToF-Kerndaten](datasheets/tof_sensors.md), [Platinenmasse](datasheets/tof200c_dimensions.md))

## Aufbau

- **Hauptgehäuse** mit ESP, TP4056, Akku und Schalter. Stehen irgendwo trocken, per Kabel verbunden.
- **2× Sensorkappe**: je eine Blindkappe, die über den Gewindestutzen des Tanks gestülpt wird (innen Ø 102 mm, 30 mm tief). Der Sensor hängt mittig an der Innenseite der Kappenplatte und misst offen nach unten durch den Stutzen in den Tank.
- **2 Kabel**, je 1–2 m, vom Hauptgehäuse zu je einem Sensor. Die Sensoren hängen am selben I2C-Bus.

## Schaltung

![Schaltplan](docs/schema_prototyp.svg)

- Beide Sensoren hängen dauerhaft an 3V3 und teilen sich SDA/SCL (GPIO6/7).
- **XSHUT = Enable je Board** (GPIO5 und GPIO10): Beide Module starten mit Adresse 0x29. ESPHome weckt sie einzeln und stellt 0x30 und 0x31 ein. Deshalb braucht jeder Sensor eine eigene XSHUT-Leitung.
- R1/R2/C1 messen die Akkuspannung (1:2 an GPIO1, ca. 2 µA).
- Pins: SDA/SCL = GPIO6/7, XSHUT1/2 = GPIO5/10, Akku = GPIO1.
- Die ToF-Module haben SDA/SCL-Pull-ups und einen Spannungsregler. Am Modul nachsehen, sonst 4,7 kΩ nach 3V3 am Streifenraster ergänzen.
- Laufzeit: noch nicht gemessen. Die Sensoren ziehen nur beim Messen ca. 19 mA, im Leerlauf wenig (Regler auf dem Modul nachmessen). Multimeter in Reihe zum Kippschalter.

## Kabel zu den Sensoren (1–2 m)

Machbar, I2C ist dafür aber nicht gedacht. Die Leitungskapazität (ca. 50–100 pF/m) plus Störungen im Heizraum (Brenner-Zündtrafo, Pumpen) sind das Risiko. Gegenmassnahmen:

- **50 kHz Bustakt** (ESPHome-Standard, so in `tankmonitor.yaml`). Nicht schneller einstellen.
- **Verdrillte Paare mit GND**: Cat5/6-Kabel (am besten geschirmt, Schirm an GND nur am Hauptgehäuse). Paare: SDA+GND, SCL+GND, VIN+GND, XSHUT+GND.
- **10–47 µF und 100 nF an VIN/GND direkt am Sensor**, auf der Platine oder in der Sensorkappe. Das fängt die 19-mA-Pulse ab.
- Kabel nicht parallel zu Netz- oder Zündleitungen führen.
- **Test:** Im Log müssen alle 7 Messungen gültig sein (siehe [firmware/README.md](firmware/README.md)). Fehlen Messungen oder hängt der Bus, helfen stärkere Pull-ups (2,2 kΩ am Streifenraster) oder ein I2C-Treiber wie P82B715. Über ca. 3 m besser ein differentieller Treiber (PCA9615).
- XSHUT-Leitungen sind statisch und unkritisch.

## Teile

| Teil | Wert |
|---|---|
| TP4056 USB-C-Modul mit Schutz (IN±, B±, OUT±) | – |
| TOF200C (VL53L0X) | 2 |
| R1, R2 | 1 MΩ |
| C1 | 100 nF |
| C2 | Elko 1 µF (besser 10–47 µF, Ø ≤ 5 mm), + an Spalte 3 |
| C3, C4 (je Sensor) | 10–47 µF und 100 nF an VIN/GND |
| Streifenraster | 10 × 14 Löcher |
| Buchsenleiste 1×8 (2×), Stiftleiste 1×5 (2×) und 1×2 | – |
| Sensorkabel Cat5/6 | 2 × 1–2 m |
| Gewindeeinsätze + Schrauben | M3 (4×, Deckel Hauptgehäuse) |
| Heissleim | – |

## Aufbau Streifenraster

![Streifenraster](docs/stripboard.svg)

Koordinaten (Spalte, Zeile) ab oben links, Bestückungsseite. Die Streifen laufen senkrecht. Spalte 0 = GND, Spalte 9 = 3V3. Im Gehäuse liegt Zeile 0 hinten (Kabelschlitz).

1. 10 × 14 Löcher zuschneiden (25,4 × 35,6 mm).
2. 10 Trennstellen bohren: Zeile 4 in den Spalten 4 und 5, Zeile 7 in den Spalten 1–8.
3. 4 Drahtbrücken:
   - Zeile 2: 3V3, verlötet an Spalte 5 und 9
   - Zeile 3: GND, verlötet an Spalte 0 und 4
   - Zeile 12: GND 0→2 und 3V3 3→9
4. Liegend unter dem ESP: R1 (1,8)–(7,8), R2 (2,9)–(7,9), C1 (2,10)–(7,10). C2 (2,13)–(3,13).
5. Stecker und Leisten:
   - J1 (Sensor 1) in Zeile 1: XSHUT, SDA, SCL, GND, VIN auf Spalte 1–5
   - J2 (Sensor 2) in Zeile 0: SDA, SCL, GND, VIN, XSHUT auf Spalte 2–6
   - J3 (GND, VBAT) bei (0,13)/(1,13)
   - Buchsenleisten für den ESP in Zeile 5 und 11, Spalten 1–8, USB-C links
6. Mit dem Multimeter prüfen: zwischen 3V3, GND und VBAT_SW darf kein Kurzschluss sein. Erst dann den ESP stecken.

Pinbelegung und Reihenabstand (15,24 mm) des SuperMini vor dem Löten am eigenen Modul prüfen. `python docs/gen_stripboard.py` prüft alle Verbindungen gegen den Schaltplan.

**Externe Verdrahtung:**
- Akku → TP4056 B+/B−
- OUT+ → Kippschalter → J3 VBAT
- **OUT− → J3 GND** (nicht B−)
- Sensorkabel: pro Sensor VIN, GND, SDA, SCL, XSHUT einzeln an J1 bzw. J2. Die Kabel gehen durch den Schlitz in der Rückwand.

## Gehäuse

`python case/gen_case.py` erzeugt per SolidCraft-CLI das Design (`.solidcraft`), alle STL und Vorschaubilder. Alle Platinen werden mit **Heissleim** eingeklebt, es gibt keine Schnappmechanismen. Stattdessen:

- Eckauflagen und Anschläge für das Streifenraster
- Sockel mit Rahmen für den TP4056
- Positionierrahmen für den Akkuhalter
- in der Sensorkappe Stifte durch die Befestigungslöcher des ToF-Boards plus Rahmen

| STL | Stück | Inhalt |
|---|---|---|
| `Gehaeuse_Unterteil.stl` | 1 | ESP, TP4056, Akku, Schalter. Innen 65 × 92 × 30 mm |
| `Gehaeuse_Deckel.stl` | 1 | Deckel dazu, Aussenseite nach unten drucken |
| `Sensorkappe.stl` | **2** | Blindkappe mit Kabelkerbe am Rand, innen Ø 102 × 30 mm tief, Platte 2 mm. Mit der Platte nach unten drucken, die Platte zeigt im Einsatz nach oben |
| `Gehaeuse_Passprobe.stl` | 1 (zuerst) | Probestück: ToF-Stifte mit Rahmen und TP4056-Sockel mit USB-C-Loch. Damit die Masse prüfen, bevor alles gedruckt wird |

- Durchbrüche im Hauptgehäuse:
  - links: USB-C des ESP und des TP4056
  - vorne: Schalter Ø 20,2 mm
  - hinten: Kabelschlitz (von oben offen) für beide Sensorkabel
- Sensorkappe: Das ToF-Board liegt mit der Rückseite mittig auf der Kappenplatte (Stifte durch die Befestigungslöcher, mit Heissleim fixieren). Die Sensorseite zeigt zur offenen Seite, also im Einsatz nach unten. Pinseite zur Kabelkerbe: Die 5 Adern werden an die Sensorseite gelötet und laufen durch die Kerbe am Kappenrand nach aussen. Die Kappe wird über den Stutzen (aussen Ø 100 mm, 1 mm Spiel je Seite) geschoben und liegt mit der Platte auf dem Stutzen auf. Das Board sitzt über der Öffnung (innen ca. 80 mm), der Messkegel bleibt frei. Schrauben, Dichtung und Gewinde sind nicht modelliert.
- Vor dem Druck nachmessen und in `gen_case.py` eintragen: TOF-Platine (`TOF_*`, siehe `datasheets/tof200c_dimensions.md`, Platinendicke und Sensorhöhe sind geschätzt), TP4056 (`TP_*`), Akkuhalter (`BAT_*`), Schalter (`SW_*`), Einschmelzmuttern (`POST_*`), ESP-Höhe (`ESP_*`), Tankdeckel (`CAP_*`).

## Wichtig

- **USB am ESP nur mit Kippschalter AUS**, sonst geht USB-5V auf den Akku. Geladen wird über den TP4056.
- ToF misst das **nächste** Ziel im Kegel (ca. 25°, bei 1,5 m Abstand ca. 0,65 m Durchmesser). Ragt der Tankrand, eine Wand oder eine Einbaute in den Kegel, kommt deren Abstand statt dem Füllstand. Sensor mittig über der Öffnung, senkrecht, Sensorseite sauber halten.
- Bei Tank 163 × 70 × 200 cm mit Öffnung 30 cm neben der Stirnwand kommt die Stirnwand ab ca. 1,35 m Tiefe in den Kegel. Die untersten ca. 12–15 cm (ca. 8–10 %) sind deshalb ungenau, die Anzeige bleibt dort bei ca. 1,38 m hängen. Darüber ist die Wand nicht im Weg. Ein Blendenrohr wäre möglich, brächte aber nur dort etwas, kostet Signal und müsste innen matt schwarz sein (weisses PLA reflektiert IR), daher weggelassen.
- Dunkles, ruhiges Öl reflektiert schlecht. Reichweite am echten Tank prüfen, die 2 m sind bei dunklen Zielen oder Sonnenlicht nicht garantiert.
- Der Sensor ist optisch, der Tank soll aber trotzdem nicht in Ex-Zonen (Benzin, Gas) betrieben werden.
