# Firmware ESP32-S3

Firmware PlatformIO du scanner 3D LiDAR.

## Prérequis

- [PlatformIO](https://platformio.org/) (CLI ou extension VS Code / Cursor)
- ESP32-S3 DevKitC-1 **N16R8** (16 Mo Flash / 8 Mo PSRAM octale)

## Compilation

```bash
pio run -t upload
pio device monitor
```

Les dépendances (`WiFiManager`, `TMCStepper`) sont téléchargées automatiquement.

## Configuration

### Wi-Fi — aucun identifiant en dur

Au premier démarrage, l'ESP32 ouvre le point d'accès `LiDAR-Scanner-Setup`. On
y renseigne le réseau local et l'adresse de la station hôte, puis tout est
mémorisé en flash. Maintenir **BOOT** au démarrage réinitialise ces
paramètres. Voir [docs/wifi.md](../docs/wifi.md).

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
│   └── wifi_setup.h    portail captif
└── src/
    ├── main.cpp        tâches FreeRTOS
    ├── ld19.cpp        décodage 47 octets + CRC8 (polynôme 0x4D)
    ├── scanner.cpp     TMC2209, homing StallGuard, profil
    └── wifi_setup.cpp
```

## Séquence d'exécution

```
setup()
  ├── UART LiDAR + consigne PWM à 5 Hz
  ├── TMC2209 : StealthChop2, 700 mA, StallGuard armé
  ├── WiFiManager
  └── création des tâches

motion_task    homing StallGuard -> montée en vitesse -> balayage 0..180 deg
lidar_task     UART -> décodage -> file
network_task   file -> datagrammes de 120 points -> UDP
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

## État

Le firmware est **structurellement complet mais n'a pas encore tourné sur du
matériel**. À valider en priorité au premier montage :

- [ ] Décodage des trames LD19 (vérifier le taux de CRC valides)
- [ ] Réglage du rapport cyclique PWM pour obtenir réellement 5 Hz
- [ ] Seuil `SGTHRS` du homing StallGuard
- [ ] Nivellement IMU (le code MPU6050 reste à écrire)
- [ ] Tenue en débit sous charge Wi-Fi réelle

La géométrie et le protocole, eux, sont couverts par les 35 tests de
`host/tests/`, exécutables sans matériel.
