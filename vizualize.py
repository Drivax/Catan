# gui.py
import pygame
import math
import sys
from game.board import Board,COLORS,PLAYER_COLORS

def draw_board(game):
    pygame.init()
    screen = pygame.display.set_mode((1400, 1000))  # ← un peu plus grand pour mieux voir
    pygame.display.set_caption("Catan - Simulation corrigée")
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
                    print(f"Tour {game.turn_number} terminé")

        screen.fill((10, 20, 50))

        data = game.board.get_render_data()

        # 1. Dessin des hexagones
        for pos, center in data['hex_centers'].items():
            tile = data['hex_tiles'][pos]
            color = COLORS.get(tile.resource, COLORS['water'])
            pygame.draw.polygon(screen, color, data['hex_polygons'][pos])
            pygame.draw.polygon(screen, (60,60,80), data['hex_polygons'][pos], 4)  # bord plus visible

            if tile.number:
                col = (220,0,0) if tile.number in (6,8) else (255,255,255)
                num = font.render(str(tile.number), True, col)
                screen.blit(num, (center[0] - num.get_width()//2, center[1] - num.get_height()//2))

            if pos == data['robber_pos']:
                pygame.draw.circle(screen, (0,0,0), (int(center[0]), int(center[1])), 28)

        # 2. Routes (traits épais sur les arêtes)
        for edge, pid in data['roads'].items():
            v1, v2 = list(edge)
            x1, y1 = data['vertex_to_pixel'](*v1)
            x2, y2 = data['vertex_to_pixel'](*v2)
            color = PLAYER_COLORS[pid % len(PLAYER_COLORS)]
            pygame.draw.line(screen, color, (x1,y1), (x2,y2), 16)
            pygame.draw.line(screen, (255,255,255), (x1,y1), (x2,y2), 4)  # contour blanc pour mieux voir

        # 3. Bâtiments (villages et villes)
        for vkey, (pid, btype) in data['buildings'].items():
            x, y = data['vertex_to_pixel'](*vkey)
            size = 18 if btype == 'settlement' else 26
            color = PLAYER_COLORS[pid % len(PLAYER_COLORS)]
            pygame.draw.circle(screen, color, (int(x), int(y)), size)
            pygame.draw.circle(screen, (255,255,255), (int(x), int(y)), size + 4, 4)  # contour blanc

        # 4. Ports (sur les arêtes extérieures)
        for port in data['ports']:
            cx, cy = port['center']
            ptype = port['type']
            color = (220, 220, 180) if ptype == 'generic' else COLORS.get(ptype, (200,200,200))
            pygame.draw.circle(screen, color, (int(cx), int(cy)), 20)
            pygame.draw.circle(screen, (0,0,0), (int(cx), int(cy)), 20, 4)

            label = small_font.render(ptype.upper()[:5], True, (0,0,0))
            screen.blit(label, (cx - label.get_width()//2, cy - 35))

        # HUD ressources
        y = 20
        for p in game.players:
            txt = f"J{p.pid}: {p.victory_points} pts  |  {dict(p.resources)}"
            surf = font.render(txt, True, PLAYER_COLORS[p.pid % len(PLAYER_COLORS)])
            screen.blit(surf, (20, y))
            y += 40

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()