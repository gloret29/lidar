# Firmware ESP32-S3

Firmware PlatformIO du scanner 3D LiDAR.

## Prérequis

- [PlatformIO](https://platformio.org/) (CLI ou extension VS Code / Cursor).
  Sans `pio` dans le PATH : `firmware/.pio-venv/bin/pio`.
- ESP32-S3 DevKitC-1 **N16R8** (16 Mo Flash / 8 Mo PSRAM octale)

## Compilation

Premier flash, **obligatoirement en USB** : l'amorce OTA. Elle ne pilote
ni le LiDAR ni le moteur. Elle ouvre le portail Wi-Fi, puis accepte les
mises à jour du firmware **et** du filesystem LittleFS. Ensuite, plus
besoin de câble.

```bash
pio run -e seed -t upload
pio device monitor
```

Au premier démarrage, se connecter à `LiDAR-Scanner-Setup` pour le Wi-Fi
et le mot de passe OTA. Puis ouvrir `http://lidar-scanner.local/`.

Les mises à jour suivantes, sans USB :

```bash
pio run -e ota -t upload      # firmware scanner
pio run -e ota -t uploadfs    # image LittleFS (data/)
```

Pour itérer sur l'amorce elle-même : `pio run -e seed-ota -t upload`.
Le firmware scanner se compile encore avec `-e usb` si un câble est
branché.

Les dépendances (`WiFiManager`, `TMCStepper`) sont téléchargées automatiquement.
Web + OTA n'en ajoutent aucune : `ArduinoOTA`, `WebServer`, `Update`,
`LittleFS` et `Preferences` font partie du core ESP32.

## Configuration

### Wi-Fi et panneau web — aucun identifiant en dur

Au premier démarrage, l'ESP32 ouvre le point d'accès `LiDAR-Scanner-Setup`. On
y renseigne le réseau local, l'adresse de la station hôte et le mot de passe
du panneau (OTA inclus). Ces valeurs sont persistées en NVS.

Après connexion, ouvrir `http://lidar-scanner.local/` : commande de balayage,
diagnostics, réglages StallGuard / courants / vitesse, et OTA.

Voir [docs/wifi.md](../docs/wifi.md), [docs/web.md](../docs/web.md) et
[docs/ota.md](../docs/ota.md).

### Paramètres

- Défauts et brochage : [`include/config.h`](include/config.h)
- Valeurs runtime (persistées) : panneau web → NVS namespace `scanset`

> **Attention** : sur la variante N16R8, les GPIO 33 à 37 sont occupés par la
> PSRAM octale. Les utiliser fait planter la carte au démarrage.

## Organisation

```
firmware/
├── platformio.ini
├── boards/              ESP32-S3 DevKitC-1 N16R8 (16 Mo + PSRAM)
├── data/                image LittleFS (`pio run -t uploadfs`)
├── include/
│   ├── config.h        brochage et défauts
│   ├── protocol.h      datagrammes UDP (v2)
│   ├── ld19.h          analyseur de trames LiDAR
│   ├── scanner.h       axe de lacet
│   ├── settings.h      réglages NVS
│   ├── control.h       file de commandes
│   ├── status.h        télémétrie
│   ├── ota.h           panneau web + OTA
│   └── wifi_setup.h
└── src/
    ├── seed/main.cpp   amorce OTA (premier flash USB)
    ├── main.cpp
    ├── ld19.cpp
    ├── scanner.cpp
    ├── settings.cpp
    ├── control.cpp
    ├── status.cpp
    ├── ota.cpp         page unique + ArduinoOTA (firmware + LittleFS)
    └── wifi_setup.cpp
```

## Séquence d'exécution

```
setup()
  ├── réglages NVS
  ├── UART LiDAR + PWM
  ├── TMC2209
  ├── WiFiManager
  ├── panneau web + ArduinoOTA
  └── tâches

motion_task    attend start/stop/rehome/estop (file FreeRTOS)
lidar_task     UART -> décodage -> file
network_task   file -> datagrammes UDP
web_task       HTTP + ArduinoOTA.handle()
```

Le scanner **ne lance plus de balayage tout seul** au démarrage.

## Points d'implémentation notables

**Les points partent en polaire brut.** La conversion cartésienne est faite
côté hôte. Voir [docs/architecture.md](../docs/architecture.md).

**Débordement de file : on abandonne le point.** Perdre un point est sans
conséquence ; bloquer l'UART corromprait toute une salve.

**StealthChop2 n'est pas un confort.** Les vibrations SpreadCycle se
transmettent au capteur optique.

**L'OTA coupe le moteur avant d'écrire**, et est refusé pendant un balayage.
Comme le scanner démarre au repos, un firmware défectueux reste rattrapable
sans fenêtre artificielle de 10 s. Détails dans [docs/ota.md](../docs/ota.md).

**Les réglages exposés sont bornés dans le firmware** (courants, StallGuard,
vitesse). La calibration géométrique reste sur l'hôte.

## État

Le firmware est **structurellement complet mais n'a pas encore tourné sur du
matériel**. À valider en priorité au premier montage :

- [ ] Décodage des trames LD19 / STL-19P (taux de CRC via le panneau)
- [ ] Consigne PWM → 5 Hz réellement mesurés
- [ ] Seuil StallGuard (curseur web + lecture live)
- [ ] Nivellement IMU (code MPU6050 à écrire)
- [ ] Commande web start/stop/rehome sur trépied
- [ ] OTA firmware **et** LittleFS, par espota et par la page web

Le premier téléversement se fait obligatoirement **par USB**, avec
l'environnement `seed`. Les suivants passent par le réseau
(`-e ota -t upload` / `uploadfs`).

La géométrie et le protocole sont couverts par les tests de `host/tests/`.
