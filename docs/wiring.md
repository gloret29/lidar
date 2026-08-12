# Câblage et pinout

## 1. Architecture d'alimentation

```
  Power bank USB-C PD 100 W
            │
            ▼
   Module trigger PD  ──► 12 V
            ├──────────────────────► TMC2209  VM
            │
            └──► Buck 12 V → 5 V 3 A
                       ├────────────► LD19        VCC (5 V, 180 mA)
                       └────────────► ESP32-S3    5V / VIN
                                          │
                                          └──3,3 V──► MPU6050
                                                      TMC2209 VIO
```

**Masse commune obligatoire** entre trigger PD, buck, ESP32, TMC2209, moteur et
LiDAR. Une masse flottante sur le TMC2209 est la cause classique de pas perdus
et de comportements erratiques.

Consommation totale : environ 8 à 12 W en balayage.

## 2. Brochage de l'ESP32-S3 DevKitC-1 (N16R8)

| Fonction | GPIO | Sens | Remarques |
|---|---|---|---|
| LiDAR UART RX | 18 | Entrée | Reçoit le TX du LD19 |
| LiDAR PWM (vitesse) | 17 | Sortie | 30 kHz, pilote la vitesse de rotation |
| I2C SDA (MPU6050) | 8 | E/S | |
| I2C SCL (MPU6050) | 9 | Sortie | |
| TMC2209 STEP | 4 | Sortie | |
| TMC2209 DIR | 5 | Sortie | |
| TMC2209 EN | 6 | Sortie | Actif à l'état bas |
| TMC2209 UART TX | 7 | Sortie | Via résistance 1 kΩ vers PDN_UART |
| TMC2209 UART RX | 15 | Entrée | Directement sur PDN_UART |
| TMC2209 DIAG (StallGuard) | 16 | Entrée | Détection de butée |
| Bouton BOOT | 0 | Entrée | Réinitialisation Wi-Fi, maintenu au démarrage |
| LED RGB embarquée | 48 | Sortie | GPIO 38 sur certaines révisions |

### Broches à ne pas utiliser

Sur la variante **N16R8**, la PSRAM octale occupe les **GPIO 33 à 37** : les
utiliser fait planter la carte au démarrage. Éviter également les GPIO 26 à 32
(flash SPI) et 19/20 (USB natif).

## 3. LiDAR LD19

Connecteur JST 4 points côté capteur.

| LD19 | Vers | Fil (typique) |
|---|---|---|
| VCC (5 V) | Sortie buck 5 V | Rouge |
| GND | Masse commune | Noir |
| TX | GPIO 18 | Jaune / vert |
| PWM | GPIO 17 | Blanc |

Le LD19 communique en **UART 230 400 bauds, 8N1**, niveaux 3,3 V, compatibles
directement avec l'ESP32-S3. La liaison est **unidirectionnelle** : le capteur
émet en continu, aucune commande à lui envoyer.

### Commande de vitesse par PWM

Broche PWM à la masse (ou non connectée) : régulation interne à 10 Hz.
Signal carré de 30 kHz appliqué : la vitesse devient réglable de 5 à 13 Hz par
le rapport cyclique, asservie en boucle fermée par le capteur.

Le firmware règle **5 Hz**, ce qui double la résolution angulaire (0,4° au lieu
de 0,8°) sans aucun coût. Voir [geometry.md](geometry.md) § 6.

### Câble tournant

Le câble du LD19 est le seul à traverser la liaison tournante. Sur ±90° de
débattement, une simple boucle de mou suffit : ni bague tournante, ni contact
glissant. Laisser environ 120 mm de mou en hélice lâche le long de la colonne
et fixer les deux extrémités par collier rilsan, jamais en tension.

## 4. MPU6050

**Monté sur la base fixe**, pas sur la tête tournante — il ne sert qu'à mesurer
la verticale au repos.

| MPU6050 | ESP32-S3 |
|---|---|
| VCC | 3,3 V |
| GND | GND |
| SDA | GPIO 8 |
| SCL | GPIO 9 |
| AD0 | GND (adresse 0x68) |

Ne **pas** l'alimenter en 5 V : la plupart des cartes GY-521 ont un régulateur,
mais les lignes I2C reviennent alors en 5 V sur l'ESP32.

Le coller à plat dans le boîtier électronique, faces bien parallèles au plateau
de base. Son orientation exacte n'a pas besoin d'être parfaite : la calibration
mesure l'écart une fois pour toutes.

## 5. TMC2209 et NEMA 17

| TMC2209 | Connexion |
|---|---|
| VM | 12 V (trigger PD) |
| GND | Masse commune |
| VIO | 3,3 V |
| STEP | GPIO 4 |
| DIR | GPIO 5 |
| EN | GPIO 6 |
| PDN_UART | GPIO 15, et GPIO 7 via 1 kΩ |
| DIAG | GPIO 16 |
| MS1 / MS2 | Voir adressage ci-dessous |
| A+ A− B+ B− | Moteur NEMA 17 |

### Liaison UART à un fil

Le TMC2209 dialogue sur une seule broche, PDN_UART. Montage usuel :

```
   ESP32 TX (GPIO 7) ──[ 1 kΩ ]──┬── PDN_UART (TMC2209)
                                 │
   ESP32 RX (GPIO 15) ───────────┘
```

La résistance évite le conflit lorsque le driver répond. Sans cette liaison, il
faudrait régler le courant au potentiomètre et renoncer à StallGuard.

L'UART apporte trois choses qui changent tout :

1. **Réglage logiciel du courant**, bien plus précis et reproductible qu'un
   potentiomètre.
2. **StealthChop2** correctement configuré, donc un balayage silencieux et sans
   vibration parasite — critique quand on porte un capteur optique.
3. **StallGuard4**, qui permet la prise de référence sans capteur.

### Adressage MS1/MS2

En mode UART, MS1 et MS2 définissent l'adresse du driver, pas le micro-pas
(réglé par registre). Un seul driver : MS1 = MS2 = GND, adresse 0.

### Courant moteur

Le 17HS4401 est donné pour 1,5 A par phase. La charge se limite au frottement
des roulements et à 110 g de tête : **inutile d'y aller fort**.

Réglage recommandé : **700 mA RMS**, par UART (`setRMSCurrent(700)`).

En repli, sans UART, régler le potentiomètre au multimètre. Avec
$R_{\text{sense}} = 0{,}11\ \Omega$ :

$$V_{\text{ref}} \approx 1{,}25 \times I_{\text{RMS}}$$

soit environ **0,88 V** pour 700 mA. Vérifier la valeur de $R_{\text{sense}}$
de la carte : elle varie selon les fabricants.

Un courant excessif chauffe pour rien, augmente les vibrations et dégrade la
qualité optique du scan.

### Prise de référence par StallGuard

La colonne porte un contrefort fixe et le berceau un secteur de 26°. À la mise
sous tension, le moteur tourne lentement jusqu'au contact ; la détection de
blocage donne le **zéro d'azimut absolu**, sans aucun capteur.

Paramètres de départ :

| Registre | Valeur | Rôle |
|---|---|---|
| `TCOOLTHRS` | 0xFFFFF | Active StallGuard sur toute la plage utile |
| `SGTHRS` | 60 à 100 | Seuil de détection, à affiner |
| Courant de homing | 300 mA | Réduit pour un contact doux |
| Vitesse de homing | 10 °/s | StallGuard exige une vitesse minimale |

`SGTHRS` se règle empiriquement : trop bas, aucune détection ; trop haut,
déclenchements intempestifs. Partir de 80 et ajuster par pas de 10.

## 6. Schéma d'ensemble

```
                       ┌──────────────────────┐
                       │      ESP32-S3        │
                       │      DevKitC-1       │
                       └──┬────┬────┬────┬────┘
             GPIO 18/17 ──┘    │    │    └── GPIO 4/5/6/7/15/16
                  UART+PWM     │    │              STEP/DIR/EN/UART/DIAG
                     │      GPIO 8/9│                    │
                     │        I2C   │                    │
              ┌──────┴─────┐  ┌─────┴────┐        ┌──────┴─────┐
              │   LD19     │  │ MPU6050  │        │  TMC2209   │
              │ (tournant) │  │  (fixe)  │        │            │
              └────────────┘  └──────────┘        └──────┬─────┘
                                                         │
                                                   ┌─────┴─────┐
                                                   │  NEMA 17  │
                                                   └───────────┘
```

## 7. Contrôle avant première mise sous tension

- [ ] Continuité des masses entre tous les modules
- [ ] Sortie du trigger PD mesurée à 12 V ± 0,5 V, **avant** de la relier
- [ ] Sortie du buck mesurée à 5 V ± 0,2 V, **avant** de la relier
- [ ] MPU6050 alimenté en 3,3 V, pas en 5 V
- [ ] LD19 TX bien vers ESP32 **RX** (erreur la plus fréquente)
- [ ] Résistance de 1 kΩ en place sur la ligne TX du TMC2209
- [ ] Courant du TMC2209 réglé bas avant le premier mouvement
- [ ] Câble du LiDAR avec du mou, libre sur ±90°
- [ ] Rien ne frotte lorsqu'on fait tourner la tête à la main

Premier démarrage : brancher **sans le moteur**, vérifier que le LD19 émet et
que le Wi-Fi monte, puis seulement connecter le moteur.
