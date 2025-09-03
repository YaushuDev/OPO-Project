# gui/main_window.py
"""
Ventana principal del bot que configura el layout con 3 paneles.
Panel superior grande y dos paneles inferiores para gestión completa.
"""

import tkinter as tk
from tkinter import ttk
from gui.components.top_panel import TopPanel
from gui.components.bottom_left_panel import BottomLeftPanel
from gui.components.bottom_right_panel import BottomRightPanel


class MainWindow:
    """Clase principal que maneja la ventana y el layout del bot."""

    def __init__(self):
        """Inicializa la ventana principal y configura el layout."""
        self.root = tk.Tk()
        self._setup_window()
        self._create_layout()
        self._load_components()

    def _setup_window(self):
        """Configura las propiedades básicas de la ventana."""
        self.root.title("Bot de Búsqueda de Correos - v2.0")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')

    def _create_layout(self):
        """Crea la estructura de layout con frames para cada sección."""
        # Frame principal
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Configurar redimensionamiento
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=2)  # Panel superior más grande
        self.main_frame.rowconfigure(1, weight=1)  # Panel inferior más pequeño

        # Frame superior (ocupa todo el ancho)
        self.top_frame = ttk.LabelFrame(
            self.main_frame,
            text="Perfiles de Búsqueda",
            padding="10"
        )
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 5))

        # Frame inferior izquierdo
        self.bottom_left_frame = ttk.LabelFrame(
            self.main_frame,
            text="Configuración",
            padding="10"
        )
        self.bottom_left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))

        # Frame inferior derecho
        self.bottom_right_frame = ttk.LabelFrame(
            self.main_frame,
            text="Estado",
            padding="10"
        )
        self.bottom_right_frame.grid(row=1, column=1, sticky="nsew")

        # Configurar pesos para los frames inferiores
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)

    def _load_components(self):
        """Carga los componentes en cada panel."""
        # Primero inicializar el panel de logs para poder pasarlo como referencia
        self.bottom_right_panel = BottomRightPanel(self.bottom_right_frame)

        # Luego inicializar el panel izquierdo con referencia al panel de logs
        self.bottom_left_panel = BottomLeftPanel(self.bottom_left_frame, self.bottom_right_panel)

        # Finalmente, inicializar el panel superior con la referencia al panel de logs
        self.top_panel = TopPanel(self.top_frame, self.bottom_right_panel)

        # Registrar la inicialización en el log
        self.bottom_right_panel.add_log_entry("Aplicación iniciada correctamente")
        self.bottom_right_panel.add_log_entry("Sistema de perfiles y reportes cargado")
        self.bottom_right_panel.add_log_entry("Funcionalidades disponibles:")
        self.bottom_right_panel.add_log_entry("  • Gestión de perfiles de búsqueda")
        self.bottom_right_panel.add_log_entry("  • Configuración SMTP")
        self.bottom_right_panel.add_log_entry("  • Configuración de destinatarios")
        self.bottom_right_panel.add_log_entry("  • Generación de reportes Excel")
        self.bottom_right_panel.add_log_entry("  • Envío automático por correo")

    def run(self):
        """Inicia el loop principal de la aplicación."""
        self.root.mainloop()

    def get_component(self, component_name):
        """
        Retorna una referencia al componente solicitado.

        Args:
            component_name (str): 'top', 'bottom_left', 'bottom_right'

        Returns:
            Component: Instancia del componente o None si no existe
        """
        components = {
            'top': getattr(self, 'top_panel', None),
            'bottom_left': getattr(self, 'bottom_left_panel', None),
            'bottom_right': getattr(self, 'bottom_right_panel', None)
        }
        return components.get(component_name, None)