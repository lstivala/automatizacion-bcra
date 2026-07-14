import logging
import pandas as pd
import os

from sqlalchemy import select, text
from modulos.proceso_bcra.tablas import obtener_engine, unoDSF , unoDSF_2 , metadata

logs = logging.getLogger(__name__)

# Inicialización global a nivel de módulo
engine = obtener_engine()
path_datos = r'/home/luciano/Escritorio/automatizacion/archivos_bcra/1DSF.txt'

def garantizar_tabla_1dsf_2():
    """
    Asegura que la tabla unoDSF_2 (1DSF2) exista físicamente en el motor de base de datos
    respetando la definición dinámica centralizada en tablas.py.
    """
    logs.info("[ETL 1DSF] Verificando existencia física de la tabla unoDSF_2...")
    metadata.create_all(engine, tables=[unoDSF_2])
    return unoDSF_2

def extraer_filtrar_y_cargar_por_lotes_1dsf():
    """
    Lee el archivo 1DSF.txt en bloques de ancho fijo, aplica filtros de CUIT
    e inyecta el flujo directamente en la tabla unoDSF_2.
    """
    logs.info(f"[ETL 1DSF] Iniciando extracción por lotes. Verificando archivo: {path_datos}")
    
    # 1. CONTROL DE EXISTENCIA FISICA
    if not os.path.exists(path_datos):
        raise FileNotFoundError(f"El archivo no existe: {path_datos}")        
    
    # 2. CONTROL DE NOMBRE EXACTO
    if os.path.basename(path_datos).lower() != '1dsf.txt':
        raise ValueError(f"Se esperaba '1DSF.txt' pero se recibió: '{os.path.basename(path_datos)}'")
    
    # 3. CONTROL DE TAMAÑO
    if os.path.getsize(path_datos) == 0:
        raise ValueError(f"El archivo de 1DSF está vacío: {path_datos}")

    # Estructura y nombre de los campos
    anchos = [2, 11, 8]
    columnas = ['TipoEnt', 'CUIT', 'Fecha']
    
    # Configuración del lote a 500.000 registros
    tamano_lote = 500000
    total_procesado = 0

    logs.info(f"[ETL 1DSF] Procesando ancho fijo en bloques de {tamano_lote} filas...")
    
    # El chunksize devuelve un iterable para cuidar los consumos de memoria
    lector_bloques = pd.read_fwf(
        path_datos, 
        widths=anchos, 
        names=columnas, 
        dtype=str, 
        chunksize=tamano_lote,
    )
    
    for i, bloque in enumerate(lector_bloques, start=1):
        # Filtrado sobre el lote actual: CUIT válido numérico de 11 dígitos
        bloque_filtrado = bloque[
            (bloque['CUIT'].str.isnumeric() == True) & 
            (bloque['CUIT'].str.len() == 11)
        ].copy()
        
        filas_validas = len(bloque_filtrado)
        if filas_validas > 0:
            # Volcado inmediato a SQL Server en la tabla unoDSF_2.
            bloque_filtrado.to_sql(
                name=unoDSF_2.name, 
                con=engine, 
                schema=unoDSF_2.schema or 'dbo', 
                if_exists='append', 
                index=False
            )
            total_procesado += filas_validas
            
        logs.info(f"[ETL 1DSF] Bloque {i} procesado en DB. Acumulado válido: {total_procesado} filas.")
    
    # 4. CONTROL DE FILAS UTILES POST-FILTRADO GLOBLAL
    if total_procesado == 0:
        raise ValueError("El proceso terminó pero se encontraron 0 registros válidos en todo el archivo.")
        
    logs.info(f"[ETL 1DSF] Extracción y carga masiva terminada. Total en la tabla unoDSF_2: {total_procesado}")
    return

def unoDSF2_a_unoDSF():
    """
    Realiza el intercambio de datos.
    Limpia la tabla original 1DSF con TRUNCATE, vuelca los datos de la unoDSF_2
    y finalmente elimina (DROP) unoDSF_2.
    """
    logs.info("[ETL 1DSF] Vaciando tabla 1DSF definitiva, migrando datos y eliminando tabla unoDSF_2...")
    with engine.begin() as conn:
        # 1. Vaciamos la tabla definitiva
        conn.execute(text(f"TRUNCATE TABLE {unoDSF.schema or 'dbo'}.{unoDSF.name}"))
        
        # 2. Insertamos lo que se cargó en la unoDSF_2 hacia unoDSF
        query_copia = unoDSF.insert().from_select(unoDSF.c.keys(), select(unoDSF_2))
        conn.execute(query_copia)
        
    # 3. Fuera de la transacción de copia, eliminamos unoDSF_2
    logs.info("[ETL 1DSF] Ejecutando DROP TABLE sobre la tabla unoDSF_2...")
    unoDSF_2.drop(engine, checkfirst=True)

def ejecutar_proceso_1dsf():
    """Coordinador de la tabla 1DSF"""
    try:
        # Paso 1: Asegurar que la tabla unoDSF_2 exista en la base
        garantizar_tabla_1dsf_2()
        
        # Paso 2: Extraer, filtrar y volcar por bloques directamente a la unoDSF_2
        extraer_filtrar_y_cargar_por_lotes_1dsf()
        
        # Paso 3: Intercambio por TRUNCATE y DROP
        unoDSF2_a_unoDSF()

        logs.info("[ETL 1DSF] ¡Prueba de carga por lotes completada de forma segura!")
        
    except Exception as e:
        logs.error(f"[ETL 1DSF] Error crítico en el pipeline: {e}")
        raise