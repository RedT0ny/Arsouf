# gameui.py
import pygame
from config import *

class GameUI:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont('Arial', 24)
        self.log_font = pygame.font.SysFont('Arial', LOG_FONT_SIZE)
        self.log_messages = []        

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

    def draw_log_panel(self):
        """Dibuja el panel de log en la parte inferior."""
        panel_rect = pygame.Rect(0, SCREEN_HEIGHT - LOG_PANEL_HEIGHT, SCREEN_WIDTH, LOG_PANEL_HEIGHT)
        pygame.draw.rect(self.game.screen, LOG_PANEL_COLOR, panel_rect)
        
        # Dibujar mensajes de log (los últimos que caben)
        y_offset = panel_rect.y + LOG_MARGIN
        max_lines = (LOG_PANEL_HEIGHT - 2*LOG_MARGIN) // (LOG_FONT_SIZE + 2)
        
        for msg in self.log_messages[-max_lines:]:
            log_text = self.log_font.render(msg, True, LOG_TEXT_COLOR)
            self.game.screen.blit(log_text, (panel_rect.x + LOG_MARGIN, y_offset))
            y_offset += LOG_FONT_SIZE + 2

    def add_log_message(self, message):
        """Añade un mensaje al log."""
        self.log_messages.append(message)
        # Limitar el número máximo de mensajes almacenados
        if len(self.log_messages) > 100:
            self.log_messages.pop(0)

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