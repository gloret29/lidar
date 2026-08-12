#include "scanner.h"

#include <TMCStepper.h>
#include <esp_timer.h>

#include "config.h"

namespace {

HardwareSerial tmc_serial(2);
TMC2209Stepper driver(&tmc_serial, 0.11f, TMC_ADDRESS);

volatile int32_t position_steps = 0;   // 0 = butée mécanique
volatile ScanState state = ScanState::Idle;

int32_t target_steps = 0;
uint32_t step_interval_us = 0;
uint64_t next_step_us = 0;

inline void pulse() {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(3);
    digitalWrite(STEP_PIN, LOW);
}

uint32_t intervalFor(float deg_per_s) {
    const float steps_per_s = deg_per_s * STEPS_PER_DEGREE;
    return static_cast<uint32_t>(1e6f / steps_per_s);
}

}  // namespace

void scannerInit() {
    pinMode(STEP_PIN, OUTPUT);
    pinMode(DIR_PIN, OUTPUT);
    pinMode(EN_PIN, OUTPUT);
    pinMode(TMC_DIAG_PIN, INPUT);
    digitalWrite(EN_PIN, HIGH);  // driver désactivé au démarrage

    tmc_serial.begin(115200, SERIAL_8N1, TMC_RX_PIN, TMC_TX_PIN);
    driver.begin();
    driver.toff(4);
    driver.blank_time(24);
    driver.rms_current(CURRENT_SCAN_MA);
    driver.microsteps(MICROSTEPS);
    driver.en_spreadCycle(false);  // StealthChop2 : indispensable, un
                                   // balayage vibrant ruine la mesure optique
    driver.pwm_autoscale(true);
    driver.TCOOLTHRS(0xFFFFF);
    driver.SGTHRS(STALLGUARD_THRESHOLD);

    digitalWrite(EN_PIN, LOW);
    Serial.printf("[scanner] TMC2209 version 0x%02X\n", driver.version());
}

bool scannerHome() {
    state = ScanState::Homing;
    driver.rms_current(CURRENT_HOMING_MA);

    digitalWrite(DIR_PIN, LOW);
    const uint32_t interval = intervalFor(HOMING_SPEED_DEG_S);
    const int32_t max_steps = STEPS_PER_REV + STEPS_PER_REV / 4;

    // StallGuard exige une vitesse établie : on ignore les premiers pas.
    const int32_t settle = static_cast<int32_t>(STEPS_PER_DEGREE * 5);

    for (int32_t i = 0; i < max_steps; i++) {
        pulse();
        delayMicroseconds(interval);
        if (i > settle && digitalRead(TMC_DIAG_PIN) == HIGH) {
            delay(50);
            // On recule légèrement pour libérer la butée.
            digitalWrite(DIR_PIN, HIGH);
            for (int32_t k = 0; k < static_cast<int32_t>(STEPS_PER_DEGREE * 2); k++) {
                pulse();
                delayMicroseconds(interval);
            }
            position_steps = 0;
            driver.rms_current(CURRENT_SCAN_MA);
            Serial.printf("[scanner] butée trouvée après %d pas\n", i);
            return true;
        }
    }

    driver.rms_current(CURRENT_SCAN_MA);
    state = ScanState::Fault;
    Serial.println("[scanner] ÉCHEC du homing : aucun contact détecté");
    return false;
}

void scannerStartSweep() {
    target_steps = static_cast<int32_t>(SCAN_END_DEG * STEPS_PER_DEGREE);
    step_interval_us = intervalFor(SCAN_SPEED_DEG_S);
    next_step_us = esp_timer_get_time();
    digitalWrite(DIR_PIN, HIGH);
    state = ScanState::Scanning;
    Serial.printf("[scanner] balayage : %d pas, %.1f deg/s\n", target_steps,
                  SCAN_SPEED_DEG_S);
}

void scannerTick() {
    if (state != ScanState::Scanning) return;

    const uint64_t now = esp_timer_get_time();
    if (now < next_step_us) return;

    if (position_steps >= target_steps) {
        state = ScanState::Done;
        Serial.println("[scanner] balayage terminé");
        return;
    }

    pulse();
    position_steps++;
    next_step_us += step_interval_us;

    // Rattrapage si l'ordonnanceur nous a mis en retard.
    if (now > next_step_us + step_interval_us) next_step_us = now + step_interval_us;
}

void scannerEmergencyStop() {
    digitalWrite(EN_PIN, HIGH);  // driver désactivé, moteur non alimenté
    if (state == ScanState::Scanning || state == ScanState::Homing ||
        state == ScanState::Spinup)
        state = ScanState::Fault;
    Serial.println("[scanner] arrêt d'urgence : moteur désactivé");
}

int32_t scannerPsiMdeg() {
    const int32_t steps = position_steps;
    return static_cast<int32_t>(steps * 1000.0f / STEPS_PER_DEGREE);
}

ScanState scannerState() { return state; }

void scannerSetState(ScanState s) { state = s; }
