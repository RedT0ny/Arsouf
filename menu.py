# menu.py
import pygame
import gettext
_ = gettext.gettext
from config import *

class Menu:
    """
    Clase base para manejar menús en el juego.
    Proporciona funcionalidad común para todos los tipos de menús.
    """
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont('Arial', 24)
    
    def draw_button(self, rect, text, color, text_color=COLOR_TEXTO):
        """Dibuja un botón con texto centrado."""
        pygame.draw.rect(self.screen, color, rect)
        button_text = self.font.render(_(text), True, text_color)
        self.screen.blit(button_text, (rect.centerx - button_text.get_width()//2, 
                                     rect.centery - button_text.get_height()//2))
        return rect

class SetupMenu(Menu):
    """
    Menú de configuración del juego.
    Permite cambiar la escala de pantalla, el idioma, ver las reglas, etc.
    """
    def __init__(self, screen):
        super().__init__(screen)
    
    def draw(self):
        """Dibuja el menú de configuración."""
        self.screen.fill(COLOR_BG)

        # Título
        title = self.font.render(_("Menú de Configuración"), True, COLOR_TEXTO)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, TITULO_Y))

        # Botones del menú
        button_y = OPCIONES_Y
        button_spacing = 70  # Espacio entre botones

        # 1. Botón de escala de pantalla
        scale_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, button_y, BOTON_WIDTH, BOTON_HEIGHT)
        self.draw_button(scale_rect, f"{_('Escala de pantalla')}: {int(DISPLAY_SCALING * 100)}%", (100, 150, 200))
        button_y += button_spacing

        # 2. Botón de idioma
        language_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, button_y, BOTON_WIDTH, BOTON_HEIGHT)
        self.draw_button(language_rect, _("Idioma"), (150, 100, 200))
        button_y += button_spacing

        # 3. Botón de valores predeterminados
        defaults_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, button_y, BOTON_WIDTH, BOTON_HEIGHT)
        self.draw_button(defaults_rect, _("Valores predeterminados"), (200, 150, 100))
        button_y += button_spacing

        # 4. Botón de ver reglas
        rules_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, button_y, BOTON_WIDTH, BOTON_HEIGHT)
        self.draw_button(rules_rect, _("Ver Reglas"), COLOR_CRUZADOS)
        button_y += button_spacing

        # 5. Botón de selección de bando
        side_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, button_y, BOTON_WIDTH, BOTON_HEIGHT)
        self.draw_button(side_rect, _("Seleccionar bando"), (100, 200, 150))
        button_y += button_spacing

        # 6. Botón de salir
        quit_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, button_y, BOTON_WIDTH, BOTON_HEIGHT)
        self.draw_button(quit_rect, _("Salir"), COLOR_BOTON_CANCELAR)

        pygame.display.flip()
        return scale_rect, language_rect, defaults_rect, rules_rect, side_rect, quit_rect
    
    def handle_event(self, event):
        """Maneja las interacciones con el menú de configuración."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            scale_rect, language_rect, defaults_rect, rules_rect, side_rect, quit_rect = self.draw()
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

class SideSelectionMenu(Menu):
    """
    Menú de selección de bando.
    Permite elegir entre jugar como Cruzados o Sarracenos.
    """
    def __init__(self, screen):
        super().__init__(screen)
    
    def draw(self):
        """Dibuja la pantalla de selección de lado."""
        self.screen.fill(COLOR_BG)

        # Título
        title = self.font.render(_("Selecciona tu bando:"), True, COLOR_TEXTO)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, TITULO_Y))

        # Botón Cruzados
        cruzados_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, OPCIONES_Y, BOTON_WIDTH, BOTON_HEIGHT)
        self.draw_button(cruzados_rect, _("Jugar como Cruzados"), COLOR_CRUZADOS)

        # Botón Sarracenos
        sarracenos_rect = pygame.Rect(SCREEN_WIDTH//2 - BOTON_WIDTH//2, OPCIONES_Y + OPCIONES_ESPACIADO, BOTON_WIDTH, BOTON_HEIGHT)
        self.draw_button(sarracenos_rect, _("Jugar como Sarracenos"), COLOR_SARRACENOS)

        pygame.display.flip()
        return cruzados_rect, sarracenos_rect
    
    def handle_event(self, event):
        """Maneja la selección de bando."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            cruzados_rect, sarracenos_rect = self.draw()
            mouse_pos = pygame.mouse.get_pos()

            if cruzados_rect.collidepoint(mouse_pos):
                return SIDE_CRUSADERS
            elif sarracenos_rect.collidepoint(mouse_pos):
                return SIDE_SARACENS
        return None