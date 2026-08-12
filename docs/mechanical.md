# Conception mécanique

## Principe

Le LiDAR LD19 effectue un balayage azimutal continu (360°). La nacelle complète (LiDAR + MPU6050) pivote sur un axe vertical (élévation $\phi$) guidé par un roulement 608ZZ.

```
        Trépied 1/4"-20
              │
         ┌────┴────┐
         │  Base   │  ← pièce 3D + insert laiton
         └────┬────┘
              │ axe vertical (608ZZ)
         ┌────┴────┐
         │ Nacelle │  ← LD19 + IMU
         │  LD19   │
         └─────────┘
              ▲
         NEMA 17 (entraînement φ)
```

## Pièces à concevoir (STL)

| Pièce | Fonction |
|-------|----------|
| `base_tripod.stl` | Interface trépied 1/4"-20, support roulement inférieur |
| `vertical_axis.stl` | Arbre vertical, porte-roulement 608ZZ |
| `gimbal_arm.stl` | Bras porteur LiDAR + IMU |
| `motor_mount.stl` | Fixation NEMA 17, courroie ou direct drive |
| `lid.stl` | Capot câbles (optionnel) |

Placer les fichiers dans `mechanical/stl/` une fois modélisés.

## Inserts laiton 1/4"-20

- Perçage : Ø 6.35 mm (1/4")
- Profondeur : selon insert (typ. 6–8 mm)
- Installation à chaud (fer à souder 200–250 °C)
- Filetage trépied : 1/4"-20 UNC standard

## Roulement 608ZZ

- Alésage : Ø 22 mm (outer)
- Arbre : Ø 8 mm (inner)
- Précharge légère pour limiter le jeu radial (impact sur la précision Z)

## NEMA 17 — transmission

Options :

1. **Direct drive** : arbre moteur = axe vertical (simple, backlash faible si précharge)
2. **Courroie GT2** : rapport 1:1 ou 1:2 pour couple / résolution

Objectif : incrément vertical ≤ 0.5° par step (micro-pas 1/16).

## Rigidité

- Minimiser la distance entre centre optique LD19 et axe de rotation
- IMU collée sur la nacelle, proche du LD19 (même corps rigide)
- Éviter câbles en traction pendant le balayage

## Checklist impression 3D

- [ ] PETG ou ABS (rigidité > PLA)
- [ ] Parois ≥ 1.2 mm sur zones de fixation
- [ ] Tolérances alésages testées (roulement, inserts)
- [ ] Passages de câbles prévus (LD19, I2C, moteur)
