# hexgrid.py
from collections import deque

import pygame
import math
import gettext
_ = gettext.gettext

from typing import List, Tuple, Optional  # Añadir estas importaciones
from units import *
from config import COMBAT_COLORS, HEX_WIDTH, HEX_HEIGHT, HEX_ROWS, HEX_COLS, MARGENES_ESCALADOS, ROAD_HEXES, FORBIDDEN_HEXES, RIVER_BARRIERS, FORD_HEX

class HexGrid:
    def __init__(self) -> None:
        self.rows = HEX_ROWS
        self.cols = HEX_COLS

        self.grid = [[None for _ in range(HEX_COLS)] for _ in range(HEX_ROWS)]

        # Geometría hexagonal (usando dimensiones reales)
        self.hex_width = HEX_WIDTH   # Ancho del hexágono (104px escalado)
        self.hex_height = HEX_HEIGHT  # Altura del hexágono (120px escalado)

        # Factor de superposición vertical para hexágonos
        self.vertical_overlap_factor = 0.75

        # Offsets para alineación visual (ajustar según necesidad)
        self.offset_x = MARGENES_ESCALADOS["izquierdo"] + int(self.hex_width * 0.5)
        self.offset_y = MARGENES_ESCALADOS["superior"] + int(self.hex_height * 0.5)

    def hex_to_pixel(self, row, col) -> tuple[int, int]:
        """
        Convierte coordenadas de grid a píxeles en pantalla.
        Para hexágonos verticales (vértices arriba/abajo), el espaciado horizontal
        es igual al ancho del hexágono, y el espaciado vertical es 3/4 de la altura.
        """
        # Para hexágonos verticales, las filas pares están indentadas
        indentacion = self.hex_width * 0.5 if row % 2 == 0 else 0

        # Espaciado horizontal: ancho del hexágono
        x = col * self.hex_width + indentacion

        # Espaciado vertical: factor de superposición de la altura para que se superpongan correctamente
        y = row * (self.hex_height * self.vertical_overlap_factor)

        return int(x + self.offset_x), int(y + self.offset_y)

    def add_unit(self, row: int, col: int, unit: Unit) -> None:
        """
        Añade una unidad al grid hexagonal y actualiza su posición.

        Parámetros:
            row (int): Fila del grid (0 a HEX_ROWS-1)
            col (int): Columna del grid (0 a HEX_COLS-1)
            unit (Unit): Instancia de la unidad (Ricardo, Templario, etc.)

        Ejemplo:
            grid.add_unit(0, 21, Ricardo()) # Añade Ricardo en esquina superior derecha
        """
        # 1. Validar coordenadas
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise ValueError(_("Coordenadas ({row}, {col}) fuera del grid {rows}x{cols}").format(row=row, col=col, rows=self.rows, cols=self.cols))

        # 2. Verificar si la posición está ocupada
        if self.grid[row][col] is not None:
            print(_("¡Advertencia: Sobreescribiendo unidad en ({row}, {col})!").format(row=row, col=col))

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

        possible_moves: List[Tuple[int, int]] = []
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
        # Direcciones para hex grid vertical (vértices arriba/abajo)
        # Estructura: (dr, dc) donde dr = cambio en fila, dc = cambio en columna
        directions = [
            [(-1,0), (-1,1), (0,1), (1,0), (1,1), (0,-1)],  # Filas pares (indentadas)
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

            # Verificar si hay una unidad enemiga en la casilla (no se puede saltar sobre enemigos)
            neighbor_unit = self.grid[nr][nc]
            if neighbor_unit and neighbor_unit.side != unit.side:
                continue  # No se puede mover a través de unidades enemigas

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
        if side == SIDE_CRUSADERS:
            return col >= HEX_COLS - 4 and row < 4
        else:
            return col < 8 and row >= HEX_ROWS - 2

    # En hexgrid.py
    def get_adjacent_enemies(self, row, col, side):
        """Devuelve unidades enemigas adyacentes"""
        enemies = []
        for r, c in self.get_adjacent_positions(row, col):
            unit = self.get_unit(r, c)
            if unit and unit.side != side:
                enemies.append(unit)
        return enemies

    def get_adjacent_positions(self, row, col):
        """Devuelve posiciones adyacentes"""
        directions = [
            [(-1,0), (-1,1), (0,1), (1,0), (1,1), (0,-1)],  # Filas pares (indentadas)
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

        # Definir direcciones para hex grid vertical (vértices arriba/abajo)
        directions = [
            [(-1, 0), (-1, 1), (0, 1), (1, 0), (1, 1), (0, -1)],  # Filas pares (indentadas)
            [(-1, -1), (-1, 0), (0, 1), (1, -1), (1, 0), (0, -1)]  # Filas impares
        ]

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

        # Para hexágonos verticales, el ancho total es el número de columnas por el ancho del hexágono
        width = (cols * self.hex_width) + self.hex_width * 0.5

        # Para hexágonos verticales, la altura total es el número de filas por el factor de superposición de la altura
        # (debido a la superposición vertical)
        height = rows * (self.hex_height * self.vertical_overlap_factor)

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
                    x += tablero_x
                    y += tablero_y

                    img = images.get(unit.image_key)
                    if img:
                        # Centrar la imagen en el hexágono
                        img_x = x - img.get_width() // 2
                        img_y = y - img.get_height() // 2
                        screen.blit(img, (img_x, img_y))

                        # Dibujar aspa roja si la unidad está herida
                        if unit.wounded_mark:
                            # Calcular las coordenadas para el aspa
                            img_width = img.get_width()
                            img_height = img.get_height()

                            # Dibujar líneas diagonales (aspa)
                            pygame.draw.line(screen, COMBAT_COLORS['wounded'], 
                                           (img_x + 0.25*img_width, img_y + 0.25*img_height),
                                           (img_x + 0.75*img_width, img_y + 0.75*img_height), 3)
                            pygame.draw.line(screen, COMBAT_COLORS['wounded'], 
                                           (img_x + 0.75*img_width, img_y + 0.25*img_height),
                                           (img_x + 0.25*img_width, img_y + 0.75*img_height), 3)

    def draw_hex_debug(self, screen, tablero_x=0, tablero_y=0):
        """
        Debug visual mejorado - Dibuja círculos centrados en cada hexágono
        para visualizar la posición exacta del centro de cada celda.

        Parámetros:
            screen: Superficie de Pygame donde dibujar
            tablero_x: Offset horizontal del tablero (opcional)
            tablero_y: Offset vertical del tablero (opcional)
        """
        for row in range(self.rows):
            for col in range(self.cols):
                # Obtener el centro del hexágono
                x, y = self.hex_to_pixel(row, col)

                # Aplicar offset del tablero centrado
                x += tablero_x
                y += tablero_y

                # Dibujar círculo centrado en el hexágono
                # El radio es proporcional al tamaño del hexágono para mejor visualización
                radius = min(self.hex_width, self.hex_height) * 0.5
                pygame.draw.circle(screen, (0, 255, 255, 128), (x, y), radius, 1)  # círculos cian semi-transparentes
