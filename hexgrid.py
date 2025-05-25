# hexgrid.py
import pygame
import math
from config import *

class HexGrid:
    def __init__(self):
        self.rows = HEX_ROWS
        self.cols = HEX_COLS
        self.hex_size = HEX_SIZE  # Usamos el valor ya escalado de config.py
        
        self.grid = [[None for _ in range(HEX_COLS)] for _ in range(HEX_ROWS)]
        
        # Geometría hexagonal (precalculada)
        self.hex_width = HEX_SIZE
        self.hex_height = int(2* HEX_SIZE / math.sqrt(3))
        
        # Offsets para alineación visual (ajustar según necesidad)
        self.offset_x = MARGENES_ESCALADOS["izquierdo"] + int(self.hex_width * 0.5)
        self.offset_y = MARGENES_ESCALADOS["superior"] + int(self.hex_height * 0.5)        
        
    def hex_to_pixel(self, row, col):
        # Ajuste horizontal: filas impares indentadas
        indentacion = self.hex_width * 0.5 if not row % 2 else 0  # Cambiado a row % 2 != 0
        x = col * self.hex_width * 1.025 + indentacion
        
        # Ajuste vertical
        y = row * self.hex_height * 0.79
        
        return (int(x + self.offset_x), int(y + self.offset_y))

    def add_unit(self, row, col, unit):
        """
        Añade una unidad al grid hexagonal y actualiza su posición.
        
        Parámetros:
            row (int): Fila del grid (0 a HEX_ROWS-1)
            col (int): Columna del grid (0 a HEX_COLS-1)
            unit (Unit): Instancia de la unidad (Ricardo, Templario, etc.)
        
        Ejemplo:
            grid.add_unit(0, 21, Ricardo())  # Añade Ricardo en esquina superior derecha
        """
        # 1. Validar coordenadas
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise ValueError(f"Coordenadas ({row}, {col}) fuera del grid {self.rows}x{self.cols}")

        # 2. Verificar si la posición está ocupada
        if self.grid[row][col] is not None:
            print(f"¡Advertencia: Sobreescribiendo unidad en ({row}, {col})!")
        
        # 3. Asignar unidad al grid
        self.grid[row][col] = unit
        
        # 4. Actualizar posición interna de la unidad
        unit.set_position(row, col)

    def is_in_deployment_zone(self, row, col, side):
        """Determina si una posición está en la zona de despliegue."""
        if side == "CRUZADOS":
            return col >= HEX_COLS - 4 and row < 4
        else:
            return col < 8 and row >= HEX_ROWS - 2
            
    def calculate_zone_rect(self, start_col, start_row, cols, rows):
        """Calcula el rectángulo que engloba una zona del grid."""
        x, y = self.hex_to_pixel(start_row, start_col)
        width = cols * self.hex_width * 1.025
        height = rows * self.hex_height * 0.79
        return pygame.Rect(x, y, width, height)

    def draw(self, screen, images, tablero_x=0, tablero_y=0):
        """
        Dibuja todas las unidades en el grid.
        
        Parámetros:
            screen: Superficie de Pygame donde dibujar
            images: Diccionario de imágenes cargadas
            tablero_x: Offset horizontal del tablero (opcional)
            tablero_y: Offset vertical del tablero (opcional)
        """
        for row in range(self.rows):
            for col in range(self.cols):
                unit = self.grid[row][col]
                if unit:
                    x, y = self.hex_to_pixel(row, col)
                    # Aplicar offset del tablero centrado
#                     x += tablero_x
#                     y += tablero_y

                    img = images.get(unit.image_key)
                    if img:
                        # Centrar la imagen en el hexágono
                        screen.blit(img, (x - img.get_width() // 2, y - img.get_height() // 2))
                        
    def draw_hex_debug(self, screen):
        """Debug visual mejorado"""
        for row in range(self.rows):
            for col in range(self.cols):
                x, y = self.hex_to_pixel(row, col)
                pygame.draw.circle(screen, (0, 255, 255, 0.2), (x, y), self.hex_width * 0.5, 1)  # círculos cian