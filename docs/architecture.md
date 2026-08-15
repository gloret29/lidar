# Architecture logicielle

## Vue d'ensemble

```
   ┌──────────────────── Tête tournante ────────────────────┐
   │   STL-19P  (plan vertical, 5 Hz, 5000 pts/s)   │
   └────────────────────────┬───────────────────────────────┘
                            │ UART 230400
   ┌────────────────────────┴───────────────────────────────┐
   │                      ESP32-S3                          │
   │                                                        │
   │   lidar_task  ──►  file  ──►  network_task             │
   │   (coeur 1)                   (coeur 0)                │
   │        ▲                                               │
   │   motion_task ──► TMC2209 ──► NEMA 17                  │
   │   (coeur 1)                                            │
   │                                                        │
   │   ota_task    ──► ArduinoOTA (3232) + web (80)         │
   │   (coeur 0)                                            │
   └────────────────────────┬───────────────────────────────┘
                            │ UDP, points POLAIRES BRUTS
   ┌────────────────────────┴───────────────────────────────┐
   │                   Station hôte                          │
   │   protocol ──► transform (calibration) ──► Open3D      │
   └────────────────────────────────────────────────────────┘
```

## Décision structurante : transmettre en polaire brut

La conversion cartésienne se fait **sur l'hôte**, pas sur l'ESP32.

L'argument n'est pas la bande passante — 36 ko/s en polaire contre 72 ko/s en
cartésien, les deux sont négligeables en Wi-Fi. L'argument est la
**reprocessabilité** : le bras de levier, le zéro d'azimut et le nivellement
sont des paramètres de calibration. Les garder côté hôte permet de corriger un
réglage et de rejouer un scan déjà enregistré, sans reflasher ni retourner sur
site.

C'est d'autant plus pertinent que la transformation est exactement l'endroit où
une erreur de conception s'était glissée initialement (voir
[geometry.md](geometry.md) § 3).

## Tâches du firmware

| Tâche | Cœur | Priorité | Rôle |
|---|---|---|---|
| `lidar_task` | 1 | 5 | Lecture UART, décodage des trames LD19, mise en file |
| `motion_task` | 1 | 4 | Nivellement IMU (10 s), homing StallGuard, profil de balayage |
| `network_task` | 0 | 3 | Agrégation en datagrammes, émission UDP |
| `ota_task` / `web_task` | 0 | 2 | Panneau web + OTA firmware **et** LittleFS ([web.md](web.md), [ota.md](ota.md)) |
| `loop()` | 0 | 1 | Télémétrie sur le port série |

La file entre `lidar_task` et `network_task` compte 2 048 entrées, soit environ
410 ms de marge à 5 000 pts/s. En cas de saturation, `lidar_task` **abandonne
le point** plutôt que de bloquer : perdre un point est sans conséquence, perdre
la synchronisation de l'UART corromprait toute une salve de trames.

### Synchronisation des angles

À 2 °/s, l'azimut ne varie que de **0,005°** pendant l'émission d'une trame de
12 points (2,7 ms). C'est trois ordres de grandeur sous la résolution visée
(0,4°). Relever $\psi$ une fois par trame suffit donc largement.

Les bornes `psi_start` et `psi_end` sont néanmoins transmises à chaque
datagramme, et l'hôte interpole selon l'horodatage : la chaîne reste correcte
si l'on décide un jour d'accélérer le balayage.

## Ports réseau

| Port | Protocole | Rôle |
|---|---|---|
| 9000 | UDP, sortant | Flux de points vers la station hôte |
| 3232 | TCP | Mise à jour ArduinoOTA / espota |
| 80 | TCP | Page de commande, `/info`, OTA web (`/update`, `/updatefs`) |

Le port 3232 n'est pas servi pendant un balayage, et le port 80 renvoie alors
503 sur `/update` et `/updatefs` : une mise à jour en pleine acquisition
perdrait le scan et laisserait la mécanique dans un état indéterminé.

Une mise à jour relâche `EN` du TMC2209 **avant** la première écriture en
flash, puis suspend `lidar_task` et `network_task`. Le scanner démarre au
repos (plus de balayage automatique) : l'OTA et le panneau de commande sont
joignables immédiatement. Détails dans [web.md](web.md) et [ota.md](ota.md).

## Protocole UDP, version 2

Port par défaut : **9000**. L'adresse de l'hôte se configure via le portail
WiFiManager ([wifi.md](wifi.md)). Tout est en little-endian.

### En-tête (32 octets)

| Offset | Type | Champ |
|---|---|---|
| 0 | `uint32` | Magic `0x4C444152` (« LDAR ») |
| 4 | `uint16` | Version du protocole (2) |
| 6 | `uint16` | Drapeaux |
| 8 | `uint32` | Numéro de séquence |
| 12 | `uint16` | Nombre de points |
| 14 | `uint16` | Vitesse du LD19, en 0,1 Hz |
| 16 | `uint64` | Horodatage du premier point (µs) |
| 24 | `int32` | Azimut au premier point (millidegrés) |
| 28 | `int32` | Azimut au dernier point (millidegrés) |

### Point (8 octets)

| Offset | Type | Champ |
|---|---|---|
| 0 | `uint16` | Distance $\rho$, millimètres |
| 2 | `uint16` | Angle LiDAR $\theta$ = **élévation**, centidegrés |
| 4 | `uint8` | Intensité |
| 5 | `uint8` | Réservé |
| 6 | `uint16` | Décalage depuis l'horodatage d'en-tête (µs) |

### Drapeaux

| Bit | Nom | Signification |
|---|---|---|
| 0 | `SCAN_START` | Premier datagramme d'un scan |
| 1 | `SCAN_END` | Balayage terminé |
| 2 | `LEVEL_VALID` | Nivellement IMU réussi |
| 3 | `SHOCK_DETECTED` | Le trépied a bougé : scan suspect |

120 points par datagramme, soit 992 octets — sous la MTU, donc jamais de
fragmentation IP.

Le numéro de séquence permet à l'hôte de chiffrer les pertes. UDP est retenu
sciemment : sur un nuage de plusieurs centaines de milliers de points, quelques
pertes sont sans importance, alors que la latence de retransmission de TCP
perturberait l'affichage temps réel.

## Station hôte

```
host/src/lidar_host/
├── protocol.py      décodage v2, vectorisé NumPy
├── transform.py     polaire -> cartésien, calibration, nivellement
├── receiver.py      socket UDP, accumulation, export
├── visualize.py     affichage temps réel Open3D
└── postprocess.py   filtrage, recalage ICP, maillage Poisson
```

Le décodage est vectorisé : `np.frombuffer` sur un dtype structuré, sans boucle
Python. Un datagramme de 120 points se décode en quelques microsecondes, très
loin des 37 datagrammes par seconde à absorber.

## Débit

| Étage | Débit |
|---|---|
| LD19 / STL-19P en sortie UART | 5 000 pts/s, soit ~19,6 ko/s de trames |
| Points valides après filtrage | ~5 000 pts/s (CRC + distance valide) |
| Charge utile UDP | ~32 ko/s |
| Avec en-têtes UDP/IP | ~34 ko/s |

Très largement dans les capacités d'un 802.11n, y compris en périphérie de
couverture.

## Amorce OTA

Le premier flash USB installe un firmware minimal (`src/seed/`) : Wi-Fi,
ArduinoOTA et page web, sans LiDAR ni moteur. Les mises à jour suivantes —
firmware scanner **et** image LittleFS — passent par le réseau. Voir
[ota.md](ota.md).

## Tests

```bash
cd host && PYTHONPATH=src .venv/bin/python -m pytest tests/ -q
```

38 tests couvrent le décodage du protocole et la transformation géométrique,
sans aucun matériel. Ils comprennent notamment un **garde-fou contre le retour
à la formule sphérique naïve** : c'est l'erreur la plus coûteuse possible sur
ce projet, car elle produit un nuage plausible mais faux.
