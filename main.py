# main.py
#from config import CURRENT_LANGUAGE
from game import Game

def main():
    """Función principal que inicia el juego.

    El flujo de inicialización es el siguiente:
    1. Cargar constantes de config.py según el locale por defecto
    2. Generar y cargar la pantalla de introducción
    3. Generar y cargar el menú de configuración
       - Si se cambia el idioma, solo se recarga el menú de configuración
    4. Generar y cargar el menú de selección de bando
    5. Generar hexgrid y gameui
    6. Generar las unidades
    """
    # Crear el juego (solo inicializa lo mínimo necesario para la intro)
    game = Game()

    # Establecer el idioma según la configuración
    #game._change_language(CURRENT_LANGUAGE)

    # Iniciar el bucle principal del juego
    # Los componentes se cargarán bajo demanda según se necesiten
    game.run()

if __name__ == "__main__":
    main()
