# hexgrid.py
import pygame
import math
from typing import List, Tuple, Optional  # Añadir estas importaciones
from config import *
from units import Unit

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

    def get_possible_moves(self, row, col, speed, moved_units=None, current_path=None):
        """Calcula todos los movimientos posibles desde una posición dada."""
        if moved_units is None:
            moved_units = set()
        if current_path is None:
            current_path = []
        
        possible_moves = []
        unit = self.grid[row][col]
        
        if not unit or (row, col) in moved_units:
            return possible_moves

        # Ajusta velocidad de unidades a pie (slow) en carretera
        effective_speed = speed
        if hasattr(unit, 'slow') and (row, col) in ROAD_HEXES:
            effective_speed += 1  # Bonus por empezar en carretera
        
        from collections import deque
        visited = {}
        queue = deque()
        queue.append((row, col, 0.0, current_path.copy())) # (row, col, accumulated_cost, path)
        visited[(row, col)] = 0.0

        while queue:
            r, c, dist, path = queue.popleft()
            
            if dist > 0 and self.grid[r][c] is None:
                possible_moves.append((r, c))

            for (nr, nc), cost in self._get_valid_neighbors(r, c, path, unit):
                new_dist = dist + cost
                if new_dist <= effective_speed and (nr, nc not in visited or new_dist < visited.get((nr, nc), float('inf'))):
                    visited[(nr, nc)] = new_dist
                    queue.append((nr, nc, new_dist, path + [(r, c)]))
                            
        return possible_moves
    
    def _get_valid_neighbors(self, row, col, current_path, unit):
        """Devuelve vecinos válidos y costo de movimiento, considerando barreras"""
        # Direcciones para hex grid vertical (punto arriba)
        # Estructura: (dr, dc) donde dr = cambio en fila, dc = cambio en columna
        # Organizadas en anillos concéntricos
        directions = [
            [(-1,0), (-1,1), (0,1), (1,0), (1,1), (0,-1)],  # Filas pares
            [(-1,-1), (-1,0), (0,1), (1,-1), (1,0), (0,-1)]  # Filas impares
        ]
        
        neighbors = []
        dir_set = directions[row % 2]
        
        for dr, dc in dir_set:
            nr = row + dr
            nc = col + dc
            
            # 1. Verificar límites y hexágonos prohibidos
            if not (0 <= nr < self.rows and 0 <= nc < self.cols):
                continue
            if (nr, nc) in FORBIDDEN_HEXES:
                continue
            
            # 2. Determinar costo base del movimiento
            move_pair = frozenset({(row, col), (nr, nc)})
            cost = 1  # Costo base
            
            # 3. Aplicar modificadores de terreno
            # a) Barreras de río
            if move_pair in RIVER_BARRIERS:
                if FORD_HEX not in current_path and FORD_HEX != (row, col) and FORD_HEX != (nr, nc):
                    continue # Bloquear movimiento
                cost = 2 # Penalización por cruzar río
            
            # Modificadores para unidades slow
            if hasattr(unit, 'slow'):
                on_road_start = (row, col) in ROAD_HEXES
                on_road_end = (nr, nc) in ROAD_HEXES
                
                # Bonus: movimiento más rápido EN carretera
                if on_road_start and on_road_end:
                    cost = 0.75  # Mitad de costo en carretera continua
                # Penalización: salir de carretera
                elif on_road_start and not on_road_end:
                    cost = 1.25  # Costo extra por dejar carretera
                    
            neighbors.append(((nr, nc), cost))
        
        return neighbors

    def is_unit_of_side(self, unit, side):
        """Determina si una unidad pertenece a un bando."""
        if side == "CRUZADOS":
            return isinstance(unit, (Ricardo, Templario, Hospitalario, Caballero, Infanteria, Bagaje))
        else:
            return isinstance(unit, (Saladino, Mameluco, Arquero, Explorador))

    def move_unit(self, from_row, from_col, to_row, to_col):
        """Mueve una unidad entre posiciones."""
        if not (0 <= to_row < self.rows and 0 <= to_col < self.cols):
            return False
            
        unit = self.grid[from_row][from_col]
        if unit and self.grid[to_row][to_col] is None:
            self.grid[from_row][from_col] = None
            self.add_unit(to_row, to_col, unit)
            return True
        return False

    def is_in_deployment_zone(self, row, col, side):
        """Determina si una posición está en la zona de despliegue."""
        if side == "CRUZADOS":
            return col >= HEX_COLS - 4 and row < 4
        else:
            return col < 8 and row >= HEX_ROWS - 2

    def get_adjacent_enemies(self, row, col, side):
        """Devuelve unidades enemigas adyacentes"""
        enemies = []
        for (r, c), _ in self._get_valid_neighbors(row, col, []):
            unit = self.grid[r][c]
            if unit and unit.side != side:
                enemies.append(unit)
        return enemies

    def get_adjacent_positions(self, row: int, col: int) -> List[tuple]:
        """Nuevo método: devuelve posiciones adyacentes sin validar"""
        directions = [
            [(-1,0), (-1,1), (0,1), (1,0), (1,1), (0,-1)],  # Filas pares
            [(-1,-1), (-1,0), (0,1), (1,-1), (1,0), (0,-1)]  # Filas impares
        ]
        return [(row + dr, col + dc) for dr, dc in directions[row % 2]]

    def get_unit(self, row: int, col: int) -> Optional['Unit']:
        """Método seguro para obtener unidades"""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col]
        return None

    def eliminar_unidad(self, row, col):
        self.grid[row][col] = None
        
    def get_units_in_radius(self, row, col, radius, side=None):
        """Obtiene unidades en un radio, filtrando por bando si se especifica"""
        units = []
        visited = set()
        queue = deque()
        queue.append((row, col, 0))
        visited.add((row, col))
        
        while queue:
            r, c, dist = queue.popleft()
            
            if 0 < dist <= radius:
                unit = self.grid[r][c]
                if unit and (side is None or unit.side == side):
                    units.append(unit)
            
            if dist < radius:
                dir_set = directions[r % 2]
                for dr, dc in dir_set:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < self.rows and 0 <= nc < self.cols and 
                        (nr, nc) not in visited):
                        visited.add((nr, nc))
                        queue.append((nr, nc, dist + 1))
        
        return units
    
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