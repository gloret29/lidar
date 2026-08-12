# Architecture

## Vue d'ensemble

Le scanner combine un LiDAR 2D en rotation continue (azimut $\theta$) avec un balayage vertical discret ou continu (élévation $\phi$) pour produire un nuage de points 3D.

```
                    ┌─────────────────┐
                    │   Station hôte   │
                    │  Open3D / ROS2   │
                    └────────▲────────┘
                             │ WiFi (UDP)
                    ┌────────┴────────┐
                    │   ESP32-S3      │
                    │  ┌───────────┐  │
                    │  │ Transform │  │
                    │  │  (X,Y,Z)  │  │
                    │  └─────▲─────┘  │
                    │   ┌────┴────┐   │
                    │   │ Queues  │   │
                    │   └──┬───┬──┘   │
                    └───┬──┴───┴───┬───┘
                        │      │   │
                   UART │  I2C │   │ STEP/DIR
                        │      │   │
                   ┌────┴──┐ ┌─┴───┴──┐
                   │ LD19  │ │MPU6050 │
                   └───────┘ └────────┘
                              │
                         ┌────┴────┐
                         │ NEMA 17 │
                         │ TMC2209 │
                         └─────────┘
```

## Firmware — tasks FreeRTOS

| Task | Priorité | Période / déclenchement |
|------|----------|-------------------------|
| `lidar_task` | Haute | Lecture UART (DMA), push `(ρ, θ, t)` |
| `stepper_task` | Moyenne | Profil de balayage $\phi$, push `(φ_cmd, t)` |
| `imu_task` | Moyenne | 100–200 Hz, push `(pitch, t)` |
| `fusion_task` | Haute | Associe ρ, θ, φ, pitch → `(X, Y, Z)` |
| `network_task` | Moyenne | Envoi UDP par paquets |

### Synchronisation temporelle

Chaque point LiDAR doit être associé à :

- $\phi_{\text{cmd}}$ : angle commandé du stepper au timestamp $t$
- $\phi_{\text{imu}}$ : pitch mesuré par MPU6050 (correction mécanique)
- $\phi_{\text{effective}} = \phi_{\text{cmd}} + \phi_{\text{imu\_offset}}$

Utiliser `esp_timer_get_time()` comme horloge commune.

## Protocole réseau (UDP)

Port par défaut : **9000**

L'adresse IP de la station hôte est configurée via le portail **WiFiManager** au premier démarrage (persistée en flash). Voir [wifi.md](wifi.md).

### En-tête paquet (16 octets, little-endian)

| Offset | Type | Champ |
|--------|------|-------|
| 0 | `uint32` | Magic `0x4C444152` ("LDAR") |
| 4 | `uint16` | Version protocole |
| 6 | `uint16` | Nombre de points |
| 8 | `uint64` | Timestamp scan (µs) |

### Point (16 octets)

| Offset | Type | Champ |
|--------|------|-------|
| 0 | `float` | X (m) |
| 4 | `float` | Y (m) |
| 8 | `float` | Z (m) |
| 12 | `uint32` | Intensité / qualité (optionnel) |

## Station hôte

```
host/
└── lidar_host/
    ├── receiver.py    # Socket UDP, parsing binaire
    ├── point_cloud.py # Accumulation, filtrage
    └── visualize.py   # Viewer Open3D temps réel
```

Pipeline hôte :

1. Réception UDP → buffer de points
2. Filtrage statistique (radius outlier removal)
3. Visualisation ou enregistrement `.PCD`
4. (Optionnel) reconstruction mesh Poisson

## Débit estimé

- LD19 : ~4 500 pts/s
- 12 octets/point (XYZ float) + overhead ≈ **54–60 Ko/s**
- WiFi 802.11n suffisant en conditions normales ; prévoir buffer PSRAM côté firmware
