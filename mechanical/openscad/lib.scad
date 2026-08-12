// ============================================================
//  Primitives réutilisables
// ============================================================

include <params.scad>

// Empreinte hexagonale pour écrou (entreplat = af)
module nut_pocket(af = m3_nut_af, h = m3_nut_h, slot = 0) {
    d = af / cos(30);
    union() {
        cylinder(d = d, h = h, $fn = 6);
        // couloir d'insertion latéral
        if (slot > 0)
            translate([0, -af / 2, 0]) cube([slot, af, h]);
    }
}

// Trou de passage M3 avec lamage pour tête cylindrique
module m3_counterbore(depth, head_depth = m3_head_h) {
    translate([0, 0, -0.1]) cylinder(d = m3_clear, h = depth + 0.2);
    translate([0, 0, depth - head_depth]) cylinder(d = m3_head_d, h = head_depth + 0.1);
}

// Lumière oblongue (slot) orientée selon X, traversant en Z
module slot(d, len, h) {
    hull() {
        translate([-len / 2, 0, 0]) cylinder(d = d, h = h);
        translate([len / 2, 0, 0]) cylinder(d = d, h = h);
    }
}

// Fenêtre hexagonale auto-portante (sommet vers le haut),
// axe horizontal selon X, à percer dans une paroi.
module hex_window(across, depth) {
    rotate([0, 90, 0]) rotate([0, 0, 90])
        cylinder(d = across / cos(30), h = depth, $fn = 6, center = true);
}

// Congé de raccordement (quart de tore) à la base d'un cylindre
module fillet_ring(r_outer, r_fillet) {
    rotate_extrude()
        translate([r_outer, 0, 0])
            difference() {
                square([r_fillet, r_fillet]);
                translate([r_fillet, r_fillet]) circle(r = r_fillet);
            }
}

// Passe-câble : fente arrondie traversante
module cable_slot(len, width, h) {
    hull() {
        translate([-len / 2, 0, -0.1]) cylinder(d = width, h = h + 0.2);
        translate([len / 2, 0, -0.1]) cylinder(d = width, h = h + 0.2);
    }
}

// Trous pour collier de serrage (rilsan) : deux fentes parallèles
module zip_tie_pair(spacing = 10, w = 4, t = 2.2, h = 10) {
    for (s = [-1, 1])
        translate([s * spacing / 2, 0, -0.1])
            cube([t, w, h + 0.2], center = false);
}
