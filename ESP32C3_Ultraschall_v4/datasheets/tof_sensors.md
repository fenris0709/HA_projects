# ToF-Sensoren: Kerndaten

Zusammenfassung der Datenblätter, damit man nicht jedes Mal das PDF öffnen muss.

**Achtung:** Das PDF `RBS17667-RBS17668-VL6180X-Datasheet.pdf` (ST DocID026171 Rev 6, 79 Seiten) gehört zum **TOF050C** (VL6180X, 0–10 cm). Im Projekt wird die **2-m-Variante TOF200C** (VL53L0X) verwendet. Für den VL53L0X liegt kein Datenblatt im Ordner, seine Werte unten stammen aus dem allgemeinen ST-Datenblatt und sind **nicht** aus dem PDF geprüft. Zusammen mit dem Platinenmass siehe [tof200c_dimensions.md](tof200c_dimensions.md).

## TOF200C (VL53L0X), im Projekt verwendet

Quelle: ST VL53L0X-Datenblatt (nicht im Ordner), Werte vor dem Einsatz am eigenen Modul prüfen.

| Parameter | Wert |
|---|---|
| Messbereich | ca. 3 cm bis 2 m (Langstreckenmodus). Bei Sonne und dunklem Ziel deutlich weniger |
| Genauigkeit | ca. ±3 % (Standard) bis ±5 % (Langstrecke) |
| Sichtfeld | ca. 25° |
| Wellenlänge | 940 nm Laser (Klasse 1) |
| I2C-Adresse | 0x29 (7 Bit), per Software änderbar, geht bei Spannungsverlust zurück auf 0x29 |
| Versorgung Chip | 2.6–3.5 V |
| Versorgung Modul | meist VIN 2.6–5.5 V über Regler auf dem Modul (beim Verkäufer prüfen) |
| Strom beim Messen | ca. 19 mA |
| Standby (XSHUT = LOW) | wenige µA, plus Ruhestrom des Reglers auf dem Modul |
| XSHUT | Aktiv-LOW-Reset/Standby, Eingang. Auf dem Modul meist mit Pull-up |
| GPIO1 | Interrupt-Ausgang, offen lassen |
| Pins (6) | VIN, GND, SCL, SDA, GPIO1, XSHUT (Reihenfolge am Silkscreen prüfen) |

### Zwei Sensoren an einem Bus

Beide haben nach dem Einschalten 0x29. Ablauf:

1. Beide XSHUT auf LOW.
2. XSHUT von Sensor 1 auf HIGH, Adresse auf z. B. 0x30 setzen.
3. XSHUT von Sensor 2 auf HIGH (bleibt auf 0x29) oder ebenfalls umadressieren.

ESPHome macht das automatisch, wenn bei jedem `vl53l0x` `address` und `enable_pin` gesetzt sind.

### Zu beachten bei Heizöl

- Das Sichtfeld von ca. 25° ist deutlich enger als beim Ultraschall, aber nicht null: Bei 1.5 m Abstand hat der Messfleck rund 0.65 m Durchmesser. Der Sensor meldet das **nächste** Ziel im Kegel, also auch die Tankwand oder Einbauten, wenn sie näher sind als die Oberfläche.
- Ruhige, dunkle Flüssigkeitsoberflächen reflektieren schlecht und eher spiegelnd. Reichweite und Stabilität am echten Tank prüfen.
- Sensor möglichst senkrecht über der Oberfläche und weit weg von der Wand.

## TOF050C (VL6180X), Datenblatt im Ordner

Quelle: `RBS17667-RBS17668-VL6180X-Datasheet.pdf`. Seiten in Klammern.

| Parameter | Wert | Seite |
|---|---|---|
| Messbereich | 0–100 mm (darüber möglich, nicht garantiert) | 8 |
| Zusätzlich | Umgebungslichtsensor (ALS), < 1 lx bis 100 klx | 8 |
| Betriebsspannung Chip | 2.6–3.0 V (optimal 2.7–2.9 V) | 8, 33 |
| Absolute Maximalwerte | AVDD, AVDD_VCSEL, SCL, SDA, GPIO0/1: −0.5 bis 3.6 V | 33 |
| Temperatur | −20 bis 70 °C (optimal −10 bis 60 °C), Lager −40 bis 85 °C | 33 |
| Strom Messen | 1.7 mA (10 Hz, 17 % Ziel bei 50 mm) | 8, 24 |
| Strom ALS | 300 µA typ., 350 µA max. | 33 |
| Strom Standby | < 1 µA (Hardware: GPIO0 = 0, und Software) | 8, 24 |
| IR-Quelle | 850 nm VCSEL | 8 |
| I2C | bis 400 kHz, Adresse 0x29 (7 Bit), im Register 0x212 änderbar | 8, 37, 68 |
| Rauschen | max. 2 mm Standardabweichung | 35 |
| Offset | typ. 1 mm, max. 3 mm | 35 |
| Konvergenzzeit | max. 15 ms (3 % Ziel bei 100 mm) | 35 |
| Gehäuse | LGA12, 4.8 × 2.8 × 1.0 mm | 8 |

Reichweite je nach Fremdlicht (Tabelle 20, Seite 35), Wert = Mindestreichweite in mm:

| Zielreflexion | dunkel | 1 klx Halogen | 5 klx Halogen |
|---|---|---|---|
| 3 % | > 100 | > 80 | > 40 |
| 5 % | > 100 | > 90 | > 45 |
| 17 % | > 100 | > 100 | > 60 |
| 88 % | > 100 | > 100 | > 70 |

Pins des Chips (Seite 10), auf dem Breakout nur teilweise herausgeführt:

| Pin | Signal | Funktion |
|---|---|---|
| 1 | GPIO1 | Interrupt-Ausgang, Open-Drain |
| 4 | GPIO0/CE | Chip-Enable, aktiv HIGH, mit 47 kΩ nach oben ziehen |
| 5 | SCL | I2C-Takt |
| 6 | SDA | I2C-Daten |
| 8 | AVDD_VCSEL | 2.6–3.0 V |
| 10 | AVDD | 2.6–3.0 V |
| 9, 12 | AVSS_VCSEL, AVSS | Masse |
| 2, 3, 7, 11 | NC | offen oder Masse |

Einschaltablauf (Seite 14): AVDD_VCSEL gleichzeitig mit oder vor AVDD. MCU-Boot beginnt, wenn AVDD da ist und GPIO0 HIGH. Boot dauert max. 1 ms, danach Software-Standby. Schaltung: 4.7 µF und 100 nF an der Versorgung, Pull-ups für SDA/SCL einmal pro Bus.
