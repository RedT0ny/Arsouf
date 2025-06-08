# game.py
import sys
import os
import pygame
import gettext
import config

_ = gettext.gettext  # type: callable
import random

from hexgrid import HexGrid
from gameui import GameUI
from menu import SetupMenu, SideSelectionMenu
from units import *

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()  # Inicializar el sistema de audio

        # Estados del juego
        self.state = config.GAME_STATES["INTRO"]  # Comenzar con la pantalla de introducción
        self.player_side = None
        self.ai_side = None

        # Variables para la pantalla de introducción
        self.intro_start_time = pygame.time.get_ticks()
        self.intro_duration = 207000  # 3:27 minutos en milisegundos (duración de la música de intro)

        # Cargar sonidos (necesarios para la intro)
        self.sounds = self._load_sounds()

        # Fases del turno
        self.turn_phase = config.TURN_PHASES["MOVEMENT"]  # Fase actual del turno (movimiento o combate)
        self.combat_attacker = None  # Unidad seleccionada para atacar
        self.combat_targets = []  # Posibles objetivos de ataque

        # Objetivos del juego
        self.arsouf_hexes = [(1, 0), (1, 1)]  # Hexágonos de Arsouf
        self.units_in_arsouf = {
            config.BAGGAGE_NAME: 0,  # Contador de unidades de bagaje en Arsouf
            "other": 0    # Contador de otras unidades en Arsouf
        }
        self.game_over = False
        self.winner = None

        # Inicializar pantalla (necesaria para la intro)
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption(f"{_('game_name')} {VERSION}")

        # Inicializar el reloj (necesario para el bucle principal)
        self.clock = pygame.time.Clock()
        self.running = True

        # Inicializar variables que se usarán más tarde
        self.tablero_escalado = None
        self.grid = None
        self.ui = None
        self.setup_menu = None
        self.side_selection_menu = None
        self.images = None
        self.units_to_deploy = None
        self.current_deploying_unit = None
        self.selected_unit = None
        self.possible_moves = []
        self.moved_units = set()  # Unidades que ya han movido en este turno
        self.attacked_units = set()  # Unidades que ya han atacado en este turno
        self.current_turn_side = None  # Bandos del turno actual
        self.last_moved_unit_pos = None  # Tupla con (posición original, posición nueva) de la última unidad movida

    @staticmethod
    def _load_unit_images():
        global size
        images = {}
        for key, path in config.IMAGE_PATHS.items():
            if key in {"board","cover","reglas","rules"}: continue
            try:
                img = pygame.image.load(path).convert_alpha()
                # Usar el tamaño más pequeño entre ancho y alto para que las unidades quepan bien en los hexágonos
                size = int(min(config.HEX_WIDTH, config.HEX_HEIGHT) * 0.85)
                images[key] = pygame.transform.smoothscale(img, (size, size))
            except Exception as e:
                print(f"{_('Error loading')} {path}: {e}")
                images[key] = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(images[key], (0, 255, 0), (size // 2, size // 2), size // 2)

        return images

    @staticmethod
    def _load_sounds():
        sounds = {}
        for key, path in config.AUDIO_PATHS.items():
            try:
                if key in ["arabesque", "victory", "defeat"]:
                    # Estos son archivos de música que se reproducirán con pygame.mixer.music
                    sounds[key] = path  # Solo guardamos la ruta
                else:
                    # Efectos de sonido que se reproducirán con pygame.mixer.Sound
                    sounds[key] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"{_('Error loading audio')} {path}: {e}")
        return sounds

    @staticmethod
    def _load_rules():
        try:
            os.startfile(config.IMAGE_PATHS["rules"] if CURRENT_LANGUAGE == 'en' else config.IMAGE_PATHS["reglas"])
        except AttributeError:  # Para otros sistemas operativos
            print(_('Error loading rules file'))

    @staticmethod
    def _get_initial_units():
        """Devuelve las unidades iniciales para cada bando."""
        return {
            config.SIDE_CRUSADERS: [
                Ricardo(), Templario(), Hospitalario(),
                Caballero(), Caballero(), Caballero(),
                *[Infanteria() for _ in range(6)],
                *[Bagaje() for _ in range(4)]
            ],
            config.SIDE_SARACENS: [
                Saladino(),
                *[Mameluco() for _ in range(4)],
                *[Arquero() for _ in range(6)],
                *[Explorador() for _ in range(5)]
            ]
        }

    def get_current_turn(self):
        return self.state

    def get_current_turn_phase(self):
        return self.turn_phase

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False

            # Manejar eventos de la pantalla de introducción
            if self.state == config.GAME_STATES["INTRO"]:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Saltar la introducción si se hace clic
                    self._end_intro()
                continue

            # Si el juego ha terminado, solo procesar eventos de salida
            if self.game_over:
                continue

            # Primero manejar eventos de UI (scroll)
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                              pygame.MOUSEMOTION, pygame.MOUSEWHEEL):
                if self.ui.handle_scroll_event(event):
                    continue  # Si el UI consumió el evento, no procesarlo más

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                button_rect = self.ui.get_button_rect()
                rules_button_rect = self.ui.get_rules_button()

                # Manejar botón de reglas
                if rules_button_rect.collidepoint(mouse_pos):
                    self._load_rules()
                    continue

                # Manejar botón de finalizar fase
                if button_rect and button_rect.collidepoint(mouse_pos):
                    self._end_player_turn()
                    continue

                # Manejo específico por estado y fase
                if self.state == config.GAME_STATES["SETUP_MENU"]:
                    self._handle_setup_menu(event)
                elif self.state == config.GAME_STATES["SELECT_SIDE"]:
                    self._handle_side_selection(event)
                elif self.state == config.GAME_STATES["DEPLOY_PLAYER"]:
                    self._handle_deployment(event)
                elif self.state == config.GAME_STATES["PLAYER_TURN"]:
                    if self.turn_phase == config.TURN_PHASES["MOVEMENT"]:
                        self._handle_movement_phase(event)
                    elif self.turn_phase == config.TURN_PHASES["COMBAT"]:
                        self._handle_combat_phase(event)  # Asegurar que se llama aquí

    def _handle_movement_phase(self, event):
        """Maneja la fase de movimiento (existente)"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            pos_x = (config.SCREEN_WIDTH - self.tablero_escalado.get_width() - config.PANEL_WIDTH) // 2
            pos_y = (config.SCREEN_HEIGHT - self.tablero_escalado.get_height() - config.LOG_PANEL_HEIGHT) // 2
            tablero_rect = pygame.Rect(pos_x, pos_y, self.tablero_escalado.get_width(),
                                       self.tablero_escalado.get_height())

            if tablero_rect.collidepoint(mouse_pos):
                self._handle_board_click(mouse_pos, event.button)

    def _handle_combat_phase(self, event):
        """Maneja los eventos durante la fase de combate"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Verificar si es un clic derecho y hay un atacante seleccionado
            if event.button == 3 and self.combat_attacker:
                # Cancelar la selección del atacante
                self.ui.add_log_message(_("Selección de {} cancelada").format(_(self.combat_attacker.image_key)))
                self.combat_attacker = None
                self.combat_targets = []
                return

            mouse_pos = pygame.mouse.get_pos()

            # Primero verificar si se hizo clic en el botón de finalizar fase
            button_rect = self.ui.get_button_rect()
            if button_rect and button_rect.collidepoint(mouse_pos):
                self._end_current_phase()
                return

            # Verificar clic en el tablero
            pos_x = (config.SCREEN_WIDTH - self.tablero_escalado.get_width() - config.PANEL_WIDTH) // 2
            pos_y = (config.SCREEN_HEIGHT - self.tablero_escalado.get_height() - config.LOG_PANEL_HEIGHT) // 2
            tablero_rect = pygame.Rect(pos_x, pos_y, self.tablero_escalado.get_width(),
                                       self.tablero_escalado.get_height())
            if tablero_rect.collidepoint(mouse_pos):
                hex_pos = self._get_hex_under_mouse(mouse_pos)
                if hex_pos:
                    row, col = hex_pos
                    self._process_combat_click(row, col)

    def _end_current_phase(self):
        """Finaliza la fase actual y pasa a la siguiente"""
        if self.state == config.GAME_STATES["PLAYER_TURN"]:
            if self.turn_phase == config.TURN_PHASES["MOVEMENT"]:
                self.turn_phase = config.TURN_PHASES["COMBAT"]
                self.ui.add_log_message(_("Fase de combate iniciada"))
                self.moved_units = set()  # Resetear unidades movidas
                self.last_moved_unit_pos = None  # Resetear la última unidad movida
                self.attacked_units = set()  # Resetear unidades atacantes
            elif self.turn_phase == config.TURN_PHASES["COMBAT"]:
                self.turn_phase = config.TURN_PHASES["MOVEMENT"]
                self.state = config.GAME_STATES["AI_TURN"]
                self.ui.add_log_message(_("Turno del jugador finalizado"))
                self._check_unit_recovery()
                self._reset_charging_flags()  # Limpiar flags de carga al final de la fase de combate

        self.selected_unit = None
        self.possible_moves = []
        self.combat_attacker = None
        self.combat_targets = []

    def _reset_charging_flags(self):
        """Resetea los flags de carga de todas las unidades en el tablero"""
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                unit = self.grid.get_unit(row, col)
                if unit:
                    unit.charging_hex = None

    def _get_hex_under_mouse(self, mouse_pos):
        """Encuentra el hexágono bajo el cursor"""
        # Calcular la posición del tablero
        pos_x = (config.SCREEN_WIDTH - self.tablero_escalado.get_width() - config.PANEL_WIDTH) // 2
        pos_y = (config.SCREEN_HEIGHT - self.tablero_escalado.get_height() - config.LOG_PANEL_HEIGHT) // 2

        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                x, y = self.grid.hex_to_pixel(row, col)
                # Aplicar offset del tablero
                x += pos_x
                y += pos_y
                distance = ((mouse_pos[0] - x) ** 2 + (mouse_pos[1] - y) ** 2) ** 0.5
                if distance < config.HEX_MIN_SIZE / 2:
                    return row, col
        return None

    def _load_grid(self):
        """Carga el grid hexagonal"""
        if self.grid is None:
            self.grid = HexGrid()

    def _load_ui(self):
        """Carga la interfaz de usuario"""
        if self.ui is None:
            self.ui = GameUI(self)

    def _load_images(self):
        """Carga las imágenes de las unidades"""
        #if self.images is None:
        self.images = self._load_unit_images()

    def _load_units(self):
        """Carga las unidades iniciales"""
        if self.units_to_deploy is None:
            self.units_to_deploy = self._get_initial_units()

    def _start_game(self, player_side):
        # Cargar componentes necesarios para el juego
        self._load_board()
        self._load_grid()
        self._load_ui()
        self._load_images()
        self._load_units()

        self.player_side = player_side
        self.ai_side = config.SIDE_SARACENS if player_side == config.SIDE_CRUSADERS else config.SIDE_CRUSADERS
        self.state = config.GAME_STATES["DEPLOY_PLAYER"]
        self.current_deploying_unit = self.units_to_deploy[self.player_side].pop(0)
        self.ui.add_log_message(_("Jugando como {player_side}. Comienza el despliegue.").format(player_side=_(self.player_side)))

    def _load_side_selection_menu(self):
        """Carga el menú de selección de bando"""
        if self.side_selection_menu is None:
            self.side_selection_menu = SideSelectionMenu(self.screen)

    def _handle_setup_menu(self, event):
        """Maneja las interacciones con el menú de configuración."""
        action = self.setup_menu.handle_event(event)
        if action:
            if action == "SCALE":
                # Cambiar la escala de pantalla
                self._change_display_scale()
            elif action == "LANGUAGE":
                # Cambiar el idioma
                self._change_language()
            elif action == "DEFAULTS":
                # Restaurar valores predeterminados
                self._restore_defaults()
            elif action == "RULES":
                # Mostrar las reglas
                self._load_rules()
            elif action == "SELECT_SIDE":
                # Ir a la pantalla de selección de bando
                self._load_side_selection_menu()
                self.state = config.GAME_STATES["SELECT_SIDE"]
            elif action == "QUIT":
                # Salir del juego
                print(_("Saliendo del juego"))
                self.running = False

    def _load_board(self):
        """Carga y escala el tablero según la escala actual."""
        if self.tablero_escalado is None:
            # Cargar la imagen del tablero
            board_img = pygame.image.load(config.IMAGE_PATHS["board"]).convert_alpha()

            # Escalar el tablero según la escala actual
            self.tablero_escalado = pygame.transform.smoothscale(
                board_img,
                (int(config.TABLERO_REAL_WIDTH * config.ESCALA), int(config.TABLERO_REAL_HEIGHT * config.ESCALA))
            )

    def _change_display_scale(self, scale: float = None):
        """Cambia la escala de pantalla."""
        # Ciclar entre diferentes escalas (40%, 50%, 60%, 75%)
        scales = [0.4, 0.5, 0.6, 0.75]

        import config

        if scale == config.DISPLAY_SCALING:
            return False
        elif scale in scales:
            config.DISPLAY_SCALING = scale
        else:
            current_index = scales.index(config.DISPLAY_SCALING) if config.DISPLAY_SCALING in scales else 0
            next_index = (current_index + 1) % len(scales)
            config.DISPLAY_SCALING = scales[next_index]

        # Actualizar dimensiones de pantalla
        config.SCREEN_WIDTH = config.TABLERO_REAL_WIDTH * config.DISPLAY_SCALING + 300
        config.SCREEN_HEIGHT = config.TABLERO_REAL_HEIGHT * config.DISPLAY_SCALING + 170

        # Ajustar el ancho y alto de los botones según la escala
        config.MENU_BUTTON_WIDTH = max(260 * config.DISPLAY_SCALING / 0.75, 200)
        config.MENU_BUTTON_HEIGHT = max(50 * config.DISPLAY_SCALING / 0.75, 40)

        # Ajustar las posiciones verticales del título y los botones
        config.TITLE_Y = int(200 * config.DISPLAY_SCALING / 0.75)
        config.OPTIONS_Y = int(300 * config.DISPLAY_SCALING / 0.75)

        # Ajustar el espaciado entre opciones
        config.OPTIONS_SPACING = int(100 * config.DISPLAY_SCALING / 0.75)

        # Recalcular ESCALA basado en las nuevas dimensiones
        config.AVAILABLE_WIDTH = config.SCREEN_WIDTH - config.PANEL_WIDTH
        config.AVAILABLE_HEIGHT = config.SCREEN_HEIGHT - config.LOG_PANEL_HEIGHT
        config.ESCALA = min(config.AVAILABLE_WIDTH / config.TABLERO_REAL_WIDTH, config.AVAILABLE_HEIGHT / config.TABLERO_REAL_HEIGHT)

        # Recalcular dimensiones de hexágonos
        config.HEX_HEIGHT = int(config.HEX_REAL_HEIGHT * config.ESCALA)
        config.HEX_WIDTH = int(config.HEX_REAL_WIDTH * config.ESCALA)
        config.HEX_SIZE = config.HEX_WIDTH  # Mantenemos config.HEX_SIZE para compatibilidad
        config.HEX_MIN_SIZE = min(config.HEX_WIDTH, config.HEX_HEIGHT)

        # Recalcular márgenes escalados
        config.MARGENES_ESCALADOS = {
            "superior": int(config.MARGENES["superior"] * config.ESCALA),
            "izquierdo": int(config.MARGENES["izquierdo"] * config.ESCALA)
        }

        # Recrear la pantalla con las nuevas dimensiones
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

        # Reiniciar componentes que dependen del tamaño de la pantalla
        self.setup_menu = None
        self.side_selection_menu = None
        self.tablero_escalado = None
        self.ui = None

        self._load_setup_menu()
        self._load_ui()

        # Mensaje de log en consola
        print(_("Escala de pantalla cambiada a {scale}%").format(scale=int(config.DISPLAY_SCALING * 100)))

    def _change_language(self, language: str =None):
        """Cambia el idioma del juego."""
        global CURRENT_LANGUAGE, _

        # Lista de idiomas disponibles
        available_languages = config.AVAILABLE_LANGUAGES

        # Determinar si el idioma solicitado está entre los disponibles
        if language == CURRENT_LANGUAGE:
            return False
        elif language in available_languages:
            new_language = language
        else:
            # Obtener el siguiente idioma en la lista
            current_index = available_languages.index(CURRENT_LANGUAGE) if CURRENT_LANGUAGE in available_languages else 0
            next_index = (current_index + 1) % len(available_languages)
            new_language = available_languages[next_index]

        # Actualizar la variable global en config.py
        CURRENT_LANGUAGE = new_language

        # Cargar las traducciones para el nuevo idioma
        try:
            translation = gettext.translation(
                TRANSLATION_DOMAIN,
                localedir=LOCALE_DIR,
                languages=[new_language],
                fallback=True
            )
            _ = translation.gettext
            # Instalar la traducción globalmente
            translation.install()

            # Actualizar la función de traducción en todos los módulos que la usan
            import gameui
            gameui._ = _
            import hexgrid
            hexgrid._ = _
            import menu
            menu._ = _
            import units
            units._ = _
            # Actualizar la función de traducción en el módulo actual (game.py)
            import sys
            current_module = sys.modules[__name__]
            current_module._ = _

            self._load_setup_menu()

            # Mensaje de éxito (usando formato de cadena normal en lugar de f-string con _())
            language_changed_msg = _("Idioma cambiado a: {lang}")
            if self.ui is not None:
                self.ui.add_log_message(language_changed_msg.format(lang=new_language))
            print(f"{_('Idioma cambiado a:')} {new_language}")
            return True
        except Exception as e:
            if self.ui is not None:
                self.ui.add_log_message(_("Error al cambiar idioma"))
            print(f"{_('Error al cambiar idioma')}: {e}")
            return False

    def _restore_defaults(self):
        """Restaura los valores predeterminados."""

        if config.DISPLAY_SCALING != 0.5:
            self._change_display_scale(0.5)

        # Intentar obtener el idioma del sistema
        try:
            current_locale, encoding = locale.getlocale()
            if current_locale is None:
                language = 'es'  # Idioma por defecto: español
            else:
                language = current_locale.split('_')[0]
                # Asegurarse de que el idioma sea uno de los disponibles
                if language not in ['es', 'en']:
                    language = 'es'  # Si no es un idioma soportado, usar español
        except (ValueError, AttributeError):
            language = 'es'  # Idioma por defecto si hay algún error

        # Cambiar el idioma si no es el predeterminado
        if CURRENT_LANGUAGE != language:
            self._change_language(language)
        else:
            # Recargar los componentes necesarios para el estado actual
            self._load_setup_menu()

        # Mensaje de log
        print(_("Valores predeterminados restaurados"))

    def _handle_side_selection(self, event):
        side = self.side_selection_menu.handle_event(event)
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
                    _("Colocado {}. Siguiente unidad lista.").format(_(self.current_deploying_unit.image_key))
                )
            else:
                self.current_deploying_unit = None
                self.ui.add_log_message(_("¡Despliegue completado!"))
        else:
            self.ui.add_log_message(_("Posición inválida para despliegue"))

    def _end_player_turn(self):
        """Maneja la finalización del turno del jugador o fase de despliegue"""
        if self.state == config.GAME_STATES["DEPLOY_PLAYER"] and not self.current_deploying_unit:
            # Confirmar despliegue del jugador
            self.state = config.GAME_STATES["DEPLOY_AI"]
            self.ui.add_log_message(_("Despliegue confirmado. El ordenador está desplegando"))

            # Limpiar selecciones
            self.selected_unit = None
            self.possible_moves = []

            # Iniciar despliegue de la IA
            self._ai_deploy_units()

        elif self.state == config.GAME_STATES["PLAYER_TURN"]:
            if self.turn_phase == config.TURN_PHASES["MOVEMENT"]:
                # Pasar a fase de combate
                self.turn_phase = config.TURN_PHASES["COMBAT"]
                self.ui.add_log_message(_("Fase de combate iniciada"))
                self.moved_units = set()  # Resetear unidades movidas
                self.last_moved_unit_pos = None  # Resetear la última unidad movida
                self.attacked_units = set()  # Resetear unidades atacantes

            elif self.turn_phase == config.TURN_PHASES["COMBAT"]:
                # Finalizar turno completo
                self.turn_phase = config.TURN_PHASES["MOVEMENT"]
                self.state = config.GAME_STATES["AI_TURN"]
                self.current_turn_side = self.ai_side
                self.ui.add_log_message(_("Turno del jugador finalizado"))
                self._check_unit_recovery()

    def _handle_board_click(self, mouse_pos, button=1):
        # Calcular la posición del tablero
        pos_x = (config.SCREEN_WIDTH - self.tablero_escalado.get_width() - config.PANEL_WIDTH) // 2
        pos_y = (config.SCREEN_HEIGHT - self.tablero_escalado.get_height() - config.LOG_PANEL_HEIGHT) // 2

        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                x, y = self.grid.hex_to_pixel(row, col)
                # Aplicar offset del tablero
                x += pos_x
                y += pos_y

                distance = ((mouse_pos[0] - x) ** 2 + (mouse_pos[1] - y) ** 2) ** 0.5
                if distance < config.HEX_MIN_SIZE / 2:
                    # Mensaje de debug para verificar coordenadas
                    print(_("Has hecho click en coordenadas del grid: ({row}, {col})").format(row=row, col=col))
                    print(_("Posición en píxeles: ({x}, {y})").format(x=x, y=y))

                    self._process_hex_click(row, col, button)
                    return

        # DEBUG: Si no se encontró ningún hexágono
        print(_("Click fuera del tablero o entre hexágonos"))

    def _process_hex_click(self, row, col, button=1):
        unit = self.grid.grid[row][col]

        # Verificar si se hizo clic derecho en la posición de último movimiento (para deshacer)
        if button == 3 and self.last_moved_unit_pos and (row, col) == self.last_moved_unit_pos[0]:
            # Usar directamente la posición de la última unidad movida
            moved_row, moved_col = self.last_moved_unit_pos[1]
            moved_unit = self.grid.grid[moved_row][moved_col]

            if moved_unit:
                # Devolver la unidad a su posición original
                if self.grid.move_unit(moved_row, moved_col, row, col):
                    # Reproducir sonido de cancelar movimiento
                    self._play_sound("cancel_move")
                    # Eliminar la unidad de moved_units
                    self.moved_units.remove((moved_row, moved_col))
                    self.ui.add_log_message(_("{} ha vuelto a su posición original").format(_(moved_unit.image_key)))
                    self.last_moved_unit_pos = None
                    return
            return

        if not self.selected_unit and unit and self._is_player_unit(unit):
            if (row, col) in self.moved_units:
                self.ui.add_log_message(_("Ya has movido a {} este turno").format(_(unit.image_key)))
                return

            # Reproducir sonido de selección
            self._play_sound("select")
            self.selected_unit = (row, col)
            # Asignar el resultado a self.possible_moves
            self.possible_moves = self.grid.get_possible_moves(row, col, unit.speed, self.moved_units)
        elif self.selected_unit and (row, col) in self.possible_moves:
            old_row, old_col = self.selected_unit
            moved_unit = self.grid.grid[old_row][old_col]

            # Verificar si es una unidad cruzada llegando a Arsouf
            if moved_unit.side == config.SIDE_CRUSADERS and (row, col) in self.arsouf_hexes:
                # Unidad llega a Arsouf
                self._unit_reaches_arsouf(moved_unit)
                # Eliminar la unidad del tablero original
                self.grid.grid[old_row][old_col] = None
                self.ui.add_log_message(_("{} ha llegado a Arsouf!").format(_(moved_unit.image_key)))
                # Verificar condición de victoria
                self._check_win_condition()
            else:
                # Movimiento normal
                if self.grid.move_unit(old_row, old_col, row, col):
                    # Reproducir sonido de movimiento
                    self._play_sound("move")
                    self.moved_units.add((row, col))
                    self.last_moved_unit_pos = ((old_row, old_col), (row, col))  # Guardar posiciones original y nueva
                    self._set_charging_hex(old_row, old_col, row, col)

            self.selected_unit = None
            self.possible_moves = []
        else:
            self.selected_unit = None
            self.possible_moves = []

    def _set_charging_hex(self, old_row, old_col, row, col):
        """Fija el hexágono sobre el que un caballero cruzado está cargando"""
        # Verificar si es un caballero cruzado para posible carga
        moved_unit = self.grid.grid[row][col]
        if (isinstance(moved_unit, Caballero) or 
            isinstance(moved_unit, Templario) or 
            isinstance(moved_unit, Hospitalario)):

            # Diccionario de direcciones de carga posibles
            directions = {
                (0, -2): (0, -3),    # O
                (-2, -1): (-3, -1),  # NO
                (-2, 1): (-3, 2),    # NE
                (0, 2): (0, 3),      # E
                (2, 1): (3, 2),      # SE
                (2, -1): (3, -1)     # SO
            }

            # Calcular la dirección del movimiento
            dir = (row - old_row, col - old_col)

            # Comprobar si ha movido dos casillas en la misma dirección
            if dir in directions:
                drow, dcol = directions[dir]
                next_row, next_col = old_row + drow, old_col + dcol

                # Verificar si el hexágono está dentro del tablero
                if (0 <= next_row < self.grid.rows and 0 <= next_col < self.grid.cols):
                    # Verificar si hay una unidad sarracena en ese hexágono
                    target_unit = self.grid.get_unit(next_row, next_col)
                    if target_unit and target_unit.side == config.SIDE_SARACENS:
                        # Establecer el hexágono de carga
                        moved_unit.charging_hex = (next_row, next_col)
                        self.ui.add_log_message(_("{unit_type} cargando sobre {target} en ({next_row},{next_col})!").format(
                            unit_type=_(moved_unit.image_key),
                            target=_(target_unit.image_key),
                            next_row=next_row,
                            next_col=next_col
                        ))

    def _is_player_unit(self, unit):
        """Verifica si una unidad pertenece al jugador."""
        return unit.side == self.player_side

    def _ai_deploy_units(self):
        if not self.units_to_deploy[self.ai_side]:
            self.state = config.GAME_STATES["PLAYER_TURN"]
            return

        # Obtener todas las posiciones válidas de despliegue
        valid_positions = []
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                if self.grid.grid[row][col] is None and self.grid.is_in_deployment_zone(row, col, self.ai_side):
                    valid_positions.append((row, col))

        if not valid_positions:
            return

        # Estrategia específica según el bando de la IA
        if self.ai_side == config.SIDE_CRUSADERS:
            # Estrategia para Cruzados: proteger bagajes cerca del borde derecho

            # Buscar unidades de bagaje para desplegar primero
            bagaje_units = [u for u in self.units_to_deploy[self.ai_side] if isinstance(u, Bagaje)]
            if bagaje_units:
                unit = bagaje_units[0]
                self.units_to_deploy[self.ai_side].remove(unit)

                # Posicionar bagajes en el borde derecho (columnas altas)
                right_edge_positions = [pos for pos in valid_positions if pos[1] >= config.HEX_COLS - 3]
                if right_edge_positions:
                    row, col = random.choice(right_edge_positions)
                else:
                    row, col = random.choice(valid_positions)
            else:
                # Buscar unidades de infantería para formar un muro protector
                infantry_units = [u for u in self.units_to_deploy[self.ai_side] if isinstance(u, Infanteria)]
                if infantry_units:
                    unit = infantry_units[0]
                    self.units_to_deploy[self.ai_side].remove(unit)

                    # Posicionar infantería delante de los bagajes
                    middle_positions = [pos for pos in valid_positions if pos[1] >= config.HEX_COLS - 4 and pos[1] < config.HEX_COLS - 2]
                    if middle_positions:
                        row, col = random.choice(middle_positions)
                    else:
                        row, col = random.choice(valid_positions)
                else:
                    # Buscar a Ricardo para mantenerlo cerca de unidades fuertes
                    ricardo_units = [u for u in self.units_to_deploy[self.ai_side] if isinstance(u, Ricardo)]
                    if ricardo_units:
                        unit = ricardo_units[0]
                        self.units_to_deploy[self.ai_side].remove(unit)

                        # Posicionar a Ricardo en el centro del despliegue
                        center_positions = [pos for pos in valid_positions if pos[1] >= config.HEX_COLS - 3 and pos[1] < config.HEX_COLS - 1]
                        if center_positions:
                            row, col = random.choice(center_positions)
                        else:
                            row, col = random.choice(valid_positions)
                    else:
                        # Desplegar caballeros y otras unidades en el frente
                        unit = random.choice(self.units_to_deploy[self.ai_side])
                        self.units_to_deploy[self.ai_side].remove(unit)

                        # Posicionar caballeros en el frente
                        front_positions = [pos for pos in valid_positions if pos[1] < config.HEX_COLS - 2]
                        if front_positions and (isinstance(unit, Caballero) or isinstance(unit, Templario) or isinstance(unit, Hospitalario)):
                            row, col = random.choice(front_positions)
                        else:
                            row, col = random.choice(valid_positions)
        else:  # SARRACENOS
            # Estrategia para Sarracenos: rodear a los cruzados

            # Buscar a Saladino para mantenerlo cerca de unidades fuertes
            saladino_units = [u for u in self.units_to_deploy[self.ai_side] if isinstance(u, Saladino)]
            if saladino_units:
                unit = saladino_units[0]
                self.units_to_deploy[self.ai_side].remove(unit)

                # Posicionar a Saladino en el centro del despliegue
                center_positions = [pos for pos in valid_positions if 3 <= pos[1] <= 6]
                if center_positions:
                    row, col = random.choice(center_positions)
                else:
                    row, col = random.choice(valid_positions)
            else:
                # Buscar unidades fuertes (Mamelucos) para el centro
                mameluco_units = [u for u in self.units_to_deploy[self.ai_side] if isinstance(u, Mameluco)]
                if mameluco_units:
                    unit = mameluco_units[0]
                    self.units_to_deploy[self.ai_side].remove(unit)

                    # Posicionar Mamelucos en el centro
                    center_positions = [pos for pos in valid_positions if 2 <= pos[1] <= 7]
                    if center_positions:
                        row, col = random.choice(center_positions)
                    else:
                        row, col = random.choice(valid_positions)
                else:
                    # Buscar arqueros para posicionarlos en los flancos
                    arquero_units = [u for u in self.units_to_deploy[self.ai_side] if isinstance(u, Arquero)]
                    if arquero_units:
                        unit = arquero_units[0]
                        self.units_to_deploy[self.ai_side].remove(unit)

                        # Posicionar arqueros en los flancos
                        flank_positions = [pos for pos in valid_positions if pos[1] <= 2 or pos[1] >= 6]
                        if flank_positions:
                            row, col = random.choice(flank_positions)
                        else:
                            row, col = random.choice(valid_positions)
                    else:
                        # Desplegar exploradores en posiciones avanzadas
                        unit = random.choice(self.units_to_deploy[self.ai_side])
                        self.units_to_deploy[self.ai_side].remove(unit)

                        if isinstance(unit, Explorador):
                            # Posicionar exploradores en posiciones avanzadas
                            advanced_positions = [pos for pos in valid_positions if pos[0] < config.HEX_ROWS - 1]
                            if advanced_positions:
                                row, col = random.choice(advanced_positions)
                            else:
                                row, col = random.choice(valid_positions)
                        else:
                            row, col = random.choice(valid_positions)

        # Añadir la unidad al tablero
        self.grid.add_unit(row, col, unit)

        # Mensaje de log para depuración
        self.ui.add_log_message(_("IA despliega {unit_type} en ({row},{col})").format(unit_type=_(unit.image_key), row=row, col=col))

        if not self.units_to_deploy[self.ai_side]:
            self.state = "PLAYER_TURN"

    def _ai_turn(self):
        # 1. Inicializar el turno de la IA si es nuevo
        if not hasattr(self, '_ai_turn_initialized'):
            self.ui.add_log_message(_("Turno del ordenador - Fase de movimiento"))
            self._ai_turn_initialized = True
            self._ai_moved_units_this_turn = set()
            self.turn_phase = config.TURN_PHASES["MOVEMENT"]  # Usar la variable global turn_phase

            # Obtener todas las unidades de la IA
            all_ai_units = [
                (r, c, u) for r in range(self.grid.rows)
                for c in range(self.grid.cols)
                if (u := self.grid.grid[r][c]) and not self._is_player_unit(u)
            ]

            # Ordenar unidades según prioridad estratégica
            if self.ai_side == config.SIDE_CRUSADERS:
                # Para Cruzados: primero mover Ricardo y unidades fuertes, luego infantería, bagajes al final
                leaders = [(r, c, u) for r, c, u in all_ai_units if isinstance(u, Ricardo)]
                strong_units = [(r, c, u) for r, c, u in all_ai_units
                               if isinstance(u, Templario) or isinstance(u, Hospitalario) or isinstance(u, Caballero)]
                infantry = [(r, c, u) for r, c, u in all_ai_units if isinstance(u, Infanteria)]
                baggage = [(r, c, u) for r, c, u in all_ai_units if isinstance(u, Bagaje)]

                # Ordenar por prioridad
                self._ai_units_to_consider = leaders + strong_units + infantry + baggage
            else:  # SARRACENOS
                # Para Sarracenos: primero mover exploradores, luego arqueros, mamelucos y Saladino
                leaders = [(r, c, u) for r, c, u in all_ai_units if isinstance(u, Saladino)]
                explorers = [(r, c, u) for r, c, u in all_ai_units if isinstance(u, Explorador)]
                archers = [(r, c, u) for r, c, u in all_ai_units if isinstance(u, Arquero)]
                mamelucos = [(r, c, u) for r, c, u in all_ai_units if isinstance(u, Mameluco)]

                # Ordenar por prioridad
                self._ai_units_to_consider = explorers + archers + mamelucos + leaders

        # 2. Fase de movimiento
        if self.turn_phase == config.TURN_PHASES["MOVEMENT"]:
            if hasattr(self, '_ai_units_to_consider') and self._ai_units_to_consider:
                row, col, unit = self._ai_units_to_consider.pop()

                if hasattr(self, '_ai_moved_units_this_turn') and (row, col) not in self._ai_moved_units_this_turn:
                    self.possible_moves = self.grid.get_possible_moves(row, col, unit.speed)

                    if self.possible_moves:
                        # Elegir movimiento según estrategia
                        new_row, new_col = self._choose_strategic_move(row, col, unit, self.possible_moves)

                        # Verificar si es una unidad cruzada llegando a Arsouf
                        if unit.side == config.SIDE_CRUSADERS and (new_row, new_col) in self.arsouf_hexes:
                            # Unidad llega a Arsouf
                            self._unit_reaches_arsouf(unit)
                            # Eliminar la unidad del tablero original
                            self.grid.grid[row][col] = None
                            self.ui.add_log_message(_("{} ha llegado a Arsouf!").format(_(unit.image_key)))
                            # Verificar condición de victoria
                            self._check_win_condition()
                        else:
                            # Realizar el movimiento normal
                            self.grid.grid[row][col] = None
                            self.grid.add_unit(new_row, new_col, unit)
                            if hasattr(self, '_ai_moved_units_this_turn'):
                                self._ai_moved_units_this_turn.add((row, col))
                            self.ui.add_log_message(
                                _("{unit_type} mueve desde ({row},{col}) hasta ({new_row}, {new_col})").format(
                                    unit_type=_(unit.image_key),
                                    row=row,
                                    col=col,
                                    new_row=new_row,
                                    new_col=new_col
                                )) #TODO: Identificar instancia específica de unidad (e.g. Explorador 1..)

                            # Añadir un retraso de medio segundo para ralentizar el movimiento de la IA
                            pygame.time.delay(500)

            else:
                # Cuando se completa la fase de movimiento, pasar a la fase de combate
                self.turn_phase = config.TURN_PHASES["COMBAT"]
                self.ui.add_log_message(_("Turno del ordenador - Fase de combate"))
                self._ai_attacked_units_this_turn = set()  # Inicializar conjunto de unidades que ya atacaron

                # Obtener todas las unidades de la IA para la fase de combate
                all_ai_units = [
                    (r, c, u) for r in range(self.grid.rows)
                    for c in range(self.grid.cols)
                    if (u := self.grid.grid[r][c]) and not self._is_player_unit(u)
                ]

                # Ordenar unidades según prioridad estratégica para combate
                self._ai_combat_units = self._prioritize_units_for_combat(all_ai_units)

        # 3. Fase de combate
        elif self.turn_phase == config.TURN_PHASES["COMBAT"]:
            if hasattr(self, '_ai_combat_units') and self._ai_combat_units:
                self._execute_ai_combat()
            else:
                # Cuando se completa la fase de combate, finalizar el turno
                self._end_ai_turn()

        # 4. Finalizar turno si no quedan unidades y estamos en fase de movimiento
        if self.turn_phase == config.TURN_PHASES["MOVEMENT"] and hasattr(self, '_ai_units_to_consider') and not self._ai_units_to_consider:
            self.turn_phase = config.TURN_PHASES["COMBAT"]
            self.ui.add_log_message(_("Turno del ordenador - Fase de combate"))
            self._ai_attacked_units_this_turn = set()  # Inicializar conjunto de unidades que ya atacaron

            # Obtener todas las unidades de la IA para la fase de combate
            all_ai_units = [
                (r, c, u) for r in range(self.grid.rows)
                for c in range(self.grid.cols)
                if (u := self.grid.grid[r][c]) and not self._is_player_unit(u)
            ]

            # Ordenar unidades según prioridad estratégica para combate
            self._ai_combat_units = self._prioritize_units_for_combat(all_ai_units)

    def _end_ai_turn(self):
        self.state = config.GAME_STATES["PLAYER_TURN"]
        self.turn_phase = config.TURN_PHASES["MOVEMENT"]  # Reset to movement phase for player's turn
        self.ui.add_log_message(_("Turno del ordenador finalizado. ¡Te toca!"))
        # Limpiar variables de estado del turno de la IA
        if hasattr(self, '_ai_turn_initialized'):
            del self._ai_turn_initialized
            del self._ai_moved_units_this_turn
            del self._ai_units_to_consider
            if hasattr(self, '_ai_combat_units'):
                del self._ai_combat_units
            if hasattr(self, '_ai_attacked_units_this_turn'):
                del self._ai_attacked_units_this_turn
            # No need to delete turn_phase as it's a shared variable
        self._check_unit_recovery()
        self.selected_unit = None
        self.possible_moves = []
        self._check_win_condition()

    def _unit_reaches_arsouf(self, unit):
        """Registra una unidad que ha llegado a Arsouf"""
        if isinstance(unit, Bagaje):
            self.units_in_arsouf[config.BAGGAGE_NAME] += 1
            self.ui.add_log_message(_("¡Bagaje ha llegado a Arsouf! ({count}/2)").format(count=self.units_in_arsouf[config.BAGGAGE_NAME]))
        else:
            self.units_in_arsouf["other"] += 1
            self.ui.add_log_message(_("¡{unit_type} ha llegado a Arsouf! ({count}/2)").format(unit_type=_(unit.image_key), count=self.units_in_arsouf['other']))

    def _check_win_condition(self):
        """Verifica si se ha cumplido la condición de victoria"""
        # Victoria de los Cruzados: 2 bagajes y 2 otras unidades en Arsouf
        if self.units_in_arsouf[config.BAGGAGE_NAME] >= 2 and self.units_in_arsouf["other"] >= 2:
            self.game_over = True
            self.winner = config.SIDE_CRUSADERS
            self.ui.add_log_message(_("¡VICTORIA DE LOS CRUZADOS! Han llegado suficientes unidades a Arsouf."))

            # Reproducir música de victoria o derrota según el bando del jugador
            if self.player_side == config.SIDE_CRUSADERS:
                self._play_music("victory")
            else:
                self._play_music("defeat")

        # Victoria de los Sarracenos: imposibilidad de que los Cruzados ganen
        # Esto se verificaría si no quedan suficientes unidades cruzadas en el tablero
        crusader_units = self._count_remaining_crusader_units()
        remaining_bagaje = crusader_units[config.BAGGAGE_NAME]
        remaining_other = crusader_units["other"]

        if remaining_bagaje + self.units_in_arsouf[config.BAGGAGE_NAME] < 2 or remaining_other + self.units_in_arsouf["other"] < 2:
            self.game_over = True
            self.winner = config.SIDE_SARACENS
            self.ui.add_log_message(_("¡VICTORIA DE LOS SARRACENOS! Los Cruzados no pueden llegar a Arsouf."))

            # Reproducir música de victoria o derrota según el bando del jugador
            if self.player_side == config.SIDE_SARACENS:
                self._play_music("victory")
            else:
                self._play_music("defeat")

    def _count_remaining_crusader_units(self):
        """Cuenta las unidades cruzadas restantes en el tablero"""
        remaining = {config.BAGGAGE_NAME: 0, "other": 0}

        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                unit = self.grid.grid[row][col]
                if unit and unit.side == config.SIDE_CRUSADERS:
                    if isinstance(unit, Bagaje):
                        remaining[config.BAGGAGE_NAME] += 1
                    else:
                        remaining["other"] += 1

        return remaining

    def _check_unit_recovery(self):
        """Verifica recuperación de todas las unidades heridas"""
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                unit = self.grid.grid[row][col]
                if unit and unit.health == 1:
                    unit.recover(self.grid)

    def _process_combat_click(self, row, col):
        """Procesa clics durante la fase de combate"""
        unit = self.grid.get_unit(row, col)

        # Si no hay atacante seleccionado
        if not self.combat_attacker:
            # Seleccionar atacante (debe ser unidad aliada sana)
            if unit and unit.side == self.player_side and unit.health == 2:
                # Verificar si la unidad ya atacó este turno
                if (row, col) in self.attacked_units:
                    self.ui.add_log_message(_("{} ya ha atacado este turno").format(_(unit.image_key)))
                    return

                # Obtener enemigos adyacentes primero
                self.combat_targets = self.grid.get_adjacent_enemies(row, col, self.player_side)

                # Verificar si hay enemigos adyacentes
                if not self.combat_targets:
                    self.ui.add_log_message(_("No hay enemigos adyacentes para que {} ataque").format(_(unit.image_key)))
                    # No seleccionar la unidad si no hay objetivos
                    self.combat_attacker = None
                else:
                    # Solo seleccionar la unidad si hay objetivos válidos
                    # Reproducir sonido de selección
                    self._play_sound("select")
                    self.combat_attacker = unit
                    self.ui.add_log_message(_("{} seleccionado. Elige objetivo. (Cancelar con click derecho)").format(_(unit.image_key)))
            else:
                self.ui.add_log_message(_("Selecciona una unidad aliada sana para atacar"))
        else:
            # Seleccionar objetivo (debe ser enemigo adyacente)
            if unit and unit in self.combat_targets:
                # Realizar ataque
                is_charging = False
                if isinstance(self.combat_attacker, (Caballero, Templario, Hospitalario)) and unit.side == config.SIDE_SARACENS:
                    # Verificar si es posible una carga
                    is_charging = self.combat_attacker.charge(unit, self.grid)

                if self.combat_attacker.attack(unit, self.grid):
                    # Reproducir sonido de ataque exitoso
                    self._play_sound("success_attack")

                    # Mensaje específico si fue una carga
                    if is_charging:
                        self.ui.add_log_message(
                            _("¡Carga exitosa! {attacker_type} cargó contra {defender_type} y lo hirió").format(
                                attacker_type=_(self.combat_attacker.image_key),
                                defender_type=_(unit.image_key)))
                    else:
                        self.ui.add_log_message(
                            _("¡Ataque exitoso! {attacker_type} hirió a {defender_type}").format(
                                attacker_type=_(self.combat_attacker.image_key),
                                defender_type=_(unit.image_key)))
                else:
                    # Reproducir sonido de ataque fallido
                    self._play_sound("failed_attack")

                    # Mensaje específico si fue una carga
                    if is_charging:
                        self.ui.add_log_message(
                            _("¡Carga fallida! {attacker_type} cargó contra {defender_type} pero no logró herirlo").format(
                                attacker_type=_(self.combat_attacker.image_key),
                                defender_type=_(unit.image_key)))
                    else:
                        self.ui.add_log_message(
                            _("¡Ataque fallido! {} resistió el ataque").format(_(unit.image_key)))

                # Marcar la unidad como ya atacó este turno
                self.attacked_units.add((self.combat_attacker.row, self.combat_attacker.col))

                # Resetear selección después del ataque
                self.combat_attacker = None
                self.combat_targets = []
            else:
                self.ui.add_log_message(_("Objetivo no válido. Selecciona un enemigo adyacente"))

    def _choose_strategic_move(self, row, col, unit, possible_moves):
        """Elige un movimiento estratégico según el tipo de unidad y el bando."""
        if self.ai_side == config.SIDE_CRUSADERS:
            # Estrategia para Cruzados
            if isinstance(unit, Bagaje):
                # Bagajes: Priorizar movimiento hacia Arsouf
                # Verificar si hay un camino directo hacia Arsouf
                path_to_arsouf = self._find_path_to_arsouf(row, col, possible_moves)
                if path_to_arsouf:
                    return path_to_arsouf

                # Si no hay camino directo, mantenerse cerca del borde derecho y alejados de enemigos
                right_edge_moves = [(r, c) for r, c in possible_moves if c >= config.HEX_COLS - 3]
                if right_edge_moves:
                    # Evaluar seguridad: preferir posiciones con menos enemigos cercanos
                    safest_move = self._find_safest_position(right_edge_moves, unit)
                    return safest_move

                # Si no hay movimientos hacia el borde derecho, buscar el más seguro
                return self._find_safest_position(possible_moves, unit)

            elif isinstance(unit, Ricardo):
                # Ricardo: Priorizar protección de bagajes en camino a Arsouf
                baggage_positions = self._find_unit_positions(Bagaje)
                if baggage_positions:
                    # Verificar si hay bagajes en camino a Arsouf que necesitan protección
                    baggage_to_protect = self._find_baggage_en_route_to_arsouf(baggage_positions)
                    if baggage_to_protect:
                        return self._find_position_to_protect(baggage_to_protect, possible_moves)

                # Si no hay bagajes que proteger, mantenerse cerca de unidades fuertes
                return self._find_position_near_strong_allies(row, col, possible_moves)

            elif isinstance(unit, Infanteria):
                # Infantería: Priorizar formación de corredor seguro hacia Arsouf
                # Verificar si hay un camino hacia Arsouf que necesita protección
                arsouf_corridor = self._find_corridor_to_arsouf()
                if arsouf_corridor:
                    # Posicionarse en el corredor para protegerlo
                    corridor_positions = self._find_position_in_corridor(arsouf_corridor, possible_moves)
                    if corridor_positions:
                        return corridor_positions

                # Si no hay corredor o no podemos posicionarnos en él, proteger bagajes
                baggage_positions = self._find_unit_positions(Bagaje)
                if baggage_positions:
                    # Moverse para proteger bagajes
                    return self._find_position_to_protect(baggage_positions, possible_moves)
                else:
                    # Si no hay bagajes, moverse hacia el frente
                    return self._find_position_towards_enemy(row, col, possible_moves)

            else:  # Caballeros, Templarios, Hospitalarios
                # Unidades fuertes: Priorizar escolta de bagajes hacia Arsouf
                baggage_positions = self._find_unit_positions(Bagaje)
                if baggage_positions and random.random() < 0.6:  # 60% de probabilidad de proteger bagajes
                    return self._find_position_to_protect(baggage_positions, possible_moves)

                # Si no hay bagajes o decidimos no protegerlos, proteger a Ricardo
                ricardo_positions = self._find_unit_positions(Ricardo)
                if ricardo_positions and random.random() < 0.4:  # 40% de probabilidad de proteger a Ricardo
                    return self._find_position_near_positions(ricardo_positions, possible_moves)
                else:
                    # Avanzar hacia el enemigo
                    return self._find_position_towards_enemy(row, col, possible_moves)
        else:  # SARRACENOS
            # Estrategia para Sarracenos: impedir que los Cruzados lleguen a Arsouf

            # Identificar bagajes cruzados (objetivos prioritarios)
            crusader_baggage = self._find_enemy_baggage()

            # Identificar el corredor hacia Arsouf que debemos bloquear
            arsouf_corridor = self._find_path_to_block_to_arsouf()

            if isinstance(unit, Saladino):
                # Saladino: Coordinar el bloqueo del camino a Arsouf
                if arsouf_corridor and random.random() < 0.7:  # 70% de probabilidad de bloquear el camino
                    blocking_position = self._find_position_to_block_arsouf(arsouf_corridor, possible_moves)
                    if blocking_position:
                        return blocking_position

                # Si no bloqueamos el camino, mantenerse cerca de unidades fuertes (Mamelucos)
                mameluco_positions = self._find_unit_positions(Mameluco)
                if mameluco_positions:
                    return self._find_position_near_positions(mameluco_positions, possible_moves)
                else:
                    # Si no hay mamelucos, moverse hacia el centro
                    return self._find_position_towards_center(possible_moves)

            elif isinstance(unit, Explorador):
                # Exploradores: Priorizar interceptar bagajes cruzados
                if crusader_baggage:
                    intercept_position = self._find_position_to_intercept(crusader_baggage, possible_moves)
                    if intercept_position:
                        return intercept_position

                # Si no hay bagajes para interceptar, rodear al enemigo por los flancos
                return self._find_position_to_flank(row, col, possible_moves)

            elif isinstance(unit, Arquero):
                # Arqueros: Posicionarse para atacar bagajes o bloquear el camino a Arsouf
                if crusader_baggage and random.random() < 0.6:  # 60% de probabilidad de atacar bagajes
                    attack_position = self._find_position_to_attack_baggage(crusader_baggage, possible_moves)
                    if attack_position:
                        return attack_position

                # Si no atacamos bagajes, bloquear el camino a Arsouf
                if arsouf_corridor:
                    blocking_position = self._find_position_to_block_arsouf(arsouf_corridor, possible_moves)
                    if blocking_position:
                        return blocking_position

                # Si no podemos hacer ninguna de las anteriores, mantener distancia media
                return self._find_position_at_medium_range(row, col, possible_moves)

            else:  # Mamelucos
                # Mamelucos: Priorizar atacar bagajes cruzados
                if crusader_baggage:
                    attack_position = self._find_position_to_attack_baggage(crusader_baggage, possible_moves)
                    if attack_position:
                        return attack_position

                # Si no hay bagajes para atacar, bloquear el camino a Arsouf
                if arsouf_corridor:
                    blocking_position = self._find_position_to_block_arsouf(arsouf_corridor, possible_moves)
                    if blocking_position:
                        return blocking_position

                # Si no podemos hacer ninguna de las anteriores, avanzar hacia el enemigo
                return self._find_position_towards_enemy(row, col, possible_moves)

        # Si no se pudo aplicar ninguna estrategia específica, elegir al azar
        return random.choice(possible_moves)

    def _find_safest_position(self, positions, unit):
        """Encuentra la posición más segura (con menos enemigos cercanos)."""
        if not positions:
            return None

        # Evaluar cada posición por la cantidad de enemigos cercanos
        position_safety = {}
        for pos in positions:
            r, c = pos
            enemies_nearby = len(self.grid.get_units_in_radius(r, c, 2))
            position_safety[pos] = -enemies_nearby  # Negativo para ordenar de menos a más enemigos

        # Ordenar por seguridad (menos enemigos primero)
        sorted_positions = sorted(positions, key=lambda pos: position_safety[pos], reverse=True)

        # Devolver la posición más segura, o una aleatoria entre las más seguras
        safest_positions = [pos for pos in sorted_positions
                           if position_safety[pos] == position_safety[sorted_positions[0]]]
        return random.choice(safest_positions)

    def _find_position_near_strong_allies(self, row, col, possible_moves):
        """Encuentra una posición cerca de aliados fuertes."""
        # Buscar unidades fuertes aliadas
        strong_allies = []
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                unit = self.grid.grid[r][c]
                if unit and not self._is_player_unit(unit):
                    if (isinstance(unit, Templario) or isinstance(unit, Hospitalario)
                        or isinstance(unit, Caballero) or isinstance(unit, Mameluco)):
                        strong_allies.append((r, c))

        if not strong_allies:
            return random.choice(possible_moves)

        # Calcular distancia a unidades fuertes
        move_scores = {}
        for move in possible_moves:
            r, c = move
            # Menor distancia a cualquier unidad fuerte
            min_distance = min(abs(r - ally_r) + abs(c - ally_c) for ally_r, ally_c in strong_allies)
            move_scores[move] = -min_distance  # Negativo para ordenar de menor a mayor distancia

        # Ordenar por cercanía a unidades fuertes
        sorted_moves = sorted(possible_moves, key=lambda move: move_scores[move], reverse=True)

        # Devolver una de las mejores opciones
        best_moves = [move for move in sorted_moves[:3]]
        return random.choice(best_moves if best_moves else possible_moves)

    def _find_unit_positions(self, unit_class):
        """Encuentra las posiciones de todas las unidades de un tipo específico."""
        positions = []
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                unit = self.grid.grid[r][c]
                if unit and isinstance(unit, unit_class) and not self._is_player_unit(unit):
                    positions.append((r, c))
        return positions

    def _find_position_to_protect(self, positions_to_protect, possible_moves):
        """Encuentra una posición que ayude a proteger otras unidades."""
        if not positions_to_protect or not possible_moves:
            return random.choice(possible_moves)

        # Calcular posición promedio de las unidades a proteger
        avg_r = sum(r for r, _ in positions_to_protect) / len(positions_to_protect)
        avg_c = sum(c for _, c in positions_to_protect) / len(positions_to_protect)

        # Calcular posiciones que están entre el enemigo y las unidades a proteger
        move_scores = {}
        for move in possible_moves:
            r, c = move
            # Distancia a la posición promedio
            dist_to_protect = ((r - avg_r) ** 2 + (c - avg_c) ** 2) ** 0.5

            # Posición relativa respecto al enemigo (preferir posiciones que estén entre el enemigo y las unidades a proteger)
            enemy_direction = -1 if self.ai_side == config.SIDE_CRUSADERS else 1  # Dirección aproximada del enemigo
            relative_position = c * enemy_direction  # Valor más alto = más cerca del enemigo

            # Combinar factores: queremos estar cerca pero no demasiado
            move_scores[move] = relative_position - 0.5 * dist_to_protect

        # Ordenar por puntuación
        sorted_moves = sorted(possible_moves, key=lambda move: move_scores[move], reverse=True)

        # Devolver una de las mejores opciones
        best_moves = [move for move in sorted_moves[:3]]
        return random.choice(best_moves if best_moves else possible_moves)

    def _find_position_towards_enemy(self, row, col, possible_moves):
        """Encuentra una posición que avance hacia el enemigo."""
        if not possible_moves:
            return None

        # Determinar dirección hacia el enemigo
        enemy_col_direction = -1 if self.ai_side == config.SIDE_CRUSADERS else 1  # Izquierda para Cruzados, Derecha para Sarracenos

        # Evaluar movimientos por avance hacia el enemigo
        move_scores = {}
        for r, c in possible_moves:
            # Avance en la dirección del enemigo
            col_advance = (c - col) * enemy_col_direction

            # Bonus por acercarse a unidades enemigas
            enemy_proximity = 0
            nearby_enemies = self.grid.get_units_in_radius(r, c, 3)
            enemy_proximity = sum(1 for unit in nearby_enemies if self._is_player_unit(unit))

            move_scores[(r, c)] = col_advance + 0.2 * enemy_proximity

        # Ordenar por puntuación
        sorted_moves = sorted(possible_moves, key=lambda move: move_scores[move], reverse=True)

        # Devolver una de las mejores opciones (con algo de aleatoriedad)
        best_moves = sorted_moves[:max(1, len(sorted_moves) // 3)]
        return random.choice(best_moves)

    def _find_position_near_positions(self, target_positions, possible_moves):
        """Encuentra una posición cercana a las posiciones objetivo."""
        if not target_positions or not possible_moves:
            return random.choice(possible_moves)

        # Calcular distancia a las posiciones objetivo
        move_scores = {}
        for move in possible_moves:
            r, c = move
            # Menor distancia a cualquier posición objetivo
            min_distance = min(abs(r - target_r) + abs(c - target_c)
                              for target_r, target_c in target_positions)
            move_scores[move] = -min_distance  # Negativo para ordenar de menor a mayor distancia

        # Ordenar por cercanía
        sorted_moves = sorted(possible_moves, key=lambda move: move_scores[move], reverse=True)

        # Devolver una de las mejores opciones
        best_moves = [move for move in sorted_moves[:3]]
        return random.choice(best_moves if best_moves else possible_moves)

    def _find_position_to_flank(self, row, col, possible_moves):
        """Encuentra una posición que permita flanquear al enemigo."""
        if not possible_moves:
            return None

        # Para flanquear, preferimos movernos hacia los lados y avanzar
        move_scores = {}
        for r, c in possible_moves:
            # Avance hacia el enemigo
            forward_score = (r - row) if self.ai_side == config.SIDE_SARACENS else (row - r)

            # Movimiento lateral (flanqueo)
            lateral_movement = abs(c - col)

            # Combinar factores
            move_scores[(r, c)] = forward_score + 0.5 * lateral_movement

        # Ordenar por puntuación
        sorted_moves = sorted(possible_moves, key=lambda move: move_scores[move], reverse=True)

        # Devolver una de las mejores opciones
        best_moves = sorted_moves[:max(1, len(sorted_moves) // 3)]
        return random.choice(best_moves)

    def _find_position_at_medium_range(self, row, col, possible_moves):
        """Encuentra una posición a distancia media del enemigo (para arqueros)."""
        if not possible_moves:
            return None

        # Buscar unidades enemigas
        enemy_positions = []
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                unit = self.grid.grid[r][c]
                if unit and self._is_player_unit(unit):
                    enemy_positions.append((r, c))

        if not enemy_positions:
            return random.choice(possible_moves)

        # Calcular distancia óptima (queremos estar a distancia media, ni muy cerca ni muy lejos)
        optimal_distance = 3  # Distancia ideal para arqueros

        move_scores = {}
        for move in possible_moves:
            r, c = move
            if enemy_positions:
                # Calcular distancia al enemigo más cercano
                min_distance = min(abs(r - enemy_r) + abs(c - enemy_c)
                                  for enemy_r, enemy_c in enemy_positions)

                # Penalizar desviaciones de la distancia óptima
                distance_score = -abs(min_distance - optimal_distance)

                move_scores[move] = distance_score
            else:
                move_scores[move] = 0

        # Ordenar por puntuación
        sorted_moves = sorted(possible_moves, key=lambda move: move_scores[move], reverse=True)

        # Devolver una de las mejores opciones
        best_moves = sorted_moves[:max(1, len(sorted_moves) // 3)]
        return random.choice(best_moves)

    def _find_position_towards_center(self, possible_moves):
        """Encuentra una posición hacia el centro del tablero."""
        if not possible_moves:
            return None

        # Calcular centro del tablero
        center_r = self.grid.rows // 2
        center_c = self.grid.cols // 2

        # Evaluar movimientos por cercanía al centro
        move_scores = {}
        for r, c in possible_moves:
            distance_to_center = abs(r - center_r) + abs(c - center_c)
            move_scores[(r, c)] = -distance_to_center  # Negativo para ordenar de menor a mayor distancia

        # Ordenar por puntuación
        sorted_moves = sorted(possible_moves, key=lambda move: move_scores[move], reverse=True)

        # Devolver una de las mejores opciones
        best_moves = sorted_moves[:max(1, len(sorted_moves) // 3)]
        return random.choice(best_moves)

    def _find_path_to_arsouf(self, row, col, possible_moves):
        """Encuentra el mejor movimiento para acercarse a Arsouf."""
        if not possible_moves:
            return None

        # Calcular distancia a Arsouf para cada movimiento posible
        move_scores = {}
        for r, c in possible_moves:
            # Calcular distancia mínima a cualquiera de los hexágonos de Arsouf
            min_distance = min(abs(r - arsouf_r) + abs(c - arsouf_c)
                              for arsouf_r, arsouf_c in self.arsouf_hexes)

            # Evaluar seguridad (menos enemigos cercanos es mejor)
            enemies_nearby = len([u for u in self.grid.get_units_in_radius(r, c, 2)
                                 if u.side != self.ai_side])

            # Combinar factores: distancia a Arsouf (más importante) y seguridad
            move_scores[(r, c)] = -min_distance * 2 - enemies_nearby

        # Ordenar por puntuación (mejor primero)
        sorted_moves = sorted(possible_moves, key=lambda move: move_scores[move], reverse=True)

        # Devolver el mejor movimiento, o uno aleatorio entre los mejores
        best_moves = sorted_moves[:max(1, len(sorted_moves) // 4)]
        return random.choice(best_moves)

    def _find_baggage_en_route_to_arsouf(self, baggage_positions):
        """Identifica bagajes que están en camino hacia Arsouf y necesitan protección."""
        if not baggage_positions:
            return []

        # Filtrar bagajes que están en camino a Arsouf (más cerca que la media)
        baggage_en_route = []

        # Calcular distancia media de todos los bagajes a Arsouf
        total_distance = 0
        for r, c in baggage_positions:
            min_distance = min(abs(r - arsouf_r) + abs(c - arsouf_c)
                              for arsouf_r, arsouf_c in self.arsouf_hexes)
            total_distance += min_distance

        avg_distance = total_distance / len(baggage_positions) if baggage_positions else float('inf')

        # Seleccionar bagajes que están más cerca de Arsouf que la media
        for r, c in baggage_positions:
            min_distance = min(abs(r - arsouf_r) + abs(c - arsouf_c)
                              for arsouf_r, arsouf_c in self.arsouf_hexes)
            if min_distance <= avg_distance:
                baggage_en_route.append((r, c))

        return baggage_en_route

    def _find_corridor_to_arsouf(self):
        """Identifica un corredor estratégico hacia Arsouf."""
        # Definir un corredor aproximado hacia Arsouf
        # Este corredor es una lista de hexágonos que forman un camino seguro

        # Simplificación: definir un corredor desde el centro del despliegue hacia Arsouf
        corridor = []

        # Encontrar el centro aproximado del despliegue de los Cruzados
        crusader_units = []
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                unit = self.grid.grid[r][c]
                if unit and unit.side == config.SIDE_CRUSADERS:
                    crusader_units.append((r, c))

        if not crusader_units:
            return []

        # Calcular centro de las unidades cruzadas
        avg_r = sum(r for r, _ in crusader_units) / len(crusader_units)
        avg_c = sum(c for _, c in crusader_units) / len(crusader_units)

        # Definir un corredor desde el centro hacia Arsouf
        # Simplificación: usar una línea recta
        for i in range(10):  # Limitar a 10 hexágonos
            # Interpolar entre el centro y Arsouf
            t = i / 10.0
            r = int(avg_r * (1 - t) + self.arsouf_hexes[0][0] * t)
            c = int(avg_c * (1 - t) + self.arsouf_hexes[0][1] * t)

            # Verificar que el hexágono es válido
            if 0 <= r < self.grid.rows and 0 <= c < self.grid.cols:
                corridor.append((r, c))

        return corridor

    def _find_position_in_corridor(self, corridor, possible_moves):
        """Encuentra la mejor posición dentro del corredor hacia Arsouf."""
        if not corridor or not possible_moves:
            return None

        # Encontrar movimientos que están en el corredor
        corridor_moves = [move for move in possible_moves if move in corridor]

        if corridor_moves:
            # Preferir posiciones más cercanas a Arsouf
            move_scores = {}
            for r, c in corridor_moves:
                min_distance = min(abs(r - arsouf_r) + abs(c - arsouf_c)
                                  for arsouf_r, arsouf_c in self.arsouf_hexes)
                move_scores[(r, c)] = -min_distance

            # Ordenar por cercanía a Arsouf
            sorted_moves = sorted(corridor_moves, key=lambda move: move_scores[move], reverse=True)
            return sorted_moves[0] if sorted_moves else None

        # Si no hay movimientos en el corredor, encontrar el más cercano al corredor
        closest_to_corridor = None
        min_corridor_distance = float('inf')

        for move_r, move_c in possible_moves:
            for corr_r, corr_c in corridor:
                dist = abs(move_r - corr_r) + abs(move_c - corr_c)
                if dist < min_corridor_distance:
                    min_corridor_distance = dist
                    closest_to_corridor = (move_r, move_c)

        return closest_to_corridor

    def _find_enemy_baggage(self):
        """Encuentra las posiciones de los bagajes enemigos (Cruzados)."""
        baggage_positions = []

        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                unit = self.grid.grid[r][c]
                if unit and unit.side == config.SIDE_CRUSADERS and isinstance(unit, Bagaje):
                    baggage_positions.append((r, c))

        return baggage_positions

    def _find_path_to_block_to_arsouf(self):
        """Identifica el camino más probable que los Cruzados usarán para llegar a Arsouf."""
        # Encontrar todas las unidades cruzadas
        crusader_units = []
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                unit = self.grid.grid[r][c]
                if unit and unit.side == config.SIDE_CRUSADERS:
                    crusader_units.append((r, c))

        if not crusader_units:
            return []

        # Dar prioridad a los bagajes
        baggage_units = [(r, c) for r, c in crusader_units
                         if isinstance(self.grid.grid[r][c], Bagaje)]

        # Si hay bagajes, usar su posición como punto de partida
        if baggage_units:
            # Calcular el centro de los bagajes
            avg_r = sum(r for r, _ in baggage_units) / len(baggage_units)
            avg_c = sum(c for _, c in baggage_units) / len(baggage_units)
        else:
            # Si no hay bagajes, usar el centro de todas las unidades cruzadas
            avg_r = sum(r for r, _ in crusader_units) / len(crusader_units)
            avg_c = sum(c for _, c in crusader_units) / len(crusader_units)

        # Crear un camino desde el punto de partida hasta Arsouf
        path = []

        # Simplificación: usar una línea recta
        for i in range(15):  # Limitar a 15 hexágonos
            # Interpolar entre el punto de partida y Arsouf
            t = i / 15.0
            r = int(avg_r * (1 - t) + self.arsouf_hexes[0][0] * t)
            c = int(avg_c * (1 - t) + self.arsouf_hexes[0][1] * t)

            # Verificar que el hexágono es válido
            if 0 <= r < self.grid.rows and 0 <= c < self.grid.cols:
                path.append((r, c))

        return path

    def _find_position_to_block_arsouf(self, path_to_block, possible_moves):
        """Encuentra la mejor posición para bloquear el camino a Arsouf."""
        if not path_to_block or not possible_moves:
            return None

        # Calcular la distancia de cada posición a Arsouf
        arsouf_distances = {}
        for r, c in path_to_block:
            min_distance = min(abs(r - arsouf_r) + abs(c - arsouf_c)
                              for arsouf_r, arsouf_c in self.arsouf_hexes)
            arsouf_distances[(r, c)] = min_distance

        # Ordenar el camino por distancia a Arsouf (más cercano primero)
        sorted_path = sorted(path_to_block, key=lambda pos: arsouf_distances[pos])

        # Intentar bloquear el camino lo más cerca posible de Arsouf
        for path_r, path_c in sorted_path:
            # Buscar movimientos cercanos a este punto del camino
            for move_r, move_c in possible_moves:
                dist = abs(move_r - path_r) + abs(move_c - path_c)
                if dist <= 1:  # Adyacente o en el mismo hexágono
                    return (move_r, move_c)

        # Si no podemos bloquear directamente, encontrar el movimiento más cercano al camino
        best_move = None
        min_dist = float('inf')

        for move_r, move_c in possible_moves:
            for path_r, path_c in sorted_path[:5]:  # Considerar solo los 5 hexágonos más cercanos a Arsouf
                dist = abs(move_r - path_r) + abs(move_c - path_c)
                if dist < min_dist:
                    min_dist = dist
                    best_move = (move_r, move_c)

        return best_move

    def _find_position_to_intercept(self, baggage_positions, possible_moves):
        """Encuentra la mejor posición para interceptar bagajes enemigos."""
        if not baggage_positions or not possible_moves:
            return None

        # Calcular la distancia de cada bagaje a Arsouf
        baggage_to_arsouf = {}
        for r, c in baggage_positions:
            min_distance = min(abs(r - arsouf_r) + abs(c - arsouf_c)
                              for arsouf_r, arsouf_c in self.arsouf_hexes)
            baggage_to_arsouf[(r, c)] = min_distance

        # Ordenar bagajes por cercanía a Arsouf (más cercano primero)
        sorted_baggage = sorted(baggage_positions, key=lambda pos: baggage_to_arsouf[pos])

        # Priorizar interceptar los bagajes más cercanos a Arsouf
        priority_baggage = sorted_baggage[:2]  # Los 2 más cercanos

        # Encontrar posiciones que intercepten el camino entre los bagajes y Arsouf
        best_move = None
        best_score = float('-inf')

        for move_r, move_c in possible_moves:
            score = 0

            for bag_r, bag_c in priority_baggage:
                # Verificar si estamos en el camino entre el bagaje y Arsouf
                for arsouf_r, arsouf_c in self.arsouf_hexes:
                    # Calcular si el movimiento está en la línea entre el bagaje y Arsouf
                    # Simplificación: usar distancia Manhattan
                    dist_bag_to_arsouf = abs(bag_r - arsouf_r) + abs(bag_c - arsouf_c)
                    dist_bag_to_move = abs(bag_r - move_r) + abs(bag_c - move_c)
                    dist_move_to_arsouf = abs(move_r - arsouf_r) + abs(move_c - arsouf_c)

                    # Si estamos aproximadamente en el camino
                    if abs(dist_bag_to_arsouf - (dist_bag_to_move + dist_move_to_arsouf)) <= 2:
                        # Mejor puntuación si estamos más cerca del bagaje
                        score += 10 - dist_bag_to_move

            if score > best_score:
                best_score = score
                best_move = (move_r, move_c)

        # Si no encontramos una buena posición de intercepción, movernos hacia el bagaje más cercano
        if best_move is None and priority_baggage:
            best_move = self._find_position_near_positions(priority_baggage, possible_moves)

        return best_move

    def _find_position_to_attack_baggage(self, baggage_positions, possible_moves):
        """Encuentra la mejor posición para atacar bagajes enemigos."""
        if not baggage_positions or not possible_moves:
            return None

        # Calcular la distancia de cada movimiento a cada bagaje
        move_scores = {}
        for move_r, move_c in possible_moves:
            # Inicializar puntuación
            move_scores[(move_r, move_c)] = 0

            for bag_r, bag_c in baggage_positions:
                dist = abs(move_r - bag_r) + abs(move_c - bag_c)

                # Puntuación más alta para posiciones adyacentes a bagajes
                if dist <= 1:
                    move_scores[(move_r, move_c)] += 10
                # Puntuación decreciente con la distancia
                else:
                    move_scores[(move_r, move_c)] += max(0, 5 - dist)

        # Ordenar por puntuación
        sorted_moves = sorted(possible_moves, key=lambda move: move_scores[move], reverse=True)

        # Devolver el mejor movimiento, o uno aleatorio entre los mejores
        best_moves = sorted_moves[:max(1, len(sorted_moves) // 4)]
        return random.choice(best_moves)

    def _prioritize_units_for_combat(self, all_ai_units):
        """Prioriza las unidades para el combate según estrategias específicas."""
        # Filtrar unidades que pueden atacar (salud completa)
        combat_ready_units = [(r, c, u) for r, c, u in all_ai_units if u.health == 2]

        # Si no hay unidades listas para combate, retornar lista vacía
        if not combat_ready_units:
            return []

        # Ordenar unidades según prioridad estratégica para combate
        if self.ai_side == config.SIDE_CRUSADERS:
            # Para Cruzados: priorizar unidades fuertes y proteger bagajes
            # 1. Caballeros y unidades de élite
            strong_units = [(r, c, u) for r, c, u in combat_ready_units
                           if isinstance(u, Templario) or isinstance(u, Hospitalario) or isinstance(u, Caballero)]
            # 2. Ricardo (si está en posición de atacar)
            leaders = [(r, c, u) for r, c, u in combat_ready_units if isinstance(u, Ricardo)]
            # 3. Infantería
            infantry = [(r, c, u) for r, c, u in combat_ready_units if isinstance(u, Infanteria)]
            # 4. Bagajes (normalmente no atacan, pero por si acaso)
            baggage = [(r, c, u) for r, c, u in combat_ready_units if isinstance(u, Bagaje)]

            # Ordenar por prioridad
            return strong_units + leaders + infantry + baggage
        else:  # SARRACENOS
            # Para Sarracenos: priorizar atacar bagajes y unidades débiles
            # 1. Mamelucos (unidades fuertes)
            mamelucos = [(r, c, u) for r, c, u in combat_ready_units if isinstance(u, Mameluco)]
            # 2. Arqueros
            archers = [(r, c, u) for r, c, u in combat_ready_units if isinstance(u, Arquero)]
            # 3. Exploradores
            explorers = [(r, c, u) for r, c, u in combat_ready_units if isinstance(u, Explorador)]
            # 4. Saladino (si está en posición de atacar)
            leaders = [(r, c, u) for r, c, u in combat_ready_units if isinstance(u, Saladino)]

            # Ordenar por prioridad
            return mamelucos + archers + explorers + leaders

    def _execute_ai_combat(self):
        """Ejecuta un ataque de la IA según prioridades estratégicas."""
        if not hasattr(self, '_ai_combat_units') or not self._ai_combat_units:
            return

        # Obtener la siguiente unidad para atacar
        row, col, unit = self._ai_combat_units.pop(0)

        # Verificar si la unidad ya atacó este turno
        if hasattr(self, '_ai_attacked_units_this_turn') and (row, col) in self._ai_attacked_units_this_turn:
            return

        # Verificar si la unidad sigue existiendo y está sana
        current_unit = self.grid.get_unit(row, col)
        if not current_unit or current_unit.health != 2 or current_unit != unit:
            return

        # Obtener enemigos adyacentes
        adjacent_enemies = self.grid.get_adjacent_enemies(row, col, self.ai_side)

        # Si no hay enemigos adyacentes, pasar a la siguiente unidad
        if not adjacent_enemies:
            return

        # Seleccionar objetivo según prioridad estratégica
        target = self._select_combat_target(unit, adjacent_enemies)

        # Realizar ataque
        if target:
            if unit.attack(target, self.grid):
                self.ui.add_log_message(
                    f"{_('¡IA ataca!')} {_(unit.image_key)} {_('hirió a')} {_(target.image_key)}")
            else:
                self.ui.add_log_message(
                    f"{_('¡Ataque fallido de IA!')} {_(target.image_key)} {_('resistió el ataque de')} {_(unit.image_key)}")

            # Marcar la unidad como ya atacó este turno
            if hasattr(self, '_ai_attacked_units_this_turn'):
                self._ai_attacked_units_this_turn.add((row, col))

            # Añadir un retraso de 1 segundo para ralentizar el combate de la IA
            pygame.time.delay(1000)

    def _select_combat_target(self, attacker, possible_targets):
        """Selecciona el mejor objetivo para atacar según prioridades estratégicas."""
        if not possible_targets:
            return None

        # Calcular puntuación para cada objetivo
        target_scores = {}

        for target in possible_targets:
            score = 0

            # Prioridad base según tipo de unidad objetivo
            if isinstance(target, Bagaje):
                score += 10  # Máxima prioridad a los bagajes
            elif isinstance(target, Ricardo) or isinstance(target, Saladino):
                score += 8   # Alta prioridad a los líderes
            elif isinstance(target, Templario) or isinstance(target, Hospitalario):
                score += 7   # Alta prioridad a unidades de élite
            elif isinstance(target, Caballero) or isinstance(target, Mameluco):
                score += 6   # Prioridad a unidades fuertes
            elif isinstance(target, Infanteria):
                score += 4   # Prioridad media a infantería
            elif isinstance(target, Arquero):
                score += 3   # Prioridad media-baja a arqueros
            elif isinstance(target, Explorador):
                score += 2   # Baja prioridad a exploradores

            # Bonus por unidades heridas (más fáciles de eliminar)
            if target.health == 1:
                score += 5

            # Estrategias específicas según el bando
            if self.ai_side == config.SIDE_CRUSADERS:
                # Priorizar unidades que amenazan a los bagajes
                if isinstance(target, Explorador) or isinstance(target, Mameluco):
                    score += 3
            else:  # SARRACENOS
                # Priorizar bagajes y unidades que protegen el camino a Arsouf
                if isinstance(target, Bagaje):
                    score += 5
                elif isinstance(target, Infanteria) and self._is_unit_protecting_baggage(target):
                    score += 4

            target_scores[target] = score

        # Seleccionar el objetivo con mayor puntuación
        if target_scores:
            return max(target_scores.items(), key=lambda x: x[1])[0]
        return random.choice(possible_targets)  # Fallback a selección aleatoria

    def _is_unit_protecting_baggage(self, unit):
        """Determina si una unidad está protegiendo bagajes."""
        # Buscar bagajes cercanos
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                baggage_unit = self.grid.get_unit(r, c)
                if baggage_unit and isinstance(baggage_unit, Bagaje) and baggage_unit.side == unit.side:
                    # Calcular distancia Manhattan
                    distance = abs(unit.row - r) + abs(unit.col - c)
                    if distance <= 2:  # Si está a 2 o menos hexágonos de distancia
                        return True
        return False

    def _load_setup_menu(self):
        """Carga el menú de configuración"""
        if self.setup_menu is None:
            self.setup_menu = SetupMenu(self.screen)

    def _end_intro(self):
        """Finaliza la pantalla de introducción y pasa al menú de configuración"""
        self._load_setup_menu()
        self.state = config.GAME_STATES["SETUP_MENU"]

    def _play_music(self, music_key):
        """Reproduce música de fondo"""
        try:
            pygame.mixer.music.load(self.sounds[music_key])
            pygame.mixer.music.play(-1)  # -1 para reproducir en bucle
        except Exception as e:
            print(f"{_('Error reproduciendo música')} {music_key}: {e}")

    def _stop_music(self):
        """Detiene la música de fondo"""
        pygame.mixer.music.stop()

    def _play_sound(self, sound_key):
        """Reproduce un efecto de sonido"""
        try:
            if sound_key in self.sounds:
                self.sounds[sound_key].play()
        except Exception as e:
            print(f"{_('Error reproduciendo sonido')} {sound_key}: {e}")

    def _handle_game_over(self):
        """Maneja el estado de juego terminado"""
        # Este método se llama cuando el juego ha terminado
        # Aquí podríamos mostrar una pantalla de victoria/derrota
        # Por ahora, solo mostramos un mensaje en el log
        pass

    def _draw(self):
        # Cargar la UI para todos los estados del juego
        if self.ui is None:
            self._load_ui()

        # Para estados iniciales, asegurarse de que los componentes necesarios estén cargados
        if self.state == config.GAME_STATES["INTRO"]:
            # Cargar la imagen de portada si es necesario
            if self.images is None or "cover" not in self.images:
                self._load_cover_image()
        elif self.state == config.GAME_STATES["SETUP_MENU"]:
            # Para el menú de configuración, solo necesitamos cargar ese componente
            if self.setup_menu is None:
                self._load_setup_menu()
        elif self.state == config.GAME_STATES["SELECT_SIDE"]:
            # Para el menú de selección de bando, solo necesitamos cargar ese componente
            if self.side_selection_menu is None:
                self._load_side_selection_menu()

        # Dibujar el juego usando la UI
        if self.ui is not None:
            self.ui.draw_game(self)
        else:
            # Fallback en caso de que la UI no se haya podido cargar
            self.screen.fill(COLOR_BG)
            if self.state == config.GAME_STATES["INTRO"] and self.images is not None and "cover" in self.images:
                self.screen.blit(self.images["cover"], (0, 0))

        pygame.display.flip()

    def _load_cover_image(self):
        """Carga solo la imagen de portada"""
        if self.images is None:
            self.images = {}

        try:
            cover_img = pygame.image.load(config.IMAGE_PATHS["cover"]).convert_alpha()
            # Escalar la imagen de portada manteniendo la relación de aspecto
            img_width, img_height = cover_img.get_size()
            aspect_ratio = img_width / img_height

            # Calcular las dimensiones para mantener la relación de aspecto
            if config.SCREEN_WIDTH / config.SCREEN_HEIGHT > aspect_ratio:
                # La pantalla es más ancha que la imagen
                new_width = int(config.SCREEN_HEIGHT * aspect_ratio)
                new_height = config.SCREEN_HEIGHT
            else:
                # La pantalla es más alta que la imagen
                new_width = config.SCREEN_WIDTH
                new_height = int(config.SCREEN_WIDTH / aspect_ratio)

            # Escalar la imagen manteniendo la relación de aspecto
            scaled_img = pygame.transform.scale(cover_img, (new_width, new_height))

            # Crear una superficie del tamaño de la pantalla
            self.images["cover"] = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            self.images["cover"].fill((0, 0, 0))  # Fondo negro

            # Centrar la imagen en la pantalla
            x_offset = (config.SCREEN_WIDTH - new_width) // 2
            y_offset = (config.SCREEN_HEIGHT - new_height) // 2
            self.images["cover"].blit(scaled_img, (x_offset, y_offset))
        except Exception as e:
            print(f"{_('Error loading cover:')} {e}")
            self.images["cover"] = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            self.images["cover"].fill((0, 0, 0))  # Fondo negro

    def run(self):
        """Bucle principal del juego."""
        # Cargar la imagen de portada para la intro
        self._load_cover_image()

        # Iniciar la música de introducción
        self._play_music("arabesque")

        while self.running:
            self._handle_events()

            # Verificar si el juego ha terminado
            if self.game_over:
                self._handle_game_over()
            else:
                # Cargar componentes según el estado actual
                if self.state == config.GAME_STATES["SETUP_MENU"] and self.setup_menu is None:
                    self._load_setup_menu()
                elif self.state == config.GAME_STATES["SELECT_SIDE"] and self.side_selection_menu is None:
                    self._load_side_selection_menu()
                elif self.state in [config.GAME_STATES["DEPLOY_PLAYER"], config.GAME_STATES["DEPLOY_AI"], 
                                   config.GAME_STATES["PLAYER_TURN"], config.GAME_STATES["AI_TURN"]]:
                    # Asegurarse de que todos los componentes necesarios estén cargados
                    if self.grid is None:
                        self._load_grid()
                    if self.ui is None:
                        self._load_ui()
                    if self.tablero_escalado is None:
                        self._load_board()
                    if self.images is None:
                        self._load_images()
                    if self.units_to_deploy is None:
                        self._load_units()

                # Restaurar la lógica original de despliegue
                if self.state == config.GAME_STATES["DEPLOY_AI"]:
                    self._ai_deploy_units()
                elif self.state == config.GAME_STATES["AI_TURN"]:
                    self._ai_turn()

                # Detener la música de introducción cuando comienza el movimiento del jugador
                if self.state == config.GAME_STATES["PLAYER_TURN"] and self.turn_phase == config.TURN_PHASES["MOVEMENT"]:
                    if pygame.mixer.music.get_busy():
                        self._stop_music()

            self._draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()
