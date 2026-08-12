// ============================================================
//  01 — Plateau de base
//  Interface trépied 1/4"-20 + support moteur NEMA 17 + embase colonne
//
//  Impression : POSÉ À L'ENVERS (face supérieure sur le plateau),
//  le bossage trépied vers le haut. Aucun support nécessaire.
// ============================================================

include <lib.scad>

module base_plate() {
    difference() {
        union() {
            cylinder(d = plate_d, h = plate_t);
            translate([0, 0, -tripod_boss_h])
                cylinder(d = tripod_boss_d, h = tripod_boss_h);
            // congé de raccordement bossage / plateau
            translate([0, 0, 0]) mirror([0, 0, 1]) fillet_ring(tripod_boss_d / 2, 4);
        }

        // --- Insert laiton 1/4"-20, posé par le dessous ---
        translate([0, 0, -tripod_boss_h - 0.1])
            cylinder(d = insert_qtr_d, h = insert_qtr_l + 0.1);
        // chanfrein d'amorce
        translate([0, 0, -tripod_boss_h - 0.1])
            cylinder(d1 = insert_qtr_d + 1.6, d2 = insert_qtr_d, h = 1.7);

        // --- Dégagement du bossage de centrage moteur ---
        translate([0, 0, plate_t - nema_boss_h - 0.4])
            cylinder(d = nema_boss_d + 1.2, h = nema_boss_h + 1);

        // --- Fixation moteur : 4 x M3 carré 31 mm ---
        // Les vis montent PAR LE DESSOUS et se vissent dans les trous
        // taraudés du NEMA 17. Têtes noyées pour ne pas gêner la
        // semelle du trépied.
        for (x = [-1, 1], y = [-1, 1])
            translate([x * nema_pitch / 2, y * nema_pitch / 2, -0.1]) {
                cylinder(d = m3_clear, h = plate_t + 0.2);
                cylinder(d = m3_head_d + 0.4, h = m3_head_h + 0.6);
            }

        // --- Fixation de la colonne : 4 x M3 ---
        for (i = [0:3])
            rotate([0, 0, 90 * i])
                translate([tower_bolt_circle / 2, 0, -0.1]) {
                    cylinder(d = m3_clear, h = plate_t + 0.2);
                    nut_pocket(h = m3_nut_h + 0.3);
                }

        // --- Passage des câbles (moteur + LiDAR) vers le boîtier ---
        rotate([0, 0, 180])
            translate([36, 0, 0]) cable_slot(len = 18, width = 8, h = plate_t);

        // --- Repère d'azimut zéro gravé sur le pourtour ---
        translate([plate_d / 2 - 6, -1.2, plate_t - 1])
            cube([8, 2.4, 1.2]);
    }
}

base_plate();
