#pragma once

#include <Arduino.h>

// ============================================================
//  Analyseur de trames LD19
//
//  Format d'une trame (47 octets, little-endian) :
//    0      en-tête       0x54
//    1      VerLen        0x2C  (5 bits de poids faible = 12 points)
//    2-3    vitesse       deg/s
//    4-5    angle début   0,01 deg
//    6-41   12 x { distance uint16 mm, intensité uint8 }
//    42-43  angle fin     0,01 deg
//    44-45  horodatage    ms
//    46     CRC8          polynôme 0x4D
// ============================================================

#define LD19_FRAME_LEN 47
#define LD19_POINTS_PER_FRAME 12

struct Ld19Point {
    uint16_t distance_mm;
    uint16_t angle_cdeg;  // 0..35999
    uint8_t intensity;
};

struct Ld19Frame {
    uint16_t speed_dps;
    uint16_t timestamp_ms;
    Ld19Point points[LD19_POINTS_PER_FRAME];
};

class Ld19Parser {
public:
    void begin();

    /// Consomme un octet. Renvoie true quand une trame valide est complète.
    bool feed(uint8_t byte, Ld19Frame &out);

    uint32_t framesOk() const { return frames_ok_; }
    uint32_t framesBad() const { return frames_bad_; }

private:
    uint8_t buf_[LD19_FRAME_LEN];
    size_t len_ = 0;
    uint32_t frames_ok_ = 0;
    uint32_t frames_bad_ = 0;

    void decode(Ld19Frame &out) const;
};

/// Règle la vitesse de rotation via la broche PWM (5 à 13 Hz).
void ld19SetSpeed(float hz);
