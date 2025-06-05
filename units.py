# units.py

import random
import gettext
_ = gettext.gettext  # type: callable

from typing import TYPE_CHECKING
from config import *

if TYPE_CHECKING:
    from hexgrid import HexGrid  # Solo para type checking, no causa importación real

class Unit:
    """Clase base para todas las unidades del juego."""
    def __init__(self, image_key, side):
        self.image_key = image_key
        self.side = side  # _("CRUZADOS") o _("SARRACENOS")
        self.power = 0
        self.row = None
        self.col = None
        self.health = 2  # 2 = sana, 1 = herida, 0 = muerta
        self.speed = 0  # Velocidad actual (se establecerá en cada subclase)
        self.original_speed = 0  # Se establecerá en cada subclase
        self.wounded_mark = False  # Para mostrar cruz roja
        self.leader = False  # Indica si la unidad es un líder (Ricardo o Saladino)
        self.charging_hex = None  # Para almacenar el hexágono objetivo de una carga

    def set_position(self, row, col):
        """Establece la posición en el grid."""
        self.row = row
        self.col = col

    def attack(self, objetivo, grid):
        """Devuelve True si el ataque fue exitoso"""
        if self.health != 2:  # Solo unidades sanas pueden atacar
            return False

        attack_power = self.power + random.randint(1, 6)

        # Bonus por líder adyacente
        if self._is_leader_adjacent(grid):
            attack_power += 2

        # Bonus por carga de caballería cruzada
        is_charging = self.charge(objetivo, grid)
        if is_charging:
            attack_power += 1

        # Cálculo del poder defensivo, incluyendo bonus
        defensa_power = objetivo.power + random.randint(1, 6) + self._get_allied_bonus(objetivo, grid)

        if attack_power > defensa_power:
            objetivo.get_wound(grid)
            return True
        elif attack_power < defensa_power:
            self.get_wound(grid)
        return False

    def charge(self, objetivo, grid):
        """
        Determina si la unidad está realizando una carga contra el objetivo.
        Una carga ocurre cuando un caballero cruzado se mueve dos casillas consecutivas
        en la misma dirección y luego ataca a una unidad sarracena en la siguiente casilla
        en esa misma dirección.

        Args:
            objetivo: La unidad objetivo del ataque
            grid: El grid hexagonal

        Returns:
            bool: True si la unidad está cargando, False en caso contrario
        """
        # Solo los caballeros cruzados pueden cargar
        if not (isinstance(self, Caballero) or isinstance(self, Templario) or isinstance(self, Hospitalario)):
            return False

        # Solo se puede cargar contra unidades sarracenas
        if objetivo.side != _("SARRACENOS"):
            return False

        # Verificar si tenemos un hexágono de carga definido
        if not self.charging_hex:
            return False

        # Verificar si el objetivo está en el hexágono de carga
        target_row, target_col = self.charging_hex
        if objetivo.row != target_row or objetivo.col != target_col:
            return False

        # Si llegamos aquí, se cumplen todas las condiciones para una carga
        return True

    def get_wound(self, grid):
        if self.health == 2:  # Primera herida
            self.health = 1
            self.speed = 1
            self.wounded_mark = True
        else:  # Segunda herida
            self.health = 0
            grid.eliminar_unidad(self.row, self.col)

    def recover(self, grid):
        """Intenta recuperar la unidad si no hay enemigos cerca"""
        if (self.health == 1 and 
            not self._are_enemies_close(grid, radius=3)):
            self.health = 2
            self.speed = self.original_speed
            self.wounded_mark = False
            return True
        return False

    def _is_leader_adjacent(self, grid):
        # Detectar líder aliado adyacente usando el atributo leader
        for r, c in grid.get_adjacent_positions(self.row, self.col):
            unit = grid.get_unit(r, c)
            if unit and unit.leader and unit.side == self.side:
                return True
        return False

    def _get_allied_bonus(self, unidad_defensora: 'Unit', grid: 'HexGrid') -> float:
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
            if unidad_adyacente and self.is_leader(unidad_adyacente) and unidad_adyacente.side == unidad_defensora.side:
                bono_total += 2
                break  # Solo se cuenta una vez aunque haya múltiples líderes (por seguridad)

        return bono_total

    def is_leader(self, unidad: 'Unit') -> bool:
        """Determina si una unidad es el líder de su facción"""
        return unidad.leader

    def _are_enemies_close(self, grid, radius=3):
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
        super().__init__("ricardo",_("CRUZADOS"))
        self.power = 2
        self.original_speed = 2
        self.speed = self.original_speed
        self.bonus = 2
        self.leader = True

class Templario(Unit):
    """Caballeros Templarios (élite)."""
    def __init__(self):
        super().__init__("templario",_("CRUZADOS"))
        self.power = 4
        self.original_speed = 2
        self.speed = self.original_speed

class Hospitalario(Unit):
    """Caballeros Hospitalarios (élite)."""
    def __init__(self):
        super().__init__("hospitalario",_("CRUZADOS"))
        self.power = 4
        self.original_speed = 2
        self.speed = self.original_speed

class Caballero(Unit):
    """Caballeros estándar."""
    def __init__(self):
        super().__init__("caballero",_("CRUZADOS"))
        self.power = 3
        self.original_speed = 2
        self.speed = self.original_speed

class Infanteria(Unit):
    """Soldados de infantería básicos."""
    def __init__(self):
        super().__init__("infanteria",_("CRUZADOS"))
        self.power = 2
        self.original_speed = 1
        self.speed = self.original_speed
        self.slow = 1

class Bagaje(Unit):
    """Carros de suministros (no combaten)."""
    def __init__(self):
        super().__init__("bagaje",_("CRUZADOS"))
        self.power = 1
        self.original_speed = 1
        self.speed = self.original_speed
        self.slow = 1

# ------------------------------
# UNIDADES SARRACENAS (Saladino)
# ------------------------------

class Saladino(Unit):
    """Líder de los sarracenos."""
    def __init__(self):
        super().__init__("saladino",_("SARRACENOS"))
        self.power = 2
        self.original_speed = 3
        self.speed = self.original_speed
        self.bonus = 2
        self.leader = True

class Mameluco(Unit):
    """Caballería pesada sarracena."""
    def __init__(self):
        super().__init__("mameluco",_("SARRACENOS"))
        self.power = 3
        self.original_speed = 3
        self.speed = self.original_speed

class Arquero(Unit):
    """Arqueros a caballo."""
    def __init__(self):
        super().__init__("arquero",_("SARRACENOS"))
        self.power = 2
        self.original_speed = 3
        self.speed = self.original_speed

class Explorador(Unit):
    """Unidades rápidas de reconocimiento."""
    def __init__(self):
        super().__init__("explorador",_("SARRACENOS"))
        self.power = 1
        self.original_speed = 3
        self.speed = self.original_speed
