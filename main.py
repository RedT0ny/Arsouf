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
        self.moved_units = set()  # Unidades que ya han movido en este turno
        self.current_turn_side = None  # Bandos del turno actual
        self.last_move_debug_pos = None  # Para debug visual

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

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Manejar botón de finalizar turno/confirmar despliegue
                button_rect = self.ui.get_button_rect()  # Obtener el rect del botón
                if button_rect and button_rect.collidepoint(mouse_pos):
                    self._end_player_turn()
                    continue  # Importante para no procesar otros clicks
                    
                # Manejo específico por estado
                if self.state == "SELECT_SIDE":
                    self._handle_side_selection(event)
                elif self.state == "DEPLOY_PLAYER":
                    self._handle_deployment(event)
                elif self.state == "PLAYER_TURN":
                    self._handle_player_turn(event)
                        
    def _start_game(self, player_side):
        self.player_side = player_side
        self.ai_side = "SARRACENOS" if player_side == "CRUZADOS" else "CRUZADOS"
        self.state = "DEPLOY_PLAYER"
        self.current_deploying_unit = self.units_to_deploy[self.player_side].pop(0)
        self.ui.add_log_message(f"Jugando como {player_side}. Comienza el despliegue.")

    def _handle_side_selection(self, event):
        side = self.ui.handle_side_selection(event)
        if side:
            self._start_game(side)

    def _handle_deployment(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            hex_pos = self.ui.handle_deployment_click(pygame.mouse.get_pos(), self)
            if hex_pos:
                self._place_unit(hex_pos)    

    def _place_unit(self, hex_pos):
        """Coloca una unidad en el tablero durante el despliegue."""
        row, col = hex_pos
        
        if (self.grid.grid[row][col] is None and 
            self.grid.is_in_deployment_zone(row, col, self.player_side)):
            
            # Colocar la unidad actual
            self.grid.add_unit(row, col, self.current_deploying_unit)
            
            # Preparar siguiente unidad o finalizar despliegue
            if self.units_to_deploy[self.player_side]:
                self.current_deploying_unit = self.units_to_deploy[self.player_side].pop(0)
                self.ui.add_log_message(f"Colocado {type(self.current_deploying_unit).__name__}. Siguiente unidad lista.")
            else:
                self.current_deploying_unit = None
                self.ui.add_log_message("¡Despliegue completado!")
        else:
            self.ui.add_log_message("Posición inválida para despliegue")
            
    def _handle_player_turn(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            tablero_rect = pygame.Rect(0, 0, self.tablero_escalado.get_width(), self.tablero_escalado.get_height())
            
            if tablero_rect.collidepoint(mouse_pos):
                self._handle_board_click(mouse_pos)

    def _end_player_turn(self):
        if self.state == "PLAYER_TURN":
            self.moved_units = set()  # Resetear unidades movidas
            self.state = "AI_TURN"
            self.current_turn_side = self.ai_side
            self.ui.add_log_message("Turno del jugador finalizado")
        elif self.state == "DEPLOY_PLAYER" and not self.current_deploying_unit:
            self.state = "DEPLOY_AI"
            self.ui.add_log_message("Despliegue confirmado. El ordenador está desplegando")
        
        self.selected_unit = None
        self.possible_moves = []
        
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
            if (row, col) in self.moved_units:
                self.ui.add_log_message(f"Ya has movido a [{type(unit).__name__}] este turno")
                return
                
            self.selected_unit = (row, col)
            # Asignar el resultado a self.possible_moves
            self.possible_moves = self.grid.get_possible_moves(row, col, unit.speed, self.moved_units)
        elif self.selected_unit and (row, col) in self.possible_moves:
            old_row, old_col = self.selected_unit
            # Corregir llamada a move_unit (pasar ambas posiciones)
            if self.grid.move_unit(old_row, old_col, row, col):  # Cambiado aquí
                self.moved_units.add((row, col))
                self.last_move_debug_pos = (old_row, old_col)
                self.selected_unit = None
                self.possible_moves = []
        else:
            self.selected_unit = None
            self.possible_moves = []
                
    def _is_player_unit(self, unit):
        if self.player_side == "CRUZADOS":
            return isinstance(unit, (Ricardo, Templario, Hospitalario, Caballero, Infanteria, Bagaje))
        else:
            return isinstance(unit, (Saladino, Mameluco, Arquero, Explorador))
    
    def _ai_deploy_units(self):
        if not self.units_to_deploy[self.ai_side]:
            self.state = "PLAYER_TURN"
            return
            
        unit = random.choice(self.units_to_deploy[self.ai_side])
        self.units_to_deploy[self.ai_side].remove(unit)
        
        valid_positions = []
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                if self.grid.grid[row][col] is None and self.grid.is_in_deployment_zone(row, col, self.ai_side):
                    valid_positions.append((row, col))
        
        if valid_positions:
            row, col = random.choice(valid_positions)
            self.grid.add_unit(row, col, unit)
        
        if not self.units_to_deploy[self.ai_side]:
            self.state = "PLAYER_TURN"
  
    def _ai_turn(self):
        # 1. Inicializar el turno de la IA si es nuevo
        if not hasattr(self, '_ai_turn_initialized'):
            self.ui.add_log_message("Turno del ordenador")
            self._ai_turn_initialized = True
            self._ai_moved_units_this_turn = set()
            self._ai_units_to_consider = [
                (r, c, u) for r in range(self.grid.rows)
                for c in range(self.grid.cols)
                if (u := self.grid.grid[r][c]) and not self._is_player_unit(u)
            ]
            random.shuffle(self._ai_units_to_consider)  # Orden aleatorio

        # 2. Mover hasta 1 unidad por frame (para permitir renderizado)
        if self._ai_units_to_consider:
            row, col, unit = self._ai_units_to_consider.pop()
            
            # Decidir aleatoriamente si mover esta unidad (90% probabilidad)
            if random.random() < 1 and (row, col) not in self._ai_moved_units_this_turn:
                self.possible_moves = self.grid.get_possible_moves(row, col, unit.speed)
                if self.possible_moves:
                    new_row, new_col = random.choice(self.possible_moves)
                    self.grid.grid[row][col] = None
                    self.grid.add_unit(new_row, new_col, unit)
                    self._ai_moved_units_this_turn.add((row, col))
                    self.ui.add_log_message(f"[{type(unit).__name__}#{id(unit)}] se mueve desde ({row},{col}) hasta ({new_row}, {new_col})")
                            
        # 3. Finalizar turno cuando no queden unidades o la IA decida parar
        if not self._ai_units_to_consider: #or random.random() < 0.05:  # 5% chance de terminar temprano
            self._end_ai_turn()

    def _end_ai_turn(self):
        self.state = "PLAYER_TURN"
        self.ui.add_log_message("Turno del ordenador finalizado. ¡Te toca!")
        # Limpiar variables de estado del turno de la IA
        if hasattr(self, '_ai_turn_initialized'):
            del self._ai_turn_initialized
            del self._ai_moved_units_this_turn
            del self._ai_units_to_consider
        self.selected_unit = None
        self.possible_moves = []

    def _draw(self):
       self.ui.draw_game(self)
       pygame.display.flip()

    def run(self):
        while self.running:
            self._handle_events()
            
            # Restaurar la lógica original de despliegue
            if self.state == "DEPLOY_AI":
                self._ai_deploy_units()
            elif self.state == "AI_TURN":
                self._ai_turn()
                
            self._draw()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()
                
if __name__ == "__main__":
    game = Game()
    game.run()