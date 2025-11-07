"""
Main entry point for the Blackjack 2025 application.
"""

import sys
from PySide6.QtWidgets import QApplication
from src.logic.game_engine import GameEngine
from src.ui.main_window import MainWindow


def main():
    """
    Initializes and runs the Qt application.
    """
    app = QApplication(sys.argv)

    # Load the stylesheet
    try:
        with open("src/ui/styles/dark_casino.qss", "r") as f:
            style = f.read()
            app.setStyleSheet(style)
    except FileNotFoundError:
        print("Stylesheet 'dark_casino.qss' not found. Running with default style.")

    # Create the engine and main window
    game_engine = GameEngine()
    window = MainWindow(game_engine)

    window.show()

    # Start the application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
