# main.py
import pygame
import sys
from config import *
from hexgrid import HexGrid
from units import *

class Game:
    def __init__(self):
        pygame.init()
        
        # Inicializar
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Batalla de Arsuf")
        
        # Cargar y escalar tablero (usando constantes de config.py)
        self.tablero_escalado = pygame.transform.smoothscale(
            pygame.image.load(IMAGE_PATHS["board"]).convert_alpha(),
            (int(TABLERO_REAL_WIDTH * ESCALA), int(TABLERO_REAL_HEIGHT * ESCALA))
        )
                
        self.hex_size = HEX_SIZE  # Ajuste preciso

        # Inicializar grid
        self.grid = HexGrid()

        self.clock = pygame.time.Clock()
        self.running = True
        
        # Cargar imágenes de unidades (ya escaladas)
        self.images = self._load_images()
        self._place_initial_units()
    
    def _load_images(self):
        images = {}
        for key, path in IMAGE_PATHS.items():
            if key == "board": continue
            try:
                img = pygame.image.load(path).convert_alpha()
                # Escalar unidades al 95% del hex_size (para espacio entre ellas)
                size = int(self.hex_size * 0.95)
                images[key] = pygame.transform.smoothscale(img, (size, size))
            except Exception as e:
                print(f"Error cargando {path}: {e}")
                # Placeholder verde (para distinguir de errores)
                images[key] = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(images[key], (0, 255, 0), (size//2, size//2), size//2)
        return images
    
    def _place_initial_units(self):
        """Coloca todas las unidades en sus posiciones iniciales."""
        # ---- CRUZADOS (últimas 4 columnas, primeras 4 filas) ----
        # Líder y unidades especiales
        self.grid.add_unit(0, HEX_COLS-1, Ricardo())  # Esquina superior derecha
        self.grid.add_unit(1, HEX_COLS-2, Templario())
        self.grid.add_unit(2, HEX_COLS-1, Hospitalario())

        # 3x Caballeros
        self.grid.add_unit(0, HEX_COLS-3, Caballero())
        self.grid.add_unit(1, HEX_COLS-4, Caballero())
        self.grid.add_unit(3, HEX_COLS-2, Caballero())

        # 6x Infantería (distribuida en las primeras 4 filas, últimas 4 columnas)
        for row, col in [(0, HEX_COLS-4), (0, HEX_COLS-2),
                        (1, HEX_COLS-1), (1, HEX_COLS-3),
                        (2, HEX_COLS-3), (3, HEX_COLS-4)]:
            self.grid.add_unit(row, col, Infanteria())

        # 4x Carros de bagaje
        for row, col in [(2, HEX_COLS-2), (3, HEX_COLS-1),
                        (2, HEX_COLS-4), (3, HEX_COLS-3)]:
            self.grid.add_unit(row, col, Bagaje())

        # ---- SARACENOS (primeras 8 columnas, últimas 2 filas) ----
        # Líder
        self.grid.add_unit(HEX_ROWS-1, 0, Saladino())  # Esquina inferior izquierda

        # 4x Mamelucos (columnas impares)
        for col in [1, 3, 5, 7]:
            self.grid.add_unit(HEX_ROWS-2, col, Mameluco())

        # 6x Arqueros a caballo
        for row, col in [(HEX_ROWS-1, 1), (HEX_ROWS-1, 2),
                        (HEX_ROWS-1, 3), (HEX_ROWS-1, 4),
                        (HEX_ROWS-1, 5), (HEX_ROWS-1, 6)]:
            if col < 8:  # Asegurar que está en las primeras 8 columnas
                self.grid.add_unit(row, col, Arquero())

        # 5x Exploradores
        for row, col in [(HEX_ROWS-2, 2), (HEX_ROWS-2, 4),
                        (HEX_ROWS-2, 6), (HEX_ROWS-2, 0),
                        (HEX_ROWS-1, 7)]:
            self.grid.add_unit(row, col, Explorador())

    def run(self):
        while self.running:
            self._handle_events()
            self._draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
    
    def _draw(self):
        # Centrar el tablero escalado en la ventana
        pos_x = (SCREEN_WIDTH - self.tablero_escalado.get_width()) // 2
        pos_y = (SCREEN_HEIGHT - self.tablero_escalado.get_height()) // 2

        self.screen.fill(COLOR_BG)  # Fondo
        self.screen.blit(self.tablero_escalado, (pos_x, pos_y))
 
        if __debug__: 
            # DEBUG VISUAL: Dibuja líneas donde se calculan los bordes
            pygame.draw.line(self.screen, (255,0,0), (MARGENES_ESCALADOS["izquierdo"], 0), (MARGENES_ESCALADOS["izquierdo"], SCREEN_HEIGHT), 2)
            pygame.draw.line(self.screen, (0,255,0), (0, MARGENES_ESCALADOS["superior"]), (SCREEN_WIDTH, MARGENES_ESCALADOS["superior"]), 2)
            
            # Dibujar hexágonos DEBUG (antes que las unidades)
            self.grid.draw_hex_debug(self.screen)
    
        # Dibujar unidades (ajustando a la posición centrada del tablero)
        self.grid.draw(self.screen, self.images, pos_x, pos_y)
        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()