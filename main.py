# main.py
"""
Punto de entrada principal del bot.
Inicializa la aplicación con interfaz gráfica modular.
"""

import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gui.main_window import MainWindow


def main():
    """Función principal que inicializa y ejecuta la aplicación."""
    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"Error al inicializar la aplicación: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()