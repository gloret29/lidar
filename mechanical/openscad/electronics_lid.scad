// ============================================================
//  05 — Couvercle du boîtier électronique
//  Impression : à plat, sans support.
// ============================================================

include <lib.scad>

box_ox = box_ix + 2 * box_wall;
box_oy = box_iy + 2 * box_wall;
lid_t = 3;

module electronics_lid() {
    difference() {
        union() {
            translate([-box_ox / 2, -box_oy / 2, 0]) cube([box_ox, box_oy, lid_t]);
            // lèvre de centrage
            translate([-box_ix / 2 + 0.3, -box_iy / 2 + 0.3, -2.5])
                cube([box_ix - 0.6, box_iy - 0.6, 2.5]);
        }
        // dégagement des colonnettes (positions identiques au boîtier)
        for (x = [-1, 1], y = [-1, 1])
            translate([x * (box_ix / 2 - 4), y * (box_iy / 2 - 4), -3]) {
                cylinder(d = 10, h = 2.6);
                translate([0, 0, 2.5]) cylinder(d = m3_clear, h = lid_t + 1);
                translate([0, 0, 2.5 + lid_t - 2]) cylinder(d = m3_head_d, h = 2.5);
            }
        // aération
        for (x = [-2:2], y = [-1, 1])
            translate([x * 16, y * 22, -3]) slot(d = 5, len = 14, h = lid_t + 6);
        // fenêtre LED d'état
        translate([box_ox / 2 - 16, -box_oy / 2 + 12, -3]) cylinder(d = 6, h = lid_t + 6);
    }
}

electronics_lid();
