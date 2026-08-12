#pragma once

#include <stdint.h>

// ============================================================
//  Protocole UDP firmware -> station hôte, version 2
//
//  Les points sont transmis en POLAIRE BRUT. La conversion
//  cartésienne est faite côté hôte, ce qui permet de rejouer un
//  scan avec une calibration corrigée sans reflasher ni rescanner.
//  Voir docs/architecture.md.
//
//  Tout est en little-endian.
// ============================================================

#pragma pack(push, 1)

struct PacketHeader {
    uint32_t magic;           // PACKET_MAGIC
    uint16_t version;         // PROTOCOL_VERSION
    uint16_t flags;           // cf. PKT_FLAG_*
    uint32_t sequence;        // incrémental : détection de perte
    uint16_t point_count;
    uint16_t lidar_speed_dhz; // vitesse du LD19 en 0,1 Hz
    uint64_t t_start_us;      // horodatage du premier point
    int32_t psi_start_mdeg;   // azimut moteur au premier point
    int32_t psi_end_mdeg;     // azimut moteur au dernier point
};

struct RawPoint {
    uint16_t rho_mm;     // distance, millimètres
    uint16_t theta_cdeg; // angle interne du LiDAR = ÉLÉVATION, centidegrés
    uint8_t intensity;
    uint8_t reserved;
    uint16_t dt_us;      // décalage depuis t_start_us
};

#pragma pack(pop)

static_assert(sizeof(PacketHeader) == 32, "en-tête de 32 octets attendu");
static_assert(sizeof(RawPoint) == 8, "point de 8 octets attendu");

#define PKT_FLAG_SCAN_START 0x0001
#define PKT_FLAG_SCAN_END 0x0002
#define PKT_FLAG_LEVEL_VALID 0x0004
#define PKT_FLAG_SHOCK_DETECTED 0x0008
