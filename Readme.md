# Actualización e Importación de Archivos BCRA 🏦📈

Este proyecto es un pipeline de automatización y ETL (Extracción, Transformación y Carga) desarrollado en Python. Su objetivo principal es descargar, procesar de forma ultraeficiente y migrar a una base de datos SQL Server la información financiera provista por el Banco Central de la República Argentina (BCRA) y el padrón de actividades de ARCA.

> ⚠️ **Nota Académica / Disclaimer:** Este software fue desarrollado con fines estrictamente **educativos y de demostración** como parte de un examen final de la carrera. No tiene vinculación oficial con el BCRA ni con ARCA, y no debe ser utilizado en entornos de producción real sin las debidas auditorías de seguridad y licencias correspondientes.

---

## 📥 Origen de los Datos e Insumos

Los archivos de origen deben descargarse manualmente desde el portal oficial de **ARCA** (ex-AFIP) en el siguiente enlace:
👉 [Portal de Deudores - ARCA/BCRA](https://www5.bcra.gob.ar/ChequesyDeudores/Deudores)

> 🔑 **Requisito Obligatorio:** Para acceder a la descarga de estos archivos, es necesario contar con un **Usuario y Clave Fiscal** habilitados.

### Archivos requeridos para el proceso:
Una vez dentro del portal, deberás descargar los siguientes paquetes comprimidos y ubicarlos en la carpeta de entrada del sistema:
* **`1DSF*.7z`**: Archivo comprimido con la información del primer día hábil.
* **`*DEUDORES.7z`**: Archivo comprimido con la base de datos masiva de deudores.
* **`*PADRON.7z`**: Archivo comprimido con el padrón impositivo de grandes contribuyentes.

*(Nota: Los archivos deben ser descomprimidos en sus respectivos formatos de texto plano `.txt` dentro de la ruta configurada en el pipeline, respetando los nombres esperados por los scripts).*

---

## Características

- **Procesamiento de Grandes Volúmenes:** Diseñado con procesamiento por lotes (*chunksize*) utilizando Pandas para manejar archivos masivos (como deudores con más de 6 millones de filas) sin saturar la memoria RAM.
- **Carga Directa en Memoria:** Optimización de catálogos y tablas auxiliares livianas para procesarse de manera directa y veloz.
- **Estrategia de Carga Segura (Tablas Espejo):** Implementación de un flujo robusto utilizando tablas temporales espejo (`_2`). El proceso realiza la carga completa en la espejo, ejecuta un `TRUNCATE` en la tabla definitiva, migra los datos internamente y finaliza con un `DROP` de la tabla espejo, asegurando cero pérdida de datos ante interrupciones.
- **Interfaz Estilizada con Rich:** Uso de la librería `rich` para mostrar en la consola el inicio, progreso y estado de cada proceso con colores e indicadores visuales.
- **Historial de Eventos (Logs):** Registro interno milimétrico de cada acción clave, tiempos de procesamiento, volumen de filas migradas y excepciones críticas en un archivo de logs unificado utilizando el módulo nativo `logging`.

## Estructura del Proyecto

El sistema está modularizado para facilitar su mantenimiento y escalabilidad:

- **`main.py`:** Orquestador principal que da inicio y controla la ejecución secuencial de todo el pipeline.
- **`tablas.py`:** Declaración de los metadatos de las tablas y configuración de la base de datos utilizando SQLAlchemy.
- **`modulos/proceso_bcra/`:** Carpeta que contiene los submódulos específicos para cada archivo a procesar:
  - `sub_deudores.py` (Procesamiento masivo por chunks de deudores)
  - `sub_padron_arca.py` (Procesamiento de padrón impositivo de grandes contribuyentes)
  - `sub_1dsf.py` (Procesamiento de datos del primer día hábil)
  - `sub_maestro_de_entidades.py` (Carga del catálogo de entidades financieras)
  - `sub_actividades_arca.py` (Carga del nomenclador de actividades económicas)
- **`requirements.txt`:** Archivo con las librerías externas de Python requeridas para la ejecución.

---

## Requisitos del Sistema (Antes de empezar)

Este pipeline requiere de componentes del sistema operativo para poder compilar y conectar la base de datos SQL Server mediante `pyodbc`.

### 1. Instalar el ODBC Driver 18 para SQL Server (Ubuntu)

Ejecutá los siguientes comandos en tu terminal para registrar el repositorio de Microsoft e instalar el driver ODBC y sus dependencias de desarrollo:

```bash
# Registrar la clave y repositorio de Microsoft
curl [https://packages.microsoft.com/keys/microsoft.asc](https://packages.microsoft.com/keys/microsoft.asc) | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc
curl [https://packages.microsoft.com/config/ubuntu/$(lsb_release](https://packages.microsoft.com/config/ubuntu/$(lsb_release) -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

sudo apt-get update

# Instalar el Driver ODBC 18 y unixodbc
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18
sudo apt-get install -y unixodbc-dev build-essential
```

---

## Instalación y Configuración

1. Descarga o clona esta carpeta en tu computadora.
2. Abre una terminal dentro de la carpeta del proyecto y crea un entorno virtual limpio:
   ```bash
   python3 -m venv venv
   ```
3. Activa el entorno virtual:
   ```bash
   source venv/bin/activate
   ```
   *(Notarás que tu prompt de consola cambia para mostrar `(venv)` al inicio)*.

4. Instala las dependencias necesarias de Python:
   ```bash
   pip install -r requirements.txt
   ```

---

## Modo de Uso

Con el entorno virtual activo, simplemente dale play al sistema ejecutando el orquestador principal:

```bash
python3 main.py
```

---

## Autor y Proyecto Final
- **Luciano J. Stivala** - Desarrollo Completo de la Arquitectura, Modelado de Base de Datos y Pipelines de ETL.
- *Este proyecto fue presentado y evaluado como trabajo de examen final académico.*
