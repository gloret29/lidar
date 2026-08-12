# Scanner 3D LiDAR DIY

Scanner d'intérieur montable sur trépied photo, basé sur un LiDAR 2D (LD19) et un balayage vertical par moteur pas-à-pas NEMA 17. L'ESP32-S3 acquiert les mesures, convertit en coordonnées cartésiennes et streame le nuage de points vers une station hôte.

## Documentation

| Document | Description |
|----------|-------------|
| [PROJECT.md](PROJECT.md) | Spécification complète du projet (contexte IA) |
| [docs/architecture.md](docs/architecture.md) | Architecture hardware & software |
| [docs/wiring.md](docs/wiring.md) | Câblage et pinout ESP32-S3 |
| [docs/wifi.md](docs/wifi.md) | Configuration WiFi (WiFiManager) |
| [docs/calibration.md](docs/calibration.md) | Calibration IMU et géoréférencement |
| [docs/mechanical.md](docs/mechanical.md) | Conception mécanique et impression 3D |

## Structure du dépôt

```
lidar/
├── firmware/       # ESP32-S3 (PlatformIO)
├── host/           # Station hôte Python (réception, visualisation)
├── docs/           # Documentation technique
└── mechanical/     # Fichiers CAO / STL (à ajouter)
```

## Démarrage rapide

### Firmware

```bash
cd firmware
pio run -t upload
pio device monitor
```

### Station hôte

```bash
cd host
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m lidar_host.visualize
```

## Matériel

- ESP32-S3 DevKitC-1 (N16R8)
- LiDAR LD19 (UART 230400 baud)
- NEMA 17 + TMC2209
- MPU6050 (I2C)
- Powerbank USB-C PD + trigger 12V + buck 5V
- Roulements 608ZZ, inserts 1/4"-20, châssis imprimé 3D

## Licence

MIT
