import logging
import pandas as pd
import os

from sqlalchemy import select, text
from modulos.proceso_bcra.tablas import obtener_engine, maestro_entidades, maestro_entidades_2, metadata

logs = logging.getLogger(__name__)

# Inicialización global a nivel de módulo
engine = obtener_engine()
path_datos = r'/home/luciano/Escritorio/automatizacion/archivos_bcra/maestro_entidades.txt'

def garantizar_tabla_maestro_2():
    """
    Asegura que la tabla maestro_entidades_2 exista físicamente en la DB.
    """
    logs.info("[ETL Maestro] Verificando existencia física de la tabla maestro_entidades_2...")
    metadata.create_all(engine, tables=[maestro_entidades_2])
    return maestro_entidades_2

def extraer_filtrar_y_cargar_maestro():
    """
    Lee la totalidad del archivo de entidades en memoria,
    valida/limpia y vuelca todo directamente en la tabla maestro_entidades_2.
    """
    logs.info(f"[ETL Maestro] Iniciando extracción directa. Verificando archivo: {path_datos}")
    
    # 1. CONTROL DE EXISTENCIA FÍSICA
    if not os.path.exists(path_datos):
        raise FileNotFoundError(f"El archivo no existe: {path_datos}")        
    
    # 2. CONTROL DE NOMBRE EXACTO
    if os.path.basename(path_datos).lower() != 'maestro_entidades.txt':
        raise ValueError(f"Se esperaba 'maestro_entidades.txt' pero se recibió: '{os.path.basename(path_datos)}'")
    
    # 3. CONTROL DE TAMAÑO
    if os.path.getsize(path_datos) == 0:
        raise ValueError(f"El archivo del maestro de entidades está vacío: {path_datos}")

    # Definimos el ancho fijo del archivo de entidades
    # CodEnt (5 caracteres), Entidad (72 caracteres)
    anchos = [5, 72]
    columnas = ['CodEnt', 'Entidad']

    logs.info("[ETL Maestro] Procesando archivo completo en memoria...")
    
    # Al no usar chunksize, Pandas nos devuelve directamente un único DataFrame
    df = pd.read_fwf(
        path_datos, 
        widths=anchos, 
        names=columnas, 
        dtype=str,
        encoding='latin1',
        errors='replace'
    )
    
    # Limpieza: Aseguramos que el código de entidad sea estrictamente numérico
    df_filtrado = df[df['CodEnt'].str.isnumeric() == True].copy()
    
    total_procesado = len(df_filtrado)
    
    # 4. CONTROL DE FILAS ÚTILES
    if total_procesado == 0:
        raise ValueError("El proceso terminó pero se encontraron 0 registros válidos en el archivo.")
        
    # Volcado completo a la tabla maestro_entidades_2
    df_filtrado.to_sql(
        name=maestro_entidades_2.name, 
        con=engine, 
        schema=maestro_entidades_2.schema or 'dbo', 
        if_exists='append', 
        index=False
    )
    
    logs.info(f"[ETL Maestro] Carga completa terminada. Total en la tabla maestro_entidades_2: {total_procesado}")
    return

def maestro2_a_maestro():
    """
    Realiza el intercambio de datos entre la maestro_entidades_2 y maestro_entidades.
    """
    logs.info("[ETL Maestro] Vaciando tabla maestro_entidades, migrando datos y eliminando maestro_entidades_2...")
    with engine.begin() as conn:
        # 1. Truncate a la tabla maestro_entidades
        conn.execute(text(f"TRUNCATE TABLE {maestro_entidades.schema or 'dbo'}.{maestro_entidades.name}"))
        
        # 2. Copia directa de maestro_entidades_2 a maestro_entidades
        query_copia = maestro_entidades.insert().from_select(maestro_entidades.c.keys(), select(maestro_entidades_2))
        conn.execute(query_copia)
        
    # 3. Limpieza física de la tabla maestro_entidades_2
    logs.info("[ETL Maestro] Ejecutando DROP TABLE sobre la tabla maestro_entidades_2...")
    maestro_entidades_2.drop(engine, checkfirst=True)

def ejecutar_proceso_maestro_entidades():
    """Coordinador del Maestro de Entidades"""
    try:
        # Paso 1: Garantizar tabla maestro_entidades_2
        garantizar_tabla_maestro_2()

        # Paso 2: Extraer todo y volcar a la maestro_entidades_2
        extraer_filtrar_y_cargar_maestro()
        
        # Paso 3: Swap final (TRUNCATE + DROP)
        maestro2_a_maestro()

        logs.info("[ETL Maestro] ¡Carga del Maestro de Entidades completada de forma segura!")
        
    except Exception as e:
        logs.error(f"[ETL Maestro] Error crítico en el pipeline: {e}")
        raise