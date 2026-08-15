# Projet KiCad — Scanner 3D LiDAR

Schéma de **câblage entre modules** (pas de PCB — montage sur breadboard /
borniers dans le boîtier `electronics_box`).

## Ouvrir

1. Installer [KiCad](https://www.kicad.org/) 8 ou 9.
2. Ouvrir `lidar.kicad_pro` dans ce dossier.

## Regénérer

```bash
python3 hardware/generate_kicad.py
```

## Contenu du schéma

| Réf | Module |
|---|---|
| BAT1 | Power bank USB-C PD |
| U2 | Trigger PD → 12 V |
| U4 | Buck 12 V → 5 V |
| U1 | ESP32-S3 DevKitC-1 N16R8 |
| LD1 | LiDAR STL-19P / LD19 (tête tournante) |
| U5 | MPU6050 (base fixe) |
| U3 | TMC2209 |
| M1 | NEMA 17 |
| R1 | 1 kΩ (UART TMC, liaison un fil) |
| C1, C2 | 100 nF (découplage, optionnel sur breadboard) |

Brochage GPIO : voir [`docs/wiring.md`](../docs/wiring.md) et
[`firmware/include/config.h`](../firmware/include/config.h).

## Notes

- Les symboles `lidar:*` représentent des **modules breakout**, pas des composants
  à souder.
- Aucune PCB n'est incluse : `on_board` est à `no` pour les modules.
- Les symboles `Device:R`, `Device:C`, `power:*` viennent des bibliothèques
  KiCad standard (embarquées dans le schéma).
