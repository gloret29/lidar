#include "ld19.h"

#include "config.h"

namespace {

constexpr uint8_t kHeader = 0x54;
constexpr uint8_t kVerLen = 0x2C;

uint8_t crc_table[256];
bool crc_ready = false;

void buildCrcTable() {
    // Polynôme 0x4D, sans réflexion, init 0x00 : spécification LD19.
    for (int i = 0; i < 256; i++) {
        uint8_t crc = static_cast<uint8_t>(i);
        for (int bit = 0; bit < 8; bit++)
            crc = (crc & 0x80) ? static_cast<uint8_t>((crc << 1) ^ 0x4D)
                               : static_cast<uint8_t>(crc << 1);
        crc_table[i] = crc;
    }
    crc_ready = true;
}

uint8_t crc8(const uint8_t *data, size_t len) {
    uint8_t crc = 0;
    for (size_t i = 0; i < len; i++) crc = crc_table[crc ^ data[i]];
    return crc;
}

uint16_t rd16(const uint8_t *p) {
    return static_cast<uint16_t>(p[0]) | static_cast<uint16_t>(p[1] << 8);
}

}  // namespace

void Ld19Parser::begin() {
    if (!crc_ready) buildCrcTable();
    len_ = 0;
}

bool Ld19Parser::feed(uint8_t byte, Ld19Frame &out) {
    if (len_ == 0) {
        if (byte != kHeader) return false;
    } else if (len_ == 1 && byte != kVerLen) {
        // Faux départ : le premier octet pourrait être le vrai en-tête.
        len_ = (byte == kHeader) ? 1 : 0;
        if (len_ == 1) buf_[0] = kHeader;
        return false;
    }

    buf_[len_++] = byte;
    if (len_ < LD19_FRAME_LEN) return false;

    len_ = 0;
    if (crc8(buf_, LD19_FRAME_LEN - 1) != buf_[LD19_FRAME_LEN - 1]) {
        frames_bad_++;
        return false;
    }

    decode(out);
    frames_ok_++;
    return true;
}

void Ld19Parser::decode(Ld19Frame &out) const {
    out.speed_dps = rd16(&buf_[2]);
    const uint16_t start = rd16(&buf_[4]);
    const uint16_t end = rd16(&buf_[42]);
    out.timestamp_ms = rd16(&buf_[44]);

    // L'angle de fin peut avoir franchi 360 deg.
    int32_t span = static_cast<int32_t>(end) - static_cast<int32_t>(start);
    if (span < 0) span += 36000;
    const float step = static_cast<float>(span) / (LD19_POINTS_PER_FRAME - 1);

    for (int i = 0; i < LD19_POINTS_PER_FRAME; i++) {
        const uint8_t *p = &buf_[6 + i * 3];
        int32_t angle = static_cast<int32_t>(start + step * i + 0.5f);
        if (angle >= 36000) angle -= 36000;

        out.points[i].distance_mm = rd16(p);
        out.points[i].intensity = p[2];
        out.points[i].angle_cdeg = static_cast<uint16_t>(angle);
    }
}

void ld19SetSpeed(float hz) {
    // Le LD19 attend un signal carré de 30 kHz ; le rapport cyclique fixe
    // la consigne, asservie en boucle fermée par le capteur lui-même.
    // Broche laissée à la masse => régulation interne à 10 Hz.
    hz = constrain(hz, 5.0f, 13.0f);
    const float duty = constrain((hz - 5.0f) / 8.0f * 0.6f + 0.2f, 0.05f, 0.95f);

    ledcSetup(0, 30000, 8);
    ledcAttachPin(LIDAR_PWM_PIN, 0);
    ledcWrite(0, static_cast<uint32_t>(duty * 255));
}
