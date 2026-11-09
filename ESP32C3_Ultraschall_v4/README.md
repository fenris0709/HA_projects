# Tankmonitor Prototyp: 1 ToF-Sensor pro Tank, Lochraster + 3D-Druck-Gehäuse auf dem Tankverschluss

ESP32-C3 SuperMini, 1× TOF200C (VL53L0X, 2 m), 18650 mit TP4056-Lader. Misst stündlich und sendet per MQTT. **Ein komplettes Gerät pro Tank**, also zweimal bauen, wenn zwei Tanks überwacht werden.

Ersetzt die Variante mit zwei Sensoren an einem Bus (Kabel, Adressen, Störungen) und davor die JSN-SR04T-Ultraschallvariante (sah die Tankwände). Der ToF-Strahl ist mit ca. 25° deutlich enger.

`firmware/` ESPHome ([Anleitung](firmware/README.md)) · `docs/` [Schaltung, Pinout, Lochraster-Layout](docs/schaltung.md) · `case/` Gehäuse (SolidCraft-Skript, STL) · `datasheets/` ([ToF-Kerndaten](datasheets/tof_sensors.md), [Platinenmasse](datasheets/tof200c_dimensions.md))

## Aufbau

- **Ein Gehäuse** auf der flachen Oberseite des Original-Tankverschlusses (Ø ca. 110 mm). Der Sensor schaut durch ein Fenster im Boden und ein **gebohrtes Loch (Ø 12)** im Verschluss in den Tank. Kein Kabel, keine Sensorkappe.
- Im Gehäuse: Lochraster 60 × 40 mm (ESP und Sensor gesteckt, Rest verlötet), TP4056 mit USB-C, 18650-Halter, Kippschalter.
- Die Platine hängt mit der **Bestückungsseite nach unten** auf vier Pfosten: ESP und ToF-Modul hängen darunter, die Lötseite liegt oben.
- **Deckel schiebt von der Seite ein**, keine Schrauben am Gehäuse.
- Das Gehäuse darf über den Verschluss überstehen (ca. 90 × 69 mm). Zwei Laschen (vorne/hinten) lassen optional zwei Schrauben durch den Verschluss zu.

## Schaltung und Platine

Siehe [docs/schaltung.md](docs/schaltung.md): Pinout von ESP und Sensor mit allen Pullups und dem Pulldown, Schaltplan, Bauteilliste, Layout grob und externe Verdrahtung.

Kurz:
- I2C: SDA/SCL = GPIO6/7, 100 kHz, kurze Leitungen im Gehäuse.
- **XSHUT bleibt** an GPIO5: Der Pulldown `Rxs` (1 kΩ) hält den Sensor im Deep Sleep im Standby (Sparmodus).
- Das ganze Sensor-Pinout liegt auf einer Buchsenleiste (VIN, GND, SDA, SCL, GPIO1/INT, XSHUT). INT geht mit Pullup an GPIO4, wird nicht benutzt.
- Akku: Teiler 1 MΩ/1 MΩ an GPIO1.

## Teile (pro Gerät)

| Teil | Wert / Anzahl |
|---|---|
| ESP32-C3 SuperMini | 1 |
| TOF200C (VL53L0X) | 1 |
| Lochraster Punktraster 60 × 40 mm | 1 |
| Buchsenleisten 1×8 (2×) und 1×6 | 8,5 mm hoch |
| TP4056 USB-C-Modul mit Schutz (IN±, B±, OUT±) | 1 |
| 18650-Zelle mit 1-fach-Halter | 1 |
| Kippschalter rund, Ø 20 mm Loch, ca. 25 mm tief | 1 |
| Widerstände und Kondensatoren | siehe [Bauteilliste](docs/schaltung.md#bauteile-auf-dem-lochraster) |
| Silikon oder Heissleim | – |
| optional 2× Schrauben M3 + Dichtung für die Laschen | – |

Filament pro Gerät ca. 35 g PLA (Gehäuse 20 cm³ + Deckel 9 cm³, fast alles ist Wand, Infill spielt kaum eine Rolle). Nichts im Gehäuse wird verschraubt, alles wird mit Heissleim fixiert (Akkuhalter, TP4056) oder gesteckt (Platine auf den Zapfen).

## Gehäuse

`python case/gen_case.py` erzeugt per SolidCraft-CLI das Design (`Gehaeuse.solidcraft`), die STL und Vorschaubilder. `--no-run` schreibt nur die JSON.

| STL | Stück | Inhalt |
|---|---|---|
| `Gehaeuse.stl` | 1 pro Gerät | Boden unten drucken, ohne Stützen. Innen 87,2 × 66,2 × 23 mm, aussen ca. 90 × 69 × 27 mm |
| `Deckel.stl` | 1 pro Gerät | flach drucken, 1,6 mm dick. Schiebt von links in die Nuten |

Wenig Filament und schnell gedruckt: 1,2 mm Wände und Boden, keine Rundungen innen, Pfosten statt Rahmen, Rippen nur oben an den Längswänden (mit 45°-Stufen, ohne Stützen). Bei 0,4 mm Düse sind das 3 Linien pro Wand. Layer 0,28 mm, Infill 10 %, 2 Wandlinien reichen für Boden und Deckel.

- **Platine:** Vier Pfosten Ø 5 mm, 17,5 mm hoch, mit Zapfen Ø 1,6 × 4 mm durch die Montagelöcher (Ø 1,8, 2,5 mm vom Rand). Aufstecken, bei Bedarf mit einem Tropfen Heissleim sichern.
- **Durchbrüche:** links USB-C des ESP, rechts USB-C des TP4056 und der Schalter (Ø 20,2 mm). Im Boden das Sensorfenster Ø 12 mm.
- **Deckel:** schiebt von der linken Schmalseite (ESP-USB-C-Seite) in zwei Nuten, rechts ist die Wand der Anschlag. Die linke Wand ist oberhalb des Deckels offen, die Griffmulde im Deckel liegt dort. Sitzt er zu streng oder zu locker, `LID_C` in `gen_case.py` anpassen.
- Vor dem Druck nachmessen und in `gen_case.py` eintragen: Platine und Raster (`PCB_*`, `COL_RIM`), ESP (`ESP_*`), Sensormodul (`TOF_*`), TP4056 (`TP_*`), Akkuhalter (`BAT_*`), Schalter (`SW_*`).
- **Der Sensor sitzt ca. 8 mm über der Oberseite des Verschlusses.** Dieser Abstand ist in der Messung enthalten: `dist_empty`/`dist_full` in der Firmware am echten Tank einstellen.

## Montage auf dem Tankverschluss

1. Gehäuse auf die Verschlussoberseite stellen, **Fenster auf die gewünschte Mitte**. Durch das Fenster (Ø 12) die Mitte anzeichnen. Bei Laschen auch die Schraubenlöcher anzeichnen.
2. Verschluss abschrauben, **Ø 12 mm Loch bohren** (Ø 14 mm, wenn der Strahl streift). Grat entfernen.
3. Gehäuse mit **Silikon** rund ums Fenster aufkleben, oder mit zwei Schrauben M3 und Dichtung durch die Laschen.
4. Fertig bestückte Platine einsetzen (ESP und Modul gesteckt, Akkuhalter und TP4056 geklebt, Drähte angeschlossen), Deckel einschieben.

Das Loch bleibt offen: Öldämpfe und Feuchte gelangen ins Gehäuse. Silikon rund ums Fenster hält das Gehäuse zur Verschlussoberseite dicht, ein transparentes Fenster wäre aufwendig und ist nicht modelliert.

## Wichtig

- **USB am ESP nur mit Kippschalter AUS**, sonst geht USB-5V auf den Akku. Geladen wird über den TP4056 (USB-C an der rechten Seite). **Erstes Flashen vor dem Einbau** (BOOT/RST sind im Gehäuse nicht erreichbar), danach OTA.
- ToF misst das **nächste** Ziel im Kegel (ca. 25°, bei 1,5 m Abstand ca. 0,65 m Durchmesser). Ragt der Tankrand, eine Wand oder eine Einbaute in den Kegel, kommt deren Abstand statt dem Füllstand. Sensor mittig über der Öffnung, senkrecht, Fenster nicht verschmutzen.
- Bei Tank 163 × 70 × 200 cm mit Öffnung 30 cm neben der Stirnwand kommt die Stirnwand ab ca. 1,35 m Tiefe in den Kegel. Die untersten ca. 12–15 cm (ca. 8–10 %) sind deshalb ungenau, die Anzeige bleibt dort bei ca. 1,38 m hängen. Darüber ist die Wand nicht im Weg. Ein Blendenrohr wäre möglich, brächte aber nur dort etwas, kostet Signal und müsste innen matt schwarz sein (weisses PLA reflektiert IR), daher weggelassen.
- Dunkles, ruhiges Öl reflektiert schlecht. Reichweite am echten Tank prüfen, die 2 m sind bei dunklen Zielen oder Sonnenlicht nicht garantiert.
- Der Sensor ist optisch, der Tank soll aber trotzdem nicht in Ex-Zonen (Benzin, Gas) betrieben werden.
- Laufzeit: noch nicht gemessen. Ruhestrom mit Multimeter in Reihe zum Kippschalter messen (siehe [Firmware](firmware/README.md#sparmodus-des-sensors)).

## Stand

- Gehäuse: STL und Vorschau sind erzeugt, die Kollisionsprüfung mit den Platzhaltern (Platine, ESP, ToF, Akku, TP4056, Schalter) meldet keine Kollisionen. **Noch nicht gedruckt**, Passung (Deckel, Platine auf den Zapfen, USB-C-Stecker) ist ungetestet.
- Firmware: überarbeitet, aber **nicht neu kompiliert** und nicht auf Hardware getestet.
- Gemessen: Loch T 5,5 mm vom Plattenrand, ESP-Leisten 5 leere Reihen auseinander, ToF-Pins VIN/GND/SDA/SCL/INT/XSHUT.
- Offen: TP4056-Masse (im Gehäuse mit 17,9 × 14,1 mm angenommen), Verschlussoberseite wirklich flach.
