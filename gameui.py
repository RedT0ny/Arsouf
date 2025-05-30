# gameui.py
import pygame
from config import *

class GameUI:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont('Arial', 24)
        self.log_font = pygame.font.SysFont('Arial', LOG_FONT_SIZE)
        self.log_messages = []        
        self.log_scroll_position = 0
        self.log_scroll_dragging = False # Estado de arrastre
        self.log_scroll_handle_rect = None
        self.log_scroll_start_y = 0  # Posición inicial del arrastre
        self.log_scroll_start_position = 0  # Posición inicial del scroll
        self.debug_drawn = False # Control mensajes DEBUG

    def _get_visible_lines(self):
        """Calcula cuántas líneas son visibles en el panel con mayor precisión"""
        line_height = LOG_LINE_HEIGHT
        panel_height = LOG_PANEL_HEIGHT - 2 * LOG_MARGIN  # Altura disponible

        # Calcular número exacto de líneas que caben
        visible_lines = panel_height // line_height

        # Asegurar al menos 1 línea visible
        return max(1, visible_lines)

    def _calculate_board_position(self, tablero_surface):
        """Calcula la posición centrada del tablero."""
        pos_x = (SCREEN_WIDTH - tablero_surface.get_width() - PANEL_WIDTH) // 2
        pos_y = (SCREEN_HEIGHT - tablero_surface.get_height() - LOG_PANEL_HEIGHT) // 2
        return pos_x, pos_y

    def draw_log_panel(self):
        try:
            panel_rect = pygame.Rect(0, SCREEN_HEIGHT - LOG_PANEL_HEIGHT, 
                                   LOG_PANEL_WIDTH, LOG_PANEL_HEIGHT)

            # 1. Fondo del panel
            pygame.draw.rect(self.game.screen, (30, 30, 40), panel_rect)

            # 2. Área de texto
            text_area = pygame.Rect(
                panel_rect.x + LOG_MARGIN,
                panel_rect.y + LOG_MARGIN,
                panel_rect.width - 2*LOG_MARGIN - LOG_SCROLLBAR_WIDTH,
                panel_rect.height - 2*LOG_MARGIN
            )

            # 3. Dibujar mensajes (con scroll aplicado)
            visible_lines = self._get_visible_lines()
            total_lines = len(self.log_messages)

            # Ajustar posición del scroll
            self.log_scroll_position = max(0, min(self.log_scroll_position, total_lines - visible_lines))

            # Dibujar líneas visibles
            for i in range(visible_lines):
                line_index = int(self.log_scroll_position) + i
                if 0 <= line_index < len(self.log_messages):
                    msg = self.log_messages[line_index]
                    msg_text = self.log_font.render(msg, True, (220, 220, 220))
                    self.game.screen.blit(msg_text, 
                                        (text_area.x, 
                                         text_area.y + i * LOG_LINE_HEIGHT))

            # 4. Barra de scroll (si es necesaria)
            if total_lines > visible_lines:
                self._draw_log_scrollbar(panel_rect, total_lines, visible_lines)

        except Exception as e:
            print(f"ERROR dibujando panel LOG: {e}")
            raise

    def _draw_log_scrollbar(self, panel_rect, total_lines, visible_lines):
        """Dibuja una barra de scroll altamente visible"""
        # Área de la barra
        scrollbar_rect = pygame.Rect(
            panel_rect.right - LOG_SCROLLBAR_WIDTH - 5,
            panel_rect.y + 5,
            LOG_SCROLLBAR_WIDTH,
            panel_rect.height - 10
        )

        # Fondo de la barra (color sólido)
        pygame.draw.rect(self.game.screen, (80, 80, 100), scrollbar_rect)

        # Mango del scroll (más grande para mejor detección)
        handle_height = max(40, (visible_lines / total_lines) * scrollbar_rect.height)
        handle_y = scrollbar_rect.y + (self.log_scroll_position / total_lines) * (scrollbar_rect.height - handle_height)

        self.log_scroll_handle_rect = pygame.Rect(
            scrollbar_rect.x - 2,  # Extender área de detección
            handle_y - 2,
            scrollbar_rect.width + 4,
            handle_height + 4
        )

        # Dibujar mango con borde
        pygame.draw.rect(self.game.screen, (160, 160, 190), self.log_scroll_handle_rect)
        pygame.draw.rect(self.game.screen, (200, 200, 230), self.log_scroll_handle_rect, 2)

        # Texto de posición (solo debug)
        if __debug__:
            debug_font = pygame.font.SysFont('Arial', 12)
            debug_text = debug_font.render(f"{int(self.log_scroll_position)}/{total_lines}", True, (255, 255, 255))
            self.game.screen.blit(debug_text, (scrollbar_rect.x - 30, scrollbar_rect.y))

    def handle_events(self, event):
        """Manejo completo de eventos de scroll"""
        # Coordenadas del ratón
        mouse_pos = pygame.mouse.get_pos()
        log_panel_rect = pygame.Rect(0, SCREEN_HEIGHT - LOG_PANEL_HEIGHT, 
                                   LOG_PANEL_WIDTH, LOG_PANEL_HEIGHT)

        # Solo manejar eventos en el área del LOG
        if not log_panel_rect.collidepoint(mouse_pos):
            return False

        # Manejar eventos específicos
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_scroll_start(mouse_pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            return self._handle_scroll_end()

        elif event.type == pygame.MOUSEMOTION:
            return self._handle_scroll_drag(mouse_pos)

        elif event.type == pygame.MOUSEWHEEL:
            return self._handle_wheel_scroll(event.y)

        return False

    def _handle_scroll_start(self, mouse_pos):
        """Inicia el arrastre del scroll"""
        if hasattr(self, 'log_scroll_handle_rect') and self.log_scroll_handle_rect:
            if self.log_scroll_handle_rect.collidepoint(mouse_pos):
                self.log_scroll_dragging = True
                self.drag_start_y = mouse_pos[1]
                self.drag_start_position = self.log_scroll_position
#                 if __debug__:
#                     print("DEBUG: Scroll - Arrastre iniciado")
                return True
        return False

    def _handle_scroll_end(self):
        """Finaliza el arrastre del scroll"""
        if self.log_scroll_dragging:
            self.log_scroll_dragging = False
#             if __debug__:
#                 print("DEBUG: Scroll - Arrastre finalizado")
            return True
        return False

    def _handle_scroll_drag(self, mouse_pos):
        """Maneja el arrastre continuo"""
        if not self.log_scroll_dragging:
            return False

        delta_y = mouse_pos[1] - self.drag_start_y
        total_lines = len(self.log_messages)
        visible_lines = self._get_visible_lines()

        if total_lines <= visible_lines:
            return True

        # Cálculo preciso del desplazamiento
        handle_height = self.log_scroll_handle_rect.height
        scroll_area_height = LOG_PANEL_HEIGHT - 2*LOG_MARGIN - handle_height

        if scroll_area_height > 0:
            scroll_ratio = delta_y / scroll_area_height
            max_scroll = total_lines - visible_lines
            self.log_scroll_position = max(0, min(
                self.drag_start_position + scroll_ratio * max_scroll,
                max_scroll
            ))

        return True

    def _handle_wheel_scroll(self, wheel_delta):
        """Maneja el scroll con rueda del ratón con precisión"""
        total_lines = len(self.log_messages)
        visible_lines = self._get_visible_lines()

        if total_lines <= visible_lines:
            return

        # Ajustar la velocidad del scroll (puedes modificar el 3 para cambiar la sensibilidad)
        scroll_delta = wheel_delta * 3

        # Calcular nueva posición con límites
        max_scroll = total_lines - visible_lines
        self.log_scroll_position = max(0, min(self.log_scroll_position - scroll_delta, max_scroll))

        # Debug opcional
#         if __debug__:
#             print(f"DEBUG: Wheel scroll - Delta: {wheel_delta}, Posición: {self.log_scroll_position}/{max_scroll}")

    def add_log_message(self, message):
        """Añade un mensaje al log y ajusta el scroll al final."""
        self.log_messages.append(message)

        # Limitar el número máximo de mensajes almacenados
        if len(self.log_messages) > LOG_MAX_MESSAGES:
            self.log_messages.pop(0)

        # Calcular la posición máxima del scroll
        visible_lines = self._get_visible_lines()
        total_lines = len(self.log_messages)
        max_scroll_position: int = max(0, total_lines - visible_lines)

        # Forzar el scroll al final
        self.log_scroll_position = max_scroll_position

    def handle_deployment_click(self, mouse_pos, game):
        """Maneja el clic durante el despliegue."""
        tablero_rect = pygame.Rect(0, 0, game.tablero_escalado.get_width(), 
                                  game.tablero_escalado.get_height())

        if tablero_rect.collidepoint(mouse_pos):
            return self._get_hex_under_mouse(mouse_pos, game.grid)
        return None

    def _get_hex_under_mouse(self, mouse_pos, grid):
        """Encuentra el hexágono bajo el cursor."""
        for row in range(grid.rows):
            for col in range(grid.cols):
                x, y = grid.hex_to_pixel(row, col)
                distance = ((mouse_pos[0] - x) ** 2 + (mouse_pos[1] - y) ** 2) ** 0.5
                if distance < HEX_SIZE / 2:
                    return row, col
        return None

    def get_button_rect(self):
        """Devuelve el rect del botón actual si existe"""
        if self.game.state == "PLAYER_TURN":
            panel_rect = pygame.Rect(SCREEN_WIDTH - PANEL_WIDTH, 0, PANEL_WIDTH, SCREEN_HEIGHT)
            return pygame.Rect(panel_rect.x + (PANEL_WIDTH - BOTON_WIDTH)//2, 
                             SCREEN_HEIGHT - 80, BOTON_WIDTH, BOTON_HEIGHT)
        elif self.game.state == "DEPLOY_PLAYER" and not getattr(self.game, 'current_deploying_unit', None):
            panel_rect = pygame.Rect(SCREEN_WIDTH - PANEL_WIDTH, 0, PANEL_WIDTH, SCREEN_HEIGHT)
            return pygame.Rect(panel_rect.x + (PANEL_WIDTH - BOTON_WIDTH)//2,
                             SCREEN_HEIGHT - 80, BOTON_WIDTH, BOTON_HEIGHT)
        return None

    def handle_side_selection(self, event):
        """Maneja la selección de bando."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            cruzados_rect, sarracenos_rect = self.draw_side_selection()
            mouse_pos = pygame.mouse.get_pos()

            if cruzados_rect.collidepoint(mouse_pos):
                return "CRUZADOS"
            elif sarracenos_rect.collidepoint(mouse_pos):
                return "SARRACENOS"
        return None

    def draw_side_selection(self):
        """Dibuja la pantalla de selección de lado."""
        self.game.screen.fill(COLOR_BG)

        # Título
        title = self.font.render("Selecciona tu bando:", True, COLOR_TEXTO)
        self.game.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, TITULO_Y))

        # Botón Cruzados
        cruzados_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, OPCIONES_Y, BOTON_WIDTH, BOTON_HEIGHT)
        pygame.draw.rect(self.game.screen, COLOR_CRUZADOS, cruzados_rect)
        cruzados_text = self.font.render("Jugar como Cruzados", True, COLOR_TEXTO)
        self.game.screen.blit(cruzados_text, (cruzados_rect.centerx - cruzados_text.get_width()//2, 
                                            cruzados_rect.centery - cruzados_text.get_height()//2))

        # Botón Sarracenos
        sarracenos_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, OPCIONES_Y + OPCIONES_ESPACIADO, BOTON_WIDTH, BOTON_HEIGHT)
        pygame.draw.rect(self.game.screen, COLOR_SARRACENOS, sarracenos_rect)
        sarracenos_text = self.font.render("Jugar como Sarracenos", True, COLOR_TEXTO)
        self.game.screen.blit(sarracenos_text, (sarracenos_rect.centerx - sarracenos_text.get_width()//2, 
                                             sarracenos_rect.centery - sarracenos_text.get_height()//2))

        pygame.display.flip()
        return cruzados_rect, sarracenos_rect

    def draw_panel(self):
        """Dibuja el panel lateral con información del juego."""
        panel_rect = pygame.Rect(SCREEN_WIDTH - PANEL_WIDTH, 0, PANEL_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.game.screen, (50, 50, 70), panel_rect)
        pygame.draw.rect(self.game.screen, (200, 200, 230), panel_rect, 5)

        # Área de contenido con márgenes
        content_rect = pygame.Rect(
            panel_rect.x + 20,  # Margen izquierdo
            20,                 # Margen superior
            PANEL_WIDTH - 40,   # Ancho disponible
            panel_rect.height - 40  # Altura disponible
        )

        y_offset = content_rect.y

        # 1. Estado del juego (con ajuste automático de texto)
        status_text = self._get_status_text()
        text_width = min(status_text.get_width(), content_rect.width)  # Limitar ancho máximo

        # Centrar horizontalmente dentro del área segura
        text_x = content_rect.x + (content_rect.width - text_width) // 2
        self.game.screen.blit(status_text, (text_x, y_offset))
        y_offset += 40

        # 2. Información de la unidad actual (si aplica)
        if hasattr(self.game, 'current_deploying_unit') and self.game.current_deploying_unit:
            unit_name = type(self.game.current_deploying_unit).__name__
            unit_info = f"Coloca: {unit_name[:12]}" if len(unit_name) > 12 else f"Coloca: {unit_name}"
            unit_text = self.font.render(unit_info, True, COLOR_TEXTO)

            # Ajustar texto si es muy largo
            if unit_text.get_width() > content_rect.width:
                small_font = pygame.font.SysFont('Arial', 18)
                unit_text = small_font.render(unit_info, True, COLOR_TEXTO)

            self.game.screen.blit(unit_text, (content_rect.x, y_offset))
            y_offset += 30

        # 3. Dibujar botón según el estado del juego (sin cambios)
        button_rect = None
        if self.game.state == "PLAYER_TURN":
            button_rect = self._draw_button(panel_rect, "Finalizar Turno", COLOR_BOTON_CANCELAR, SCREEN_HEIGHT - 80)
        elif self.game.state == "DEPLOY_PLAYER" and not getattr(self.game, 'current_deploying_unit', None):
            button_rect = self._draw_button(panel_rect, "Confirmar Despliegue", COLOR_BOTON, SCREEN_HEIGHT - 80)

        return button_rect

    def _get_status_text(self):
        """Devuelve el texto de estado según el estado actual del juego."""
        # Definir máximo ancho disponible (panel_width - márgenes)
        max_width = PANEL_WIDTH - 10  # 10px de margen a cada lado

        if self.game.state == "SELECT_SIDE":
            text = "Selecciona tu bando"
        elif self.game.state == "DEPLOY_PLAYER":
            text = "Despliega tus unidades"
        elif self.game.state == "DEPLOY_AI":
            text = "Despliegue del ordenador"
        elif self.game.state == "PLAYER_TURN":
            phase = " Movimiento" if self.game.turn_phase == "movimiento" else " Combate"
            text = f"{self.game.player_side}: Fase de {phase}"
        elif self.game.state == "AI_TURN":
            text = f"Turno del ordenador ({self.game.ai_side})"  # Eliminamos el bando para acortar
        else:
            text = ""

        # Crear texto renderizado con ajuste de línea si es necesario
        return self._render_fitted_text(text, max_width)

    def _render_fitted_text(self, text, max_width):
        """Renderiza texto que se ajusta al ancho máximo"""
        # Si el texto cabe normalmente
        if self.font.size(text)[0] <= max_width:
            return self.font.render(text, True, COLOR_TEXTO)

        # Si no cabe, reducimos el tamaño de fuente
        small_font = pygame.font.SysFont('Arial', 16)  # Tamaño reducido
        return small_font.render(text, True, COLOR_TEXTO)

    def _draw_button(self, panel_rect, text, color, y_pos):
        """Dibuja un botón en el panel."""
        button_rect = pygame.Rect(panel_rect.x + (PANEL_WIDTH - BOTON_WIDTH)//2, y_pos, BOTON_WIDTH, BOTON_HEIGHT)
        pygame.draw.rect(self.game.screen, color, button_rect)
        button_text = self.font.render(text, True, COLOR_TEXTO)
        self.game.screen.blit(button_text, (button_rect.centerx - button_text.get_width()//2, 
                                         button_rect.centery - button_text.get_height()//2))
        return button_rect

    def draw_deployment_zones(self):
        """Dibuja las zonas de despliegue para cada bando."""
        if self.game.state not in ["DEPLOY_PLAYER", "DEPLOY_AI"]:
            return

        if self.game.player_side == "CRUZADOS":
            # Cruzados: últimas 4 columnas, primeras 4 filas
            player_zone = self._calculate_zone(HEX_COLS - 4, 0, 4, 4)
            ai_zone = self._calculate_zone(0, HEX_ROWS - 2, 8, 2)
        else:
            # Sarracenos: primeras 8 columnas, últimas 2 filas
            player_zone = self._calculate_zone(0, HEX_ROWS - 2, 8, 2)
            ai_zone = self._calculate_zone(HEX_COLS - 4, 0, 4, 4)

        # Dibujar zonas (solo para debug visual)
        if __debug__:
            self._draw_zone(player_zone, COLOR_ZONA_JUGADOR)
            self._draw_zone(ai_zone, COLOR_ZONA_IA)

    def _calculate_zone(self, start_col, start_row, cols, rows):
        """Calcula las coordenadas de una zona de despliegue."""
        hex_width = self.game.grid.hex_width
        hex_height = self.game.grid.hex_height

        # Calcular posición del tablero
        pos_x = -hex_width/2 #(SCREEN_WIDTH - self.game.tablero_escalado.get_width()) // 2
        pos_y = -hex_height/2 #(SCREEN_HEIGHT - self.game.tablero_escalado.get_height()) // 2

        # Calcular esquina superior izquierda de la zona
        x, y = self.game.grid.hex_to_pixel(start_row, start_col)
        x += pos_x
        y += pos_y

        # Calcular ancho y alto aproximado de la zona
        width = cols * hex_width * 1.025
        height = rows * hex_height * 0.79

        return pygame.Rect(x, y, width, height)

    def _draw_zone(self, zone_rect, color):
        """Dibuja una zona de despliegue."""
        s = pygame.Surface((zone_rect.width, zone_rect.height), pygame.SRCALPHA)
        s.fill(color)
        self.game.screen.blit(s, (zone_rect.x, zone_rect.y))

    def draw_possible_moves(self, possible_moves, grid, offset_x=0, offset_y=0):
        """Dibuja los movimientos posibles."""
        if not possible_moves:
            return

        for (row, col) in possible_moves:
            x, y = grid.hex_to_pixel(row, col)
            x += offset_x
            y += offset_y

            s = pygame.Surface((HEX_SIZE, HEX_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(s, (100, 200, 255, 150), (HEX_SIZE//2, HEX_SIZE//2), HEX_SIZE//2)
            self.game.screen.blit(s, (x - HEX_SIZE//2, y - HEX_SIZE//2))

    def draw_combat_targets(self):
        """Resalta los objetivos de ataque posibles con mejor visibilidad"""
        if self.game.combat_attacker and self.game.combat_targets:
            for target in self.game.combat_targets:
                x, y = self.game.grid.hex_to_pixel(target.row, target.col)

                # Aplicar offset del tablero centrado
                pos_x, pos_y = self._calculate_board_position(self.game.tablero_escalado)
                x += pos_x
                y += pos_y

                # Dibujar círculo rojo semitransparente más visible
                s = pygame.Surface((HEX_SIZE*1.5, HEX_SIZE*1.5), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 0, 0, 150), (HEX_SIZE//2, HEX_SIZE//2), HEX_SIZE//2)
                self.game.screen.blit(s, (x - HEX_SIZE//2, y - HEX_SIZE//2))

                # Dibujar borde rojo más grueso
                pygame.draw.circle(self.game.screen, (255, 0, 0), (x, y), HEX_SIZE//2 + 5, 3)

    def draw_combat_indicators(self):
        # Dibujar marcadores de heridas y rangos de ataque
        for row in range(self.game.grid.rows):
            for col in range(self.game.grid.cols):
                unit = self.game.grid.grid[row][col]
                if unit and unit.wounded_mark:
                    x, y = self.game.grid.hex_to_pixel(row, col)
                    pygame.draw.circle(self.game.screen, COMBAT_COLORS['wounded'], (x, y), 10, 2)

    def draw_arsouf_hexes(self, game, pos_x, pos_y):
        """Dibuja los hexágonos de Arsouf con un indicador visual"""
        for row, col in game.arsouf_hexes:
            x, y = game.grid.hex_to_pixel(row, col)
            x += pos_x
            y += pos_y

            # Dibujar un círculo dorado para indicar Arsouf
            s = pygame.Surface((HEX_SIZE*1.2, HEX_SIZE*1.2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 215, 0, 100), (HEX_SIZE//2, HEX_SIZE//2), HEX_SIZE//2)
            game.screen.blit(s, (x - HEX_SIZE//2, y - HEX_SIZE//2))

            # Dibujar un borde dorado
            pygame.draw.circle(game.screen, (255, 215, 0), (x, y), HEX_SIZE//2 + 2, 3)

            # Añadir texto "ARSOUF"
            font = pygame.font.SysFont('Arial', 14, bold=True)
            text = font.render("ARSOUF", True, (255, 215, 0))
            game.screen.blit(text, (x - text.get_width()//2, y - text.get_height()//2))

    def draw_victory_progress(self, game):
        """Dibuja el progreso hacia la victoria"""
        if game.state == "SELECT_SIDE" or game.state == "DEPLOY_PLAYER" or game.state == "DEPLOY_AI":
            return  # No mostrar durante la selección de bando o despliegue

        # Crear un panel para mostrar el progreso
        panel_width = 200
        panel_height = 80
        panel_x = SCREEN_WIDTH - PANEL_WIDTH - 20
        panel_y = 20

        # Dibujar panel
        s = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        game.screen.blit(s, (panel_x, panel_y))

        # Dibujar título
        font_title = pygame.font.SysFont('Arial', 16, bold=True)
        text_title = font_title.render("Progreso hacia Arsouf", True, (255, 255, 255))
        game.screen.blit(text_title, (panel_x + 10, panel_y + 10))

        # Dibujar progreso de bagajes
        font = pygame.font.SysFont('Arial', 14)
        text_bagaje = font.render(f"Bagajes: {game.units_in_arsouf['bagaje']}/2", True, (255, 255, 255))
        game.screen.blit(text_bagaje, (panel_x + 10, panel_y + 35))

        # Dibujar progreso de otras unidades
        text_other = font.render(f"Otras unidades: {game.units_in_arsouf['other']}/2", True, (255, 255, 255))
        game.screen.blit(text_other, (panel_x + 10, panel_y + 55))

    def draw_game_over(self, game):
        """Dibuja la pantalla de fin de juego"""
        # Crear un panel semitransparente para el mensaje de fin de juego
        panel_width = 400
        panel_height = 200
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = (SCREEN_HEIGHT - panel_height) // 2

        # Dibujar panel
        s = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 220))
        game.screen.blit(s, (panel_x, panel_y))

        # Dibujar borde
        pygame.draw.rect(game.screen, (255, 215, 0), (panel_x, panel_y, panel_width, panel_height), 3)

        # Dibujar título
        font_title = pygame.font.SysFont('Arial', 30, bold=True)
        text_title = font_title.render("FIN DEL JUEGO", True, (255, 215, 0))
        game.screen.blit(text_title, (panel_x + (panel_width - text_title.get_width())//2, panel_y + 30))

        # Dibujar mensaje de victoria
        font = pygame.font.SysFont('Arial', 20)
        if game.winner == "CRUZADOS":
            text_winner = font.render("¡Victoria de los Cruzados!", True, (255, 255, 255))
            text_reason = font.render("Han llegado suficientes unidades a Arsouf", True, (255, 255, 255))
        else:
            text_winner = font.render("¡Victoria de los Sarracenos!", True, (255, 255, 255))
            text_reason = font.render("Han impedido que los Cruzados lleguen a Arsouf", True, (255, 255, 255))

        game.screen.blit(text_winner, (panel_x + (panel_width - text_winner.get_width())//2, panel_y + 80))
        game.screen.blit(text_reason, (panel_x + (panel_width - text_reason.get_width())//2, panel_y + 120))

        # Dibujar instrucción para salir
        font_exit = pygame.font.SysFont('Arial', 16)
        text_exit = font_exit.render("Presiona ESC para salir", True, (200, 200, 200))
        game.screen.blit(text_exit, (panel_x + (panel_width - text_exit.get_width())//2, panel_y + 160))


    def draw_game(self, game):
        """Dibuja todos los elementos del juego."""
        # 1. Dibujar fondo
        game.screen.fill(COLOR_BG)

        # 2. Dibujar tablero (fondo)
        pos_x, pos_y = self._calculate_board_position(game.tablero_escalado)
        game.screen.blit(game.tablero_escalado, (pos_x, pos_y))

        # 3. Dibujar hexágonos de Arsouf
        self.draw_arsouf_hexes(game, pos_x, pos_y)

        # 4. Dibujar debug de movimiento si existe
        if __debug__ and hasattr(game, 'last_move_debug_pos') and game.last_move_debug_pos:
            row, col = game.last_move_debug_pos
            x, y = game.grid.hex_to_pixel(row, col)
            x += pos_x
            y += pos_y

            s = pygame.Surface((HEX_SIZE, HEX_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 0, 0, 180), (HEX_SIZE//2, HEX_SIZE//2), HEX_SIZE//3)
            game.screen.blit(s, (x - HEX_SIZE//2, y - HEX_SIZE//2))

        # 5. Debug hex grid (opcional)
        if __debug__: 
            game.grid.draw_hex_debug(game.screen)

        # 6. Dibujar unidades
        game.grid.draw(game.screen, game.images, pos_x, pos_y)

        # 7. Dibujar movimientos posibles si estamos en fase de movimiento
        if game.selected_unit and game.possible_moves:
            self.draw_possible_moves(game.possible_moves, game.grid, pos_x, pos_y)

        # 8. Dibujar objetivos de combate si estamos en fase de combate
        if game.state == "PLAYER_TURN" and game.turn_phase == "combate":
            self.draw_combat_targets()

        # 9. Dibujar UI
        self.draw_log_panel()
        self.draw_panel()
        self.draw_deployment_zones()

        # 10. Dibujar información de progreso hacia la victoria
        self.draw_victory_progress(game)

        # 11. Dibujar pantalla de selección si es necesario
        if game.state == "SELECT_SIDE":
            self.draw_side_selection()

        # 12. Dibujar pantalla de fin de juego si es necesario
        if game.game_over:
            self.draw_game_over(game)
