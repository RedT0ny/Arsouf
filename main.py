# main.py
import sys

import pygame

# pylint: disable=unused-import
from hexgrid import HexGrid
from gameui import GameUI
from units import *
from config import *

class Game:
    def __init__(self):
        pygame.init()

        # Estados del juego
        self.state = "SELECT_SIDE"
        self.player_side = None
        self.ai_side = None

        # Fases del turno
        self.turn_phase = "movimiento"  # "movimiento" o "combate"
        self.combat_attacker = None  # Unidad seleccionada para atacar
        self.combat_targets = []  # Posibles objetivos de ataque

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

    @staticmethod
    def _load_images():
        global size
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
                pygame.draw.circle(images[key], (0, 255, 0), (size // 2, size // 2), size // 2)
        return images

    @staticmethod
    def _get_initial_units():
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
                button_rect = self.ui.get_button_rect()

                # Manejar botón de finalizar fase
                if button_rect and button_rect.collidepoint(mouse_pos):
                    self._end_player_turn()
                    continue

                # Manejo específico por estado y fase
                if self.state == "SELECT_SIDE":
                    self._handle_side_selection(event)
                elif self.state == "DEPLOY_PLAYER":
                    self._handle_deployment(event)
                elif self.state == "PLAYER_TURN":
                    if self.turn_phase == "movimiento":
                        self._handle_movement_phase(event)
                    elif self.turn_phase == "combate":
                        self._handle_combat_phase(event)  # Asegurar que se llama aquí

    def _handle_movement_phase(self, event):
        """Maneja la fase de movimiento (existente)"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            tablero_rect = pygame.Rect(0, 0, self.tablero_escalado.get_width(),
                                       self.tablero_escalado.get_height())

            if tablero_rect.collidepoint(mouse_pos):
                self._handle_board_click(mouse_pos)

    def _handle_combat_phase(self, event):
        """Maneja los eventos durante la fase de combate"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            # Primero verificar si se hizo clic en el botón de finalizar fase
            button_rect = self.ui.get_button_rect()
            if button_rect and button_rect.collidepoint(mouse_pos):
                self._end_current_phase()
                return

            # Verificar clic en el tablero
            tablero_rect = pygame.Rect(0, 0, self.tablero_escalado.get_width(),
                                       self.tablero_escalado.get_height())
            if tablero_rect.collidepoint(mouse_pos):
                hex_pos = self._get_hex_under_mouse(mouse_pos)
                if hex_pos:
                    row, col = hex_pos
                    self._process_combat_click(row, col)

    def _end_current_phase(self):
        """Finaliza la fase actual y pasa a la siguiente"""
        if self.state == "PLAYER_TURN":
            if self.turn_phase == "movimiento":
                self.turn_phase = "combate"
                self.ui.add_log_message("Fase de combate iniciada")
                self.moved_units = set()  # Resetear unidades movidas
            elif self.turn_phase == "combate":
                self.turn_phase = "movimiento"
                self.state = "AI_TURN"
                self.ui.add_log_message("Turno del jugador finalizado")
                self._check_unit_recovery()

        self.selected_unit = None
        self.possible_moves = []
        self.combat_attacker = None
        self.combat_targets = []

    def _get_hex_under_mouse(self, mouse_pos):
        """Encuentra el hexágono bajo el cursor"""
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                x, y = self.grid.hex_to_pixel(row, col)
                distance = ((mouse_pos[0] - x) ** 2 + (mouse_pos[1] - y) ** 2) ** 0.5
                if distance < HEX_SIZE / 2:
                    return row, col
        return None

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
                self.ui.add_log_message(
                    f"Colocado {type(self.current_deploying_unit).__name__}. Siguiente unidad lista.")
            else:
                self.current_deploying_unit = None
                self.ui.add_log_message("¡Despliegue completado!")
        else:
            self.ui.add_log_message("Posición inválida para despliegue")


    def _end_player_turn(self):
        """Maneja la finalización del turno del jugador o fase de despliegue"""
        if self.state == "DEPLOY_PLAYER" and not self.current_deploying_unit:
            # Confirmar despliegue del jugador
            self.state = "DEPLOY_AI"
            self.ui.add_log_message("Despliegue confirmado. El ordenador está desplegando")

            # Limpiar selecciones
            self.selected_unit = None
            self.possible_moves = []

            # Iniciar despliegue de la IA
            self._ai_deploy_units()

        elif self.state == "PLAYER_TURN":
            if self.turn_phase == "movimiento":
                # Pasar a fase de combate
                self.turn_phase = "combate"
                self.ui.add_log_message("Fase de combate iniciada")
                self.moved_units = set()  # Resetear unidades movidas

            elif self.turn_phase == "combate":
                # Finalizar turno completo
                self.turn_phase = "movimiento"
                self.state = "AI_TURN"
                self.current_turn_side = self.ai_side
                self.ui.add_log_message("Turno del jugador finalizado")
                self._check_unit_recovery()

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
                    return

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
        return unit.side == self.player_side

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
                    self.ui.add_log_message(
                        f"[{type(unit).__name__}#{id(unit)}] se mueve desde ({row},{col}) hasta ({new_row}, {new_col})")

        # 3. Finalizar turno cuando no queden unidades o la IA decida parar
        if not self._ai_units_to_consider:  #or random.random() < 0.05:  # 5% chance de terminar temprano
            self._end_ai_turn()

    def _end_ai_turn(self):
        self.state = "PLAYER_TURN"
        self.ui.add_log_message("Turno del ordenador finalizado. ¡Te toca!")
        # Limpiar variables de estado del turno de la IA
        if hasattr(self, '_ai_turn_initialized'):
            del self._ai_turn_initialized
            del self._ai_moved_units_this_turn
            del self._ai_units_to_consider
        self._check_unit_recovery()
        self.selected_unit = None
        self.possible_moves = []

    def _check_unit_recovery(self):
        """Verifica recuperación de todas las unidades heridas"""
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                unit = self.grid.grid[row][col]
                if unit and unit.health == 1:
                    unit.recuperar(self.grid)

    def _process_combat_click(self, row, col):
        """Procesa clics durante la fase de combate"""
        unit = self.grid.get_unit(row, col)

        # Si no hay atacante seleccionado
        if not self.combat_attacker:
            # Seleccionar atacante (debe ser unidad aliada sana)
            if unit and unit.side == self.player_side and unit.health == 2:
                self.combat_attacker = unit
                self.combat_targets = self.grid.get_adjacent_enemies(row, col, self.player_side)
                self.ui.add_log_message(f"{type(unit).__name__} seleccionado para ataque. Elige objetivo.")

                # Mostrar objetivos visualmente
                if not self.combat_targets:
                    self.ui.add_log_message("No hay enemigos adyacentes para atacar")
            else:
                self.ui.add_log_message("Selecciona una unidad aliada sana para atacar")
        else:
            # Seleccionar objetivo (debe ser enemigo adyacente)
            if unit and unit in self.combat_targets:
                # Realizar ataque
                if self.combat_attacker.atacar(unit, self.grid):
                    self.ui.add_log_message(
                        f"¡Ataque exitoso! {type(self.combat_attacker).__name__} hirió a {type(unit).__name__}")
                else:
                    self.ui.add_log_message(f"¡Ataque fallido! {type(unit).__name__} resistió el ataque")

                # Resetear selección después del ataque
                self.combat_attacker = None
                self.combat_targets = []
            else:
                self.ui.add_log_message("Objetivo no válido. Selecciona un enemigo adyacente")

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
