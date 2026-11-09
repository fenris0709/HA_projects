# Firmware (ESPHome, MQTT)

`tankmonitor.yaml` wacht stündlich auf und misst den Tank mit einem ToF-Sensor (TOF200C, VL53L0X): 15 Messungen, davon der Median. Dazu kommen Akku und WLAN-Signal. Die Werte gehen per MQTT (retained) an den Broker, danach schläft der ESP wieder. Home Assistant legt die Sensoren per MQTT-Discovery automatisch an.

**Ein Gerät pro Tank.** Alle Geräte nutzen dieselbe Datei. Unterschieden werden sie nur durch den veröffentlichten Namen: `sn` ganz oben in `substitutions` (z. B. `"01"`, `"02"`). Daraus entstehen:

| | Beispiel mit `sn: "01"` |
|---|---|
| Gerätename, MQTT-Topic | `tankmonitor-01` |
| Name in Home Assistant | Tankmonitor 01 |
| OTA-Topic | `tankmonitor-01/ota_mode` |
| Schlafdauer-Topic | `tankmonitor-01/sleep_minutes` |

## Einrichten

1. MQTT-Broker bereitstellen (z. B. das Mosquitto-Add-on in HA) und die MQTT-Integration in HA einrichten.
2. `secrets.yaml.example` nach `secrets.yaml` kopieren und ausfüllen.
3. In `substitutions` die Seriennummer `sn` und die Tankmaße eintragen, in Metern ab Sensor:
   - `dist_empty`: Abstand Sensor → Boden
   - `dist_full`: Abstand Sensor → Oberfläche bei voll, mindestens 0,05
   - Werte über `max_range` (2,0 m) gelten als Fehlmessung
   - `capacity`: Liter bei voll (linear umgerechnet)
4. Erstes Flashen **vor dem Einbau**, mit dem ESP einzeln am USB (**Kippschalter AUS**): `pip install esphome`, dann `esphome run tankmonitor.yaml`. Im Gehäuse sind BOOT und RESET des ESP nach unten gerichtet und nicht erreichbar. Danach geht es per OTA.
5. Zweites Gerät: `sn` ändern (`"02"`), Tankmaße anpassen, flashen.

Benötigt ESPHome ≥ 2025.11, getestet mit 2026.6.5 (bei der Ein-Sensor-Version noch nicht neu kompiliert).

## OTA-Update

Der ESP schläft fast immer. Für ein Update hält ihn ein retained `ON` auf `tankmonitor-01/ota_mode` wach, höchstens 30 min. Bequem geht das mit diesem Schalter in der HA-`configuration.yaml` (je Gerät einen):

```yaml
mqtt:
  switch:
    - name: "Tankmonitor 01 OTA-Modus"
      command_topic: "tankmonitor-01/ota_mode"
      state_topic: "tankmonitor-01/ota_mode"
      retain: true
```

1. Schalter EIN.
2. Nächste Wachphase abwarten oder RST drücken. Sobald der Sensor „Modus“ auf „OTA aktiv“ steht, ist der ESP wach.
3. `esphome run tankmonitor.yaml` ausführen.
4. Schalter AUS: Der ESP geht sofort schlafen, „Modus“ springt auf „Normal“.

## Schlafdauer per MQTT

Die Dauer in Minuten (1 bis 1440) steht als retained Zahl auf `tankmonitor-01/sleep_minutes`. Ohne Wert gelten 60 min (`sleep_default_min`). Der ESP liest sie bei jedem Aufwachen und meldet den tatsächlichen Wert im Sensor „Schlafdauer aktiv“ zurück. Der neue Wert gilt also ab der nächsten Wachphase, bei schwachem Akku bleibt es bei der langen Pause und „Schlafdauer aktiv“ zeigt das an. Stimmen Soll und Ist überein, ist die Änderung übernommen.

Regler in der HA-`configuration.yaml`, neben dem OTA-Schalter:

```yaml
mqtt:
  number:
    - name: "Tankmonitor 01 Schlafdauer"
      command_topic: "tankmonitor-01/sleep_minutes"
      state_topic: "tankmonitor-01/sleep_minutes"
      retain: true
      min: 5
      max: 1440
      step: 5
      unit_of_measurement: "min"
```

Sofort übernehmen: RST drücken (Gehäuse offen, Platine mit ESP nach unten: besser OTA-Modus kurz ein- und ausschalten). Die Wachphase dauert wegen des Wartens auf die retained Werte bis zu 3 s länger, wenn `sleep_minutes` nie gesetzt wurde.

## Sparmodus des Sensors

XSHUT des Moduls hängt an GPIO5. ESPHome setzt ihn beim Start auf high (Sensor an). Im Deep Sleep floatet der Pin und der Pulldown `Rxs` (1 kΩ, siehe [Schaltung](../docs/schaltung.md)) hält den Sensor im Standby. Ohne `Rxs` oder mit einem Modul, das XSHUT fest hochzieht, läuft der Sensor im Schlaf weiter. Dann zeigt der Ruhestrom (Multimeter in Reihe zum Kippschalter) deutlich mehr als einige 100 µA.

## Fehlersuche

`esphome logs tankmonitor.yaml` zeigt die Zahl der gültigen Messungen (15 von 15 ist gut). Zeigt der Tank „unbekannt“, prüfen:
- Verdrahtung SDA/SCL/XSHUT und 3,3 V am Modul, Modul richtig herum in der Buchsenleiste (siehe [Schaltung](../docs/schaltung.md))
- Beim Start muss der Sensor gefunden werden (Log zeigt Adresse 0x29). Sonst XSHUT prüfen: muss nach dem Start high sein.
- Abstand grösser als `max_range`, Oberfläche zu dunkel/spiegelnd, Tankwand oder Rand im Messkegel (ToF meldet das nächste Ziel)
- Sensor hängt: Kippschalter aus und wieder ein

## Akku

- Rote Power-LED am SuperMini ablöten, falls vorhanden. Sie zieht ca. 1 mA dauerhaft.
- Unter 3,3 V wacht der ESP nur noch alle 24 h auf.
- Ruhestrom messen: Multimeter in Reihe zum Kippschalter.
