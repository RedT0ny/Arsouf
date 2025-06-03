# config.py (versión optimizada)
import json
import os

# ------------------------------
# CONFIGURACIÓN DEL JUEGO
# ------------------------------
# 0. Configuración general
GAME_NAME = "La Batalla de Arsouf"
VERSION = "Alfa 1.2.0"
AUTHOR = "Red Tony"
# 0.1. Configuración de depuración
DEBUG_MODE = False  # Cambia a False para producción

# ------------------------------
# 1. Dimensiones del tablero
# ------------------------------

# 1. Dimensiones ORIGINALES del tablero (en píxeles)
# (Estas son las dimensiones físicas del tablero en tu imagen JPG)
TABLERO_REAL_WIDTH = 2340
TABLERO_REAL_HEIGHT = 1470

# 2. Márgenes REALES (de tu imagen JPG)
MARGENES = {
    "superior": 90,  #118,
    "inferior": 0,  #60,
    "izquierdo": 0, #45,
    "derecho": 0    #40
}

# 3. Área hexagonal REAL (píxeles en tu imagen)
HEX_AREA_REAL_WIDTH = TABLERO_REAL_WIDTH - MARGENES["izquierdo"] - MARGENES["derecho"]
HEX_AREA_REAL_HEIGHT = TABLERO_REAL_HEIGHT - MARGENES["superior"] - MARGENES["inferior"]

# 4. Configuración de pantalla
DISPLAY_SCALING = 0.75
SCREEN_WIDTH = TABLERO_REAL_WIDTH * DISPLAY_SCALING + 300
SCREEN_HEIGHT = TABLERO_REAL_HEIGHT * DISPLAY_SCALING + 170
FPS = 60
COLOR_BG = (0, 0, 0)

# 5. TAMAÑOS UI
PANEL_WIDTH = 300
BOTON_WIDTH = 260
BOTON_HEIGHT = 50
TITULO_Y = 200
OPCIONES_Y = 300
OPCIONES_ESPACIADO = 100

# 5.1 PANEL LOG
LOG_PANEL_HEIGHT = 170
LOG_PANEL_WIDTH = SCREEN_WIDTH - PANEL_WIDTH
LOG_PANEL_COLOR = (30, 30, 40)
LOG_TEXT_COLOR = (200, 200, 200)
LOG_FONT_SIZE = 18
LOG_MARGIN = 10
LOG_LINE_HEIGHT = 22 #LOG_FONT_SIZE + 2
LOG_SCROLLBAR_WIDTH = 14
LOG_SCROLLBAR_COLOR = (60, 60, 80)
LOG_SCROLLBAR_HANDLE_COLOR = (130, 130, 160)
LOG_MAX_MESSAGES = 500  # Máximo de mensajes almacenados

# 5. Grid hexagonal
HEX_ROWS = 15
HEX_COLS = 22

# Zonas especiales del tablero
ROAD_HEXES = {
    (1,0), (1,1), (2,0), (2,1),
    (3,2), (3,3), (3,4), *{(3,c) for c in range(11, 22)},
    *{(4,c) for c in range(4, 11)}
}

FORBIDDEN_HEXES = {
    (0,0), (0,1),  # Mar Mediterráneo
    *{(4,c) for c in range(16, 20)},  # Pantano
    *{(5,c) for c in range(16, 19)},
    *{(6,c) for c in range(15, 18)},
    *{(7,c) for c in range(16, 19)},
    (5,20), (8,17)  # de Birket-Ramadan
}

# Barreras de río (pares de hexágonos entre los que no se puede mover directamente)
RIVER_BARRIERS = {
    frozenset({(0,17), (0,18)}),  # frozenset permite usarlo como clave en conjuntos
    frozenset({(0,17), (1,18)}),
    frozenset({(1,17), (1,18)})
}

# Vado (punto de cruce permitido)
FORD_HEX = (2,17)  # Hexágono donde se puede cruzar el río

# 6. Cálculo de ESCALA (centralizado aquí)
# Calculamos el factor de escala basado en el espacio disponible
AVAILABLE_WIDTH = SCREEN_WIDTH - PANEL_WIDTH
AVAILABLE_HEIGHT = SCREEN_HEIGHT - LOG_PANEL_HEIGHT
ESCALA = min(AVAILABLE_WIDTH / TABLERO_REAL_WIDTH, AVAILABLE_HEIGHT / TABLERO_REAL_HEIGHT)

# 7. Dimensiones originales del hexágono (según especificación)
HEX_REAL_HEIGHT = 120  # Altura original del hexágono en píxeles
HEX_REAL_WIDTH = 104   # Ancho original del hexágono en píxeles

# 8. Dimensiones escaladas del hexágono (para pantalla)
HEX_HEIGHT = int(HEX_REAL_HEIGHT * ESCALA)
HEX_WIDTH = int(HEX_REAL_WIDTH * ESCALA)
# Para compatibilidad con código existente (usar HEX_WIDTH y HEX_HEIGHT en nuevo código)
HEX_SIZE = HEX_WIDTH  # Mantenemos HEX_SIZE para compatibilidad
# Para mejor ajuste visual, usar el tamaño más pequeño entre ancho y alto
HEX_MIN_SIZE = min(HEX_WIDTH, HEX_HEIGHT)

# 9. Márgenes escalados (calculados una vez)
MARGENES_ESCALADOS = {
    "superior": int(MARGENES["superior"] * ESCALA),
    "izquierdo": int(MARGENES["izquierdo"] * ESCALA)
}

# ------------------------------
# RUTAS DE ASSETS
# ------------------------------
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# Imágenes (SVG/PNG)
IMAGE_PATHS = {
    "board": os.path.join(ASSETS_DIR, "img", "Board.png"),
    "cover": os.path.join(ASSETS_DIR, "img", "Cover.png"),
    "rules": os.path.join(ASSETS_DIR, "img", "Reglas.jpg"),
    # Cruzados
    "ricardo": os.path.join(ASSETS_DIR, "img", "Ricardo.svg"),
    "templario": os.path.join(ASSETS_DIR, "img", "Templario.svg"),
    "hospitalario": os.path.join(ASSETS_DIR, "img", "Hospitalario.svg"),
    "caballero": os.path.join(ASSETS_DIR, "img", "Caballero.svg"),
    "infanteria": os.path.join(ASSETS_DIR, "img", "Infanteria.svg"),
    "bagaje": os.path.join(ASSETS_DIR, "img", "Bagaje.svg"),
    # Sarracenos
    "saladino": os.path.join(ASSETS_DIR, "img", "Saladino.svg"),
    "mameluco": os.path.join(ASSETS_DIR, "img", "Mameluco.svg"),
    "arquero": os.path.join(ASSETS_DIR, "img", "Arquero.svg"),
    "explorador": os.path.join(ASSETS_DIR, "img", "Explorador.svg"),
}

# Archivos de audio
AUDIO_PATHS = {
    # Música
    "arabesque": os.path.join(ASSETS_DIR, "audio", "Arabesque.mp3"),
    "victory": os.path.join(ASSETS_DIR, "audio", "Victory.mp3"),
    "defeat": os.path.join(ASSETS_DIR, "audio", "Defeat.mp3"),
    # Efectos de sonido
    "select": os.path.join(ASSETS_DIR, "audio", "select.ogg"),
    "move": os.path.join(ASSETS_DIR, "audio", "move.ogg"),
    "cancel_move": os.path.join(ASSETS_DIR, "audio", "cancel_move.ogg"),
    "success_attack": os.path.join(ASSETS_DIR, "audio", "success_attack.ogg"),
    "failed_attack": os.path.join(ASSETS_DIR, "audio", "failed_attack.ogg"),
}

# Fuentes
FONT_PATHS = {
    "abbasy": os.path.join(ASSETS_DIR, "fonts", "Abbasy.ttf"),
}

# ------------------------------
# CONSTANTES DE JUEGO
# ------------------------------
# Colores para debug
COLOR_HEX_GRID = (100, 200, 100, 50)  # Verde translúcido (para debug)
COLOR_UNIT_DEBUG = (255, 0, 0)  # Rojo para placeholders

# COLORES UI
COLOR_CRUZADOS = (100, 100, 200)
COLOR_SARRACENOS = (200, 100, 100)
COLOR_BOTON = (50, 200, 50)
COLOR_BOTON_CANCELAR = (200, 50, 50)
COLOR_TEXTO = (255, 255, 255)
COLOR_ZONA_JUGADOR = (100, 200, 100, 70)
COLOR_ZONA_IA = (200, 100, 100, 70)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ------------------------------
# COMBATE
# ------------------------------
# Colores
COMBAT_COLORS = {
    'attack': (255, 50, 50),
    'defense': (50, 50, 255),
    'wounded': (255, 0, 0)
}

GAME_STATES = {
    'INTRO': 'INTRO',
    'SELECT_SIDE': 'SELECT_SIDE',
    'DEPLOY_PLAYER': 'DEPLOY_PLAYER',
    'DEPLOY_AI': 'DEPLOY_AI',
    'PLAYER_TURN': 'PLAYER_TURN',
    'AI_TURN': 'AI_TURN'
}

TURN_PHASES = {
    'MOVEMENT': 'Movimiento',
    'COMBAT': 'Combate'
}

# ------------------------------
# VALIDACIÓN DE CONFIG
# ------------------------------
if __name__ == "__main__":
    print("Configuración cargada correctamente:")
    print(f"- Tamaño de ventana: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print(f"- Tamaño del tablero: {TABLERO_REAL_WIDTH}x{TABLERO_REAL_HEIGHT} (Utilizable: {HEX_AREA_REAL_WIDTH}x{HEX_AREA_REAL_HEIGHT} px)")
    print(f"- Tamaño escalado: {SCREEN_WIDTH - PANEL_WIDTH}x{SCREEN_HEIGHT - LOG_PANEL_HEIGHT}")
    print(f"- Escala: {ESCALA:.2f}")
    print(f"- Hexágonos: {HEX_ROWS}x{HEX_COLS} (size: {HEX_SIZE}px)")
