# Câblage et pinout

## ESP32-S3 DevKitC-1 — assignation des broches

> Valeurs par défaut dans `firmware/include/config.h`. Ajuster selon votre routage PCB / câbles.

| Fonction | GPIO | Notes |
|----------|------|-------|
| LiDAR UART RX | 18 | ESP32 reçoit TX du LD19 |
| LiDAR UART TX | 17 | ESP32 envoie vers RX du LD19 (optionnel) |
| I2C SDA | 8 | MPU6050 |
| I2C SCL | 9 | MPU6050 |
| Stepper STEP | 4 | TMC2209 STEP |
| Stepper DIR | 5 | TMC2209 DIR |
| Stepper EN | 6 | TMC2209 EN (LOW = actif) |

UART LiDAR : **UART1**, 230 400 baud, 3.3 V logique.

## LiDAR LD19

| LD19 | ESP32-S3 |
|------|----------|
| VCC (5 V) | Buck 5 V |
| GND | GND commun |
| TX | GPIO 18 (RX) |
| RX | GPIO 17 (TX) — si commandes requises |

Le LD19 fonctionne en 3.3 V TTL ; alimentation typique 5 V via régulateur onboard.

## MPU6050

| MPU6050 | ESP32-S3 |
|---------|----------|
| VCC | 3.3 V |
| GND | GND |
| SDA | GPIO 8 |
| SCL | GPIO 9 |

Adresse I2C par défaut : `0x68` (AD0 à GND) ou `0x69` (AD0 à VCC).

## TMC2209 + NEMA 17

| TMC2209 | Connexion |
|---------|-----------|
| VM | 12 V (trigger PD) |
| GND | GND commun |
| VIO | 3.3 V (logique ESP32) |
| STEP | GPIO 4 |
| DIR | GPIO 5 |
| EN | GPIO 6 |
| MS1, MS2 | VIO ou GND selon micro-pas désiré |
| Motor A+, A-, B+, B- | NEMA 17 (4 fils) |

### Micro-pas recommandé

- MS1=HIGH, MS2=HIGH → 1/16 micro-step (via UART ou straps)
- StealthChop2 activé pour réduire les vibrations optiques

### Courant moteur

NEMA 17HS4401 : 1.5 A / phase. Régler le potentiomètre Vref du TMC2209 (~0.8–1.0 V selon formule TMC).

## Alimentation

```
Powerbank USB-C PD (100 W)
        │
        ▼
  Trigger PD (12 V)
        ├──► TMC2209 VM (12 V)
        │
        └──► Buck 12 V → 5 V / 3 A
                    ├──► LD19 VCC
                    └──► ESP32-S3 VIN (ou USB si debug seul)
```

**Important** : GND commun entre ESP32, LiDAR, TMC2209 et alimentation.

## Schéma simplifié

```
                    ┌──────────────┐
  PD 12V ──────────►│   TMC2209    │──── NEMA 17
                    └──────────────┘
        │
        └──► Buck 5V ──┬──► LD19
                       └──► ESP32-S3
                              │
                    ┌─────────┼─────────┐
                    │         │         │
                 LD19      MPU6050    (WiFi)
                UART       I2C
```

## Checklist avant mise sous tension

- [ ] Polarité 12 V / 5 V vérifiée
- [ ] GND commun
- [ ] EN TMC2209 câblé (moteur désactivé au boot si EN HIGH)
- [ ] LD19 TX → ESP32 RX (pas inversé)
- [ ] MPU6050 sur 3.3 V (pas 5 V)
- [ ] Vref TMC2209 ajusté avant charge mécanique
