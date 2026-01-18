HEX_POSITIONS = [
    (0, -2), (1, -2), (2, -2),      # Row 0: 3 hex
    (-1, -1), (0, -1), (1, -1), (2, -1),  # Row 1: 4
    (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),  # Row 2: 5
    (-2, 1), (-1, 1), (0, 1), (1, 1),   # Row 3: 4
    (-2, 2), (-1, 2), (0, 2)     # Row 4: 3
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
    """
    Retourne 6 vertices en coordonnées entières (q×2, r×2 style)
    Compatible avec layout axial flat-top standard Catan
    """
    # Multiplie par 2 pour avoir des entiers et forcer partage
    qq = q * 2
    rr = r * 2
    
    return [
        (qq + 2, rr + 0),     # NE
        (qq + 1, rr - 1),     # E
        (qq    , rr - 2),     # SE
        (qq - 2, rr    ),     # SW
        (qq - 1, rr + 1),     # W
        (qq    , rr + 2),     # NW
    ]