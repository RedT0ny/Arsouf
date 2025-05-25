# units.py
# import pygame
# from config import *

class Unit:
    """Clase base para todas las unidades del juego."""
    def __init__(self, image_key):
        self.image_key = image_key  # Clave para acceder a la imagen en IMAGE_PATHS
        self.row = None
        self.col = None
        self.health = 2
    
    def set_position(self, row, col):
        """Establece la posición en el grid."""
        self.row = row
        self.col = col
    
    def atacar(self, tgt_row, tgt_col):
        print(f"Atacar unidad en {tgt_row},{tgt_col}?")
        
    def herida(self):
        self.health -= 1

    def __repr__(self):
        return f"{self.__class__.__name__}(row={self.row}, col={self.col})"

# ------------------------------
# UNIDADES CRUZADAS (Ricardo Corazón de León)
# ------------------------------

class Ricardo(Unit):
    """Líder de los cruzados."""
    def __init__(self):
        super().__init__("ricardo")
        self.power = 2
        self.speed = 2
        self.bonus = 2

class Templario(Unit):
    """Caballeros Templarios (élite)."""
    def __init__(self):
        super().__init__("templario")
        self.power = 4
        self.speed = 2
        
class Hospitalario(Unit):
    """Caballeros Hospitalarios (élite)."""
    def __init__(self):
        super().__init__("hospitalario")
        self.power = 4
        self.speed = 2
        
class Caballero(Unit):
    """Caballeros estándar."""
    def __init__(self):
        super().__init__("caballero")
        self.power = 3
        self.speed = 2

class Infanteria(Unit):
    """Soldados de infantería básicos."""
    def __init__(self):
        super().__init__("infanteria")
        self.power = 2
        self.speed = 1
        self.slow = 1
        
class Bagaje(Unit):
    """Carros de suministros (no combaten)."""
    def __init__(self):
        super().__init__("bagaje")
        self.power = 1
        self.speed = 1
        self.slow = 1

# ------------------------------
# UNIDADES SARRACENAS (Saladino)
# ------------------------------

class Saladino(Unit):
    """Líder de los sarracenos."""
    def __init__(self):
        super().__init__("saladino")
        self.power = 2
        self.speed = 3
        self.bonus = 2
        
class Mameluco(Unit):
    """Caballería pesada sarracena."""
    def __init__(self):
        super().__init__("mameluco")
        self.power = 3
        self.speed = 3
        
class Arquero(Unit):
    """Arqueros a caballo."""
    def __init__(self):
        super().__init__("arquero")
        self.power = 2
        self.speed = 3
        
class Explorador(Unit):
    """Unidades rápidas de reconocimiento."""
    def __init__(self):
        super().__init__("explorador")
        self.power = 1
        self.speed = 3