# gui.py
import pygame
import math
import sys
from game.board import Board,COLORS,PLAYER_COLORS


def draw_board(game):
    pygame.init()
    screen = pygame.display.set_mode((1200, 900))
    pygame.display.set_caption("Catan - Vue Pygame")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont('arial', 32, bold=True)
    small_font = pygame.font.SysFont('arial', 20)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game.play_one_turn()   
                    print(f"Turn {game.turn_number} over")

        board_data = game.board.get_render_data()

        screen.fill((10, 30, 60))
        # Dessin hexagones
        for pos, center in board_data['hex_centers'].items():
            tile = board_data['hex_tiles'][pos]
            color = COLORS.get(tile.resource, COLORS['water'])
            pygame.draw.polygon(screen, color, board_data['hex_polygons'][pos])
            pygame.draw.polygon(screen, (40,40,40), board_data['hex_polygons'][pos], 3)

            if tile.number:
                num = font.render(str(tile.number), True, (0,0,0) if tile.number in (6,8) else (255,255,255))
                screen.blit(num, (center[0] - num.get_width()//2, center[1] - num.get_height()//2))

            if pos == board_data['robber_pos']:
                pygame.draw.circle(screen, (0,0,0), center, 22)

        # Routes
        for edge, pid in board_data['roads'].items():
            v1, v2 = list(edge)
            x1, y1 = board_data['vertex_to_pixel'](*v1)
            x2, y2 = board_data['vertex_to_pixel'](*v2)
            pygame.draw.line(screen, PLAYER_COLORS[pid], (x1,y1), (x2,y2), 14)

        # Bâtiments
        for vkey, (pid, btype) in board_data['buildings'].items():
            x, y = board_data['vertex_to_pixel'](*vkey)
            size = 16 if btype == 'settlement' else 22
            pygame.draw.circle(screen, PLAYER_COLORS[pid], (int(x), int(y)), size)
            pygame.draw.circle(screen, (255,255,255), (int(x), int(y)), size, 3)

        # Ports (petits cercles + texte)
        for port in board_data['ports']:
            cx, cy = port['center']
            pygame.draw.circle(screen, (220,220,180), (int(cx), int(cy)), 18)
            pygame.draw.circle(screen, (0,0,0), (int(cx), int(cy)), 18, 3)
            label = small_font.render(port['type'][:3].upper(), True, (0,0,0))
            screen.blit(label, (cx - label.get_width()//2, cy - label.get_height()//2 - 25))

        y = 20
        for p in game.players:
            txt = f"J{p.pid}: {p.victory_points} pts  |  {dict(p.resources)}"
            surf = font.render(txt, True, PLAYER_COLORS[p.pid])
            screen.blit(surf, (20, y))
            y += 35

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()