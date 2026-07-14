import os
import platform
import logging
import sys
import threading
import time

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

import config as cf
from logger_config import configurar_logs
from modulos.proceso_bcra.proceso_completo import ejecutar_etl_bcra

# Inicializamos logs
configurar_logs()
logs = logging.getLogger(__name__)

# Inicializamos consola
consola = Console()

def limpiar_pantalla():
    # Si el sistema operativo es Windows, usa 'cls', de lo contrario (Linux/macOS) usa 'clear'
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def mostrar_menu():
    # Inicializamos el panel de opciones de las distintas Actualizaciones.
    while True:
        limpiar_pantalla()
        consola.print(Panel("Gestor de Actualizaciones",title="ACTUALIZACIONES",border_style="bold blue",expand=False))
        consola.print("1.- BCRA",style="blue")
        consola.print("2.- Salir",style="blue")
        consola.print(Panel("      ¡Fin del menú!     ",border_style="bold blue",expand=False))

        opcion = Prompt.ask("Seleciones una opción:",choices=["1","2"])

        if opcion == "1":
            limpiar_pantalla()
            logs.info("Se inicia el proceso de Actualizacion-BCRA")
            
            # Creación del hilo: target es la función que va a correr de fondo
            hilo_bcra = threading.Thread(target=ejecutar_etl_bcra, name="Hilo-BCRA")
            
            # Arrancamos el hilo. El programa principal continúa inmediatamente abajo.
            hilo_bcra.start()
            
            consola.print("Cualquier detalle del avance o errores lo podés auditar en: [yellow]logs/automatizacion.log[/yellow]")
            consola.print("Podés continuar usando el menú de forma normal.")
            
            input("\nPresione Enter para volver al menú principal...")

        elif opcion == "2":
            limpiar_pantalla()
            logs.info("Cerrando el programa.")
            consola.print("\n[bold blue]¡Gracias por usar el Gestor de Actualizaciones![/bold blue] [bold red]Saliendo del sistema...[/bold red]")
            break

if __name__ == "__main__":
    try:
        logs.info("Inicializa el programa.")
        mostrar_menu()
    except KeyboardInterrupt:
        if en_zona_critica:
            logs.critical("INTERRUPCIÓN CRÍTICA: Se cortó el proceso MIENTRAS se escribía en la base de datos. Posible inconsistencia de datos.")
            sys.exit(1)
        else:
            logs.warning("El proceso se canceló antes de empezar a escribir los datos seguros.")
            sys.exit(0)

# EJEMPLO DE COMO USAR en_zona_critica PARA CERRAR DE FORMA PROLIJA EL PROGRAMA E INFORMAR DEL CIERRO ABRUPTO
def actualizar_sql():
    global en_zona_critica
    en_zona_critica = True
    
    logs.info("Abriendo transacción en SQL Server...")
    # ... tu lógica acá ...
    
    en_zona_critica = False