# Scanner 3D LiDAR DIY

Scanner d'intérieur sur trépied photo, à base d'un LiDAR 2D LD19 dont le plan
de balayage vertical est mis en rotation autour d'un axe vertical. L'ESP32-S3
acquiert les mesures et les diffuse en Wi-Fi ; la station hôte reconstruit le
nuage de points 3D.

![Vue d'assemblage](mechanical/renders/assembly.png)

**Environ 205 € de matériel**, pour un nuage de 200 000 à 400 000 points par
scan, à ±5 cm, en 45 à 180 secondes.

## Documentation

### Comprendre

| Document | Contenu |
|---|---|
| [PROJECT.md](PROJECT.md) | Spécification et périmètre du projet |
| [docs/geometry.md](docs/geometry.md) | **Fondement mathématique** : pourquoi cette architecture, transformation exacte, budget d'erreur |
| [docs/architecture.md](docs/architecture.md) | Tâches du firmware, protocole UDP, pipeline hôte |

### Construire

| Document | Contenu |
|---|---|
| [docs/bom.md](docs/bom.md) | Nomenclature complète, y compris les pièces manquantes |
| [docs/printing.md](docs/printing.md) | Réglages d'impression, calibration des ajustements |
| [docs/mechanical.md](docs/mechanical.md) | Conception cotée, justification des choix |
| [docs/assembly.md](docs/assembly.md) | Montage pas à pas |
| [docs/wiring.md](docs/wiring.md) | Brochage, alimentation, réglage du TMC2209 |
| [docs/wifi.md](docs/wifi.md) | Configuration réseau par portail captif |
| [docs/web.md](docs/web.md) | Panneau web : commande, diagnostics, réglages |
| [docs/ota.md](docs/ota.md) | Mise à jour du firmware par le réseau |

### Utiliser

| Document | Contenu |
|---|---|
| [docs/calibration.md](docs/calibration.md) | Les cinq mesures à effectuer une fois |
| [docs/operation.md](docs/operation.md) | Préparation des lieux, conduite d'un scan, dépannage |

## Principe

Le LD19 est un LiDAR **2D** : il balaie 360° dans un plan. Monté **sur la
tranche**, ce plan devient vertical ; en le faisant pivoter de 180° autour de
l'axe vertical, on couvre la sphère complète exactement une fois.

Conséquence contre-intuitive mais essentielle : **l'angle interne du LiDAR est
l'élévation, et l'angle moteur est l'azimut**.

$$
X = \rho \cos\psi \cos\theta, \quad
Y = \rho \sin\psi \cos\theta, \quad
Z = \rho \sin\theta
$$

Le détail, et le contre-exemple qui disqualifie la formulation inverse, sont
dans [docs/geometry.md](docs/geometry.md).

## Structure du dépôt

```
lidar/
├── firmware/            ESP32-S3 (PlatformIO / Arduino / FreeRTOS)
│   ├── include/         config, protocole, pilotes
│   └── src/             tâches, parseur LD19, axe de lacet
├── host/                Station hôte Python
│   ├── src/lidar_host/  protocole, transformation, visualisation
│   ├── tests/           35 tests, sans matériel
│   └── calibration.json paramètres de calibration
├── mechanical/
│   ├── openscad/        sources paramétriques
│   ├── stl/             pièces prêtes à imprimer
│   ├── renders/         aperçus
│   └── tools/           génération et rendu
└── docs/                documentation détaillée
```

## Démarrage rapide

### 1. Pièces mécaniques

```bash
cd mechanical/openscad
make                       # STL dans ../stl/
```

Imprimer **`test_fits` en premier** pour calibrer les ajustements, reporter les
valeurs dans `params.scad`, puis relancer `make`. Détails dans
[docs/printing.md](docs/printing.md).

### 2. Firmware

```bash
cd firmware
pio run -e usb -t upload
pio device monitor
```

Au premier démarrage, se connecter au point d'accès `LiDAR-Scanner-Setup` pour
configurer le Wi-Fi, l'adresse de la station hôte et le mot de passe OTA.

Le scanner **reste au repos** après connexion. Ouvrir
`http://lidar-scanner.local/` pour lancer un balayage, suivre la télémétrie et
ajuster StallGuard / courants / vitesse. Voir [docs/web.md](docs/web.md).

Les mises à jour passent par le réseau, sans rebrancher l'USB — soit depuis
PlatformIO, soit en déposant le `.bin` sur la même page :

```bash
pio run -e ota -t upload
```

Voir [docs/ota.md](docs/ota.md).

### 3. Station hôte

```bash
cd host
python -m venv .venv && source .venv/bin/activate
pip install -e .
lidar-visualize --port 9000
```

### 4. Post-traitement

```bash
lidar-receive --port 9000 --output scans/salon_pos1.pcd --auto-stop
lidar-register scans/salon_*.pcd --output salon.pcd
lidar-mesh salon.pcd --output salon.ply
```

## Ce que fait — et ne fait pas — ce scanner

| Usage | Adapté |
|---|---|
| Plan d'étage, surfaces, volumes | Oui |
| Modèle d'ambiance pour de la 3D | Oui |
| Vérifier l'encombrement d'un meuble | Oui |
| BIM de détail, détection de collisions | Non |
| Relevé patrimonial, contrôle au millimètre | Non |

Précision réaliste : **±5 cm**, espacement des points de 3 à 7 cm à 5 m. Un
scanner terrestre professionnel atteint ±2 mm et des dizaines de millions de
points, pour 15 000 à 50 000 €.

## Matériel

ESP32-S3 DevKitC-1 (N16R8) · LiDAR LD19 · NEMA 17 17HS4401 · TMC2209 ·
MPU6050 · 2 × roulements 608ZZ · power bank USB-C PD + trigger 12 V + buck 5 V ·
châssis imprimé en 3D avec insert 1/4"-20.

Nomenclature détaillée, y compris les compléments à acquérir, dans
[docs/bom.md](docs/bom.md).

## Licence

MIT
