# Nomenclature (BOM)

## A. Déjà commandé

| Réf | Composant | Qté utilisée | Qté au panier | Rôle |
|---|---|---|---|---|
| A1 | LiDAR STL-19P (FHL-LD19P, youyeetoo) | 1 | 1 | Mesure de distance, 360°, détection verre |
| A2 | ESP32-S3 DevKitC-1 (N16R8) | 1 | 3 | Acquisition, pilotage, Wi-Fi |
| A3 | Driver TMC2209 v2.0 | 1 | 2 | Pilotage moteur, StealthChop2 + StallGuard |
| A4 | Moteur NEMA 17 pas à pas 4 fils (17HS4401) | 1 | 1 | Entraînement STEP/DIR via TMC2209 |
| A5 | MPU6050 (GY-521) | 1 | 3 | Nivellement, détection de choc |
| A6 | Roulement 608ZZ (8×22×7) | 2 | 40 | Guidage de l'axe vertical |
| A7 | Insert laiton 1/4"-20 UNC **× 10 × 8 mm** | 1 | 50 | Fixation trépied (logement Ø8,4) |
| A8 | Module trigger USB-C PD | 1 | 5 | Extraction du 12 V depuis la power bank |
| A9 | Convertisseur buck 12 V → 5 V 3 A | 1 | 2 | Alimentation ESP32 + LiDAR |
| A10 | Power bank USB-C PD 100 W | 1 | — | Source d'énergie |

Les quantités au panier laissent une marge confortable de rechange, ce qui est
appréciable sur les pièces sensibles au montage (roulements, inserts).

## B. À acquérir en complément

Ces pièces sont indispensables et **ne figurent pas** dans la commande
initiale.

| Réf | Composant | Qté | Prix indicatif | Remarques |
|---|---|---|---|---|
| B1 | Tige acier rectifiée Ø8 h6, longueur ≥ 120 mm | 1 | 3 € | Tige linéaire d'imprimante 3D, à recouper à **115 mm** |
| B2 | Accouplement flexible 5 → 8 mm (Ø19 × 25 mm) | 1 | 4 € | Type mâchoires/araignée. Rigide **déconseillé** : il ferait forcer les roulements en cas de défaut d'alignement |
| B3 | Vis M3×12 (ou vis fournies avec le moteur) + écrou M3 | 4 | — | Moteur sur plateau — **trous traversants** sur la bride NEMA |
| B4 | Vis M3×20 + écrou M3 | 4 | — | Colonne sur plateau |
| B5 | Vis M3×25 + écrou M3 | 1 | — | Serrage du berceau sur la tige |
| B6 | Vis M3×8 | 8 | — | Couvercle du boîtier + modules |
| B7 | Vis M2,5×8 + écrou M2,5 | 3 | — | STL-19P sur le berceau (3 oreilles) |
| B8 | Colliers rilsan 2,5 × 100 mm | 10 | 2 € | Sanglage du boîtier, maintien des câbles |
| B9 | Fil silicone AWG24-26, 4 couleurs | 2 m | 4 € | Câblage interne |
| B10 | Niveau à bulle tubulaire Ø15 (optionnel) | 1 | 3 € | Pré-réglage rapide avant nivellement IMU |

Un assortiment de visserie M3 coûte environ 10 € et couvre B3 à B6.

**Total complémentaire : environ 25 €.**

## C. Pièces imprimées en 3D

Sources paramétriques dans [`mechanical/openscad/`](../mechanical/openscad/),
STL générés dans [`mechanical/stl/`](../mechanical/stl/).

| Réf | Pièce | Qté | Rôle |
|---|---|---|---|
| C0 | `test_fits` | 1 | **Coupon de calibration — à imprimer en premier** |
| C1 | `base_plate` | 1 | Interface trépied, support moteur, embase colonne |
| C2 | `bearing_tower` | 1 | Porte les deux 608ZZ, définit l'axe. Pièce critique |
| C3 | `lidar_cradle` | 1 | Présente le STL-19P sur la tranche (3 oreilles M2,5), serre sur la tige |
| C4 | `electronics_box` | 1 | Boîtier ESP32 / TMC2209 / alimentation |
| C5 | `electronics_lid` | 1 | Couvercle du boîtier |

Consommation : environ 220 g de PETG, 9 h d'impression au total.

## D. Outillage

| Outil | Usage |
|---|---|
| Imprimante 3D (volume ≥ 130 × 130 × 140 mm) | Pièces C1 à C5 |
| Fer à souder à panne large | Pose de l'insert 1/4"-20 |
| Pied à coulisse | Vérification des ajustements et du décalage optique |
| Multimètre | Réglage du Vref du TMC2209 |
| Tournevis de précision plat | Potentiomètre du TMC2209 |
| Scie à métaux ou Dremel | Recoupe de la tige Ø8 |
| Clés Allen 1,5 / 2 / 2,5 mm | Accouplement et visserie |

## E. Points de vigilance à l'achat

**Variante du LD19.** Trois versions circulent sous des noms voisins :

| Modèle | Mesures/s | Portée | Détection du verre |
|---|---|---|---|
| FHL-LD19 | 4 500 | 12 m | Non |
| FHL-LD19P / **STL-19P** | 5 000 | 12 m | Oui |
| FHL-LD19 Plus / STL-27L | 21 600 | 25 m | Oui |

L'exemplaire reçu est le **STL-19P** (FHL-LD19P) : 5 000 Hz, détection du
verre, **3 oreilles M2,5** (pas 4 fentes). Le berceau `lidar_cradle` est
dimensionné pour cette variante. Nappe : **P5V vert**, **GND jaune**,
**TX blanc**, **PWM noir** (voir [wiring.md](wiring.md) § 3).
Voir [operation.md](operation.md) pour les vitres et miroirs.

**Moteur pas à pas obligatoire.** Le châssis et le firmware supposent un NEMA
17 **4 fils** piloté en STEP/DIR par TMC2209. Un moteur brushless BLDC (ex.
42BL3802-23A) est **incompatible** — à remplacer avant tout montage électrique.
Modèles courants : Creality 42-40, STEPPERONLINE 17HE15, ou tout 17HS4401
équivalent. Câble 4 fils : **noir A+**, **bleu A−**, **vert B+**, **rouge B−**
(voir [wiring.md](wiring.md) § 5).

**Trigger PD.** Vérifier que le module retenu délivre bien 12 V et non
seulement 5/9 V. Les modules à DIP switch sont les plus souples.

**Power bank.** Elle doit tenir 12 V sous environ 1 A. Certaines coupent
automatiquement en dessous d'un seuil de consommation : le scanner tire
environ 8 à 12 W en balayage, ce qui suffit à maintenir la plupart des modèles
éveillés. Vérifier néanmoins avant une longue session.
