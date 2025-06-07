"""
Module to hold translated constants that can be updated when the language changes.
"""
import gettext
import os

# Configuración de internacionalización
LOCALE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'locale')
TRANSLATION_DOMAIN = 'messages'

# Variable global para el idioma actual
CURRENT_LANGUAGE = 'es'  # Default language

# Initialize translation function
try:
    translation = gettext.translation(
        TRANSLATION_DOMAIN,
        localedir=LOCALE_DIR,
        languages=[CURRENT_LANGUAGE],
        fallback=True
    )
    _ = translation.gettext
    # Instalar la traducción globalmente
    translation.install()
except Exception as e:
    _ = gettext.gettext  # Fallback a gettext básico
    print(f"Error loading translations: {e}")

# Translated constants
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
GAME_NAME = _("game_name")
TURN_PHASES = {
    'MOVEMENT': _('Movimiento'),
    'COMBAT': _('Combate')
}

def update_constants(new_language):
    """Update all translated constants with the new language."""
    global CURRENT_LANGUAGE, _, SIDE_CRUSADERS, SIDE_SARACENS, RICHARD_NAME, INFANTRY_NAME
    global KNIGHT_NAME, TEMPLAR_NAME, HOSPITALLER_NAME, SALADIN_NAME, MAMLUK_NAME
    global ARCHER_NAME, EXPLORER_NAME, BAGGAGE_NAME, GAME_NAME, TURN_PHASES
    
    # Update current language
    CURRENT_LANGUAGE = new_language
    
    # Create new translation function
    try:
        translation = gettext.translation(
            TRANSLATION_DOMAIN,
            localedir=LOCALE_DIR,
            languages=[new_language],
            fallback=True
        )
        _ = translation.gettext
        translation.install()
    except Exception as e:
        print(f"Error updating translations: {e}")
        return False
    
    # Update all constants
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
    GAME_NAME = _("game_name")
    TURN_PHASES = {
        'MOVEMENT': _('Movimiento'),
        'COMBAT': _('Combate')
    }
    
    return True