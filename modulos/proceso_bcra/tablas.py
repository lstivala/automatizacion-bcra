import logging
import config as cf

from sqlalchemy import create_engine, MetaData, Table, Column, Index, text,PrimaryKeyConstraint
from sqlalchemy import CHAR, VARCHAR, NVARCHAR, INT

# Inicializo
logs = logging.getLogger(__name__)

# Metadata centralizada para el esquema 'dbo'
metadata = MetaData(schema='dbo')

# Se crea el motor (engine) a la base de datos.
def obtener_engine():
    """Genera el motor de conexión."""
    return create_engine(cf.DATABASE_URL, fast_executemany=True)

def verificar_y_crear_tablas():
    """
    Inspecciona la base de datos y crea únicamente las tablas de la metadata
    que no existan en el motor de destino.
    """
    logs.info("[BCRA - Tablas] Verificando existencia de las tabla, sino se crean...")
    try:
        # metadata.create_all evalúa el diccionario de la DB.
        # Si encuentra que la tabla ya existe, no hace nada. Si falta, emite el CREATE TABLE.
        metadata.create_all(engine)
        logs.info("[BCRA - Tablas] Verificación de tablas completada.")
    except Exception as e:
        logs.error(f"[BCRA - Tablas] Error al inicializar las tablas mediante Core: {e}")
        raise

engine = obtener_engine()

# =====================================================================
# 1. TABLA: dbo.deudores
# =====================================================================
deudores = Table(
    'deudores', metadata,
    Column('CodEntidad', CHAR(5), nullable=False),
    Column('FechaInfo', CHAR(6)),
    Column('TipoId', CHAR(2)),
    Column('CUIT', CHAR(11), nullable=False),
    Column('Actividad', CHAR(3)),
    Column('Situacion', CHAR(2)),
    Column('Prestamos', CHAR(12)),
    Column('Participaciones', CHAR(12)),
    Column('Garantias', CHAR(12)),
    Column('OtrosConceptos', CHAR(12)),
    Column('GarantiasA', CHAR(12)),
    Column('GarantiasB', CHAR(12)),
    Column('SinGarantiasPreferidas', CHAR(12)),
    Column('ContragananciasPreferidasA', CHAR(12)),
    Column('ContragananciasPreferidasB', CHAR(12)),
    Column('SinContragananciasPreferidas', CHAR(12)),
    Column('Previsiones', CHAR(12)),
    Column('DeudaCubierta', CHAR(1)),
    Column('ProcesoJudicialRevision', CHAR(1)),
    Column('Refinanciaciones', CHAR(1)),
    Column('RecategorizacionObligatoria', CHAR(1)),
    Column('SituacionJuridica', CHAR(1)),
    Column('IrrecuperablesPorDisposicionTecnica', CHAR(1)),
    Column('DiasAtraso', CHAR(4)),
    Column('dummy', CHAR(2)),

    PrimaryKeyConstraint('CUIT', 'CodEntidad', name='PK_deudores_CUIT_CodEntidad'),

    Index('IX_deudores_CodEntidad', 'CodEntidad'),
    Index('IX_deudores_Situacion', 'Situacion')
)
# =====================================================================
# 2. TABLA: dbo.1DSF
# =====================================================================
unoDSF = Table(
    'unoDSF', metadata,
    Column('TipoEnt', VARCHAR(2)),
    Column('CUIT', VARCHAR(11), nullable=False),
    Column('Fecha', VARCHAR(8)),

    PrimaryKeyConstraint('CUIT', name='PK_1DSF_CUIT'),

    Index('IX_1DSF_Fecha', 'Fecha')
)

# =====================================================================
# 3. TABLA: dbo.actividades_arca
# =====================================================================
actividades_arca = Table(
    'actividades_arca', metadata,
    Column('Codigo', INT, autoincrement=False, nullable=False),
    Column('Descripcion', VARCHAR(262)),

    PrimaryKeyConstraint('Codigo', name='PK_actividades_arca_Codigo')
)

# =====================================================================
# 4. TABLA: dbo.maestro_de_entidades
# =====================================================================
maestro_entidades = Table(
    'maestro_entidades', metadata,
    Column('CodEnt', INT, autoincrement=False, nullable=False),
    Column('Entidad', VARCHAR(72)),

    PrimaryKeyConstraint('CodEnt', name='PK_maestro_entidades_CodEnt')
)

# =====================================================================
# 5. TABLA: dbo.padron_arca
# =====================================================================
padron_arca = Table(
    'padron_arca', metadata,
    Column('Cuit', NVARCHAR(11), nullable=False),
    Column('Denominacion', NVARCHAR(160)),
    Column('Actividad', NVARCHAR(6)),
    Column('MarcaDeBaja', NVARCHAR(1)),
    Column('CuitDeReemplazo', NVARCHAR(11)),
    Column('FeNac_ContSocial', NVARCHAR(10)),
    Column('Sexo', NVARCHAR(1)),
    Column('CodPostal', NVARCHAR(10)),
    Column('CodProvince', NVARCHAR(2)),  
    Column('FeFallecimiento', NVARCHAR(8)),

    PrimaryKeyConstraint('Cuit', name='PK_padron_arca_Cuit')
)

# =====================================================================
# CREACION DE TABLAS ESPEJO (Sufijo _2)
# =====================================================================
deudores_2 = Table('deudores_2', metadata, *[col.copy() for col in deudores.columns])
unoDSF_2 = Table('unoDSF_2', metadata, *[col.copy() for col in unoDSF.columns])
actividades_arca_2 = Table('actividades_arca_2', metadata, *[col.copy() for col in actividades_arca.columns])
maestro_entidades_2 = Table('maestro_entidades_2', metadata, *[col.copy() for col in maestro_entidades.columns])
padron_arca_2 = Table('padron_arca_2', metadata, *[col.copy() for col in padron_arca.columns])