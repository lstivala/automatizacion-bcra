import logging
import pandas as pd
import os

from sqlalchemy import select, text
from modulos.proceso_bcra.tablas import obtener_engine, actividades_arca, actividades_arca_2, metadata

logs = logging.getLogger(__name__)

# Inicialización global a nivel de módulo
engine = obtener_engine()
path_datos = r'/home/luciano/Escritorio/automatizacion/archivos_bcra/actividades_arca.txt'

def garantizar_tabla_actividades_2():
    """
    Asegura que la tabla actividades_arca_2 exista físicamente en la DB.
    """
    logs.info("[ETL Actividades] Verificando existencia física de la tabla actividades_arca_2...")
    metadata.create_all(engine, tables=[actividades_arca_2])
    return actividades_arca_2

def extraer_filtrar_y_cargar_actividades():
    """
    Lee la totalidad del archivo de actividades en memoria,
    valida/limpia y vuelca todo directamente en la tabla actividades_arca_2.
    """
    logs.info(f"[ETL Actividades] Iniciando extracción directa. Verificando archivo: {path_datos}")
    
    # 1. CONTROL DE EXISTENCIA FÍSICA
    if not os.path.exists(path_datos):
        raise FileNotFoundError(f"El archivo no existe: {path_datos}")        
    
    # 2. CONTROL DE NOMBRE EXACTO
    if os.path.basename(path_datos).lower() != 'actividades_arca.txt':
        raise ValueError(f"Se esperaba 'actividades_arca.txt' pero se recibió: '{os.path.basename(path_datos)}'")
    
    # 3. CONTROL DE TAMAÑO
    if os.path.getsize(path_datos) == 0:
        raise ValueError(f"El archivo de actividades ARCA está vacío: {path_datos}")

    # Definimos el ancho fijo según corresponda 
    anchos = [6, 256]
    columnas = ['Codigo', 'Descripcion']

    logs.info("[ETL Actividades] Procesando archivo completo en memoria...")
    
    # Lectura directa a memoria usando Latin1 para conservar caracteres especiales del español
    df = pd.read_fwf(
        path_datos, 
        widths=anchos, 
        names=columnas, 
        dtype=str, 
        encoding='latin1', 
        errors='replace'
    )
    
    # Limpieza: Aseguramos que el código sea estrictamente numérico
    df_filtrado = df[df['Codigo'].str.isnumeric() == True].copy()
    
    total_procesado = len(df_filtrado)
    
    # 4. CONTROL DE FILAS ÚTILES
    if total_procesado == 0:
        raise ValueError("El proceso terminó pero se encontraron 0 registros válidos en el archivo.")
        
    # Volcado completo a la tabla actividades_arca_2
    df_filtrado.to_sql(
        name=actividades_arca_2.name, 
        con=engine, 
        schema=actividades_arca_2.schema or 'dbo', 
        if_exists='append', 
        index=False
    )
    
    logs.info(f"[ETL Actividades] Carga completa terminada. Total en la tabla actividades_arca_2: {total_procesado}")
    return

def actividades2_a_actividades():
    """
    Realiza el intercambio de datos entre la tabla actividades_arca_2 y la tabla actividades_arca.
    """
    logs.info("[ETL Actividades] Vaciando tabla actividades_arca, migrando datos y eliminando actividades_arca_2...")
    with engine.begin() as conn:
        # 1. Truncate a la tabla actividades_arca
        conn.execute(text(f"TRUNCATE TABLE {actividades_arca.schema or 'dbo'}.{actividades_arca.name}"))
        
        # 2. Copia directa de actividades_arca_2 a actividades_arca.
        query_copia = actividades_arca.insert().from_select(actividades_arca.c.keys(), select(actividades_arca_2))
        conn.execute(query_copia)
        
    # 3. Limpieza física de la tabla actividades_arca_2
    logs.info("[ETL Actividades] Ejecutando DROP TABLE sobre la tabla actividades_arca_2...")
    actividades_arca_2.drop(engine, checkfirst=True)

def ejecutar_proceso_actividades_arca():
    """Coordinador de las Actividades ARCA"""
    try:
        # Paso 1: Garantizar tabla actividades_arca_2
        garantizar_tabla_actividades_2()
        
        # Paso 2: Extraer todo y volcar a actividades_arca_2
        extraer_filtrar_y_cargar_actividades()
        
        # Paso 3: Swap final (TRUNCATE activades_arca + DROP actividades_arca_2)
        actividades2_a_actividades()

        logs.info("[ETL Actividades] ¡Carga de Actividades ARCA completada de forma segura!")
        
    except Exception as e:
        logs.error(f"[ETL Actividades] Error crítico en el pipeline: {e}")
        raise