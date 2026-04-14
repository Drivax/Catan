import pygame
import math
import sys
from game.board import Board, COLORS, PLAYER_COLORS
from game.map import get_corners, HEX_POSITIONS


def draw_board(game, max_turns=150):
    pygame.init()
    screen = pygame.display.set_mode((1400, 1000))
    pygame.display.set_caption("Catan - Smart Agent Game")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont('arial', 32, bold=True)
    small_font = pygame.font.SysFont('arial', 20)

    board = game.board

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

        screen.fill((10, 20, 50))

        # --- Draw hexagons ---
        for pos, center in board.hex_centers.items():
            tile = board.hexes[pos]
            color = COLORS.get(tile.resource, COLORS['water'])
            pygame.draw.polygon(screen, color, board.hex_polygons[pos])
            pygame.draw.polygon(screen, (50, 50, 70), board.hex_polygons[pos], 3)

            if tile.number:
                col = (220, 0, 0) if tile.number in (6, 8) else (255, 255, 255)
                num = font.render(str(tile.number), True, col)
                screen.blit(num, (center[0] - num.get_width() // 2,
                                  center[1] - num.get_height() // 2))

            if pos == board.robber_pos:
                pygame.draw.circle(screen, (0, 0, 0), (int(center[0]), int(center[1])), 26)

        # --- Draw all empty settlement spots as small squares (reference style) ---
        sq = 7
        for vkey in all_vertices:
            if vkey not in board.buildings:
                x, y = board.vertex_to_pixel(vkey[0], vkey[1])
                pygame.draw.rect(screen, (190, 190, 190),
                                 (int(x) - sq, int(y) - sq, 2 * sq, 2 * sq), 2)

        # --- Draw roads ---
        for edge, pid in board.roads.items():
            v1, v2 = list(edge)
            x1, y1 = board.vertex_to_pixel(v1[0], v1[1])
            x2, y2 = board.vertex_to_pixel(v2[0], v2[1])
            color = PLAYER_COLORS[pid % len(PLAYER_COLORS)]
            pygame.draw.line(screen, color, (int(x1), int(y1)), (int(x2), int(y2)), 12)
            pygame.draw.line(screen, (255, 255, 255), (int(x1), int(y1)), (int(x2), int(y2)), 3)

        # --- Draw placed buildings ---
        for vkey, (pid, btype) in board.buildings.items():
            x, y = board.vertex_to_pixel(vkey[0], vkey[1])
            color = PLAYER_COLORS[pid % len(PLAYER_COLORS)]
            if btype == 'settlement':
                size = 13
                pygame.draw.circle(screen, color, (int(x), int(y)), size)
                pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), size, 3)
            else:  # city
                size = 18
                pygame.draw.circle(screen, color, (int(x), int(y)), size)
                pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), size, 4)
                # Extra inner ring to distinguish from settlement
                pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), size - 6, 2)

        # --- HUD: Player info ---
        y = 20
        for pid in range(game.num_players):
            p = game.players[pid]
            txt = f"J{p.pid}: {p.victory_points}pts | {dict(p.resources)}"
            surf = small_font.render(txt, True, PLAYER_COLORS[pid % len(PLAYER_COLORS)])
            screen.blit(surf, (20, y))
            y += 30

        turn_txt = f"Turn: {game.turn_number}/{max_turns}"
        turn_surf = font.render(turn_txt, True, (255, 255, 255))
        screen.blit(turn_surf, (20, y + 20))

        if game.winner is not None:
            winner_txt = f"WINNER: Player {game.winner}!"
            winner_surf = font.render(winner_txt, True, (255, 215, 0))
            screen.blit(winner_surf, (400, 400))

        controls = "SPACE: Step  |  A: Auto-play  |  Q: Quit"
        ctrl_surf = small_font.render(controls, True, (200, 200, 200))
        screen.blit(ctrl_surf, (20, 900))

        pygame.display.flip()
        clock.tick(30 if auto_play else 10)

    if game.winner is not None:
        print(f"\n=== GAME OVER ===")
        print(f"WINNER: Player {game.winner}!")
        print(f"Turn {game.turn_number}")
    else:
        print(f"\nGame reached turn limit ({max_turns})")

    pygame.quit()