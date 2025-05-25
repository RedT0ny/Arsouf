# main.py
import pygame
import sys
import random
from config import *
from hexgrid import HexGrid
from units import *
from gameui import GameUI

class Game:
    def __init__(self):
        pygame.init()
        
        # Inicializar
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Batalla de Arsuf")
        
        # Cargar y escalar tablero
        self.tablero_escalado = pygame.transform.smoothscale(
            pygame.image.load(IMAGE_PATHS["board"]).convert_alpha(),
            (int(TABLERO_REAL_WIDTH * ESCALA), int(TABLERO_REAL_HEIGHT * ESCALA))
        )
        
        # Inicializar componentes
        self.grid = HexGrid()
        self.ui = GameUI(self)
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Cargar imágenes de unidades
        self.images = self._load_images()
        
        # Estados del juego
        self.state = "SELECT_SIDE"
        self.player_side = None
        self.ai_side = None
        
        # Unidades por colocar
        self.units_to_deploy = self._get_initial_units()
        self.current_deploying_unit = None
        
        # Movimiento
        self.selected_unit = None
        self.possible_moves = []
    
    def _load_images(self):
        images = {}
        for key, path in IMAGE_PATHS.items():
            if key == "board": continue
            try:
                img = pygame.image.load(path).convert_alpha()
                size = int(HEX_SIZE * 0.95)
                images[key] = pygame.transform.smoothscale(img, (size, size))
            except Exception as e:
                print(f"Error cargando {path}: {e}")
                images[key] = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(images[key], (0, 255, 0), (size//2, size//2), size//2)
        return images
    
    def _get_initial_units(self):
        """Devuelve las unidades iniciales para cada bando."""
        return {
            "CRUZADOS": [
                Ricardo(), Templario(), Hospitalario(),
                Caballero(), Caballero(), Caballero(),
                *[Infanteria() for _ in range(6)],
                *[Bagaje() for _ in range(4)]
            ],
            "SARRACENOS": [
                Saladino(),
                *[Mameluco() for _ in range(4)],
                *[Arquero() for _ in range(6)],
                *[Explorador() for _ in range(5)]
            ]
        }
    
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
                
            # Primero manejar eventos de UI (scroll)
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, 
                             pygame.MOUSEMOTION, pygame.MOUSEWHEEL):
                if self.ui.handle_events(event):
                    continue  # Si el UI consumió el evento, no procesarlo más
            
            if self.state == "SELECT_SIDE":
                self._handle_side_selection(event)
            elif self.state == "DEPLOY_PLAYER":
                self._handle_deployment(event)
            elif self.state == "PLAYER_TURN":
                self._handle_player_turn(event)
    
    def _handle_side_selection(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            cruzados_rect, sarracenos_rect = self.ui.draw_side_selection()
            mouse_pos = pygame.mouse.get_pos()
            
            if cruzados_rect.collidepoint(mouse_pos):
                self._start_game("CRUZADOS")
            elif sarracenos_rect.collidepoint(mouse_pos):
                self._start_game("SARRACENOS")
    
    def _start_game(self, player_side):
        self.player_side = player_side
        self.ai_side = "SARRACENOS" if player_side == "CRUZADOS" else "CRUZADOS"
        self.state = "DEPLOY_PLAYER"
        self.current_deploying_unit = self.units_to_deploy[self.player_side].pop(0)
        self.ui.add_log_message(f"Jugando como {player_side}. Comienza el despliegue.")
    
    def _handle_deployment(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            pos_x = 0 #(SCREEN_WIDTH - self.tablero_escalado.get_width()) // 2
            pos_y = 0 #(SCREEN_HEIGHT - self.tablero_escalado.get_height()) // 2
            tablero_rect = pygame.Rect(pos_x, pos_y, self.tablero_escalado.get_width(), self.tablero_escalado.get_height())
            
            if tablero_rect.collidepoint(mouse_pos):
                self._place_unit(mouse_pos, pos_x, pos_y)
    
    def _place_unit(self, mouse_pos, offset_x, offset_y):
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                x, y = self.grid.hex_to_pixel(row, col)
                x += offset_x
                y += offset_y
                
                distance = ((mouse_pos[0] - x) ** 2 + (mouse_pos[1] - y) ** 2) ** 0.5
                if distance < HEX_SIZE / 2 and self.grid.grid[row][col] is None:
                    if self._is_in_deployment_zone(row, col, self.player_side):
                        self.grid.add_unit(row, col, self.current_deploying_unit)
                        if self.units_to_deploy[self.player_side]:
                            self.current_deploying_unit = self.units_to_deploy[self.player_side].pop(0)
                        else:
                            self.current_deploying_unit = None
    
    def _is_in_deployment_zone(self, row, col, side):
        if side == "CRUZADOS":
            return col >= HEX_COLS - 4 and row < 4
        else:
            return col < 8 and row >= HEX_ROWS - 2
    
    def _handle_player_turn(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            tablero_rect = pygame.Rect(0, 0, self.tablero_escalado.get_width(), self.tablero_escalado.get_height())
            
            if tablero_rect.collidepoint(mouse_pos):
                self._handle_board_click(mouse_pos)
    
    def _handle_board_click(self, mouse_pos):
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                x, y = self.grid.hex_to_pixel(row, col)
                
                distance = ((mouse_pos[0] - x) ** 2 + (mouse_pos[1] - y) ** 2) ** 0.5
                if distance < HEX_SIZE / 2:
                    # Mensaje de debug para verificar coordenadas
                    print(f"Has hecho click en coordenadas del grid: ({row}, {col})")
                    print(f"Posición en píxeles: {self.grid.hex_to_pixel(row, col)}")

                    self._process_hex_click(row, col)
                    break
    # DEBUG: Si no se encontró ningún hexágono
    print("Click fuera del tablero o entre hexágonos")

    def _process_hex_click(self, row, col):
        unit = self.grid.grid[row][col]
        
        if not self.selected_unit and unit and self._is_player_unit(unit):
            self.selected_unit = (row, col)
            self._calculate_possible_moves(row, col, unit.speed)
        elif self.selected_unit and (row, col) in self.possible_moves:
            self._move_unit(row, col)
        else:
            self.selected_unit = None
            self.possible_moves = []
    
    def _move_unit(self, row, col):
        old_row, old_col = self.selected_unit
        moving_unit = self.grid.grid[old_row][old_col]
        self.grid.grid[old_row][old_col] = None
        self.grid.add_unit(row, col, moving_unit)
        self.selected_unit = None
        self.possible_moves = []
    
    def _is_player_unit(self, unit):
        if self.player_side == "CRUZADOS":
            return isinstance(unit, (Ricardo, Templario, Hospitalario, Caballero, Infanteria, Bagaje))
        else:
            return isinstance(unit, (Saladino, Mameluco, Arquero, Explorador))
    
    def _calculate_possible_moves(self, row, col, speed):
        self.possible_moves = []
        unit = self.grid.grid[row][col]
        
        # Ajustar velocidad si es unidad lenta empezando en carretera
        effective_speed = speed
        if hasattr(unit, 'slow') and (row, col) in ROAD_HEXES:
            effective_speed += 1
        
        from collections import deque
        visited = {}
        queue = deque()
        queue.append((row, col, 0.0, []))  # (row, col, accumulated_cost, path)
        visited[(row, col)] = 0.0

        while queue:
            r, c, dist, path = queue.popleft()
            
            if dist > 0 and self.grid.grid[r][c] is None:
                self.possible_moves.append((r, c))

            for (nr, nc), cost in self._get_valid_neighbors(r, c, path):
                new_dist = dist + cost
                # Solo considerar si está dentro del límite y es mejor camino
                if new_dist <= effective_speed and (nr, nc not in visited or new_dist < visited.get((nr, nc), float('inf'))):
                    visited[(nr, nc)] = new_dist
                    queue.append((nr, nc, new_dist, path + [(r, c)]))
                
        # Debug: Mostrar resultados ordenados
        if __debug__:
            print("\nMovimientos calculados para velocidad", speed)
            print("Posición inicial:", (row, col))
            print("Posibles movimientos (ordenados):")
            for r in range(max(0, row-speed), min(self.grid.rows, row+speed+1)):
                line = []
                for c in range(max(0, col-speed), min(self.grid.cols, col+speed+1)):
                    if (r, c) in self.possible_moves:
                        line.append(f"({r},{c})")
                    elif r == row and c == col:
                        line.append("POS")
                    else:
                        line.append("    ")
                # Alineación para mostrar estructura hexagonal
                if r % 2 == 1:
                    print("  " + "  ".join(line))
                else:
                    print("    " + "  ".join(line))

    def _get_valid_neighbors(self, row, col, current_path):
        """Devuelve vecinos válidos y costo de movimiento, considerando barreras"""
        # Direcciones para hex grid vertical (punto arriba)
        # Estructura: (dr, dc) donde dr = cambio en fila, dc = cambio en columna
        # Organizadas en anillos concéntricos
        directions = [
            # Primer anillo (distancia 1)
            [(-1,0), (-1,1), (0,1), (1,0), (1,1), (0,-1)],  # Filas pares
            [(-1,-1), (-1,0), (0,1), (1,-1), (1,0), (0,-1)]  # Filas impares
        ]
        
        neighbors = []
        dir_set = directions[row % 2]
        unit = self.grid.grid[row][col]
        
        for dr, dc in dir_set:
            nr = row + dr
            nc = col + dc
            
            # 1. Verificar límites y hexágonos prohibidos
            if not (0 <= nr < self.grid.rows and 0 <= nc < self.grid.cols):
                continue
            if (nr, nc) in FORBIDDEN_HEXES:
                continue
                
            # 2. Determinar costo base del movimiento
            move_pair = frozenset({(row, col), (nr, nc)})
            cost = 1  # Costo normal
            
            # 3. Aplicar modificadores de terreno
            # a) Barreras de río
            if move_pair in RIVER_BARRIERS:
                if FORD_HEX not in current_path and FORD_HEX != (row, col) and FORD_HEX != (nr, nc):
                    continue  # Bloquear movimiento
                cost = 2  # Penalización por cruzar río
            
            # b) Bonus en carretera para unidades slow
            if hasattr(unit, 'slow'):
                on_road_start = (row, col) in ROAD_HEXES
                on_road_end = (nr, nc) in ROAD_HEXES
                
                # Bonus: movimiento más rápido EN carretera
                if on_road_start and on_road_end:
                    cost = 0.5  # Mitad de costo en carretera continua
                # Penalización: salir de carretera
                elif on_road_start and not on_road_end:
                    cost = 1.5  # Costo extra por dejar carretera
            
            neighbors.append(((nr, nc), cost))
        
        return neighbors

    def _ai_deploy_units(self):
        if not self.units_to_deploy[self.ai_side]:
            self.state = "PLAYER_TURN"
            return
            
        unit = random.choice(self.units_to_deploy[self.ai_side])
        self.units_to_deploy[self.ai_side].remove(unit)
        
        valid_positions = []
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                if self.grid.grid[row][col] is None and self._is_in_deployment_zone(row, col, self.ai_side):
                    valid_positions.append((row, col))
        
        if valid_positions:
            row, col = random.choice(valid_positions)
            self.grid.add_unit(row, col, unit)
        
        if not self.units_to_deploy[self.ai_side]:
            self.state = "PLAYER_TURN"
    
    def _ai_turn(self):
        # Añadir mensaje solo al comenzar el turno de la IA
        if not hasattr(self, '_ai_turn_started'):
            self.ui.add_log_message("Turno del ordenador")
            self._ai_turn_started = True
        
        # Realizar movimientos de la IA
        ai_units = []
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                unit = self.grid.grid[row][col]
                if unit and not self._is_player_unit(unit):
                    ai_units.append((row, col, unit))
        
        for row, col, unit in ai_units:
            if random.random() < 0.7:
                self._calculate_possible_moves(row, col, unit.speed)
                if self.possible_moves:
                    new_row, new_col = random.choice(self.possible_moves)
                    self.grid.grid[row][col] = None
                    self.grid.add_unit(new_row, new_col, unit)
                    self.ui.add_log_message(f"{type(unit).__name__} se mueve a ({new_row}, {new_col})")
        
        # Finalizar turno de la IA
        self.state = "PLAYER_TURN"
        self.ui.add_log_message("Turno del ordenador finalizado")
        delattr(self, '_ai_turn_started')  # Limpiar flag
    
    def run(self):
        while self.running:
            self._handle_events()
            
            if self.state == "DEPLOY_AI":
                self._ai_deploy_units()
            elif self.state == "AI_TURN":
                self._ai_turn()
            
            self._draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()
    
    def _draw(self):
        # Dibujar elementos en el orden correcto (los últimos se superponen)
        self.screen.fill(COLOR_BG)
        
        # 1. Dibujar tablero (fondo)
        pos_x = (SCREEN_WIDTH - self.tablero_escalado.get_width() - PANEL_WIDTH) // 2
        pos_y = (SCREEN_HEIGHT - self.tablero_escalado.get_height() - LOG_PANEL_HEIGHT) // 2  # Ajuste para el panel LOG
        
        self.screen.blit(self.tablero_escalado, (pos_x, pos_y))
        
        # 2. Dibujar elementos del juego (unidades, etc.)
        if __debug__: 
            self.grid.draw_hex_debug(self.screen)
        
        self.grid.draw(self.screen, self.images, pos_x, pos_y)
        self._draw_possible_moves()
        
        # 3. Dibujar paneles de UI (encima del tablero)
        self.ui.draw_log_panel()
        button_rect = self.ui.draw_panel()
        self.ui.draw_deployment_zones()
        
        # 4. Dibujar pantalla de selección ENCIMA de todo si es necesario
        if self.state == "SELECT_SIDE":
            self.ui.draw_side_selection()
        
        # Manejar clics en el botón del panel
        if button_rect and pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()
            if button_rect.collidepoint(mouse_pos):
                if self.state == "PLAYER_TURN":
                    self.state = "AI_TURN"
                    self.ui.add_log_message("Turno pasado al ordenador")
                elif self.state == "DEPLOY_PLAYER" and not self.current_deploying_unit:
                    self.state = "DEPLOY_AI"
                    self.ui.add_log_message("Despliegue confirmado. El ordenador está desplegando")
        
        pygame.display.flip()
    
    def _draw_possible_moves(self):
        if not self.selected_unit or not self.possible_moves:
            return
            
        for (row, col) in self.possible_moves:
            x, y = self.grid.hex_to_pixel(row, col)
            
            s = pygame.Surface((HEX_SIZE, HEX_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(s, (100, 200, 255, 150), (HEX_SIZE//2, HEX_SIZE//2), HEX_SIZE//2)
            self.screen.blit(s, (x - HEX_SIZE//2, y - HEX_SIZE//2))

if __name__ == "__main__":
    game = Game()
    game.run()