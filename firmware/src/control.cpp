#include "control.h"

namespace {

QueueHandle_t cmd_queue = nullptr;

}  // namespace

void controlInit() {
    cmd_queue = xQueueCreate(4, sizeof(ScanCommand));
}

bool controlSend(ScanCommand cmd) {
    if (!cmd_queue) return false;
    // Une commande d'urgence passe toujours : on vide les autres.
    if (cmd == ScanCommand::EStop || cmd == ScanCommand::Stop) {
        xQueueReset(cmd_queue);
    }
    return xQueueSend(cmd_queue, &cmd, 0) == pdTRUE;
}

ScanCommand controlWait() {
    ScanCommand cmd = ScanCommand::Start;
    xQueueReceive(cmd_queue, &cmd, portMAX_DELAY);
    return cmd;
}

bool controlTryRecv(ScanCommand& out) {
    return cmd_queue && xQueueReceive(cmd_queue, &out, 0) == pdTRUE;
}
