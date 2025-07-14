# gameui.py
import pygame
import gettext
_ = gettext.gettext
import config

class GameUI:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont('Arial', 24)
        self.log_font = pygame.font.SysFont('Arial', config.LOG_FONT_SIZE)
        self.log_messages = []
        self.log_scroll_position = 0
        self.log_scroll_dragging = False
        self.log_scroll_handle_rect = None
        self.log_scroll_start_y = 0
        self.log_scroll_start_position = 0
        self.debug_drawn = False

        # Map scrolling variables
        self.map_scroll_x = 0
        self.map_scroll_y = 0
        self.map_scroll_dragging = False
        self.map_scroll_handle_rect_h = None  # Horizontal scrollbar handle
        self.map_scroll_handle_rect_v = None  # Vertical scrollbar handle
        self.map_drag_start_x = 0
        self.map_drag_start_y = 0
        self.map_drag_start_scroll_x = 0
        self.map_drag_start_scroll_y = 0

    def _get_visible_lines(self):
        line_height = config.LOG_LINE_HEIGHT
        panel_height = config.LOG_PANEL_HEIGHT - 2 * config.LOG_MARGIN
        visible_lines = panel_height // line_height
        return max(1, visible_lines)

    def _calculate_board_position(self, tablero_surface):
        # Calculate the available area for the map
        available_width = config.SCREEN_WIDTH - config.PANEL_WIDTH
        available_height = config.SCREEN_HEIGHT - config.LOG_PANEL_HEIGHT

        # Apply scroll offset (negative because we're moving the board, not the viewport)
        pos_x = -self.map_scroll_x
        pos_y = -self.map_scroll_y

        # Limit scrolling to keep some part of the board visible
        max_scroll_x = max(0, tablero_surface.get_width() - available_width)
        max_scroll_y = max(0, tablero_surface.get_height() - available_height)

        self.map_scroll_x = max(0, min(self.map_scroll_x, max_scroll_x))
        self.map_scroll_y = max(0, min(self.map_scroll_y, max_scroll_y))

        # Recalculate position with clamped scroll values
        pos_x = -self.map_scroll_x
        pos_y = -self.map_scroll_y

        return pos_x, pos_y

    def draw_log_panel(self):
        try:
            panel_rect = pygame.Rect(0, config.SCREEN_HEIGHT - config.LOG_PANEL_HEIGHT,
                                   config.LOG_PANEL_WIDTH, config.LOG_PANEL_HEIGHT)
            pygame.draw.rect(self.game.screen, (30, 30, 40), panel_rect)
            text_area = pygame.Rect(
                panel_rect.x + config.LOG_MARGIN,
                panel_rect.y + config.LOG_MARGIN,
                panel_rect.width - 2*config.LOG_MARGIN - config.LOG_SCROLLBAR_WIDTH,
                panel_rect.height - 2*config.LOG_MARGIN
            )
            visible_lines = self._get_visible_lines()
            total_lines = len(self.log_messages)
            self.log_scroll_position = max(0, min(self.log_scroll_position, total_lines - visible_lines))
            for i in range(visible_lines):
                line_index = int(self.log_scroll_position) + i
                if 0 <= line_index < len(self.log_messages):
                    msg = self.log_messages[line_index]
                    msg_text = self.log_font.render(msg, True, (220, 220, 220))
                    self.game.screen.blit(msg_text,
                                        (text_area.x,
                                         text_area.y + i * config.LOG_LINE_HEIGHT))
            if total_lines > visible_lines:
                self._draw_log_scrollbar(panel_rect, total_lines, visible_lines)
        except Exception as e:
            print(f"{_('ERROR dibujando panel LOG:')} {e}")
            raise

    def _draw_log_scrollbar(self, panel_rect, total_lines, visible_lines):
        scrollbar_rect = pygame.Rect(
            panel_rect.right - config.LOG_SCROLLBAR_WIDTH - 5,
            panel_rect.y + 5,
            config.LOG_SCROLLBAR_WIDTH,
            panel_rect.height - 10
        )
        pygame.draw.rect(self.game.screen, (80, 80, 100), scrollbar_rect)
        handle_height = max(40, (visible_lines / total_lines) * scrollbar_rect.height)
        handle_y = scrollbar_rect.y + (self.log_scroll_position / total_lines) * (scrollbar_rect.height - handle_height)
        self.log_scroll_handle_rect = pygame.Rect(
            scrollbar_rect.x - 2,
            handle_y - 2,
            scrollbar_rect.width + 4,
            handle_height + 4
        )
        pygame.draw.rect(self.game.screen, (160, 160, 190), self.log_scroll_handle_rect)
        pygame.draw.rect(self.game.screen, (200, 200, 230), self.log_scroll_handle_rect, 2)
        if __debug__:
            debug_font = pygame.font.SysFont('Arial', 12)
            debug_text = debug_font.render(f"{int(self.log_scroll_position)}/{total_lines}", True, (255, 255, 255))
            self.game.screen.blit(debug_text, (scrollbar_rect.x - 30, scrollbar_rect.y))

    def handle_scroll_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        log_panel_rect = pygame.Rect(0, config.SCREEN_HEIGHT - config.LOG_PANEL_HEIGHT,
                                   config.LOG_PANEL_WIDTH, config.LOG_PANEL_HEIGHT)
        if not log_panel_rect.collidepoint(mouse_pos):
            return False
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
        if hasattr(self, 'log_scroll_handle_rect') and self.log_scroll_handle_rect:
            if self.log_scroll_handle_rect.collidepoint(mouse_pos):
                self.log_scroll_dragging = True
                self.drag_start_y = mouse_pos[1]
                self.drag_start_position = self.log_scroll_position
                return True
        return False

    def _handle_scroll_end(self):
        if self.log_scroll_dragging:
            self.log_scroll_dragging = False
            return True
        return False

    def _handle_scroll_drag(self, mouse_pos):
        if not self.log_scroll_dragging:
            return False
        delta_y = mouse_pos[1] - self.drag_start_y
        total_lines = len(self.log_messages)
        visible_lines = self._get_visible_lines()
        if total_lines <= visible_lines:
            return True
        handle_height = self.log_scroll_handle_rect.height
        scroll_area_height = config.LOG_PANEL_HEIGHT - 2*config.LOG_MARGIN - handle_height
        if scroll_area_height > 0:
            scroll_ratio = delta_y / scroll_area_height
            max_scroll = total_lines - visible_lines
            self.log_scroll_position = max(0, min(
                self.drag_start_position + scroll_ratio * max_scroll,
                max_scroll
            ))
        return True

    def _handle_wheel_scroll(self, wheel_delta):
        total_lines = len(self.log_messages)
        visible_lines = self._get_visible_lines()
        if total_lines <= visible_lines:
            return
        scroll_delta = wheel_delta * 3
        max_scroll = total_lines - visible_lines
        self.log_scroll_position = max(0, min(self.log_scroll_position - scroll_delta, max_scroll))

    def add_log_message(self, message):
        self.log_messages.append(message)
        if len(self.log_messages) > config.LOG_MAX_MESSAGES:
            self.log_messages.pop(0)
        visible_lines = self._get_visible_lines()
        total_lines = len(self.log_messages)
        max_scroll_position = max(0, total_lines - visible_lines)
        self.log_scroll_position = max_scroll_position

    def center_view_on_unit(self, unit_row, unit_col, tablero_surface):
        """Center the map view on a specific unit position"""
        if not tablero_surface:
            return

        # Get the pixel position of the hex
        hex_pixel_x, hex_pixel_y = self.game.grid.hex_to_pixel(unit_row, unit_col)

        # Calculate available screen area for the map
        available_width = config.SCREEN_WIDTH - config.PANEL_WIDTH
        available_height = config.SCREEN_HEIGHT - config.LOG_PANEL_HEIGHT

        # Calculate the center of the available area
        center_screen_x = available_width // 2
        center_screen_y = available_height // 2

        # Calculate the scroll values needed to center the hex
        target_scroll_x = hex_pixel_x - center_screen_x
        target_scroll_y = hex_pixel_y - center_screen_y

        # Limit scrolling to valid ranges
        max_scroll_x = max(0, tablero_surface.get_width() - available_width)
        max_scroll_y = max(0, tablero_surface.get_height() - available_height)

        self.map_scroll_x = max(0, min(target_scroll_x, max_scroll_x))
        self.map_scroll_y = max(0, min(target_scroll_y, max_scroll_y))

    def _draw_map_scrollbars(self, tablero_surface):
        """Draw horizontal and vertical scrollbars for the map"""
        available_width = config.AVAILABLE_WIDTH
        available_height = config.AVAILABLE_HEIGHT

        board_width = tablero_surface.get_width()
        board_height = tablero_surface.get_height()

        scrollbar_width = config.LOG_SCROLLBAR_WIDTH
        scrollbar_color = config.LOG_SCROLLBAR_COLOR
        handle_color = config.LOG_SCROLLBAR_HANDLE_COLOR

        # Draw horizontal scrollbar if needed
        if board_width > available_width:
            scrollbar_rect = pygame.Rect(
                0, available_height - scrollbar_width,
                available_width - scrollbar_width, scrollbar_width
            )
            pygame.draw.rect(self.game.screen, scrollbar_color, scrollbar_rect)

            # Calculate handle position and size
            handle_width = max(40, (available_width / board_width) * scrollbar_rect.width)
            max_scroll_x = board_width - available_width
            # Fix handle position calculation to use proper scroll range
            if max_scroll_x > 0:
                handle_x = scrollbar_rect.x + (self.map_scroll_x / max_scroll_x) * (scrollbar_rect.width - handle_width)
            else:
                handle_x = scrollbar_rect.x

            self.map_scroll_handle_rect_h = pygame.Rect(
                handle_x, scrollbar_rect.y,
                handle_width, scrollbar_rect.height
            )
            pygame.draw.rect(self.game.screen, handle_color, self.map_scroll_handle_rect_h)
            pygame.draw.rect(self.game.screen, (200, 200, 230), self.map_scroll_handle_rect_h, 2)

        # Draw vertical scrollbar if needed
        if board_height > available_height:
            scrollbar_rect = pygame.Rect(
                available_width - scrollbar_width, 0,
                scrollbar_width, available_height - scrollbar_width
            )
            pygame.draw.rect(self.game.screen, scrollbar_color, scrollbar_rect)

            # Calculate handle position and size
            handle_height = max(40, (available_height / board_height) * scrollbar_rect.height)
            max_scroll_y = board_height - available_height
            # Fix handle position calculation to use proper scroll range
            if max_scroll_y > 0:
                handle_y = scrollbar_rect.y + (self.map_scroll_y / max_scroll_y) * (scrollbar_rect.height - handle_height)
            else:
                handle_y = scrollbar_rect.y

            self.map_scroll_handle_rect_v = pygame.Rect(
                scrollbar_rect.x, handle_y,
                scrollbar_rect.width, handle_height
            )
            pygame.draw.rect(self.game.screen, handle_color, self.map_scroll_handle_rect_v)
            pygame.draw.rect(self.game.screen, (200, 200, 230), self.map_scroll_handle_rect_v, 2)

    def handle_map_scroll_event(self, event, tablero_surface):
        """Handle scrolling events for the map"""
        mouse_pos = pygame.mouse.get_pos()
        available_width = config.SCREEN_WIDTH - config.PANEL_WIDTH
        available_height = config.SCREEN_HEIGHT - config.LOG_PANEL_HEIGHT

        # Check if mouse is in the map area
        map_area = pygame.Rect(0, 0, available_width, available_height)
        if not map_area.collidepoint(mouse_pos):
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_map_scroll_start(mouse_pos, tablero_surface)
        elif event.type == pygame.MOUSEBUTTONUP:
            return self._handle_map_scroll_end()
        elif event.type == pygame.MOUSEMOTION:
            return self._handle_map_scroll_drag(mouse_pos, tablero_surface)
        elif event.type == pygame.MOUSEWHEEL:
            return self._handle_map_wheel_scroll(event.x, event.y, tablero_surface)
        return False

    def _handle_map_scroll_start(self, mouse_pos, tablero_surface):
        """Handle start of map scrollbar dragging"""
        # Check horizontal scrollbar
        if (hasattr(self, 'map_scroll_handle_rect_h') and 
            self.map_scroll_handle_rect_h and 
            self.map_scroll_handle_rect_h.collidepoint(mouse_pos)):
            self.map_scroll_dragging = True
            self.map_drag_start_x = mouse_pos[0]
            self.map_drag_start_scroll_x = self.map_scroll_x
            return True

        # Check vertical scrollbar
        if (hasattr(self, 'map_scroll_handle_rect_v') and 
            self.map_scroll_handle_rect_v and 
            self.map_scroll_handle_rect_v.collidepoint(mouse_pos)):
            self.map_scroll_dragging = True
            self.map_drag_start_y = mouse_pos[1]
            self.map_drag_start_scroll_y = self.map_scroll_y
            return True

        return False

    def _handle_map_scroll_end(self):
        """Handle end of map scrollbar dragging"""
        if self.map_scroll_dragging:
            self.map_scroll_dragging = False
            return True
        return False

    def _handle_map_scroll_drag(self, mouse_pos, tablero_surface):
        """Handle map scrollbar dragging"""
        if not self.map_scroll_dragging:
            return False

        available_width = config.SCREEN_WIDTH - config.PANEL_WIDTH
        available_height = config.SCREEN_HEIGHT - config.LOG_PANEL_HEIGHT
        board_width = tablero_surface.get_width()
        board_height = tablero_surface.get_height()

        # Handle horizontal scrollbar drag
        if hasattr(self, 'map_drag_start_x') and self.map_drag_start_x > 0:
            delta_x = mouse_pos[0] - self.map_drag_start_x
            if board_width > available_width:
                scrollbar_width = available_width - config.LOG_SCROLLBAR_WIDTH
                # Calculate handle dimensions to get proper movement range
                handle_width = max(40, (available_width / board_width) * scrollbar_width)
                handle_movement_range = scrollbar_width - handle_width

                # Improved scroll ratio calculation for better control
                if handle_movement_range > 0:
                    scroll_ratio = delta_x / handle_movement_range
                    max_scroll_x = board_width - available_width
                    self.map_scroll_x = max(0, min(
                        self.map_drag_start_scroll_x + scroll_ratio * max_scroll_x,
                        max_scroll_x
                    ))

        # Handle vertical scrollbar drag
        if hasattr(self, 'map_drag_start_y') and self.map_drag_start_y > 0:
            delta_y = mouse_pos[1] - self.map_drag_start_y
            if board_height > available_height:
                scrollbar_height = available_height - config.LOG_SCROLLBAR_WIDTH
                # Calculate handle dimensions to get proper movement range
                handle_height = max(40, (available_height / board_height) * scrollbar_height)
                handle_movement_range = scrollbar_height - handle_height

                # Improved scroll ratio calculation for better control
                if handle_movement_range > 0:
                    scroll_ratio = delta_y / handle_movement_range
                    max_scroll_y = board_height - available_height
                    self.map_scroll_y = max(0, min(
                        self.map_drag_start_scroll_y + scroll_ratio * max_scroll_y,
                        max_scroll_y
                    ))

        return True

    def _handle_map_wheel_scroll(self, wheel_x, wheel_y, tablero_surface):
        """Handle mouse wheel scrolling for the map"""
        available_width = config.SCREEN_WIDTH - config.PANEL_WIDTH
        available_height = config.SCREEN_HEIGHT - config.LOG_PANEL_HEIGHT
        board_width = tablero_surface.get_width()
        board_height = tablero_surface.get_height()

        scroll_speed = 50  # pixels per wheel step

        # Check for CTRL key modifier for horizontal scrolling
        keys = pygame.key.get_pressed()
        ctrl_pressed = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]

        # If CTRL is pressed, convert vertical wheel to horizontal scroll
        if ctrl_pressed and wheel_y != 0 and board_width > available_width:
            max_scroll_x = board_width - available_width
            self.map_scroll_x = max(0, min(
                self.map_scroll_x - wheel_y * scroll_speed,
                max_scroll_x
            ))
            return True  # Consume the event to prevent click interpretation

        # Normal vertical scrolling (when CTRL is not pressed)
        if wheel_y != 0 and board_height > available_height and not ctrl_pressed:
            max_scroll_y = board_height - available_height
            self.map_scroll_y = max(0, min(
                self.map_scroll_y - wheel_y * scroll_speed,
                max_scroll_y
            ))
            return True  # Consume the event to prevent click interpretation

        # Horizontal scrolling (native wheel_x support for mice that have it)
        if wheel_x != 0 and board_width > available_width:
            max_scroll_x = board_width - available_width
            self.map_scroll_x = max(0, min(
                self.map_scroll_x - wheel_x * scroll_speed,
                max_scroll_x
            ))
            return True  # Consume the event to prevent click interpretation

        # If no scrolling occurred, still consume the wheel event to prevent click interpretation
        return wheel_x != 0 or wheel_y != 0

    def handle_deployment_click(self, mouse_pos, game):
        pos_x, pos_y = self._calculate_board_position(game.tablero_escalado)
        tablero_rect = pygame.Rect(pos_x, pos_y, game.tablero_escalado.get_width(),
                                  game.tablero_escalado.get_height())
        if tablero_rect.collidepoint(mouse_pos):
            return self._get_hex_under_mouse(mouse_pos, game.grid)
        return None

    def _get_hex_under_mouse(self, mouse_pos, grid):
        pos_x, pos_y = self._calculate_board_position(self.game.tablero_escalado)
        for row in range(grid.rows):
            for col in range(grid.cols):
                x, y = grid.hex_to_pixel(row, col)
                x += pos_x
                y += pos_y
                distance = ((mouse_pos[0] - x) ** 2 + (mouse_pos[1] - y) ** 2) ** 0.5
                if distance < config.HEX_MIN_SIZE / 2:
                    return row, col
        return None

    def get_button_rect(self):
        if self.game.state == "PLAYER_TURN":
            panel_rect = pygame.Rect(config.SCREEN_WIDTH - config.PANEL_WIDTH, 0, config.PANEL_WIDTH, config.SCREEN_HEIGHT)
            return pygame.Rect(panel_rect.x + (config.PANEL_WIDTH - config.PANEL_BUTTON_WIDTH) // 2,
                               config.SCREEN_HEIGHT - 80, config.PANEL_BUTTON_WIDTH, config.PANEL_BUTTON_HEIGHT)
        elif self.game.state == "DEPLOY_PLAYER" and not getattr(self.game, 'current_deploying_unit', None):
            panel_rect = pygame.Rect(config.SCREEN_WIDTH - config.PANEL_WIDTH, 0, config.PANEL_WIDTH, config.SCREEN_HEIGHT)
            return pygame.Rect(panel_rect.x + (config.PANEL_WIDTH - config.PANEL_BUTTON_WIDTH) // 2,
                               config.SCREEN_HEIGHT - 80, config.PANEL_BUTTON_WIDTH, config.PANEL_BUTTON_HEIGHT)
        return None

    def get_rules_button(self):
        panel_rect = pygame.Rect(config.SCREEN_WIDTH - config.PANEL_WIDTH, 0, config.PANEL_WIDTH, config.SCREEN_HEIGHT)
        return self._draw_rules_button(panel_rect, config.SCREEN_HEIGHT - 250)

    def draw_setup_menu(self):
        return self.game.setup_menu.draw()

    def draw_side_selection(self):
        return self.game.side_selection_menu.draw()

    def _get_selected_unit(self):
        if hasattr(self.game, 'selected_unit') and self.game.selected_unit:
            row, col = self.game.selected_unit
            return self.game.grid.grid[row][col]
        if hasattr(self.game, 'combat_attacker') and self.game.combat_attacker:
            return self.game.combat_attacker
        return None

    def draw_panel(self):
        panel_rect = pygame.Rect(config.SCREEN_WIDTH - config.PANEL_WIDTH, 0, config.PANEL_WIDTH, config.SCREEN_HEIGHT)
        pygame.draw.rect(self.game.screen, (50, 50, 70), panel_rect)
        pygame.draw.rect(self.game.screen, (200, 200, 230), panel_rect, 5)
        content_rect = pygame.Rect(
            panel_rect.x + 20,
            20,
            config.PANEL_WIDTH - 40,
            panel_rect.height - 40
        )
        y_offset = content_rect.y
        status_text = self._get_status_text()
        text_width = min(status_text.get_width(), content_rect.width)
        text_x = content_rect.x + (content_rect.width - text_width) // 2
        self.game.screen.blit(status_text, (text_x, y_offset))
        y_offset += 40
        if hasattr(self.game, 'current_deploying_unit') and self.game.current_deploying_unit:
            unit_name = self.game.current_deploying_unit.image_key
            unit_info = f"{_('Coloca')}: {_(unit_name)}"
            unit_text = self.font.render(unit_info, True, config.COLOR_TEXTO)
            if unit_text.get_width() > content_rect.width:
                small_font = pygame.font.SysFont('Arial', 18)
                unit_text = small_font.render(unit_info, True, config.COLOR_TEXTO)
            self.game.screen.blit(unit_text, (content_rect.x, y_offset))
            y_offset += 30
        selected_unit = self._get_selected_unit()
        if selected_unit:
            self._draw_unit_info(selected_unit, content_rect, y_offset)
            y_offset += 150
        rules_button_rect = self._draw_rules_button(panel_rect, config.SCREEN_HEIGHT - 250)
        button_rect = None
        if self.game.state == "PLAYER_TURN":
            button_rect = self._draw_button(panel_rect, _("Finalizar movimiento") if self.game.turn_phase == config.TURN_PHASES["MOVEMENT"] else _("Finalizar Combate"), config.COLOR_BOTON_CANCELAR, config.SCREEN_HEIGHT - 80)
        elif self.game.state == "DEPLOY_PLAYER" and not getattr(self.game, 'current_deploying_unit', None):
            button_rect = self._draw_button(panel_rect, _("Confirmar Despliegue"), config.COLOR_BOTON, config.SCREEN_HEIGHT - 80)
        return button_rect

    def _get_status_text(self):
        max_width = config.PANEL_WIDTH - 10
        if self.game.state == config.GAME_STATES["SETUP_MENU"]:
            text = _("Menú de Configuración")
        elif self.game.state == config.GAME_STATES["SELECT_SIDE"]:
            text = _("Selecciona tu bando")
        elif self.game.state == config.GAME_STATES["DEPLOY_PLAYER"]:
            text = _("Despliega tus unidades")
        elif self.game.state == config.GAME_STATES["DEPLOY_AI"]:
            text = _("Despliegue del ordenador")
        elif self.game.state == config.GAME_STATES["PLAYER_TURN"]:
            phase = self.game.turn_phase
            text = f"{_(self.game.player_side)}: {_(phase)}"
        elif self.game.state == config.GAME_STATES["AI_TURN"]:
            text = _("Turno del ordenador")
        else:
            text = ""
        return self._render_fitted_text(text, max_width)

    def _render_fitted_text(self, text, max_width, color=None, font_size=20):
        if color is None:
            color = config.COLOR_TEXTO
        font = pygame.font.SysFont('Arial', font_size)
        if font.size(text)[0] <= max_width:
            return font.render(text, True, color)
        small_font = pygame.font.SysFont('Arial', max(12, font_size - 6))
        return small_font.render(text, True, color)

    def _draw_unit_info(self, unit, content_rect, y_offset):
        max_width = content_rect.width
        unit_name = unit.image_key
        title_font = pygame.font.SysFont('Arial', 20, bold=True)
        title_text = title_font.render(_(unit_name), True, config.COLOR_TEXTO)
        title_x = content_rect.x + (max_width - title_text.get_width()) // 2
        self.game.screen.blit(title_text, (title_x, y_offset))
        y_offset += 30
        if hasattr(unit, 'image_key') and unit.image_key in self.game.images:
            img = self.game.images[unit.image_key]
            img_size = min(max_width, 250)
            img_scaled = pygame.transform.smoothscale(img, (img_size, img_size))
            img_x = content_rect.x + (max_width - img_size) // 2
            self.game.screen.blit(img_scaled, (img_x, y_offset))
            y_offset += img_size + 10
        info_font_size = 16
        line_height = info_font_size + 4
        side_color = config.COLOR_CRUZADOS if unit.side == config.SIDE_CRUSADERS else config.COLOR_SARRACENOS
        side_text = self._render_fitted_text(f"{_('Bando')}: {_(unit.side)}", max_width, side_color, info_font_size)
        self.game.screen.blit(side_text, (content_rect.x, y_offset))
        y_offset += line_height
        power_text = self._render_fitted_text(f"{_('Fuerza')}: {unit.power}", max_width, config.COLOR_TEXTO, info_font_size)
        self.game.screen.blit(power_text, (content_rect.x, y_offset))
        y_offset += line_height
        speed_text = self._render_fitted_text(f"{_('Velocidad')}: {unit.speed}/{unit.original_speed}", max_width, config.COLOR_TEXTO, info_font_size)
        self.game.screen.blit(speed_text, (content_rect.x, y_offset))
        y_offset += line_height
        if unit.leader:
            leader_text = self._render_fitted_text(f"{_('Líder')}: {_('Sí')}", max_width, (255, 215, 0), info_font_size)
            self.game.screen.blit(leader_text, (content_rect.x, y_offset))
            y_offset += line_height
        health_status = _("Sana") if unit.health == 2 else _("Herida")
        health_color = (50, 200, 50) if unit.health == 2 else config.COMBAT_COLORS['wounded']
        health_text = self._render_fitted_text(f"{_('Estado')}: {health_status}", max_width, health_color, info_font_size)
        self.game.screen.blit(health_text, (content_rect.x, y_offset))

    def _draw_button(self, panel_rect, text, color, y_pos):
        button_rect = pygame.Rect(panel_rect.x + (config.PANEL_WIDTH - config.PANEL_BUTTON_WIDTH) // 2, y_pos, config.PANEL_BUTTON_WIDTH, config.PANEL_BUTTON_HEIGHT)
        pygame.draw.rect(self.game.screen, color, button_rect)
        button_text = self.font.render(_(text), True, config.COLOR_TEXTO)
        self.game.screen.blit(button_text, (button_rect.centerx - button_text.get_width()//2,
                                         button_rect.centery - button_text.get_height()//2))
        return button_rect

    def _draw_rules_button(self, panel_rect, y_position):
        rules_button_rect = self._draw_button(panel_rect, _("Ver Reglas"), config.COLOR_CRUZADOS, y_position)
        return rules_button_rect

    def draw_deployment_zones(self):
        if self.game.state not in ["DEPLOY_PLAYER", "DEPLOY_AI"] or not config.DEBUG_MODE:
            return
        if self.game.player_side == config.SIDE_CRUSADERS:
            player_zone = self._calculate_zone(config.HEX_COLS - 4, 0, 4, 4)
            ai_zone = self._calculate_zone(0, config.HEX_ROWS - 2, 8, 2)
        else:
            player_zone = self._calculate_zone(0, config.HEX_ROWS - 2, 8, 2)
            ai_zone = self._calculate_zone(config.HEX_COLS - 4, 0, 4, 4)
        if __debug__:
            self._draw_zone(player_zone, config.COLOR_ZONA_JUGADOR)
            self._draw_zone(ai_zone, config.COLOR_ZONA_IA)

    def _calculate_zone(self, start_col, start_row, cols, rows):
        hex_width = self.game.grid.hex_width
        hex_height = self.game.grid.hex_height
        pos_x = -hex_width/2
        pos_y = -hex_height/2
        x, y = self.game.grid.hex_to_pixel(start_row, start_col)
        x += pos_x
        y += pos_y

        # Apply scroll offset to position the zone correctly
        board_pos_x, board_pos_y = self._calculate_board_position(self.game.tablero_escalado)
        x += board_pos_x
        y += board_pos_y

        width = cols * hex_width * 1.025
        height = rows * hex_height * 0.79
        return pygame.Rect(x, y, width, height)

    def _draw_zone(self, zone_rect, color):
        s = pygame.Surface((zone_rect.width, zone_rect.height), pygame.SRCALPHA)
        s.fill(color)
        self.game.screen.blit(s, (zone_rect.x, zone_rect.y))

    def draw_possible_moves(self, possible_moves, grid, offset_x=0, offset_y=0):
        if not possible_moves:
            return
        for (row, col) in possible_moves:
            x, y = grid.hex_to_pixel(row, col)
            x += offset_x
            y += offset_y
            s = pygame.Surface((config.HEX_MIN_SIZE, config.HEX_MIN_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(s, (100, 200, 255, 150), (config.HEX_MIN_SIZE//2, config.HEX_MIN_SIZE//2), config.HEX_MIN_SIZE//2)
            self.game.screen.blit(s, (x - config.HEX_MIN_SIZE//2, y - config.HEX_MIN_SIZE//2))

    def draw_combat_targets(self):
        if self.game.combat_attacker and self.game.combat_targets:
            for target in self.game.combat_targets:
                x, y = self.game.grid.hex_to_pixel(target.row, target.col)
                pos_x, pos_y = self._calculate_board_position(self.game.tablero_escalado)
                x += pos_x
                y += pos_y
                s = pygame.Surface((config.HEX_MIN_SIZE*1.5, config.HEX_MIN_SIZE*1.5), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 0, 0, 150), (config.HEX_MIN_SIZE//2, config.HEX_MIN_SIZE//2), config.HEX_MIN_SIZE//2)
                self.game.screen.blit(s, (x - config.HEX_MIN_SIZE//2, y - config.HEX_MIN_SIZE//2))
                pygame.draw.circle(self.game.screen, (255, 0, 0), (x, y), config.HEX_MIN_SIZE//2 + 5, 3)

    def draw_victory_progress(self, game):
        if game.state == "SELECT_SIDE" or game.state == "DEPLOY_PLAYER" or game.state == "DEPLOY_AI":
            return
        panel_width = 200
        panel_height = 100
        panel_x = config.SCREEN_WIDTH - config.PANEL_WIDTH + 50
        panel_y = config.SCREEN_HEIGHT - 190
        s = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        game.screen.blit(s, (panel_x, panel_y))
        font_title = pygame.font.SysFont('Arial', 16, bold=True)
        text_title = font_title.render(_("Progreso hacia Arsouf"), True, config.COLOR_TEXTO)
        game.screen.blit(text_title, (panel_x + 10, panel_y + 10))
        font = pygame.font.SysFont('Arial', 14)
        text_turn = font.render(f"{_('Turno')}: {game.turn_count} / {game.max_turns}", True, config.COLOR_TEXTO)
        game.screen.blit(text_turn, (panel_x + 10, panel_y + 35))
        text_bagaje = font.render(f"{_('Bagajes')}: {game.units_in_arsouf[config.BAGGAGE_NAME]}/2", True, config.COLOR_TEXTO)
        game.screen.blit(text_bagaje, (panel_x + 10, panel_y + 55))
        text_other = font.render(f"{_('Otras unidades')}: {game.units_in_arsouf['other']}/2", True, config.COLOR_TEXTO)
        game.screen.blit(text_other, (panel_x + 10, panel_y + 75))

    def draw_intro(self, game):
        try:
            if not hasattr(game, 'images') or game.images is None or "cover" not in game.images:
                game.screen.fill(config.COLOR_BG)
            else:
                game.screen.blit(game.images["cover"], (0, 0))
            try:
                intro_font = pygame.font.Font(config.FONT_PATHS["abbasy"], 120)
            except Exception as e:
                print(f"Error loading font: {e}")
                intro_font = pygame.font.SysFont('Arial', 80, bold=True)
            intro_text = config.GAME_NAME
            intro_text_surface = intro_font.render(intro_text, True, config.WHITE)
            intro_text_rect = intro_text_surface.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 120))
            game.screen.blit(intro_text_surface, intro_text_rect)
            if hasattr(game, 'intro_start_time') and hasattr(game, 'intro_duration'):
                current_time = pygame.time.get_ticks()
                if current_time - game.intro_start_time >= game.intro_duration:
                    game._end_intro()
        except Exception as e:
            print(f"Error drawing intro screen: {e}")
            game.screen.fill(config.COLOR_BG)

    def draw_game_over(self, game):
        panel_width = 400
        panel_height = 200
        panel_x = (config.SCREEN_WIDTH - panel_width) // 2
        panel_y = (config.SCREEN_HEIGHT - panel_height) // 2
        s = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 220))
        game.screen.blit(s, (panel_x, panel_y))
        pygame.draw.rect(game.screen, (255, 215, 0), (panel_x, panel_y, panel_width, panel_height), 3)
        font_title = pygame.font.SysFont('Arial', 30, bold=True)
        text_title = font_title.render(_("FIN DEL JUEGO"), True, (255, 215, 0))
        game.screen.blit(text_title, (panel_x + (panel_width - text_title.get_width())//2, panel_y + 30))
        font = pygame.font.SysFont('Arial', 20)
        if game.winner == config.SIDE_CRUSADERS:
            text_winner = font.render(_("¡Victoria de los Cruzados!"), True, (255, 255, 255))
            text_reason = font.render(_("Han llegado a Arsouf"), True, (255, 255, 255))
        else:
            text_winner = font.render(_("¡Victoria de los Sarracenos!"), True, (255, 255, 255))
            text_reason = font.render(_("Los Cruzados no han llegado a Arsouf"), True, (255, 255, 255))
        game.screen.blit(text_winner, (panel_x + (panel_width - text_winner.get_width())//2, panel_y + 80))
        game.screen.blit(text_reason, (panel_x + (panel_width - text_reason.get_width())//2, panel_y + 120))
        font_exit = pygame.font.SysFont('Arial', 16)
        text_exit = font_exit.render(_("Presiona ESC para salir"), True, (200, 200, 200))
        game.screen.blit(text_exit, (panel_x + (panel_width - text_exit.get_width())//2, panel_y + 160))

    def draw_game(self, game):
        game.screen.fill(config.COLOR_BG)
        if game.state == config.GAME_STATES["INTRO"]:
            self.draw_intro(game)
        elif game.state == config.GAME_STATES["SETUP_MENU"]:
            self.draw_setup_menu()
        elif game.state == config.GAME_STATES["SELECT_SIDE"]:
            self.draw_side_selection()
        else:
            if game.tablero_escalado is not None:
                # Create a clipping area for the map to prevent drawing outside bounds
                available_width = config.SCREEN_WIDTH - config.PANEL_WIDTH
                available_height = config.SCREEN_HEIGHT - config.LOG_PANEL_HEIGHT
                map_clip_rect = pygame.Rect(0, 0, available_width, available_height)

                # Set clipping area
                game.screen.set_clip(map_clip_rect)

                pos_x, pos_y = self._calculate_board_position(game.tablero_escalado)
                game.screen.blit(game.tablero_escalado, (pos_x, pos_y))
                if hasattr(game, 'last_moved_unit_pos') and game.last_moved_unit_pos:
                    row, col = game.last_moved_unit_pos[0]
                    x, y = game.grid.hex_to_pixel(row, col)
                    x += pos_x
                    y += pos_y
                    s = pygame.Surface((config.HEX_MIN_SIZE, config.HEX_MIN_SIZE), pygame.SRCALPHA)
                    pygame.draw.circle(s, (255, 0, 0, 180), (config.HEX_MIN_SIZE//2, config.HEX_MIN_SIZE//2), config.HEX_MIN_SIZE//3)
                    game.screen.blit(s, (x - config.HEX_MIN_SIZE//2, y - config.HEX_MIN_SIZE//2))
                if __debug__ and game.grid is not None:
                    game.grid.draw_hex_debug(game.screen, pos_x, pos_y)
                if game.grid is not None and game.images is not None:
                    game.grid.draw(game.screen, game.images, pos_x, pos_y)
                if game.selected_unit and game.possible_moves:
                    self.draw_possible_moves(game.possible_moves, game.grid, pos_x, pos_y)
                if game.state == "PLAYER_TURN" and game.turn_phase == config.TURN_PHASES["COMBAT"]:
                    self.draw_combat_targets()
                self.draw_deployment_zones()

                # Remove clipping
                game.screen.set_clip(None)

                # Draw map scrollbars
                self._draw_map_scrollbars(game.tablero_escalado)

                #self.draw_victory_progress(game)
            self.draw_log_panel()
            self.draw_panel()
            self.draw_victory_progress(game)
        if game.game_over:
            self.draw_game_over(game)
