import logging
import pandas as pd
import os

from sqlalchemy import select, text
from modulos.proceso_bcra.tablas import obtener_engine, padron_arca, padron_arca_2, metadata

logs = logging.getLogger(__name__)

# Inicialización global a nivel de módulo
engine = obtener_engine()
path_datos = r'/home/luciano/Escritorio/automatizacion/archivos_bcra/padron_arca.txt'

def garantizar_tabla_padron_2():
    """
    Asegura que padron_arca_2 exista físicamente en el motor de base de datos.
    """
    logs.info("[ETL Padrón ARCA] Verificando existencia física de padron_arca_2...")
    metadata.create_all(engine, tables=[padron_arca_2])
    return padron_arca_2

def extraer_filtrar_y_cargar_por_lotes():
    """
    Lee el archivo de padrón en bloques de ancho fijo, filtra CUITs válidos
    e inyecta el flujo directamente en padron_arca_2.
    """
    logs.info(f"[ETL Padrón ARCA] Iniciando extracción por lotes. Verificando archivo: {path_datos}")
    
    # 1. CONTROL DE EXISTENCIA FISICA
    if not os.path.exists(path_datos):
        raise FileNotFoundError(f"El archivo no existe: {path_datos}") 

    # 2. CONTROL DE NOMBRE EXACTO      
    if os.path.basename(path_datos).lower() != 'padron_arca.txt':
        raise ValueError(f"Se esperaba 'padron_arca.txt' pero se recibió: '{os.path.basename(path_datos)}'")
    
    # 3. CONTROL DE TAMAÑO
    if os.path.getsize(path_datos) == 0:
        raise ValueError(f"El archivo de padrón ARCA está vacío: {path_datos}")

    # Estructura de los campos
    anchos = [11, 160, 6, 1, 11, 10, 1, 10, 2, 8]

    # Nombres de los campos
    columnas = [
        'Cuit', 'Denominacion', 'Actividad', 'MarcaDeBaja', 'CuitDeReemplazo',
        'FeNac_ContSocial', 'Sexo', 'CodPostal', 'CodProvince', 'FeFallecimiento'
    ]
    
    tamano_lote = 500000
    total_procesado = 0
    errores_omitidos = 0
    max_errores_tolerados = 10

    logs.info(f"[ETL Padrón ARCA] Procesando ancho fijo en bloques de {tamano_lote} filas...")
    
    # SOLUCIÓN 1: CODEPAGE -> Agregamos encoding='latin1' (Aceptación de Ñ y "Tildes")
    # SOLUCIÓN 2: MAXERRORS -> on_bad_lines='skip' evita que Pandas aborte el script si una línea tiene un ancho incorrecto
    lector_bloques = pd.read_fwf(
        path_datos, 
        widths=anchos, 
        names=columnas, 
        dtype=str, 
        chunksize=tamano_lote,
        encoding='latin1',
        errors='replace',
        on_bad_lines='skip' 
    )
    
    for i, bloque in enumerate(lector_bloques, start=1):
        # 1. Filtro estricto: El CUIT debe ser numérico y tener exactamente 11 caracteres.
        # Esto descarta de raíz líneas en blanco, cabeceras o filas rotas que se hayan desfasado.
        bloque_filtrado = bloque[
            (bloque['Cuit'].str.isnumeric() == True) & 
            (bloque['Cuit'].str.len() == 11)
        ].copy()
        
        # Calculamos cuántas filas "raras" o deformes se filtraron en este lote
        filas_descartadas = len(bloque) - len(bloque_filtrado)
        if filas_descartadas > 0:
            errores_omitidos += filas_descartadas
            logs.warning(f"[ETL Padrón ARCA] Bloque {i}: Se omitieron {filas_descartadas} filas sospechosas/malformadas.")
            
            # Si acumulamos más de los errores permitidos, tiramos una alerta
            if errores_omitidos > max_errores_tolerados:
                logs.warning(f"[ETL Padrón ARCA] Alerta: Se superaron las {max_errores_tolerados} filas omitidas (Total: {errores_omitidos}). El proceso continuará igual de forma segura.")

        # Limpieza rápida de strings para evitar que pesen de más en la base
        for col in ['Denominacion', 'CodPostal']:
            if col in bloque_filtrado.columns:
                bloque_filtrado[col] = bloque_filtrado[col].str.strip()
        
        filas_validas = len(bloque_filtrado)
        if filas_validas > 0:
            # Volcado inmediato a la tabla padron_arca_2
            bloque_filtrado.to_sql('padron_arca_2', con=engine, schema='dbo', if_exists='append', index=False)
            total_procesado += filas_validas
            
        logs.info(f"[ETL Padrón ARCA] Bloque {i} procesado en DB. Acumulado válido: {total_procesado} filas.")
    
    if total_procesado == 0:
        raise ValueError("El proceso terminó pero se encontraron 0 registros válidos en todo el padrón.")
        
    logs.info(f"[ETL Padrón ARCA] Extracción terminada. Válidos: {total_procesado} | Omitidos: {errores_omitidos}")
    return

def padron2_a_padron():
    """
    Intercambio rápido de datos mediante TRUNCATE y clonación interna hacia padron_arca y DROP de padron_arca_2.
    """
    logs.info("[ETL Padrón ARCA] Vaciando tabla padron_arca, migrando datos y eliminando padron_arca_2...")
    with engine.begin() as conn:
        # 1. Vaciar tabla definitiva (mantiene índices y estructura)
        conn.execute(text(f"TRUNCATE TABLE {padron_arca.schema}.{padron_arca.name}"))
        
        # 2. Copia directa de tabla a tabla dentro del motor
        query_copia = padron_arca.insert().from_select(padron_arca.c.keys(), select(padron_arca_2))
        conn.execute(query_copia)
        
    # 3. Borrado físico de la padron_arca_2
    logs.info("[ETL Padrón ARCA] Ejecutando DROP TABLE sobre padron_arca_2...")
    padron_arca_2.drop(engine, checkfirst=True)

def ejecutar_proceso_padron_arca():
    """Coordinador de la tabla padron_arca"""
    try:
        # Paso 1: Asegurar tabla padron_arca_2
        garantizar_tabla_padron_2()
        
        # Paso 2: Carga por lotes
        extraer_filtrar_y_cargar_por_lotes()
        
        # Paso 3: Swapping
        padron2_a_padron()
        
        logs.info("[ETL Padrón ARCA] ¡Proceso completado de forma segura!")
        
    except Exception as e:
        logs.error(f"[ETL Padrón ARCA] Error crítico en el pipeline: {e}")
        raise