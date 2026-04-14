HEX_POSITIONS = [
    (0, -2), (1, -2), (2, -2),      # Row 0: 3 hex
    (-1, -1), (0, -1), (1, -1), (2, -1),  # Row 1: 4
    (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),  # Row 2: 5
    (-2, 1), (-1, 1), (0, 1), (1, 1),   # Row 3: 4
    (-2, 2), (-1, 2), (0, 2)     # Row 4: 3
]

PORTS = [

    ( (0, -4), (2, -4) ),     # generic 3:1
    ( (-2, -2), (0, -2) ),    # wood 2:1
    
    ( (4, -2), (3, -1) ),     # sheep 2:1
    
    ( (4, 2), (2, 2) ),       # brick 2:1
    ( (2, 4), (0, 4) ),       # generic 3:1
    
    ( (-2, 4), (-4, 2) ),     # ore 2:1
    
    ( (-4, 0), (-3, 1) ),     # wheat 2:1
    
    ( (-4, -2), (-2, -2) ),   # generic 3:1
    ( (-2, -4), (0, -4) ),    # generic 3:1
]

# (clockwise, flat-top)
CORNER_FRAC_OFFSETS = [
    (1.0, -0.5),   # Coin 0
    (0.5, -1.0),   # 1
    (-0.5, -0.5),  # 2
    (-1.0, 0.5),   # 3
    (-0.5, 1.0),   # 4
    (0.5, 0.5)     # 5
]

def get_corners(q, r):
    """Return 6 shared vertex keys for a flat-top axial hex at (q, r).

    Keys are integer tuples (vq, vr) that convert to screen pixels via:
        x = vq * HEX_RADIUS / 2 + OFFSET_X
        y = vr * HEX_RADIUS * sqrt(3) / 2 + OFFSET_Y

    Adjacent hexes share the EXACT same key for every shared corner,
    guaranteeing roads and buildings render at the correct hex-edge positions.
    Corner order matches _compute_hex_points() angle order (60*i, flat-top).
    """
    s = q + 2 * r
    return [
        (3*q + 2, s),      # i=0: East  (right tip, 0 deg)
        (3*q + 1, s + 1),  # i=1: SE               (60 deg)
        (3*q - 1, s + 1),  # i=2: SW              (120 deg)
        (3*q - 2, s),      # i=3: West (left tip, 180 deg)
        (3*q - 1, s - 1),  # i=4: NW              (240 deg)
        (3*q + 1, s - 1),  # i=5: NE              (300 deg)
    ]