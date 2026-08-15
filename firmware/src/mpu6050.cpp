#include "mpu6050.h"

#include <Wire.h>
#include <math.h>

#include "config.h"

namespace {

constexpr uint8_t kRegSmplrtDiv = 0x19;
constexpr uint8_t kRegConfig = 0x1A;
constexpr uint8_t kRegAccelConfig = 0x1C;
constexpr uint8_t kRegAccelXoutH = 0x3B;
constexpr uint8_t kRegPwrMgmt1 = 0x6B;
constexpr uint8_t kRegWhoAmI = 0x75;
constexpr uint8_t kWhoAmIExpected = 0x68;

// ±2 g : 16 384 LSB/g
constexpr float kLsbPerG = 16384.0f;

bool ready_ = false;
float level_ref_[3] = {0.0f, 0.0f, -1.0f};
bool has_level_ref_ = false;
bool shock_flag_ = false;

bool writeReg(uint8_t reg, uint8_t val) {
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(reg);
    Wire.write(val);
    return Wire.endTransmission() == 0;
}

bool readBytes(uint8_t reg, uint8_t *buf, size_t len) {
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(reg);
    if (Wire.endTransmission(false) != 0) return false;
    if (Wire.requestFrom(static_cast<uint8_t>(MPU6050_ADDR), len) != len)
        return false;
    for (size_t i = 0; i < len; i++) buf[i] = Wire.read();
    return true;
}

bool readRaw(int16_t &ax, int16_t &ay, int16_t &az) {
    uint8_t buf[6];
    if (!readBytes(kRegAccelXoutH, buf, 6)) return false;
    ax = static_cast<int16_t>((buf[0] << 8) | buf[1]);
    ay = static_cast<int16_t>((buf[2] << 8) | buf[3]);
    az = static_cast<int16_t>((buf[4] << 8) | buf[5]);
    return true;
}

void rawToG(int16_t ax, int16_t ay, int16_t az, float g[3]) {
    g[0] = ax / kLsbPerG;
    g[1] = ay / kLsbPerG;
    g[2] = az / kLsbPerG;
}

float vectorNorm(const float v[3]) {
    return sqrtf(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
}

void normalize(float v[3]) {
    const float n = vectorNorm(v);
    if (n < 1e-6f) return;
    v[0] /= n;
    v[1] /= n;
    v[2] /= n;
}

bool readAvg(float g[3], uint16_t samples, uint32_t period_ms,
             bool (*abort_fn)()) {
    double sx = 0.0, sy = 0.0, sz = 0.0;
    for (uint16_t i = 0; i < samples; i++) {
        if (abort_fn && abort_fn()) return false;

        int16_t ax, ay, az;
        if (!readRaw(ax, ay, az)) return false;

        sx += ax / kLsbPerG;
        sy += ay / kLsbPerG;
        sz += az / kLsbPerG;

        if (period_ms > 0 && i + 1 < samples) delay(period_ms);
    }

    g[0] = static_cast<float>(sx / samples);
    g[1] = static_cast<float>(sy / samples);
    g[2] = static_cast<float>(sz / samples);
    return true;
}

bool isStableBatch(uint16_t samples, uint32_t period_ms, bool (*abort_fn)()) {
    float buf[MPU6050_STABLE_CHECK_SAMPLES][3];
    if (samples > MPU6050_STABLE_CHECK_SAMPLES) samples = MPU6050_STABLE_CHECK_SAMPLES;

    float mean[3] = {0.0f, 0.0f, 0.0f};
    for (uint16_t i = 0; i < samples; i++) {
        if (abort_fn && abort_fn()) return false;

        int16_t ax, ay, az;
        if (!readRaw(ax, ay, az)) return false;
        rawToG(ax, ay, az, buf[i]);
        mean[0] += buf[i][0];
        mean[1] += buf[i][1];
        mean[2] += buf[i][2];

        if (period_ms > 0 && i + 1 < samples) delay(period_ms);
    }

    mean[0] /= samples;
    mean[1] /= samples;
    mean[2] /= samples;

    const float mag = vectorNorm(mean);
    if (mag < 0.85f || mag > 1.15f) return false;

    float max_dev = 0.0f;
    for (uint16_t i = 0; i < samples; i++) {
        const float dx = buf[i][0] - mean[0];
        const float dy = buf[i][1] - mean[1];
        const float dz = buf[i][2] - mean[2];
        const float dev = sqrtf(dx * dx + dy * dy + dz * dz);
        if (dev > max_dev) max_dev = dev;
    }

    return max_dev <= MPU6050_STABLE_MAX_DEV_G;
}

}  // namespace

bool mpu6050Init() {
    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    Wire.setClock(400000);

    uint8_t who = 0;
    if (!readBytes(kRegWhoAmI, &who, 1) || who != kWhoAmIExpected) {
        Serial.printf("[mpu6050] absent ou inattendu (WHO_AM_I=0x%02X)\n", who);
        ready_ = false;
        return false;
    }

    if (!writeReg(kRegPwrMgmt1, 0x00)) return false;
    delay(10);
    // DLPF ≈ 44 Hz accel ; SMPLRT_DIV=9 → 100 Hz
    if (!writeReg(kRegConfig, 0x03)) return false;
    if (!writeReg(kRegSmplrtDiv, 9)) return false;
    if (!writeReg(kRegAccelConfig, 0x00)) return false;
    delay(50);

    ready_ = true;
    Serial.println("[mpu6050] initialisé (±2 g, 100 Hz)");
    return true;
}

bool mpu6050Ready() { return ready_; }

bool mpu6050MeasureLevel(float g[3], bool (*abort_fn)()) {
    if (!ready_) return false;

    Serial.println("[mpu6050] nivellement : immobilité requise");

    if (!isStableBatch(MPU6050_STABLE_CHECK_SAMPLES, 1000 / MPU6050_SAMPLE_HZ,
                       abort_fn)) {
        Serial.println("[mpu6050] base instable avant nivellement");
        return false;
    }

    const uint32_t period_ms = 1000 / MPU6050_SAMPLE_HZ;
    double sx = 0.0, sy = 0.0, sz = 0.0;

    for (uint16_t i = 0; i < MPU6050_LEVEL_SAMPLES; i++) {
        if (abort_fn && abort_fn()) {
            Serial.println("[mpu6050] nivellement interrompu");
            return false;
        }

        int16_t ax, ay, az;
        if (!readRaw(ax, ay, az)) {
            Serial.println("[mpu6050] lecture I2C échouée");
            return false;
        }

        sx += ax / kLsbPerG;
        sy += ay / kLsbPerG;
        sz += az / kLsbPerG;

        if ((i + 1) % MPU6050_SAMPLE_HZ == 0) {
            Serial.printf("[mpu6050] nivellement %u/%u s\n",
                          (i + 1) / MPU6050_SAMPLE_HZ,
                          MPU6050_LEVEL_SAMPLES / MPU6050_SAMPLE_HZ);
        }

        if (i + 1 < MPU6050_LEVEL_SAMPLES) delay(period_ms);
    }

    g[0] = static_cast<float>(sx / MPU6050_LEVEL_SAMPLES);
    g[1] = static_cast<float>(sy / MPU6050_LEVEL_SAMPLES);
    g[2] = static_cast<float>(sz / MPU6050_LEVEL_SAMPLES);

    const float mag = vectorNorm(g);
    if (mag < 0.90f || mag > 1.10f) {
        Serial.printf("[mpu6050] |g|=%.3f g hors plage\n", mag);
        return false;
    }

    normalize(g);
    Serial.printf("[mpu6050] g=(%.4f, %.4f, %.4f)\n", g[0], g[1], g[2]);
    return true;
}

float mpu6050TiltDeg(const float ref[3], const float cur[3]) {
    float a[3] = {ref[0], ref[1], ref[2]};
    float b[3] = {cur[0], cur[1], cur[2]};
    normalize(a);
    normalize(b);

    float dot = a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    dot = constrain(dot, -1.0f, 1.0f);
    return acosf(dot) * 57.2957795f;
}

bool mpu6050DetectShock(const float ref[3]) {
    if (!ready_) return false;

    float cur[3];
    if (!mpu6050ReadGravity(cur)) return false;

    return mpu6050TiltDeg(ref, cur) > MPU6050_SHOCK_DEG;
}

bool mpu6050ReadGravity(float g[3]) {
    if (!ready_) return false;
    if (!readAvg(g, 10, 5, nullptr)) return false;
    return true;
}

void mpu6050StoreLevelRef(const float g[3]) {
    level_ref_[0] = g[0];
    level_ref_[1] = g[1];
    level_ref_[2] = g[2];
    has_level_ref_ = true;
}

bool mpu6050HasLevelRef() { return has_level_ref_; }

void mpu6050GetLevelRef(float g[3]) {
    g[0] = level_ref_[0];
    g[1] = level_ref_[1];
    g[2] = level_ref_[2];
}

void mpu6050SetShockFlag(bool v) { shock_flag_ = v; }

bool mpu6050ShockFlag() { return shock_flag_; }
