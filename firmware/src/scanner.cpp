#include "scanner.h"

#include <TMCStepper.h>
#include <esp_timer.h>

#include "config.h"

namespace {

HardwareSerial tmc_serial(2);
TMC2209Stepper driver(&tmc_serial, 0.11f, TMC_ADDRESS);

volatile int32_t position_steps = 0;
volatile ScanState state = ScanState::Idle;
volatile bool stop_requested = false;

int32_t target_steps = 0;
uint32_t step_interval_us = 0;
uint64_t next_step_us = 0;

uint16_t i_scan_ma = CURRENT_SCAN_MA;
uint16_t i_home_ma = CURRENT_HOMING_MA;
uint16_t sg_threshold = STALLGUARD_THRESHOLD;
uint8_t tmc_version = 0;
bool tmc_ok = false;
volatile bool homed_ok = false;

inline void pulse() {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(3);
    digitalWrite(STEP_PIN, LOW);
}

uint32_t intervalFor(float deg_per_s) {
    const float steps_per_s = deg_per_s * STEPS_PER_DEGREE;
    return static_cast<uint32_t>(1e6f / steps_per_s);
}

// TMC2209 : DIAG serait actif si SG_RESULT ≤ 2 × SGTHRS. Même critère en UART.
bool stallViaUart() {
    const uint32_t sg = driver.SG_RESULT();
    if (sg > 1023) return false;
    return sg <= static_cast<uint32_t>(sg_threshold) * 2;
}

}  // namespace

void scannerInit() {
    pinMode(STEP_PIN, OUTPUT);
    pinMode(DIR_PIN, OUTPUT);
    pinMode(EN_PIN, OUTPUT);
    digitalWrite(EN_PIN, HIGH);

    tmc_serial.begin(115200, SERIAL_8N1, TMC_RX_PIN, TMC_TX_PIN);
    driver.begin();
    driver.toff(4);
    driver.blank_time(24);
    driver.rms_current(i_scan_ma);
    driver.microsteps(MICROSTEPS);
    driver.en_spreadCycle(false);
    driver.pwm_autoscale(true);
    driver.TCOOLTHRS(0xFFFFF);
    driver.SGTHRS(sg_threshold);

    digitalWrite(EN_PIN, LOW);
    state = ScanState::Idle;
    tmc_version = driver.version();
    tmc_ok = (tmc_version != 0 && tmc_version != 0xFF);
    Serial.printf("[scanner] TMC2209 version 0x%02X\n", tmc_version);
}

void scannerApplySettings(const ScanSettings& s) {
    i_scan_ma = s.current_scan_ma;
    i_home_ma = s.current_homing_ma;
    sg_threshold = s.stallguard;
    driver.rms_current(i_scan_ma);
    driver.SGTHRS(sg_threshold);
}

void scannerEnable() {
    digitalWrite(EN_PIN, LOW);
    if (state == ScanState::Fault) state = ScanState::Idle;
}

bool scannerHome() {
    stop_requested = false;
    state = ScanState::Homing;
    digitalWrite(EN_PIN, LOW);
    if (!scannerTmcOk()) {
        state = ScanState::Fault;
        homed_ok = false;
        Serial.println("[scanner] ÉCHEC du homing : TMC2209 absent (UART PDN)");
        return false;
    }
    driver.rms_current(i_home_ma);
    driver.SGTHRS(sg_threshold);

    digitalWrite(DIR_PIN, LOW);
    const uint32_t interval = intervalFor(HOMING_SPEED_DEG_S);
    const int32_t max_steps = STEPS_PER_REV + STEPS_PER_REV / 4;
    const int32_t settle = static_cast<int32_t>(STEPS_PER_DEGREE * 5);

    for (int32_t i = 0; i < max_steps; i++) {
        if (stop_requested) {
            state = ScanState::Idle;
            driver.rms_current(i_scan_ma);
            Serial.println("[scanner] homing interrompu");
            return false;
        }
        pulse();
        delayMicroseconds(interval);
        if (i > settle && (i % 4) == 0 && stallViaUart()) {
            delay(50);
            digitalWrite(DIR_PIN, HIGH);
            for (int32_t k = 0; k < static_cast<int32_t>(STEPS_PER_DEGREE * 2); k++) {
                pulse();
                delayMicroseconds(interval);
            }
            position_steps = 0;
            driver.rms_current(i_scan_ma);
            state = ScanState::Idle;
            homed_ok = true;
            Serial.printf("[scanner] butée trouvée après %d pas\n", i);
            return true;
        }
    }

    driver.rms_current(i_scan_ma);
    state = ScanState::Fault;
    homed_ok = false;
    Serial.println("[scanner] ÉCHEC du homing : aucun contact détecté");
    return false;
}

void scannerStartSweep() {
    const ScanSettings& s = settings();
    stop_requested = false;
    target_steps = static_cast<int32_t>(s.scan_end_deg * STEPS_PER_DEGREE);
    step_interval_us = intervalFor(s.scan_speed_deg_s);
    next_step_us = esp_timer_get_time();
    digitalWrite(EN_PIN, LOW);
    digitalWrite(DIR_PIN, HIGH);
    driver.rms_current(i_scan_ma);
    state = ScanState::Scanning;
    Serial.printf("[scanner] balayage : %d pas, %.1f deg/s jusqu'à %.0f deg\n",
                  target_steps, s.scan_speed_deg_s, s.scan_end_deg);
}

void scannerRequestStop() { stop_requested = true; }

void scannerTick() {
    if (state != ScanState::Scanning) return;

    const uint64_t now = esp_timer_get_time();
    if (now < next_step_us) return;

    if (stop_requested || position_steps >= target_steps) {
        state = ScanState::Done;
        Serial.println(stop_requested ? "[scanner] balayage arrêté"
                                      : "[scanner] balayage terminé");
        return;
    }

    pulse();
    position_steps++;
    next_step_us += step_interval_us;

    if (now > next_step_us + step_interval_us) next_step_us = now + step_interval_us;
}

void scannerEmergencyStop() {
    stop_requested = true;
    digitalWrite(EN_PIN, HIGH);
    homed_ok = false;
    if (state == ScanState::Scanning || state == ScanState::Homing ||
        state == ScanState::Spinup)
        state = ScanState::Fault;
    Serial.println("[scanner] arrêt d'urgence : moteur désactivé");
}

int16_t scannerSgResult() {
    // SG_RESULT est un registre 10 bits ; une valeur aberrante signale
    // souvent une UART muette plutôt qu'une charge réelle.
    const uint32_t raw = driver.SG_RESULT();
    if (raw > 1023) return -1;
    return static_cast<int16_t>(raw);
}

bool scannerTmcOk() {
    if (!tmc_ok) return false;
    const uint8_t v = driver.version();
    return v != 0 && v != 0xFF;
}

uint8_t scannerTmcVersion() { return tmc_version; }

bool scannerMotorEnabled() { return digitalRead(EN_PIN) == LOW; }

bool scannerHomedOk() { return homed_ok; }

int32_t scannerPsiMdeg() {
    return static_cast<int32_t>(position_steps * 1000.0f / STEPS_PER_DEGREE);
}

ScanState scannerState() { return state; }

void scannerSetState(ScanState s) { state = s; }
