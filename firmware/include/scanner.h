#pragma once

#include <Arduino.h>

#include "settings.h"

// ============================================================
//  Axe de lacet : pilotage du NEMA 17 via TMC2209
// ============================================================

enum class ScanState : uint8_t {
    Idle,
    Levelling,
    Homing,
    Spinup,
    Scanning,
    Done,
    Fault,
};

void scannerInit();

/// Applique courants et seuil StallGuard depuis les réglages.
void scannerApplySettings(const ScanSettings& s);

/// Réactive le driver après un arrêt d'urgence.
void scannerEnable();

/// Prise de référence par StallGuard contre la butée mécanique.
bool scannerHome();

/// Démarre un balayage continu selon les réglages courants.
void scannerStartSweep();

/// Demande l'arrêt en fin de pas courant (balayage uniquement).
void scannerRequestStop();

/// À appeler périodiquement : avance le moteur selon le profil.
void scannerTick();

/// Coupe l'alimentation du moteur et abandonne le mouvement en cours.
void scannerEmergencyStop();

/// Lecture StallGuard (0..511 typique). -1 si le driver ne répond pas.
int16_t scannerSgResult();

/// true si le TMC2209 répond sur UART (version valide).
bool scannerTmcOk();

/// Version du driver lue à l'initialisation (0 si absent).
uint8_t scannerTmcVersion();

/// true si la broche EN est active (moteur alimenté).
bool scannerMotorEnabled();

int32_t scannerPsiMdeg();
ScanState scannerState();
void scannerSetState(ScanState s);
