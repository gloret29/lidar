# Firmware ESP32-S3

Firmware PlatformIO pour le scanner 3D LiDAR DIY.

## Prérequis

- [PlatformIO](https://platformio.org/) (CLI ou extension VS Code / Cursor)
- Câble USB-C pour ESP32-S3 DevKitC-1

## Configuration

### WiFi — WiFiManager (portail captif)

Aucun SSID/mot de passe à compiler. Au premier démarrage :

1. Se connecter à l'AP `LiDAR-Scanner-Setup`
2. Configurer le WiFi + l'IP de la station hôte (UDP)
3. Maintenir **BOOT** au démarrage pour réinitialiser le WiFi

Voir [docs/wifi.md](../docs/wifi.md).

### Autres paramètres

Éditer `include/config.h` si besoin : broches, port UDP, profil de scan.

### Compiler et flasher

```bash
pio run -t upload
pio device monitor
```

## Structure

```
firmware/
├── platformio.ini
├── include/
│   └── config.h       # Pinout, WiFi, paramètres scan
└── src/
    └── main.cpp       # Squelette tasks + transform + UDP
```

## Prochaines étapes

- [ ] Driver LD19 (parsing paquets UART)
- [ ] Driver MPU6050 (I2C)
- [ ] Profil de balayage stepper (FreeRTOS task)
- [ ] Fusion temporelle ρ/θ/φ
- [ ] Buffer PSRAM + streaming par paquets

Voir [docs/architecture.md](../docs/architecture.md) et [docs/wiring.md](../docs/wiring.md).
