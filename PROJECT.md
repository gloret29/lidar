# Scanner 3D LiDAR DIY — spécification

> Document de référence, également utilisé comme contexte pour les assistants
> de développement.

## Objectif

Concevoir et fabriquer un scanner 3D d'intérieur autonome, à bas coût, montable
sur trépied photo standard, générant un nuage de points $(X, Y, Z)$
géoréférencé d'une pièce ou d'un bâtiment.

Budget matériel : environ **205 €**. Précision visée : **±5 cm**.

## Architecture retenue

Le STL-19P (FHL-LD19P, protocole LD19) est monté **couché sur la tranche** :
son plan de balayage est vertical
et contient l'axe de rotation. L'ensemble pivote de 180° autour de l'**axe
vertical**, entraîné en prise directe par un NEMA 17.

| Angle | Origine | Rôle |
|---|---|---|
| $\theta$ | Angle interne du LD19 | **Élévation** |
| $\psi$ | Angle moteur | **Azimut** |

$$
X = \rho \cos\psi \cos\theta, \quad
Y = \rho \sin\psi \cos\theta, \quad
Z = \rho \sin\theta
$$

Justification complète et budget d'erreur : [docs/geometry.md](docs/geometry.md).

### Pourquoi pas un basculement autour d'un axe horizontal

Tous les plans de balayage contiennent l'axe de rotation : ce sont donc des
grands cercles passant par deux pôles. Avec un axe vertical, ces pôles sont le
zénith et le nadir — le nadir étant de toute façon masqué par le trépied. Avec
un axe horizontal, ils tomberaient sur deux murs quelconques, produisant deux
taches hyper-denses entourées de zones clairsemées.

S'y ajoutent trois avantages : couple moteur constant (pas de gravité à
vaincre), absence de fléchissement variable, et axe de rotation naturellement
confondu avec la verticale.

## Matériel

### Mesure optique

LiDAR 2D DToF **LDRobot STL-19P** (FHL-LD19P) : portée 0,02 à 12 m,
**5 000 mesures/s**, 360°, **détection du verre**, UART 3,3 V à 230 400 bauds,
précision ±45 mm, tolérance 30 klux. Fixation mécanique : **3 oreilles M2,5**
(gauche, droite, haut — câble en bas), corps **54 × 46,29 × 35 mm**.

Vitesse de rotation pilotable par PWM de 5 à 13 Hz. Le firmware la règle à
**5 Hz**, ce qui double la résolution angulaire (0,4° au lieu de 0,8°) sans
contrepartie sur trépied.

### Entraînement

NEMA 17 **pas à pas 4 fils** (ex. **17HS4401**) piloté par **TMC2209** en
1/16 de pas, StealthChop2, en prise directe. Résolution : 0,1125° par
micro-pas, soit 3,5 fois plus fin que le pas de balayage. Guidage par deux
roulements **608ZZ** sur tige acier Ø8.

> **Incompatible** : moteur brushless BLDC type 42BL3802 (Amazon B097JKJ9VV) —
> pas de pilotage STEP/DIR, ne convient pas au TMC2209 ni au firmware.

Prise de référence d'azimut par **StallGuard4** contre une butée imprimée :
aucun capteur de fin de course.

### Calcul et télémétrie

**ESP32-S3 DevKitC-1 (N16R8)**, 16 Mo de Flash et 8 Mo de PSRAM. Configuration
réseau par portail captif WiFiManager.

**MPU6050** monté sur la **base fixe** — et non sur la tête tournante. Il ne
sert qu'au nivellement statique et à la détection de choc, jamais à la
correction angulaire point par point : son bruit de 0,5 à 1° dégraderait la
mesure d'un facteur 2 à 4 par rapport au moteur.

### Alimentation

Power bank USB-C PD → trigger 12 V (TMC2209) → buck 12 V/5 V 3 A (ESP32 et
LD19). Consommation d'environ 8 à 12 W en balayage.

### Châssis

Cinq pièces imprimées en PETG, paramétriques (OpenSCAD), avec insert laiton
1/4"-20 UNC pour trépied photo. Hauteur totale 229 mm, tête tournante de 110 g.

## Chaîne logicielle

### Firmware (C++ / FreeRTOS)

| Tâche | Rôle |
|---|---|
| `lidar_task` | Décodage des trames LD19 (47 octets, CRC8 polynôme 0x4D) |
| `motion_task` | Nivellement, homing StallGuard, profil de balayage |
| `network_task` | Agrégation et émission UDP |
| `ota_task` / panneau web | Commande, diagnostics, réglages NVS, OTA firmware + LittleFS |

Les points sont transmis en **polaire brut** $(\rho, \theta)$, avec l'azimut en
en-tête de datagramme. La conversion cartésienne est faite côté hôte, ce qui
permet de corriger la calibration et de rejouer un scan **sans reflasher ni
rescanner**.

Le scanner démarre au repos. Les balayages se lancent depuis
`http://lidar-scanner.local/` (ou l'API). Le premier flash USB installe une
**amorce OTA** (Wi-Fi + mises à jour firmware/filesystem) ; le firmware
scanner arrive ensuite par le réseau. Le moteur est coupé avant toute
écriture en flash.

### Station hôte (Python)

Décodage vectorisé NumPy, transformation avec calibration (bras de levier,
décalages angulaires, redressement sur la gravité), visualisation temps réel
Open3D, recalage ICP multi-positions, maillage Poisson, export `.pcd` / `.ply`.
Un simulateur UDP (`lidar-simulate`) permet de valider toute la chaîne sans
scanner.

## Contraintes de conception

1. Le centre optique du STL-19P doit être aussi proche que possible de l'axe de
   rotation. Le résidu se compense en post-traitement : ignoré, il courbe les
   murs de façon **systématique**, donc non filtrable.
2. Le moteur est la référence angulaire. L'IMU ne sert qu'au nivellement.
3. Un cône d'environ 20° de demi-angle est perdu au nadir, masqué par la
   colonne. On le comble depuis une seconde position de scan.
4. Repère : origine au centre optique, $Z$ aligné sur la gravité après
   redressement IMU.

## État d'avancement

| Volet | Statut |
|---|---|
| Géométrie et mathématiques | Validées, 35 tests automatisés |
| Pièces 3D | 6 pièces paramétriques, rendues et vérifiées |
| Documentation de construction | Complète |
| Firmware | Amorce OTA compilée ; scanner compilé, **non testé sur matériel** |
| Station hôte | Protocole, transform, Open3D, simulateur UDP, tests |
| Calibration | Procédures écrites, à exécuter sur le prototype |

## Limites connues

- **Miroirs** : produisent une pièce virtuelle complète et géométriquement
  cohérente. Aucun filtrage ne les élimine ; il faut les couvrir.
- **Vitres** : la variante **STL-19P** détecte le verre (surface mesurée sur
  la vitre). Fermer les volets reste utile pour une surface opaque derrière et
  pour limiter l'éblouissement solaire.
- **Densité** : environ 300 000 points par scan, contre des dizaines de
  millions pour un scanner professionnel.
- **Nadir** : cône aveugle d'environ 20°, comblé par une seconde station.
