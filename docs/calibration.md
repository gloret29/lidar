# Calibration

## 1. IMU (MPU6050) — offset statique

Au démarrage, le scanner est posé sur trépied, immobile :

1. Échantillonner 500–1000 mesures gyro + accel
2. Calculer offset gyro (moyenne)
3. Calculer pitch/roll de référence depuis l'accéléromètre (niveau à bulle virtuel)
4. Stocker les offsets en NVS (flash ESP32)

```cpp
// Pseudo-code
pitch_offset = mean(accel_to_pitch(samples));
gyro_z_offset = mean(gyro_z_samples);
```

Pendant le scan, $\phi_{\text{effective}} = \phi_{\text{stepper}} + (pitch_{\text{live}} - pitch_{\text{offset}})$.

## 2. Stepper — steps par degré

1. Compter les steps pour un tour complet (360°) ou utiliser la réduction mécanique
2. Mesurer l'angle réel avec inclinomètre ou rapport connu (ex. 1:1 direct drive)

```
steps_per_degree = total_steps / measured_degrees
```

Ajuster dans `config.h` : `STEPS_PER_DEGREE`.

## 3. LiDAR — offset azimut

Le zéro mécanique du LD19 peut ne pas coïncider avec le repère du châssis :

1. Placer une cible à distance connue, face à une marque de référence sur le châssis
2. Noter l'angle $\theta_{\text{raw}}$ reporté par le LD19
3. `theta_offset = theta_reference - theta_raw`

## 4. Géoréférencement

Repère scanner (convention proposée) :

| Axe | Direction |
|-----|-----------|
| +X | Avant du châssis (ou marque blanche) |
| +Y | Gauche |
| +Z | Haut (opposé à la gravité) |

**Origine** : centre optique du LD19 au démarrage du scan.

Procédure :

1. Niveler le trépied (IMU : pitch/roll < 0.5°)
2. Définir l'azimut de référence (marque ou bouton « set heading »)
3. Enregistrer la pose initiale dans le fichier `.PCD` (metadata)

## 5. Validation

| Test | Critère |
|------|---------|
| Mur plat à 2 m | Nuage forme un plan (épaisseur < 2 cm) |
| Coin de pièce | Angle 90° ± 1° |
| Hauteur plafond | Z cohérent avec mètre ruban ± 5 cm |
| Scan complet | Pas de bandes manquantes (sync φ/θ) |

## 6. Filtrage hôte (post-traitement)

Paramètres Open3D de départ :

- **Statistical outlier removal** : `nb_neighbors=20`, `std_ratio=2.0`
- **Voxel downsample** : `voxel_size=0.01` (1 cm) pour preview
- **Poisson mesh** : `depth=8` pour reconstruction surface
