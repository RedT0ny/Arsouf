# units.py
# import pygame
import random
from typing import TYPE_CHECKING
from config import *

if TYPE_CHECKING:
    from hexgrid import HexGrid  # Solo para type checking, no causa importación real

class Unit:
    """Clase base para todas las unidades del juego."""
    def __init__(self, image_key, side):
        self.image_key = image_key
        self.side = side  # "CRUZADOS" o "SARRACENOS"
        self.power = 0
        self.row = None
        self.col = None
        self.health = 2  # 2 = sana, 1 = herida, 0 = muerta
        self.original_speed = 0  # Se establecerá en cada subclase
        self.wounded_mark = False  # Para mostrar cruz roja
        
    def set_position(self, row, col):
        """Establece la posición en el grid."""
        self.row = row
        self.col = col
    
    def atacar(self, objetivo, grid):
        """Devuelve True si el ataque fue exitoso"""
        if self.health != 2:  # Solo unidades sanas pueden atacar
            return False
            
        ataque_power = self.power + random.randint(1, 6)
        
        # Bonus por líder adyacente
        if self._tiene_lider_adyacente(grid):
            ataque_power += 2
            
        # Cálculo del poder defensivo, incluyendo bonus
        defensa_power = objetivo.power + random.randint(1, 6) + self._calcular_bono_aliados(objetivo, grid)

        if ataque_power > defensa_power:
            objetivo.recibir_herida(grid)
            return True
        return False
        
    def recibir_herida(self, grid):
        if self.health == 2:  # Primera herida
            self.health = 1
            self.speed = 1  # Reducir velocidad
            self.wounded_mark = True
        else:  # Segunda herida
            self.health = 0
            grid.eliminar_unidad(self.row, self.col)

    def recuperar(self, grid):
        """Intenta recuperar la unidad si no hay enemigos cerca"""
        if (self.health == 1 and 
            not self._enemigos_cercanos(grid, radius=3)):
            self.health = 2
            self.speed = self.original_speed
            self.wounded_mark = False
            return True
        return False

    def _tiene_lider_adyacente(self, grid):
        # Implementar lógica para detectar líder aliado adyacente
        lider = "Ricardo" if self.side == "CRUZADOS" else "Saladino"
        for r, c in grid.get_adjacent_positions(self.row, self.col):
            unit = grid.get_unit(r, c)
            if unit and type(unit).__name__ == lider:
                return True
        return False
        
    def _calcular_bono_aliados(self, unidad_defensora: 'Unit', grid: 'HexGrid') -> float:
        """Calcula el bono de defensa por unidades aliadas adyacentes a la unidad ATACANTE,
        con bono adicional si el líder está adyacente al DEFENSOR.
        
        Reglas:
        - Cada unidad aliada adyacente al ATACANTE aporta la MITAD de su poder
        - Si el líder está adyacente al DEFENSOR, aporta +2 adicionales
        - No hay límite máximo de bono
        """
        bono_total = 0.0
        
        # 1. Bono por aliados adyacentes al ATACANTE (self)
        for r, c in grid.get_adjacent_positions(self.row, self.col):
            unidad_adyacente = grid.get_unit(r, c)
            if unidad_adyacente and unidad_adyacente.side == self.side:  # Aliados del atacante
                bono_total += round(unidad_adyacente.power / 2, 1)
        
        # 2. Bono adicional si el líder está adyacente al DEFENSOR
        for r, c in grid.get_adjacent_positions(unidad_defensora.row, unidad_defensora.col):
            unidad_adyacente = grid.get_unit(r, c)
            if unidad_adyacente and self._es_lider(unidad_adyacente) and unidad_adyacente.side == unidad_defensora.side:
                bono_total += 2
                break  # Solo se cuenta una vez aunque haya múltiples líderes (por seguridad)
        
        return bono_total

    def _es_lider(self, unidad: 'Unit') -> bool:
        """Determina si una unidad es el líder de su facción"""
        if unidad.side == "CRUZADOS":
            return isinstance(unidad, Ricardo)
        else:
            return isinstance(unidad, Saladino)
        
    def _enemigos_cercanos(self, grid, radius=3):
        """Verifica si hay enemigos en un radio determinado"""
        enemies = grid.get_units_in_radius(self.row, self.col, radius)
        return any(unit.side != self.side for unit in enemies)
    
    def __repr__(self):
        return f"{self.__class__.__name__}(row={self.row}, col={self.col})"

# ------------------------------
# UNIDADES CRUZADAS (Ricardo Corazón de León)
# ------------------------------

class Ricardo(Unit):
    """Líder de los cruzados."""
    def __init__(self):
        super().__init__("ricardo","CRUZADOS")
        self.power = 2
        self.speed = 2
        self.bonus = 2

class Templario(Unit):
    """Caballeros Templarios (élite)."""
    def __init__(self):
        super().__init__("templario","CRUZADOS")
        self.power = 4
        self.speed = 2
        
class Hospitalario(Unit):
    """Caballeros Hospitalarios (élite)."""
    def __init__(self):
        super().__init__("hospitalario","CRUZADOS")
        self.power = 4
        self.speed = 2
        
class Caballero(Unit):
    """Caballeros estándar."""
    def __init__(self):
        super().__init__("caballero","CRUZADOS")
        self.power = 3
        self.speed = 2

class Infanteria(Unit):
    """Soldados de infantería básicos."""
    def __init__(self):
        super().__init__("infanteria","CRUZADOS")
        self.power = 2
        self.speed = 1
        self.slow = 1
        
class Bagaje(Unit):
    """Carros de suministros (no combaten)."""
    def __init__(self):
        super().__init__("bagaje","CRUZADOS")
        self.power = 1
        self.speed = 1
        self.slow = 1

# ------------------------------
# UNIDADES SARRACENAS (Saladino)
# ------------------------------

class Saladino(Unit):
    """Líder de los sarracenos."""
    def __init__(self):
        super().__init__("saladino","SARRACENOS")
        self.power = 2
        self.speed = 3
        self.bonus = 2
        
class Mameluco(Unit):
    """Caballería pesada sarracena."""
    def __init__(self):
        super().__init__("mameluco","SARRACENOS")
        self.power = 3
        self.speed = 3
        
class Arquero(Unit):
    """Arqueros a caballo."""
    def __init__(self):
        super().__init__("arquero","SARRACENOS")
        self.power = 2
        self.speed = 3
        
class Explorador(Unit):
    """Unidades rápidas de reconocimiento."""
    def __init__(self):
        super().__init__("explorador","SARRACENOS")
        self.power = 1
        self.speed = 3