# Description du projet : Scanner 3D LiDAR DIY (3D Point Cloud Generator)

> Document de référence pour le contexte IA (LLM, assistant de code, agent autonome).

## Objectif du projet

Concevoir et fabriquer un scanner 3D d'intérieur mobile, autonome et à bas coût, montable sur trépied photo standard, capable de générer un nuage de points 3D $(X, Y, Z)$ géoréférencé d'une pièce ou d'un bâtiment pour de la numérisation d'intérieur.

## Architecture Matérielle (Hardware Stack)

### Unité de mesure optique (Axe X/Y — Azimut)

- **Capteur** : LiDAR 2D DToF LDRobot LD19 (ou D500)
- **Spécifications** : portée 12 m, 4 500 points/s, balayage horizontal 360°, UART 3.3 V @ 230 400 baud

### Unité de balayage vertical (Axe Z — Élévation)

- **Actuateur** : NEMA 17 (17HS4401)
- **Contrôleur** : TMC2209 (micro-pas, StealthChop2)
- **Guidage** : roulement 608ZZ sur axe vertical

### Calcul embarqué & télémétrie

- **MCU** : ESP32-S3 DevKitC-1 (N16R8 : 16 Mo Flash / 8 Mo PSRAM)
- **IMU** : MPU6050 (I2C) sur la nacelle mobile — mesure du pitch réel
- **Châssis** : pièces 3D + inserts laiton 1/4"-20 UNC (trépied photo)

### Alimentation

- **Source** : power bank USB-C PD (UGREEN Nexode 100 W)
- **Distribution** :
  - Trigger PD → 12 V DC (moteur + TMC2209)
  - Buck 12 V → 5 V / 3 A (ESP32-S3 + LiDAR)

## Architecture Logicielle & Pipeline

### Firmware ESP32-S3 (C++ / FreeRTOS)

| Task | Rôle |
|------|------|
| **LiDAR** | Parsing UART LD19 (paquets 12 points : distance $\rho$, angle $\theta$) |
| **Cinématique & IMU** | Pilotage NEMA 17 ($\phi$) + lecture pitch MPU6050 |
| **Transform** | Conversion cartésienne (voir ci-dessous) |
| **Network** | Streaming $(X, Y, Z)$ via WiFi (UDP / WebSocket) ; config WiFi via **WiFiManager** (portail captif) |

**Conversion trigonométrique** :

$$
X = \rho \cdot \cos(\phi) \cdot \cos(\theta)
$$

$$
Y = \rho \cdot \cos(\phi) \cdot \sin(\theta)
$$

$$
Z = \rho \cdot \sin(\phi)
$$

### Traitement PC / serveur hôte

- **Réception & filtrage** : bruit, outliers (Open3D / PCL)
- **Visualisation** : CloudCompare, RViz2, ou viewer Open3D temps réel
- **Reconstruction** : mesh Poisson, export `.PCD` / `.PLY` (CAO / BIM)

## Contraintes de conception

1. Synchroniser chaque point $(\rho, \theta)$ avec l'angle $\phi$ et un timestamp au moment de l'acquisition.
2. Corriger le pitch mécanique via IMU (calibration statique au démarrage).
3. Bufferiser en PSRAM si le débit WiFi est insuffisant (~54 Ko/s brut).
4. Origine géoréférencée = position du scanner sur trépied ; axe Z aligné sur la gravité.

## État d'avancement

| Composant | Statut |
|-----------|--------|
| Documentation | En place |
| Firmware (squelette) | En place |
| Host Python (squelette) | En place |
| Mécanique (STL) | À concevoir |
| Calibration | À valider sur banc |
