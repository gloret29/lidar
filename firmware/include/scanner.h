#pragma once

#include <Arduino.h>

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

/// Prise de référence par StallGuard contre la butée mécanique.
/// Renvoie false si aucun contact n'est détecté dans le tour imparti.
bool scannerHome();

/// Démarre un balayage continu de SCAN_START_DEG à SCAN_END_DEG.
void scannerStartSweep();

/// À appeler périodiquement : avance le moteur selon le profil.
void scannerTick();

/// Azimut courant en millidegrés, sûr en lecture concurrente.
int32_t scannerPsiMdeg();

ScanState scannerState();
void scannerSetState(ScanState s);
