# main.py
from config import CURRENT_LANGUAGE
from game import Game

def main():
    """Función principal que inicia el juego."""
    game = Game()
    game._change_language(CURRENT_LANGUAGE)
    game.run()

if __name__ == "__main__":
    main()
