# Firmware (ESPHome, MQTT)

`tankmonitor.yaml` wacht stündlich auf und misst beide Tanks mit je einem ToF-Sensor (TOF200C, VL53L0X) am gemeinsamen I2C-Bus: je 7 Messungen, davon der Median. Dazu kommen Akku und WLAN-Signal. Die Werte gehen per MQTT (retained) an den Broker, danach schläft der ESP wieder. Home Assistant legt die Sensoren per MQTT-Discovery automatisch an.

## Einrichten

1. MQTT-Broker bereitstellen (z. B. das Mosquitto-Add-on in HA) und die MQTT-Integration in HA einrichten.
2. `secrets.yaml.example` nach `secrets.yaml` kopieren und ausfüllen.
3. Tankmaße unter `substitutions` eintragen, in Metern ab Sensor:
   - `tX_dist_empty`: Abstand Sensor → Boden
   - `tX_dist_full`: Abstand Sensor → Oberfläche bei voll, mindestens 0,05
   - Werte über `max_range` (2,0 m) gelten als Fehlmessung
   - `tX_capacity`: Liter bei voll (linear umgerechnet)
4. Erstes Flashen per USB, **Kippschalter AUS**: `pip install esphome`, dann `esphome run tankmonitor.yaml`.

Benötigt ESPHome ≥ 2025.11, getestet mit 2026.6.5.

## OTA-Update

Der ESP schläft fast immer. Für ein Update hält ihn ein retained `ON` auf `tankmonitor/ota_mode` wach, höchstens 30 min. Bequem geht das mit diesem Schalter in der HA-`configuration.yaml`:

```yaml
mqtt:
  switch:
    - name: "Tankmonitor OTA-Modus"
      command_topic: "tankmonitor/ota_mode"
      state_topic: "tankmonitor/ota_mode"
      retain: true
```

1. Schalter EIN.
2. Nächste Wachphase abwarten oder RST drücken.
3. `esphome run tankmonitor.yaml` ausführen.
4. Schalter AUS: Der ESP geht sofort schlafen.

## Fehlersuche

`esphome logs tankmonitor.yaml` zeigt die Zahl der gültigen Messungen (7 von 7 ist gut). Zeigt ein Tank „unbekannt“, prüfen:
- Verdrahtung SDA/SCL und XSHUT des Sensors, 3,3 V am Modul
- Beim Start müssen beide Sensoren gefunden werden (Log zeigt Adresse 0x30 und 0x31). Fehlt einer, zuerst dessen Kabel und XSHUT prüfen.
- Abstand grösser als `max_range`, Oberfläche zu dunkel/spiegelnd, Tankwand oder Rand im Messkegel (ToF meldet das nächste Ziel)
- Lange Kabel: gelegentlich fehlende Messungen deuten auf Störungen. Siehe Abschnitt „Kabel zu den Sensoren“ in der [Haupt-README](../README.md): 50 kHz, verdrillte Paare mit GND, Kondensator am Sensor, stärkere Pull-ups.
- Sensor hängt: Kippschalter aus und wieder ein

## Akku

- Rote Power-LED am SuperMini ablöten, falls vorhanden. Sie zieht ca. 1 mA dauerhaft.
- Unter 3,3 V wacht der ESP nur noch alle 24 h auf.
- Ruhestrom messen: Multimeter in Reihe zum Kippschalter.
