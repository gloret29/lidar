// ============================================================
//  Coupon d'essai — empreinte STL-19P
//
//  Platine seule : rebord, 3 × M2,5, fente nappe. Sans moyeu ni voile.
//  Même cotes que lidar_cradle (params.scad). ~20 min, pas de support.
//
//  Impression : telle quelle, rebord vers le haut.
//  Câble / 2 oreilles vers le bord MARQUÉ (fente ouverte).
// ============================================================

include <params.scad>

rim_t = 2.5;
rim_h = 2.5;
margin = 4;

plate_w = lidar_w + 2 * margin;                 // 62
plate_l = lidar_h + rim_t + margin;             // ~52,8
plate_t = 5;  // = cradle_plate_t

// Origine : centre de l'empreinte, bord câble en Y négatif
module test_lidar_fit() {
    difference() {
        union() {
            translate([-plate_w / 2, -lidar_h / 2 - rim_t, 0])
                cube([plate_w, plate_l, plate_t]);
            translate([-(lidar_w / 2 + rim_t), -(lidar_h / 2 + rim_t), plate_t - 1])
                cube([lidar_w + 2 * rim_t, lidar_h + 2 * rim_t, rim_h + 1]);
        }

        // Logement capteur (évide le rebord)
        translate([-(lidar_w / 2 + 0.25), -(lidar_h / 2 + 0.25), plate_t])
            cube([lidar_w + 0.5, lidar_h + 0.5, rim_h + 0.3]);

        // 2 oreilles côté câble (Y = −lidar_h/2)
        y_side = -lidar_h / 2 + lidar_side_hole_z;
        y_top  = -lidar_h / 2 + lidar_top_hole_z;
        for (p = [[-lidar_hole_y, y_side], [lidar_hole_y, y_side], [0, y_top]])
            translate([p[0], p[1], -0.1])
                cylinder(d = lidar_screw_d, h = plate_t + rim_h + 0.4);

        // Fente nappe : ouverte sur le bord câble
        y0 = -lidar_h / 2 - rim_t - 0.1;
        y1 = -lidar_h / 2 + lidar_cable_h;
        translate([-lidar_cable_w / 2, y0, -0.1])
            cube([lidar_cable_w, y1 - y0, plate_t + rim_h + 0.4]);
        translate([0, y1, -0.1])
            cylinder(d = lidar_cable_w, h = plate_t + rim_h + 0.4);
    }
}

test_lidar_fit();
