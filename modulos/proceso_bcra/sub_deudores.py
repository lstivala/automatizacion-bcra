import logging
import pandas as pd
import os

from sqlalchemy import select, text
from modulos.proceso_bcra.tablas import obtener_engine, deudores, deudores_2, metadata

logs = logging.getLogger(__name__)

# Inicialización global a nivel de módulo
engine = obtener_engine()
path_datos = r'/home/luciano/Escritorio/automatizacion/archivos_bcra/deudores.txt'

def garantizar_tabla_deudeores_2():
    """
    Asegura que deudores_2 exista físicamente en el motor de base de datos
    respetando la definición dinámica centralizada en tablas.py.
    """
    logs.info("[ETL Deudores] Verificando existencia física de deudores_2...")
    metadata.create_all(engine, tables=[deudores_2])
    return deudores_2

def extraer_filtrar_y_cargar_por_lotes():
    """
    Lee el archivo gigante en bloques de ancho fijo, aplica filtros iniciales
    e inyecta el flujo directamente en deudores_2.
    """
    logs.info(f"[ETL Deudores] Iniciando extracción por lotes. Verificando archivo: {path_datos}")
    
    # 1. CONTROL DE EXISTENCIA FISICA
    if not os.path.exists(path_datos):
        raise FileNotFoundError(f"El archivo no existe: {path_datos}")        
    
    # 2. CONTROL DE NOMBRE EXACTO
    if os.path.basename(path_datos).lower() != 'deudores.txt':
        raise ValueError(f"Se esperaba 'deudores.txt' pero se recibió: '{os.path.basename(path_datos)}'")
    
    # 3. CONTROL DE TAMAÑO
    if os.path.getsize(path_datos) == 0:
        raise ValueError(f"El archivo de deudores está vacío: {path_datos}")

    # Estructuras de los campos
    anchos = [
        5, 6, 2, 11, 3, 2, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 
        1, 1, 1, 1, 1, 1, 4, 2
    ]

    # Nombres de los campos.
    columnas = [
        'CodEntidad', 'FechaInfo', 'TipoId', 'CUIT', 'Actividad', 'Situacion',
        'Prestamos', 'Participaciones', 'Garantias', 'OtrosConceptos', 'GarantiasA',
        'GarantiasB', 'SinGarantiasPreferidas', 'ContragananciasPreferidasA',
        'ContragananciasPreferidasB', 'SinContragananciasPreferidas', 'Previsiones',
        'DeudaCubierta', 'ProcesoJudicialRevision', 'Refinanciaciones',
        'RecategorizacionObligatoria', 'SituacionJuridica', 'IrrecuperablesPorDisposicionTecnica',
        'DiasAtraso', 'dummy'
    ]
    
    # Configuración del lote a 500.000 registros
    tamano_lote = 500000
    total_procesado = 0

    logs.info(f"[ETL Deudores] Procesando ancho fijo en bloques de {tamano_lote} filas...")
    
    # El chunksize nos devuelve un objeto iterable en lugar de un DataFrame entero
    lector_bloques = pd.read_fwf(path_datos, widths=anchos, names=columnas, dtype=str, chunksize=tamano_lote)
    
    for i, bloque in enumerate(lector_bloques, start=1):
        # Filtrado el lote actual: WHERE ISNUMERIC(cuit) = 1
        bloque_filtrado = bloque[bloque['CUIT'].str.isnumeric() == True]
        
        filas_validas = len(bloque_filtrado)
        if filas_validas > 0:
            # Volcado inmediato a SQL Server (append en la tabla deudores_2)
            bloque_filtrado.to_sql('deudores_2', con=engine, schema='dbo', if_exists='append', index=False)
            total_procesado += filas_validas
            
        logs.info(f"[ETL Deudores] Bloque {i} procesado en DB. Acumulado válido: {total_procesado} filas.")
    
    # 4. CONTROL DE FILAS UTILES POST-FILTRADO GLOBLAL
    if total_procesado == 0:
        raise ValueError("El proceso terminó pero se encontraron 0 registros válidos en todo el archivo.")
        
    logs.info(f"[ETL Deudores] Extracción y carga masiva terminada. Total en deudores_2: {total_procesado}")
    return

def deudores2_a_deudores():
    """
    Realiza el intercambio de datos.
    Limpia la tabla deudores con TRUNCATE, vuelca los datos de deudores_2 y finalmente
    elimina (DROP) deudores_2 para liberar espacio en el motor.
    """
    logs.info("[ETL Deudores] Vaciando tabla deudores, migrando datos y eliminando deudores_2...")
    with engine.begin() as conn:
        # 1. Vaciamos la tabla deudores definitiva al instante sin generar logs pesados
        conn.execute(text(f"TRUNCATE TABLE {deudores.schema}.{deudores.name}"))
        
        # 2. Insertamos lo que se cargó en deudores_2 hacia deudores.
        query_copia = deudores.insert().from_select(deudores.c.keys(), select(deudores_2))
        conn.execute(query_copia)
        
    # 3. Fuera de la transacción de copia, eliminamos físicamente deudores_2.
    logs.info("[ETL Deudores] Ejecutando DROP TABLE sobre deudores_2...")
    deudores_2.drop(engine, checkfirst=True)

def ejecutar_proceso_deudores():
    """Coordinador de la tabla deudores"""
    try:
        # Paso 1: Asegurar que deudores_2 exista en la base
        garantizar_tabla_deudeores_2()

        # Paso 2: Extraer, filtrar y volcar por bloques directamente a deudores_2
        extraer_filtrar_y_cargar_por_lotes()
        
        # Paso 3: Intercambio por TRUNCATE y DROP de deudores_2 hacia deudores.
        deudores2_a_deudores()

        logs.info("[ETL Deudores] ¡Prueba de carga por lotes completada de forma segura!")
        
    except Exception as e:
        logs.error(f"[ETL Deudores] Error crítico en el pipeline: {e}")
        raise