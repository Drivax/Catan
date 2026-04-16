import pygame

from game.board import COLORS, PLAYER_COLORS
from game.map import get_corners
from game.rules import RESOURCES


WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 1000
SIDEBAR_X = 1020
SIDEBAR_Y = 28
SIDEBAR_WIDTH = 380
SIDEBAR_HEIGHT = 944

RESOURCE_STYLES = {
    "wood": {"label": "Wood", "short": "W", "color": (62, 122, 74)},
    "brick": {"label": "Brick", "short": "B", "color": (153, 78, 61)},
    "sheep": {"label": "Sheep", "short": "S", "color": (126, 178, 95)},
    "wheat": {"label": "Wheat", "short": "H", "color": (210, 171, 64)},
    "ore": {"label": "Ore", "short": "O", "color": (104, 110, 126)},
}


def shift_color(color, delta):
    return tuple(max(0, min(255, channel + delta)) for channel in color)


def inset_polygon(points, center, factor):
    cx, cy = center
    return [
        (
            cx + (point[0] - cx) * factor,
            cy + (point[1] - cy) * factor,
        )
        for point in points
    ]


def draw_hex_texture(screen, resource, center):
    cx, cy = int(center[0]), int(center[1])
    accent = {
        "wood": (44, 98, 54),
        "brick": (129, 58, 46),
        "sheep": (101, 146, 74),
        "wheat": (187, 149, 38),
        "ore": (83, 89, 104),
        "desert": (176, 147, 105),
    }.get(resource, (90, 115, 160))

    if resource == "wood":
        for offset in (-16, -6, 4, 14):
            pygame.draw.line(screen, accent, (cx - 24, cy + offset), (cx + 24, cy + offset - 6), 2)
    elif resource == "brick":
        for row in range(3):
            y = cy - 16 + row * 12
            pygame.draw.line(screen, accent, (cx - 24, y), (cx + 24, y), 2)
        for col in (-16, 0, 16):
            pygame.draw.line(screen, accent, (cx + col, cy - 16), (cx + col, cy + 8), 2)
    elif resource == "sheep":
        pygame.draw.circle(screen, accent, (cx - 10, cy - 4), 9, 2)
        pygame.draw.circle(screen, accent, (cx + 2, cy - 6), 9, 2)
        pygame.draw.circle(screen, accent, (cx + 13, cy - 2), 9, 2)
    elif resource == "wheat":
        pygame.draw.line(screen, accent, (cx - 4, cy + 14), (cx - 4, cy - 16), 2)
        pygame.draw.line(screen, accent, (cx + 4, cy + 14), (cx + 4, cy - 16), 2)
        for step in range(5):
            y = cy - 12 + step * 6
            pygame.draw.line(screen, accent, (cx - 11, y + 2), (cx - 4, y - 1), 2)
            pygame.draw.line(screen, accent, (cx + 11, y + 2), (cx + 4, y - 1), 2)
    elif resource == "ore":
        pygame.draw.polygon(screen, accent, [(cx - 14, cy + 8), (cx - 2, cy - 14), (cx + 12, cy - 2), (cx + 2, cy + 14)], 2)
        pygame.draw.line(screen, accent, (cx - 2, cy - 14), (cx + 2, cy + 14), 2)
    elif resource == "desert":
        pygame.draw.arc(screen, accent, (cx - 20, cy - 8, 22, 18), 3.14, 6.1, 2)
        pygame.draw.arc(screen, accent, (cx - 2, cy - 2, 24, 16), 3.14, 6.1, 2)


def draw_stylized_hex(screen, polygon, center, resource):
    base_color = COLORS.get(resource, COLORS["water"])
    shadow = [(point[0] + 4, point[1] + 5) for point in polygon]
    pygame.draw.polygon(screen, (20, 26, 38), shadow)

    pygame.draw.polygon(screen, shift_color(base_color, -8), polygon)
    inner = inset_polygon(polygon, center, 0.92)
    pygame.draw.polygon(screen, base_color, inner)

    highlight = inset_polygon(polygon, center, 0.82)
    pygame.draw.polygon(screen, shift_color(base_color, 18), highlight, 2)
    pygame.draw.polygon(screen, (241, 236, 222), polygon, 2)

    draw_hex_texture(screen, resource, center)


def draw_vertical_gradient(screen, top_color, bottom_color):
    height = screen.get_height()
    width = screen.get_width()
    for y in range(height):
        blend = y / max(1, height - 1)
        color = tuple(
            int(top_color[index] + (bottom_color[index] - top_color[index]) * blend)
            for index in range(3)
        )
        pygame.draw.line(screen, color, (0, y), (width, y))


def draw_panel(screen, rect, fill, border, radius=28):
    pygame.draw.rect(screen, fill, rect, border_radius=radius)
    pygame.draw.rect(screen, border, rect, width=2, border_radius=radius)


def draw_resource_badge(screen, label_font, value_font, resource, amount, x, y, width=56, height=66):
    style = RESOURCE_STYLES[resource]
    base_rect = pygame.Rect(x, y, width, height)
    draw_panel(screen, base_rect, style["color"], (255, 255, 255), radius=18)

    short_label = label_font.render(style["short"], True, (246, 241, 233))
    value_label = value_font.render(str(amount), True, (255, 255, 255))

    screen.blit(short_label, (x + (width - short_label.get_width()) // 2, y + 8))
    screen.blit(value_label, (x + (width - value_label.get_width()) // 2, y + 30))


def draw_player_card(screen, fonts, player, index, y, auto_play):
    color = PLAYER_COLORS[index % len(PLAYER_COLORS)]
    card_rect = pygame.Rect(SIDEBAR_X + 22, y, SIDEBAR_WIDTH - 44, 144)
    draw_panel(screen, card_rect, (30, 44, 69), color, radius=22)

    title = fonts["body"].render(f"Player {player.pid}", True, (244, 239, 228))
    points = fonts["title"].render(str(player.victory_points), True, (255, 255, 255))
    point_label = fonts["small"].render("points", True, (188, 198, 214))

    screen.blit(title, (card_rect.x + 18, card_rect.y + 16))
    screen.blit(points, (card_rect.right - 64, card_rect.y + 10))
    screen.blit(point_label, (card_rect.right - 80, card_rect.y + 52))

    stats = [
        ("Roads", player.roads_built),
        ("Settlements", player.settlements_built),
        ("Cities", player.cities_built),
        ("Cards", sum(player.resources.values())),
    ]
    stat_y = card_rect.y + 56
    stat_x = card_rect.x + 18
    for label, value in stats:
        stat = fonts["small"].render(f"{label}: {value}", True, (188, 198, 214))
        screen.blit(stat, (stat_x, stat_y))
        stat_y += 18

    badge_y = card_rect.y + 76
    badge_x = card_rect.x + 16
    for resource in RESOURCES:
        draw_resource_badge(
            screen,
            fonts["small"],
            fonts["body"],
            resource,
            player.resources[resource],
            badge_x,
            badge_y,
        )
        badge_x += 62

    if index == 0:
        mode_text = "AUTO" if auto_play else "STEP"
        mode_color = (132, 218, 165) if auto_play else (240, 202, 110)
        mode = fonts["small"].render(mode_text, True, mode_color)
        screen.blit(mode, (card_rect.right - 72, card_rect.bottom - 30))


def draw_sidebar(screen, fonts, game, max_turns, auto_play):
    sidebar_rect = pygame.Rect(SIDEBAR_X, SIDEBAR_Y, SIDEBAR_WIDTH, SIDEBAR_HEIGHT)
    draw_panel(screen, sidebar_rect, (19, 28, 46), (65, 88, 129), radius=32)

    title = fonts["hero"].render("Catan Match", True, (246, 241, 233))
    subtitle = fonts["small"].render("Live board state", True, (166, 181, 205))
    turn_text = fonts["body"].render(f"Turn {game.turn_number} / {max_turns}", True, (255, 255, 255))
    controls = fonts["small"].render("SPACE step   A autoplay   Q quit", True, (166, 181, 205))

    screen.blit(title, (SIDEBAR_X + 22, SIDEBAR_Y + 20))
    screen.blit(subtitle, (SIDEBAR_X + 24, SIDEBAR_Y + 64))
    screen.blit(turn_text, (SIDEBAR_X + 22, SIDEBAR_Y + 98))
    screen.blit(controls, (SIDEBAR_X + 22, SIDEBAR_Y + SIDEBAR_HEIGHT - 36))

    y = SIDEBAR_Y + 144
    for pid in range(game.num_players):
        draw_player_card(screen, fonts, game.players[pid], pid, y, auto_play)
        y += 158

    if game.winner is not None:
        winner_rect = pygame.Rect(SIDEBAR_X + 22, SIDEBAR_Y + SIDEBAR_HEIGHT - 116, SIDEBAR_WIDTH - 44, 62)
        draw_panel(screen, winner_rect, (123, 95, 34), (255, 223, 131), radius=18)
        winner_text = fonts["body"].render(f"Winner: Player {game.winner}", True, (255, 249, 233))
        screen.blit(winner_text, (winner_rect.x + 18, winner_rect.y + 16))


def draw_board(game, max_turns=150):
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Catan - Smart Agent Game")
    clock = pygame.time.Clock()

    fonts = {
        "hero": pygame.font.SysFont("georgia", 34, bold=True),
        "title": pygame.font.SysFont("georgia", 28, bold=True),
        "body": pygame.font.SysFont("trebuchetms", 22, bold=True),
        "small": pygame.font.SysFont("trebuchetms", 16),
    }

    board = game.board
    centers = list(board.hex_centers.values())
    min_x = min(point[0] for point in centers)
    max_x = max(point[0] for point in centers)
    min_y = min(point[1] for point in centers)
    max_y = max(point[1] for point in centers)
    board_aura_rect = pygame.Rect(
        int(min_x - 210),
        int(min_y - 175),
        int((max_x - min_x) + 420),
        int((max_y - min_y) + 350),
    )

    # Pre-collect all unique vertex keys for settlement-spot display
    all_vertices = set()
    for pos in board.hexes:
        all_vertices.update(get_corners(*pos))

    running = True
    auto_play = False  # Press 'A' to auto-play

    while running and game.winner is None and game.turn_number < max_turns:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not auto_play:
                        game.play_one_turn()
                if event.key == pygame.K_a:
                    auto_play = not auto_play
                if event.key == pygame.K_q:
                    running = False

        if auto_play:
            if game.winner is None and game.turn_number < max_turns:
                game.play_one_turn()

        draw_vertical_gradient(screen, (10, 19, 34), (33, 49, 82))
        pygame.draw.circle(screen, (24, 40, 68), (180, 160), 150)
        pygame.draw.circle(screen, (14, 31, 56), (920, 860), 180)
        pygame.draw.ellipse(screen, (18, 44, 79), board_aura_rect)
        pygame.draw.ellipse(screen, (89, 124, 171), board_aura_rect, 3)

        # --- Draw hexagons ---
        for pos, center in board.hex_centers.items():
            tile = board.hexes[pos]
            draw_stylized_hex(screen, board.hex_polygons[pos], center, tile.resource)

            if tile.number:
                pygame.draw.circle(screen, (24, 31, 42), (int(center[0]), int(center[1])), 28)
                pygame.draw.circle(screen, (255, 248, 229), (int(center[0]), int(center[1])), 26)
                col = (183, 32, 32) if tile.number in (6, 8) else (49, 54, 68)
                num = fonts["title"].render(str(tile.number), True, col)
                screen.blit(num, (center[0] - num.get_width() // 2,
                                  center[1] - num.get_height() // 2))

            if pos == board.robber_pos:
                pygame.draw.circle(screen, (14, 14, 14), (int(center[0]), int(center[1])), 32)
                pygame.draw.circle(screen, (220, 220, 220), (int(center[0]), int(center[1])), 30, 3)
                pygame.draw.circle(screen, (35, 35, 35), (int(center[0]), int(center[1])), 10)

        # --- Draw all empty settlement spots as small squares (reference style) ---
        sq = 7
        for vkey in all_vertices:
            if vkey not in board.buildings:
                x, y = board.vertex_to_pixel(vkey[0], vkey[1])
                pygame.draw.rect(screen, (214, 218, 227),
                                 (int(x) - sq, int(y) - sq, 2 * sq, 2 * sq), 2)

        # --- Draw roads ---
        for edge, pid in board.roads.items():
            v1, v2 = list(edge)
            x1, y1 = board.vertex_to_pixel(v1[0], v1[1])
            x2, y2 = board.vertex_to_pixel(v2[0], v2[1])
            color = PLAYER_COLORS[pid % len(PLAYER_COLORS)]
            pygame.draw.line(screen, color, (int(x1), int(y1)), (int(x2), int(y2)), 12)
            pygame.draw.line(screen, (248, 245, 236), (int(x1), int(y1)), (int(x2), int(y2)), 3)

        # --- Draw placed buildings ---
        for vkey, (pid, btype) in board.buildings.items():
            x, y = board.vertex_to_pixel(vkey[0], vkey[1])
            color = PLAYER_COLORS[pid % len(PLAYER_COLORS)]
            if btype == 'settlement':
                size = 13
                pygame.draw.circle(screen, color, (int(x), int(y)), size)
                pygame.draw.circle(screen, (248, 245, 236), (int(x), int(y)), size, 3)
            else:  # city
                size = 18
                pygame.draw.circle(screen, color, (int(x), int(y)), size)
                pygame.draw.circle(screen, (248, 245, 236), (int(x), int(y)), size, 4)
                # Extra inner ring to distinguish from settlement
                pygame.draw.circle(screen, (248, 245, 236), (int(x), int(y)), size - 6, 2)

        draw_sidebar(screen, fonts, game, max_turns, auto_play)

        pygame.display.flip()
        clock.tick(30 if auto_play else 10)

    if game.winner is not None:
        print(f"\n=== GAME OVER ===")
        print(f"WINNER: Player {game.winner}!")
        print(f"Turn {game.turn_number}")
    else:
        print(f"\nGame reached turn limit ({max_turns})")

    pygame.quit()