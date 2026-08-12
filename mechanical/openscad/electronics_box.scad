// ============================================================
//  04 — Boîtier électronique  (ESP32-S3, TMC2209, buck, trigger PD)
//
//  Se sangle par colliers rilsan sur la colonne centrale du trépied
//  (berceaux en Ø32 sous le fond). L'électronique reste ainsi au sol :
//  la tête rotative demeure légère et le trépied équilibré.
//
//  Impression : ouverture vers le haut, sans support.
// ============================================================

include <lib.scad>

box_ox = box_ix + 2 * box_wall;
box_oy = box_iy + 2 * box_wall;
box_floor = 3;

// Colonnettes d'angle : volontairement fusionnées aux deux parois
// adjacentes, une colonnette isolée de Ø8 sur 34 mm casserait net.
post_x = box_ix / 2 - 4;
post_y = box_iy / 2 - 4;

module post(x, y) {
    translate([x, y, box_floor]) cylinder(d = 9, h = box_iz);
}

module electronics_box() {
    difference() {
        union() {
            // ---------- Coque ----------
            translate([-box_ox / 2, -box_oy / 2, 0])
                cube([box_ox, box_oy, box_iz + box_floor]);

            // ---------- Berceau de sanglage sur colonne de trépied ----------
            // Le boîtier reste au sol, sur la colonne centrale : la tête
            // rotative demeure légère et le trépied équilibré.
            for (x = [-34, 34])
                translate([x, 0, -6]) {
                    difference() {
                        translate([-7, -box_oy / 2, 0]) cube([14, box_oy, 6.01]);
                        translate([0, 0, -14]) rotate([90, 0, 0])
                            cylinder(d = 32, h = box_oy + 2, center = true);
                    }
                }
        }

        // ---------- Volume intérieur ----------
        translate([-box_ix / 2, -box_iy / 2, box_floor])
            cube([box_ix, box_iy, box_iz + 1]);

        // ---------- Presse-étoupe / passages de câbles ----------
        // câble LiDAR + moteur (côté colonne)
        for (y = [-22, 0, 22])
            translate([-box_ox / 2 - 1, y, box_floor + 14])
                rotate([0, 90, 0]) cylinder(d = 8, h = box_wall + 2);
        // entrée USB-C PD
        translate([box_ox / 2 - 1, 0, box_floor + 10])
            rotate([0, 90, 0]) cylinder(d = 12, h = box_wall + 2);
        // sortie USB-C de programmation ESP32
        translate([box_ox / 2 - 1, 30, box_floor + 10])
            rotate([0, 90, 0]) cylinder(d = 12, h = box_wall + 2);

        // ---------- Ventilation ----------
        for (x = [-3:3], y = [-1, 1])
            translate([x * 12, y * 26, -0.1]) cylinder(d = 5, h = box_floor + 0.2);

        // ---------- Passages rilsan (sanglage trépied) ----------
        for (x = [-34, 34], y = [-1, 1])
            translate([x, y * (box_oy / 2 - 1), box_floor + 6])
                rotate([90, 0, 0]) cube([5, 3, box_wall + 3], center = true);

    }

    // ---------- Colonnettes de couvercle ----------
    for (x = [-1, 1], y = [-1, 1])
        difference() {
            post(x * post_x, y * post_y);
            // avant-trou taraudé par la vis M3
            translate([x * post_x, y * post_y, box_iz + box_floor - 9])
                cylinder(d = 2.6, h = 10);
        }

    // ---------- Rails de montage des modules ----------
    // Grille de bossages M3 : fixation par vis autotaraudeuses ou rilsan.
    for (x = [-40, -14, 14, 40], y = [-20, 20])
        difference() {
            translate([x, y, box_floor]) cylinder(d = 7, h = 4);
            translate([x, y, box_floor + 0.5]) cylinder(d = 2.6, h = 5);
        }
}

electronics_box();
