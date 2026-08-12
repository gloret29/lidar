# Firmware ESP32-S3

Firmware PlatformIO du scanner 3D LiDAR.

## Prérequis

- [PlatformIO](https://platformio.org/) (CLI ou extension VS Code / Cursor)
- ESP32-S3 DevKitC-1 **N16R8** (16 Mo Flash / 8 Mo PSRAM octale)

## Compilation

```bash
pio run -e usb -t upload      # par câble
pio device monitor
```

```bash
pio run -e ota -t upload      # par le réseau
```

Les dépendances (`WiFiManager`, `TMCStepper`) sont téléchargées automatiquement.
L'OTA n'en ajoute aucune : `ArduinoOTA`, `WebServer` et `Update` font partie du
core ESP32.

## Configuration

### Wi-Fi et OTA — aucun identifiant en dur

Au premier démarrage, l'ESP32 ouvre le point d'accès `LiDAR-Scanner-Setup`. On
y renseigne le réseau local, l'adresse de la station hôte et le mot de passe
OTA. Ces trois valeurs sont persistées en NVS et relues à chaque démarrage.
Maintenir **BOOT** au démarrage remet tout à zéro.

Voir [docs/wifi.md](../docs/wifi.md) et [docs/ota.md](../docs/ota.md).

### Autres paramètres

Tout est dans [`include/config.h`](include/config.h) : brochage, vitesse du
LiDAR, profil de balayage, courants moteur, seuil StallGuard.

> **Attention** : sur la variante N16R8, les GPIO 33 à 37 sont occupés par la
> PSRAM octale. Les utiliser fait planter la carte au démarrage.

## Organisation

```
firmware/
├── platformio.ini
├── include/
│   ├── config.h        brochage et paramètres
│   ├── protocol.h      format des datagrammes UDP (v2)
│   ├── ld19.h          analyseur de trames LiDAR
│   ├── scanner.h       axe de lacet
│   ├── ota.h           mise à jour par le réseau
│   └── wifi_setup.h    portail captif, persistance NVS
└── src/
    ├── main.cpp        tâches FreeRTOS, accroches OTA
    ├── ld19.cpp        décodage 47 octets + CRC8 (polynôme 0x4D)
    ├── scanner.cpp     TMC2209, homing StallGuard, profil
    ├── ota.cpp         ArduinoOTA + serveur web d'upload
    └── wifi_setup.cpp
```

## Séquence d'exécution

```
setup()
  ├── UART LiDAR + consigne PWM à 5 Hz
  ├── TMC2209 : StealthChop2, 700 mA, StallGuard armé
  ├── WiFiManager (réglages relus depuis la NVS)
  ├── OTA : ArduinoOTA + serveur web + mDNS
  └── création des tâches

motion_task    fenêtre OTA 10 s -> homing -> montée en vitesse -> balayage 180 deg
lidar_task     UART -> décodage -> file
network_task   file -> datagrammes de 120 points -> UDP
ota_task       ArduinoOTA.handle() + serveur web
```

## Points d'implémentation notables

**Les points partent en polaire brut.** La conversion cartésienne est faite
côté hôte, ce qui permet de corriger la calibration et de rejouer un scan sans
reflasher. Voir [docs/architecture.md](../docs/architecture.md).

**Débordement de file : on abandonne le point.** Perdre un point sur 400 000
est sans conséquence ; bloquer la lecture de l'UART corromprait toute une salve
de trames.

**StealthChop2 n'est pas un confort.** Les vibrations d'un moteur en
SpreadCycle se transmettent directement au capteur optique et dégradent la
mesure. C'est la raison d'être de la liaison UART vers le TMC2209.

**L'OTA coupe le moteur avant d'écrire.** Redémarrer avec le TMC2209 encore
alimenté laisserait l'axe en couple pendant plusieurs secondes. Une mise à jour
relâche donc `EN` en premier, avant toute écriture en flash.

**L'OTA est refusé pendant un balayage**, et une fenêtre de 10 s est ménagée à
chaque démarrage. Sans elle, un firmware qui plante en cours de scan ne serait
plus récupérable que par USB — le scanner redémarrerait en boucle sans jamais
laisser d'occasion de le corriger. Détails dans [docs/ota.md](../docs/ota.md).

## État

Le firmware est **structurellement complet mais n'a pas encore tourné sur du
matériel**. À valider en priorité au premier montage :

- [ ] Décodage des trames LD19 (vérifier le taux de CRC valides)
- [ ] Réglage du rapport cyclique PWM pour obtenir réellement 5 Hz
- [ ] Seuil `SGTHRS` du homing StallGuard
- [ ] Nivellement IMU (le code MPU6050 reste à écrire)
- [ ] Tenue en débit sous charge Wi-Fi réelle
- [ ] OTA de bout en bout, par les deux voies

Le premier téléversement se fait obligatoirement **par USB** : l'OTA suppose
qu'un firmware sachant l'assurer tourne déjà.

La géométrie et le protocole, eux, sont couverts par les 35 tests de
`host/tests/`, exécutables sans matériel.
