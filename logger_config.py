import logging
import os

def configurar_logs():
    # Se crea el directorio logs, en caso de no existir.
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Formato del texto que se imprime en el archivo .log. AÑO-MES-DIA HS:MIN:SEG - Archivo.py:lineacodigo - [NIVEL] - Mensaje
    formato = logging.Formatter(
        '%(asctime)s - %(filename)s:%(lineno)d - [%(levelname)s] - %(message)s',
        datefmt='%Y-%M-%D %H:%M:%S'
    )

    # Archivo handler (guarda todo de forma interna en el disco)
    archivo_handler = logging.FileHandler('logs/automatizacion.log', encoding='utf-8')
    archivo_handler.setLevel(logging.INFO)  # Nivel de captura > = INFO
    archivo_handler.setFormatter(formato)
    
    # Creamos el logger raíz del proyecto y le asignamos el archivo
    logs = logging.getLogger()
    logs.setLevel(logging.INFO) # Nivel de captura > = INFO
    logs.addHandler(archivo_handler)
    
    return logs