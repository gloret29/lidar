#pragma once

#include <Arduino.h>

// ============================================================
//  Commandes de balayage (file FreeRTOS)
//
//  motion_task reste en vie et attend une commande. Plus de
//  « un scan par démarrage » : le même appareil se relance
//  depuis le téléphone après chaque repositionnement.
// ============================================================

enum class ScanCommand : uint8_t {
    Start = 1,
    Stop = 2,
    Rehome = 3,
    EStop = 4,
};

void controlInit();
bool controlSend(ScanCommand cmd);

/// Bloquant : attend la prochaine commande (utilisé par motion_task).
ScanCommand controlWait();

/// Non bloquant : commande en attente, ou 0 si la file est vide.
bool controlTryRecv(ScanCommand& out);
