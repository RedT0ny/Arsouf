# gameui.py
import pygame
import gettext
_ = gettext.gettext
from config import *

# Para mejor ajuste visual, usar el tamaño más pequeño entre ancho y alto
HEX_MIN_SIZE = min(HEX_WIDTH, HEX_HEIGHT)

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

    def handle_scroll_event(self, event):
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
        pos_x, pos_y = self._calculate_board_position(game.tablero_escalado)
        tablero_rect = pygame.Rect(pos_x, pos_y, game.tablero_escalado.get_width(), 
                                  game.tablero_escalado.get_height())

        if tablero_rect.collidepoint(mouse_pos):
            return self._get_hex_under_mouse(mouse_pos, game.grid)
        return None

    def _get_hex_under_mouse(self, mouse_pos, grid):
        """Encuentra el hexágono bajo el cursor."""
        # Calcular la posición del tablero
        pos_x, pos_y = self._calculate_board_position(self.game.tablero_escalado)

        for row in range(grid.rows):
            for col in range(grid.cols):
                x, y = grid.hex_to_pixel(row, col)
                # Aplicar offset del tablero
                x += pos_x
                y += pos_y
                distance = ((mouse_pos[0] - x) ** 2 + (mouse_pos[1] - y) ** 2) ** 0.5
                if distance < HEX_MIN_SIZE / 2:
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

    def get_rules_button(self):
        # Create a panel rect instead of passing the screen
        panel_rect = pygame.Rect(SCREEN_WIDTH - PANEL_WIDTH, 0, PANEL_WIDTH, SCREEN_HEIGHT)
        return self._draw_rules_button(panel_rect, SCREEN_HEIGHT - 250)

    def handle_setup_menu(self, event):
        """Maneja las interacciones con el menú de configuración."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            scale_rect, language_rect, defaults_rect, rules_rect, side_rect, quit_rect = self.draw_setup_menu()
            mouse_pos = pygame.mouse.get_pos()

            # Verificar en qué botón se hizo clic
            if scale_rect.collidepoint(mouse_pos):
                return "SCALE"
            elif language_rect.collidepoint(mouse_pos):
                return "LANGUAGE"
            elif defaults_rect.collidepoint(mouse_pos):
                return "DEFAULTS"
            elif rules_rect.collidepoint(mouse_pos):
                return "RULES"
            elif side_rect.collidepoint(mouse_pos):
                return "SELECT_SIDE"
            elif quit_rect.collidepoint(mouse_pos):
                return "QUIT"
        return None

    def handle_side_selection(self, event):
        """Maneja la selección de bando."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            cruzados_rect, sarracenos_rect = self.draw_side_selection()
            mouse_pos = pygame.mouse.get_pos()

            if cruzados_rect.collidepoint(mouse_pos):
                return _("CRUZADOS")
            elif sarracenos_rect.collidepoint(mouse_pos):
                return _("SARRACENOS")
        return None

    def draw_setup_menu(self):
        """Dibuja la pantalla del menú de configuración."""
        self.game.screen.fill(COLOR_BG)

        # Título
        title = self.font.render(_("Menú de Configuración"), True, COLOR_TEXTO)
        self.game.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, TITULO_Y))

        # Botones del menú
        button_y = OPCIONES_Y
        button_spacing = 70  # Espacio entre botones

        # 1. Botón de escala de pantalla
        scale_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, button_y, BOTON_WIDTH, BOTON_HEIGHT)
        pygame.draw.rect(self.game.screen, (100, 150, 200), scale_rect)
        scale_text = self.font.render(f"{_('Escala de pantalla')}: {int(DISPLAY_SCALING * 100)}%", True, COLOR_TEXTO)
        self.game.screen.blit(scale_text, (scale_rect.centerx - scale_text.get_width()//2, 
                                         scale_rect.centery - scale_text.get_height()//2))
        button_y += button_spacing

        # 2. Botón de idioma
        language_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, button_y, BOTON_WIDTH, BOTON_HEIGHT)
        pygame.draw.rect(self.game.screen, (150, 100, 200), language_rect)
        language_text = self.font.render(_("Idioma"), True, COLOR_TEXTO)
        self.game.screen.blit(language_text, (language_rect.centerx - language_text.get_width()//2, 
                                            language_rect.centery - language_text.get_height()//2))
        button_y += button_spacing

        # 3. Botón de valores predeterminados
        defaults_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, button_y, BOTON_WIDTH, BOTON_HEIGHT)
        pygame.draw.rect(self.game.screen, (200, 150, 100), defaults_rect)
        defaults_text = self.font.render(_("Valores predeterminados"), True, COLOR_TEXTO)
        self.game.screen.blit(defaults_text, (defaults_rect.centerx - defaults_text.get_width()//2, 
                                            defaults_rect.centery - defaults_text.get_height()//2))
        button_y += button_spacing

        # 4. Botón de ver reglas
        rules_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, button_y, BOTON_WIDTH, BOTON_HEIGHT)
        pygame.draw.rect(self.game.screen, COLOR_CRUZADOS, rules_rect)
        rules_text = self.font.render(_("Ver Reglas"), True, COLOR_TEXTO)
        self.game.screen.blit(rules_text, (rules_rect.centerx - rules_text.get_width()//2, 
                                        rules_rect.centery - rules_text.get_height()//2))
        button_y += button_spacing

        # 5. Botón de selección de bando
        side_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, button_y, BOTON_WIDTH, BOTON_HEIGHT)
        pygame.draw.rect(self.game.screen, (100, 200, 150), side_rect)
        side_text = self.font.render(_("Seleccionar bando"), True, COLOR_TEXTO)
        self.game.screen.blit(side_text, (side_rect.centerx - side_text.get_width()//2, 
                                        side_rect.centery - side_text.get_height()//2))
        button_y += button_spacing

        # 6. Botón de salir
        quit_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, button_y, BOTON_WIDTH, BOTON_HEIGHT)
        pygame.draw.rect(self.game.screen, COLOR_BOTON_CANCELAR, quit_rect)
        quit_text = self.font.render(_("Salir"), True, COLOR_TEXTO)
        self.game.screen.blit(quit_text, (quit_rect.centerx - quit_text.get_width()//2, 
                                        quit_rect.centery - quit_text.get_height()//2))

        pygame.display.flip()
        return scale_rect, language_rect, defaults_rect, rules_rect, side_rect, quit_rect

    def draw_side_selection(self):
        """Dibuja la pantalla de selección de lado."""
        self.game.screen.fill(COLOR_BG)

        # Título
        title = self.font.render(_("Selecciona tu bando:"), True, COLOR_TEXTO)
        self.game.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, TITULO_Y))

        # Botón Cruzados
        cruzados_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, OPCIONES_Y, BOTON_WIDTH, BOTON_HEIGHT)
        pygame.draw.rect(self.game.screen, COLOR_CRUZADOS, cruzados_rect)
        cruzados_text = self.font.render(_("Jugar como Cruzados"), True, COLOR_TEXTO)
        self.game.screen.blit(cruzados_text, (cruzados_rect.centerx - cruzados_text.get_width()//2, 
                                            cruzados_rect.centery - cruzados_text.get_height()//2))

        # Botón Sarracenos
        sarracenos_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, OPCIONES_Y + OPCIONES_ESPACIADO, BOTON_WIDTH, BOTON_HEIGHT)
        pygame.draw.rect(self.game.screen, COLOR_SARRACENOS, sarracenos_rect)
        sarracenos_text = self.font.render(_("Jugar como Sarracenos"), True, COLOR_TEXTO)
        self.game.screen.blit(sarracenos_text, (sarracenos_rect.centerx - sarracenos_text.get_width()//2, 
                                             sarracenos_rect.centery - sarracenos_text.get_height()//2))

        pygame.display.flip()
        return cruzados_rect, sarracenos_rect

    def _get_selected_unit(self):
        """Obtiene la unidad actualmente seleccionada (movimiento o combate)."""
        # Caso 1: Unidad seleccionada para movimiento
        if hasattr(self.game, 'selected_unit') and self.game.selected_unit:
            row, col = self.game.selected_unit
            return self.game.grid.grid[row][col]

        # Caso 2: Unidad seleccionada para combate
        if hasattr(self.game, 'combat_attacker') and self.game.combat_attacker:
            return self.game.combat_attacker

        return None

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

        # 2. Información de la unidad actual para despliegue
        if hasattr(self.game, 'current_deploying_unit') and self.game.current_deploying_unit:
            unit_name = type(self.game.current_deploying_unit).__name__
            unit_info = f"{_('Coloca')}: {_(unit_name[:12])}" if len(unit_name) > 12 else f"{_('Coloca')}: {_(unit_name)}"
            unit_text = self.font.render(unit_info, True, COLOR_TEXTO)

            # Ajustar texto si es muy largo
            if unit_text.get_width() > content_rect.width:
                small_font = pygame.font.SysFont('Arial', 18)
                unit_text = small_font.render(unit_info, True, COLOR_TEXTO)

            self.game.screen.blit(unit_text, (content_rect.x, y_offset))
            y_offset += 30

        # 3. Información de la unidad seleccionada (movimiento o combate)
        selected_unit = self._get_selected_unit()
        if selected_unit:
            self._draw_unit_info(selected_unit, content_rect, y_offset)
            y_offset += 150  # Espacio para la información de la unidad

        # 4. Dibujar botón de reglas
        rules_button_rect = self._draw_rules_button(panel_rect, SCREEN_HEIGHT - 250)

        # 5. Dibujar botón según el estado del juego
        button_rect = None
        if self.game.state == "PLAYER_TURN":
            button_rect = self._draw_button(panel_rect, _("Finalizar movimiento") if self.game.turn_phase == TURN_PHASES["MOVEMENT"] else _("Finalizar Combate"), COLOR_BOTON_CANCELAR, SCREEN_HEIGHT - 80)
        elif self.game.state == "DEPLOY_PLAYER" and not getattr(self.game, 'current_deploying_unit', None):
            button_rect = self._draw_button(panel_rect, _("Confirmar Despliegue"), COLOR_BOTON, SCREEN_HEIGHT - 80)

        return button_rect

    def _get_status_text(self):
        """Devuelve el texto de estado según el estado actual del juego."""
        # Definir máximo ancho disponible (panel_width - márgenes)
        max_width = PANEL_WIDTH - 10  # 10px de margen a cada lado

        if self.game.state == GAME_STATES["SETUP_MENU"]:
            text = _("Menú de Configuración")
        elif self.game.state == GAME_STATES["SELECT_SIDE"]:
            text = _("Selecciona tu bando")
        elif self.game.state == GAME_STATES["DEPLOY_PLAYER"]:
            text = _("Despliega tus unidades")
        elif self.game.state == GAME_STATES["DEPLOY_AI"]:
            text = _("Despliegue del ordenador")
        elif self.game.state == GAME_STATES["PLAYER_TURN"]:
            phase = self.game.turn_phase
            text = f"{_(self.game.player_side)}: {_(phase)}"
        elif self.game.state == GAME_STATES["AI_TURN"]:
            text = _("Turno del ordenador")
        else:
            text = ""

        # Crear texto renderizado con ajuste de línea si es necesario
        return self._render_fitted_text(text, max_width)

    def _render_fitted_text(self, text, max_width, color=COLOR_TEXTO, font_size=24):
        """Renderiza texto que se ajusta al ancho máximo"""
        # Usar el tamaño de fuente especificado
        font = pygame.font.SysFont('Arial', font_size)

        # Si el texto cabe normalmente
        if font.size(text)[0] <= max_width:
            return font.render(text, True, color)

        # Si no cabe, reducimos el tamaño de fuente
        small_font = pygame.font.SysFont('Arial', max(12, font_size - 6))  # Tamaño reducido
        return small_font.render(text, True, color)

    def _draw_unit_info(self, unit, content_rect, y_offset):
        """Dibuja la información detallada de una unidad en el panel lateral."""
        # Obtener el ancho disponible para el texto
        max_width = content_rect.width

        # Título: Tipo de unidad
        unit_name = type(unit).__name__
        title_font = pygame.font.SysFont('Arial', 20, bold=True)
        title_text = title_font.render(_(unit_name), True, COLOR_TEXTO)

        # Centrar el título
        title_x = content_rect.x + (max_width - title_text.get_width()) // 2
        self.game.screen.blit(title_text, (title_x, y_offset))
        y_offset += 30

        # Dibujar imagen de la unidad
        if hasattr(unit, 'image_key') and unit.image_key in self.game.images:
            img = self.game.images[unit.image_key]
            img_size = min(max_width, 120)  # Limitar tamaño de imagen (aumentado un 50%)
            img_scaled = pygame.transform.scale(img, (img_size, img_size))

            # Centrar imagen
            img_x = content_rect.x + (max_width - img_size) // 2
            self.game.screen.blit(img_scaled, (img_x, y_offset))
            y_offset += img_size + 10

        # Información de la unidad (con ajuste de texto)
        info_font_size = 16
        line_height = info_font_size + 4

        # Bando
        side_color = COLOR_CRUZADOS if unit.side == "CRUZADOS" else COLOR_SARRACENOS
        side_text = self._render_fitted_text(f"{_('Bando')}: {_(unit.side)}", max_width, side_color, info_font_size)
        self.game.screen.blit(side_text, (content_rect.x, y_offset))
        y_offset += line_height

        # Fuerza de combate
        power_text = self._render_fitted_text(f"{_('Fuerza')}: {unit.power}", max_width, COLOR_TEXTO, info_font_size)
        self.game.screen.blit(power_text, (content_rect.x, y_offset))
        y_offset += line_height

        # Velocidad
        speed_text = self._render_fitted_text(f"{_('Velocidad')}: {unit.speed}/{unit.original_speed}", max_width, COLOR_TEXTO, info_font_size)
        self.game.screen.blit(speed_text, (content_rect.x, y_offset))
        y_offset += line_height

        # Líder (si aplica)
        if unit.leader:
            leader_text = self._render_fitted_text(f"{_('Líder')}: {_('Sí')}", max_width, (255, 215, 0), info_font_size)
            self.game.screen.blit(leader_text, (content_rect.x, y_offset))
            y_offset += line_height

        # Estado de salud
        health_status = _("Sana") if unit.health == 2 else _("Herida")
        health_color = (50, 200, 50) if unit.health == 2 else COMBAT_COLORS['wounded']
        health_text = self._render_fitted_text(f"{_('Estado')}: {health_status}", max_width, health_color, info_font_size)
        self.game.screen.blit(health_text, (content_rect.x, y_offset))

    def _draw_button(self, panel_rect, text, color, y_pos):
        """Dibuja un botón en el panel."""
        button_rect = pygame.Rect(panel_rect.x + (PANEL_WIDTH - BOTON_WIDTH)//2, y_pos, BOTON_WIDTH, BOTON_HEIGHT)
        pygame.draw.rect(self.game.screen, color, button_rect)
        button_text = self.font.render(_(text), True, COLOR_TEXTO)
        self.game.screen.blit(button_text, (button_rect.centerx - button_text.get_width()//2, 
                                         button_rect.centery - button_text.get_height()//2))
        return button_rect

    def _draw_rules_button(self, panel_rect, y_position):
        rules_button_rect = self._draw_button(panel_rect, _("Ver Reglas"), COLOR_CRUZADOS, y_position)
        return rules_button_rect

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

            s = pygame.Surface((HEX_MIN_SIZE, HEX_MIN_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(s, (100, 200, 255, 150), (HEX_MIN_SIZE//2, HEX_MIN_SIZE//2), HEX_MIN_SIZE//2)
            self.game.screen.blit(s, (x - HEX_MIN_SIZE//2, y - HEX_MIN_SIZE//2))

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
                s = pygame.Surface((HEX_MIN_SIZE*1.5, HEX_MIN_SIZE*1.5), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 0, 0, 150), (HEX_MIN_SIZE//2, HEX_MIN_SIZE//2), HEX_MIN_SIZE//2)
                self.game.screen.blit(s, (x - HEX_MIN_SIZE//2, y - HEX_MIN_SIZE//2))

                # Dibujar borde rojo más grueso
                pygame.draw.circle(self.game.screen, (255, 0, 0), (x, y), HEX_MIN_SIZE//2 + 5, 3)

    def draw_combat_indicators(self):
        # Dibujar marcadores de heridas y rangos de ataque
        for row in range(self.game.grid.rows):
            for col in range(self.game.grid.cols):
                unit = self.game.grid.grid[row][col]
                if unit and unit.wounded_mark:
                    x, y = self.game.grid.hex_to_pixel(row, col)
                    pygame.draw.circle(self.game.screen, COMBAT_COLORS['wounded'], (x, y), 10, 2)

    def draw_victory_progress(self, game):
        """Dibuja el progreso hacia la victoria"""
        if game.state == "SELECT_SIDE" or game.state == "DEPLOY_PLAYER" or game.state == "DEPLOY_AI":
            return  # No mostrar durante la selección de bando o despliegue

        # Crear un panel para mostrar el progreso
        panel_width = 200
        panel_height = 80
        panel_x = SCREEN_WIDTH - PANEL_WIDTH - 20
        panel_y = SCREEN_HEIGHT - 170  # Posicionado ligeramente sobre el botón de finalizar turno

        # Dibujar panel
        s = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        game.screen.blit(s, (panel_x, panel_y))

        # Dibujar título
        font_title = pygame.font.SysFont('Arial', 16, bold=True)
        text_title = font_title.render(_("Progreso hacia Arsouf"), True, (255, 255, 255))
        game.screen.blit(text_title, (panel_x + 10, panel_y + 10))

        # Dibujar progreso de bagajes
        font = pygame.font.SysFont('Arial', 14)
        text_bagaje = font.render(f"{_('Bagajes')}: {game.units_in_arsouf['bagaje']}/2", True, (255, 255, 255))
        game.screen.blit(text_bagaje, (panel_x + 10, panel_y + 35))

        # Dibujar progreso de otras unidades
        text_other = font.render(f"{_('Otras unidades')}: {game.units_in_arsouf['other']}/2", True, (255, 255, 255))
        game.screen.blit(text_other, (panel_x + 10, panel_y + 55))

    def draw_intro(self, game):
        """Dibuja la pantalla de introducción"""
        # Cargar la fuente para el texto de introducción
        intro_font = pygame.font.Font(FONT_PATHS["abbasy"], 144)

        # Crear el texto
        intro_text = _("The Battle of Arsouf")
        intro_text_surface = intro_font.render(intro_text, True, WHITE)

        # Obtener rectángulo del texto para centrarlo
        intro_text_rect = intro_text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200))

        # Dibujar la imagen de portada a pantalla completa
        game.screen.blit(game.images["cover"], (0, 0))

        # Dibujar el texto encima
        game.screen.blit(intro_text_surface, intro_text_rect)

        # Verificar si han pasado los 3m 27s segundos de duración máxima
        current_time = pygame.time.get_ticks()
        if current_time - game.intro_start_time >= game.intro_duration:
            game._end_intro()

        # Actualizar la pantalla
        pygame.display.flip()

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
        text_title = font_title.render(_("FIN DEL JUEGO"), True, (255, 215, 0))
        game.screen.blit(text_title, (panel_x + (panel_width - text_title.get_width())//2, panel_y + 30))

        # Dibujar mensaje de victoria
        font = pygame.font.SysFont('Arial', 20)
        if game.winner == "CRUZADOS":
            text_winner = font.render(_("¡Victoria de los Cruzados!"), True, (255, 255, 255))
            text_reason = font.render(_("Han llegado suficientes unidades a Arsouf"), True, (255, 255, 255))
        else:
            text_winner = font.render(_("¡Victoria de los Sarracenos!"), True, (255, 255, 255))
            text_reason = font.render(_("Han impedido que los Cruzados lleguen a Arsouf"), True, (255, 255, 255))

        game.screen.blit(text_winner, (panel_x + (panel_width - text_winner.get_width())//2, panel_y + 80))
        game.screen.blit(text_reason, (panel_x + (panel_width - text_reason.get_width())//2, panel_y + 120))

        # Dibujar instrucción para salir
        font_exit = pygame.font.SysFont('Arial', 16)
        text_exit = font_exit.render(_("Presiona ESC para salir"), True, (200, 200, 200))
        game.screen.blit(text_exit, (panel_x + (panel_width - text_exit.get_width())//2, panel_y + 160))


    def draw_game(self, game):
        """Dibuja todos los elementos del juego."""
        # 1. Dibujar fondo
        game.screen.fill(COLOR_BG)

        # 2. Dibujar tablero (fondo)
        pos_x, pos_y = self._calculate_board_position(game.tablero_escalado)
        game.screen.blit(game.tablero_escalado, (pos_x, pos_y))

        # 3. Dibujar indicador de último movimiento si existe (para función de deshacer)
        if hasattr(game, 'last_moved_unit_pos') and game.last_moved_unit_pos:
            row, col = game.last_moved_unit_pos[0]  # Posición original
            x, y = game.grid.hex_to_pixel(row, col)
            x += pos_x
            y += pos_y

            s = pygame.Surface((HEX_MIN_SIZE, HEX_MIN_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 0, 0, 180), (HEX_MIN_SIZE//2, HEX_MIN_SIZE//2), HEX_MIN_SIZE//3)
            game.screen.blit(s, (x - HEX_MIN_SIZE//2, y - HEX_MIN_SIZE//2))

        # 4. Debug hex grid (opcional)
        if __debug__: 
            game.grid.draw_hex_debug(game.screen, pos_x, pos_y)

        # 5. Dibujar unidades
        game.grid.draw(game.screen, game.images, pos_x, pos_y)

        # 6. Dibujar movimientos posibles si estamos en fase de movimiento
        if game.selected_unit and game.possible_moves:
            self.draw_possible_moves(game.possible_moves, game.grid, pos_x, pos_y)

        # 7. Dibujar objetivos de combate si estamos en fase de combate
        if game.state == "PLAYER_TURN" and game.turn_phase == TURN_PHASES["COMBAT"]:
            self.draw_combat_targets()

        # 8. Dibujar UI
        self.draw_log_panel()
        self.draw_panel()
        self.draw_deployment_zones()

        # 9. Dibujar información de progreso hacia la victoria
        self.draw_victory_progress(game)

        # 10. Dibujar pantalla de menú de configuración si es necesario
        if game.state == GAME_STATES["SETUP_MENU"]:
            self.draw_setup_menu()

        # 11. Dibujar pantalla de selección si es necesario
        if game.state == GAME_STATES["SELECT_SIDE"]:
            self.draw_side_selection()

        # 12. Dibujar pantalla de introducción si es necesario
        if game.state == GAME_STATES["INTRO"]:
            self.draw_intro(game)

        # 13. Dibujar pantalla de fin de juego si es necesario
        if game.game_over:
            self.draw_game_over(game)
