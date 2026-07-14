import logging
from rich.console import Console

from modulos.proceso_bcra.tablas import verificar_y_crear_tablas
from modulos.proceso_bcra.sub_deudores import ejecutar_proceso_deudores
from modulos.proceso_bcra.sub_padron_arca import ejecutar_proceso_padron_arca
from modulos.proceso_bcra.sub_1dsf import ejecutar_proceso_1dsf
from modulos.proceso_bcra.sub_maestro_de_entidades import ejecutar_proceso_maestro_entidades
from modulos.proceso_bcra.sub_actividades_arca import ejecutar_proceso_actividades_arca

logs = logging.getLogger(__name__)
consola = Console()

def ejecutar_etl_bcra():
    try:
        # 1. Control estricto de la infraestructura / Base de Datos
        verificar_y_crear_tablas()
    except Exception as e:
        logs.error(f"[BCRA] Error crítico de conexión/creación de tablas: {e}")
        consola.print(f"\n[bold red][BCRA - ERROR][/bold red] No se pudo conectar o verificar la DB. Detalle: {e}")
        print()
        input("\nPresione Enter para volver al menú principal...")
        return
  
    try:
        # 2. Ejecución independiente del Pipeline de Deudores
        ejecutar_proceso_deudores()
    except ValueError as e:
        # Captura errores (como el nombre del archivo)
        logs.error(f"[BCRA] Error de validación en el proceso: {e}")
    except Exception as e:
        # Cualquier otro error inesperado (permisos, falta de espacio, etc.)
        logs.error(f"[BCRA] Error inesperado en el ciclo ETL: {e}")

    try:
        # 3. Ejecución independiente del Pipeline de Padrón ARCA
        ejecutar_proceso_padron_arca()
    except ValueError as e:
        # Captura errores (como el nombre del archivo)
        logs.error(f"[PADRON - ARCA] Error de validación en el proceso: {e}")
    except Exception as e:
        # Cualquier otro error inesperado (permisos, falta de espacio, etc.)
        logs.error(f"[PADRON - ARCA] Error inesperado en el ciclo ETL: {e}")   
    
    try:
        # 4. Ejecución independiente del Pipeline de 1DSF
        ejecutar_proceso_1dsf()
    except ValueError as e:
        # Captura errores (como el nombre del archivo)
        logs.error(f"[1DSF] Error de validación en el proceso: {e}")
    except Exception as e:
        # Cualquier otro error inesperado (permisos, falta de espacio, etc.)
        logs.error(f"[1DSF] Error inesperado en el ciclo ETL: {e}") 
    
    try:
        # 5. Ejecución independiente del Pipeline de Maestro de Entidades
        ejecutar_proceso_maestro_entidades()
    except ValueError as e:
        # Captura errores (como el nombre del archivo)
        logs.error(f"[Mestro de Entidades] Error de validación en el proceso: {e}")
    except Exception as e:
        # Cualquier otro error inesperado (permisos, falta de espacio, etc.)
        logs.error(f"[Mestro de Entidades] Error inesperado en el ciclo ETL: {e}") 
    
    try:
        # 6. Ejecución independiente del Pipeline de Actividades Arca
        ejecutar_proceso_actividades_arca()
    except ValueError as e:
        # Captura errores (como el nombre del archivo)
        logs.error(f"[Actividades Arca] Error de validación en el proceso: {e}")
    except Exception as e:
        # Cualquier otro error inesperado (permisos, falta de espacio, etc.)
        logs.error(f"[Actividades Arca] Error inesperado en el ciclo ETL: {e}") 
        