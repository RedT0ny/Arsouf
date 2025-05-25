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
        """Calcula cuántas líneas son visibles en el panel"""
        return (LOG_PANEL_HEIGHT - 2*LOG_MARGIN) // LOG_LINE_HEIGHT

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
                if __debug__:
                    print("DEBUG: Scroll - Arrastre iniciado")
                return True
        return False

    def _handle_scroll_end(self):
        """Finaliza el arrastre del scroll"""
        if self.log_scroll_dragging:
            self.log_scroll_dragging = False
            if __debug__:
                print("DEBUG: Scroll - Arrastre finalizado")
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
        if __debug__:
            print(f"DEBUG: Wheel scroll - Delta: {wheel_delta}, Posición: {self.log_scroll_position}/{max_scroll}")

    def add_log_message(self, message):
        """Añade un mensaje al log y ajusta el scroll."""
        self.log_messages.append(message)
        if len(self.log_messages) > LOG_MAX_MESSAGES:
            self.log_messages.pop(0)
        
        # Auto-scroll al final si está cerca del final
        visible_lines = (SCREEN_HEIGHT - LOG_PANEL_HEIGHT) // LOG_LINE_HEIGHT
        if len(self.log_messages) - self.log_scroll_position <= visible_lines + 5:
            self.log_scroll_position = max(0, len(self.log_messages) - visible_lines)
            
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
        
        y_offset = 20
        
        # Estado del juego
        status_text = self._get_status_text()
        self.game.screen.blit(status_text, (panel_rect.x + PANEL_WIDTH//2 - status_text.get_width()//2, y_offset))
        y_offset += 40
        
        # Información de la unidad actual (si aplica)
        if hasattr(self.game, 'current_deploying_unit') and self.game.current_deploying_unit:
            unit_info = f"Coloca: {type(self.game.current_deploying_unit).__name__}"
            unit_text = self.font.render(unit_info, True, COLOR_TEXTO)
            self.game.screen.blit(unit_text, (panel_rect.x + 20, y_offset))
            y_offset += 30
        
        # Dibujar botón según el estado del juego
        button_rect = None
        if self.game.state == "PLAYER_TURN":
            button_rect = self._draw_button(panel_rect, "Finalizar Turno", COLOR_BOTON_CANCELAR, SCREEN_HEIGHT - 80)
        elif self.game.state == "DEPLOY_PLAYER" and not getattr(self.game, 'current_deploying_unit', None):
            button_rect = self._draw_button(panel_rect, "Confirmar Despliegue", COLOR_BOTON, SCREEN_HEIGHT - 80)
        
        return button_rect
    
    def _get_status_text(self):
        """Devuelve el texto de estado según el estado actual del juego."""
        if self.game.state == "SELECT_SIDE":
            return self.font.render("Selecciona tu bando", True, COLOR_TEXTO)
        elif self.game.state == "DEPLOY_PLAYER":
            return self.font.render("Despliega tus unidades", True, COLOR_TEXTO)
        elif self.game.state == "DEPLOY_AI":
            return self.font.render("El ordenador está desplegando", True, COLOR_TEXTO)
        elif self.game.state == "PLAYER_TURN":
            return self.font.render(f"Tu turno ({self.game.player_side})", True, COLOR_TEXTO)
        elif self.game.state == "AI_TURN":
            return self.font.render(f"Turno del ordenador ({self.game.ai_side})", True, COLOR_TEXTO)
        return self.font.render("", True, COLOR_TEXTO)
    
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
            
        color = COLOR_ZONA_JUGADOR if self.game.state == "DEPLOY_PLAYER" else COLOR_ZONA_IA
        
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
        pos_x = 0 #(SCREEN_WIDTH - self.game.tablero_escalado.get_width()) // 2
        pos_y = 0 #(SCREEN_HEIGHT - self.game.tablero_escalado.get_height()) // 2
        
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