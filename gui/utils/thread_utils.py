# thread_utils.py
"""
Utilidades de threading para operaciones asíncronas en GUI.
Proporciona decoradores y funciones helper para manejo seguro de hilos.
"""

import threading
import functools
import time
from typing import Callable, Any, Optional


class ThreadSafeOperation:
    """Clase para ejecutar operaciones de manera thread-safe con timeout."""

    def __init__(self, operation: Callable, timeout: int = 30):
        """
        Inicializa la operación thread-safe.

        Args:
            operation: Función a ejecutar
            timeout: Timeout en segundos
        """
        self.operation = operation
        self.timeout = timeout
        self.result = None
        self.exception = None
        self.completed = False

    def execute(self, *args, **kwargs):
        """Ejecuta la operación en un hilo separado."""

        def worker():
            try:
                self.result = self.operation(*args, **kwargs)
                self.completed = True
            except Exception as e:
                self.exception = e
                self.completed = True

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        thread.join(timeout=self.timeout)

        if not self.completed:
            raise TimeoutError(f"Operación excedió timeout de {self.timeout} segundos")

        if self.exception:
            raise self.exception

        return self.result


def async_operation(timeout: int = 30):
    """
    Decorador para convertir una función en operación asíncrona.

    Args:
        timeout: Timeout en segundos
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            operation = ThreadSafeOperation(func, timeout)
            return operation.execute(*args, **kwargs)

        return wrapper

    return decorator


def run_in_background(func: Callable, callback: Optional[Callable] = None,
                      error_callback: Optional[Callable] = None, daemon: bool = True):
    """
    Ejecuta una función en background con callbacks opcionales.

    Args:
        func: Función a ejecutar
        callback: Función a llamar con el resultado
        error_callback: Función a llamar en caso de error
        daemon: Si el hilo debe ser daemon
    """

    def worker():
        try:
            result = func()
            if callback:
                callback(result)
        except Exception as e:
            if error_callback:
                error_callback(e)

    thread = threading.Thread(target=worker, daemon=daemon)
    thread.start()
    return thread


class ThreadPool:
    """Pool simple de hilos para ejecutar múltiples operaciones."""

    def __init__(self, max_workers: int = 5):
        """
        Inicializa el pool de hilos.

        Args:
            max_workers: Número máximo de hilos concurrentes
        """
        self.max_workers = max_workers
        self.active_threads = []
        self.completed_threads = []

    def submit(self, func: Callable, *args, **kwargs):
        """Envía una tarea al pool."""
        # Limpiar hilos completados
        self._cleanup_completed()

        # Esperar si hay demasiados hilos activos
        while len(self.active_threads) >= self.max_workers:
            time.sleep(0.1)
            self._cleanup_completed()

        # Crear y iniciar nuevo hilo
        def worker():
            try:
                return func(*args, **kwargs)
            finally:
                # Mover a completados
                if threading.current_thread() in self.active_threads:
                    self.active_threads.remove(threading.current_thread())
                    self.completed_threads.append(threading.current_thread())

        thread = threading.Thread(target=worker, daemon=True)
        self.active_threads.append(thread)
        thread.start()
        return thread

    def _cleanup_completed(self):
        """Limpia hilos que ya terminaron."""
        self.active_threads = [t for t in self.active_threads if t.is_alive()]

    def wait_all(self, timeout: Optional[int] = None):
        """Espera a que todos los hilos terminen."""
        for thread in self.active_threads:
            thread.join(timeout=timeout)

    def active_count(self):
        """Retorna el número de hilos activos."""
        self._cleanup_completed()
        return len(self.active_threads)


def debounce(wait_time: float):
    """
    Decorador que previene ejecuciones múltiples rápidas de una función.

    Args:
        wait_time: Tiempo de espera en segundos
    """

    def decorator(func):
        last_called = [0]

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            if current_time - last_called[0] >= wait_time:
                last_called[0] = current_time
                return func(*args, **kwargs)

        return wrapper

    return decorator


def throttle(rate_limit: float):
    """
    Decorador que limita la tasa de ejecución de una función.

    Args:
        rate_limit: Máximo número de ejecuciones por segundo
    """

    def decorator(func):
        min_interval = 1.0 / rate_limit
        last_called = [0]

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            elapsed = current_time - last_called[0]

            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)

            last_called[0] = time.time()
            return func(*args, **kwargs)

        return wrapper

    return decorator


class SafeTimer:
    """Timer thread-safe que puede ser cancelado."""

    def __init__(self, interval: float, function: Callable, args=None, kwargs=None):
        """
        Inicializa el timer.

        Args:
            interval: Intervalo en segundos
            function: Función a ejecutar
            args: Argumentos posicionales
            kwargs: Argumentos de palabra clave
        """
        self.interval = interval
        self.function = function
        self.args = args or []
        self.kwargs = kwargs or {}
        self.timer = None
        self.is_running = False

    def start(self):
        """Inicia el timer."""
        if not self.is_running:
            self.is_running = True
            self.timer = threading.Timer(self.interval, self._run)
            self.timer.daemon = True
            self.timer.start()

    def cancel(self):
        """Cancela el timer."""
        if self.timer:
            self.timer.cancel()
            self.is_running = False

    def _run(self):
        """Ejecuta la función."""
        try:
            self.function(*self.args, **self.kwargs)
        finally:
            self.is_running = False


def ensure_main_thread(func):
    """
    Decorador que asegura que una función se ejecute en el hilo principal.
    Útil para operaciones de GUI.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if threading.current_thread() == threading.main_thread():
            return func(*args, **kwargs)
        else:
            # Si hay un widget tkinter disponible, usar after()
            # Este es un caso específico para Tkinter
            result = [None]
            exception = [None]

            def main_thread_worker():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e

            # Intentar encontrar un widget tkinter en los argumentos
            widget = None
            for arg in args:
                if hasattr(arg, 'after'):  # Es probablemente un widget tkinter
                    widget = arg
                    break

            if widget:
                widget.after(0, main_thread_worker)
                # Esperar hasta que se complete (no ideal, pero funcional)
                while result[0] is None and exception[0] is None:
                    time.sleep(0.01)

                if exception[0]:
                    raise exception[0]
                return result[0]
            else:
                # Si no hay widget disponible, ejecutar directamente
                # (no es thread-safe pero es mejor que fallar)
                return func(*args, **kwargs)

    return wrapper