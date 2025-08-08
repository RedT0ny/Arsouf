# config.py (versión optimizada)
import os
import gettext
import locale
import ctypes

# Configuración de internacionalización
LOCALE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'locale')
TRANSLATION_DOMAIN = 'messages'
AVAILABLE_LANGUAGES = [
    d for d in os.listdir(LOCALE_DIR)
    if os.path.isdir(os.path.join(LOCALE_DIR, d))
]

# Intentar obtener el idioma del sistema
try:
    current_locale, encoding = locale.getlocale()
    if current_locale is None:
        language = 'es'  # Idioma por defecto: español
    else:
        language = current_locale.split('_')[0]
        # Asegurarse de que el idioma sea uno de los disponibles
        if language not in ['es', 'en']:
            language = 'es'  # Si no es un idioma soportado, usar español
except (ValueError, AttributeError):
    language = 'es'  # Idioma por defecto si hay algún error

# Configurar gettext
try:
    translation = gettext.translation(
        TRANSLATION_DOMAIN,
        localedir=LOCALE_DIR,
        languages=[language],
        fallback=True
    )
    _ = translation.gettext
    # Instalar la traducción globalmente
    translation.install()
except Exception as e:
    _ = gettext.gettext  # Fallback a gettext básico
    print(_("Error al cargar traducciones:"), e)

# Variable global para el idioma actual
CURRENT_LANGUAGE = language

# Centralizar cadenas traducibles
SIDE_CRUSADERS = _("CRUZADOS")
SIDE_SARACENS = _("SARRACENOS")
RICHARD_NAME = _("Ricardo")
INFANTRY_NAME = _("Infanteria")
KNIGHT_NAME = _("Caballero")
TEMPLAR_NAME = _("Templario")
HOSPITALLER_NAME = _("Hospitalario")
SALADIN_NAME = _("Saladino")
MAMLUK_NAME = _("Mameluco")
ARCHER_NAME = _("Arquero")
EXPLORER_NAME = _("Explorador")
BAGGAGE_NAME = _("Bagaje")

# ------------------------------
# CONFIGURACIÓN DEL JUEGO
# ------------------------------
# 0. Configuración general
GAME_NAME = _("game_name")
VERSION = "Beta 2.1.1"
AUTHOR = "Red Tony"
# 0.1. Configuración de depuración
DEBUG_MODE = False  # Cambia a False para producción

# ------------------------------
# 1. Dimensiones del tablero
# ------------------------------

# 1. Dimensiones ORIGINALES del tablero (en píxeles)
# (Estas son las dimensiones físicas del tablero en tu imagen JPG)
MAP_WIDTH = 2340
MAP_HEIGHT = 1470

# 1.1. Obtener resolución de pantalla (para calcular escalado)
def get_screen_resolution():
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

screen_w, screen_h = get_screen_resolution()

# Calcula el factor de escala máximo para que la ventana sea visible
max_scaling_w = (screen_w - 300) / MAP_WIDTH
max_scaling_h = (screen_h - 170 - 30) / MAP_HEIGHT  # Reserva espacio para el caption
DISPLAY_SCALING = min(max_scaling_w, max_scaling_h, 1.0)  # No escalar por encima del 100%

# 2. Márgenes REALES (de tu imagen JPG)
MAP_MARGINS = {
    "superior": 90,  #118,
    "inferior": 0,  #60,
    "izquierdo": 0, #45,
    "derecho": 0    #40
}

# 3. Área hexagonal REAL (píxeles en tu imagen)
HEX_AREA_REAL_WIDTH = MAP_WIDTH - MAP_MARGINS["izquierdo"] - MAP_MARGINS["derecho"]
HEX_AREA_REAL_HEIGHT = MAP_HEIGHT - MAP_MARGINS["superior"] - MAP_MARGINS["inferior"]

# 4. Configuración de pantalla
SCREEN_WIDTH = MAP_WIDTH * DISPLAY_SCALING + 300
SCREEN_HEIGHT = MAP_HEIGHT * DISPLAY_SCALING + 170
FPS = 60
COLOR_BG = (0, 0, 0)

# 5. TAMAÑOS UI
PANEL_WIDTH = 300
MENU_BUTTON_WIDTH = 300
MENU_BUTTON_HEIGHT = 50
PANEL_BUTTON_WIDTH = 260
PANEL_BUTTON_HEIGHT = 50
TITLE_Y = 200
OPTIONS_Y = 300
OPTIONS_SPACING = 100

# 5.1 PANEL LOG
LOG_PANEL_HEIGHT = 170
LOG_PANEL_WIDTH = SCREEN_WIDTH - PANEL_WIDTH
LOG_PANEL_COLOR = (30, 30, 40)
LOG_TEXT_COLOR = (200, 200, 200)
LOG_FONT_SIZE = 18
LOG_MARGIN = 10
LOG_LINE_HEIGHT = 22 #LOG_FONT_SIZE + 2
LOG_MAX_MESSAGES = 500  # Máximo de mensajes almacenados

# 5.2 Barras de desplazamiento
SCROLLBAR_WIDTH = 14
SCROLLBAR_COLOR = (60, 60, 80)
SCROLLBAR_HANDLE_COLOR = (130, 130, 160)

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
SCALING_MULTIPLIER = 1

# 7. Dimensiones originales del hexágono (según especificación)
HEX_REAL_HEIGHT = 120  # Altura original del hexágono en píxeles
HEX_REAL_WIDTH = 104   # Ancho original del hexágono en píxeles

# 8. Dimensiones escaladas del hexágono (para pantalla)
HEX_HEIGHT = int(HEX_REAL_HEIGHT * SCALING_MULTIPLIER)
HEX_WIDTH = int(HEX_REAL_WIDTH * SCALING_MULTIPLIER)
# Para compatibilidad con código existente (usar HEX_WIDTH y HEX_HEIGHT en nuevo código)
HEX_SIZE = HEX_WIDTH  # Mantenemos HEX_SIZE para compatibilidad
# Para mejor ajuste visual, usar el tamaño más pequeño entre ancho y alto
HEX_MIN_SIZE = min(HEX_WIDTH, HEX_HEIGHT)

# 9. Márgenes escalados (calculados una vez)
SCALED_MARGINS = {
    "superior": int(MAP_MARGINS["superior"] * SCALING_MULTIPLIER),
    "izquierdo": int(MAP_MARGINS["izquierdo"] * SCALING_MULTIPLIER)
}

# ------------------------------
# RUTAS DE ASSETS
# ------------------------------
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# Imágenes (SVG/PNG)
IMAGE_PATHS = {
    "board": os.path.join(ASSETS_DIR, "img", "Board.png"),
    "cover": os.path.join(ASSETS_DIR, "img", "Cover.png"),
    # Docs
    "reglas": os.path.join(ASSETS_DIR, "doc", "Manual_ES.pdf"),
    "rules": os.path.join(ASSETS_DIR, "doc", "Manual_EN.pdf"),
    # Cruzados
    "Ricardo": os.path.join(ASSETS_DIR, "img", "Ricardo.svg"),
    "Templario": os.path.join(ASSETS_DIR, "img", "Templario.svg"),
    "Hospitalario": os.path.join(ASSETS_DIR, "img", "Hospitalario.svg"),
    "Caballero": os.path.join(ASSETS_DIR, "img", "Caballero.svg"),
    "Infanteria": os.path.join(ASSETS_DIR, "img", "Infanteria.svg"),
    "Bagaje": os.path.join(ASSETS_DIR, "img", "Bagaje.svg"),
    # Sarracenos
    "Saladino": os.path.join(ASSETS_DIR, "img", "Saladino.svg"),
    "Mameluco": os.path.join(ASSETS_DIR, "img", "Mameluco.svg"),
    "Arquero": os.path.join(ASSETS_DIR, "img", "Arquero.svg"),
    "Explorador": os.path.join(ASSETS_DIR, "img", "Explorador.svg"),
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
    'SETUP_MENU': 'SETUP_MENU',
    'SELECT_SIDE': 'SELECT_SIDE',
    'DEPLOY_PLAYER': 'DEPLOY_PLAYER',
    'DEPLOY_AI': 'DEPLOY_AI',
    'PLAYER_TURN': 'PLAYER_TURN',
    'AI_TURN': 'AI_TURN'
}

TURN_PHASES = {
    'MOVEMENT': _('Movimiento'),
    'COMBAT': _('Combate')
}

MAX_TURNS = 35  # Número máximo de turnos por partida

# ------------------------------
# VALIDACIÓN DE CONFIG
# ------------------------------
if __name__ == "__main__":
    print(_("Configuración cargada correctamente:"))
    print(_("- Tamaño de ventana: {width}x{height}").format(width=SCREEN_WIDTH, height=SCREEN_HEIGHT))
    print(_("- Tamaño del tablero: {width}x{height} (Utilizable: {area_width}x{area_height})").format(
        width=MAP_WIDTH, height=MAP_HEIGHT,
        area_width=HEX_AREA_REAL_WIDTH, area_height=HEX_AREA_REAL_HEIGHT))
    print(_("- Tamaño escalado: {width}x{height}").format(
        width=SCREEN_WIDTH - PANEL_WIDTH, height=SCREEN_HEIGHT - LOG_PANEL_HEIGHT))
    print(_("- Escala: {scale:.2f}").format(scale=SCALING_MULTIPLIER))
    print(_("- Hexágonos: {rows}x{cols} (size: {size}px)").format(rows=HEX_ROWS, cols=HEX_COLS, size=HEX_SIZE))
