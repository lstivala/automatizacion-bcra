import os

# Configuración de la conexión al SQL Server en Docker
DB_USER = "sa"
DB_PASS = "Tomates123"
DB_HOST = "localhost"
DB_PORT = "1433"
DB_NAME = "master"

# URL de conexión pasar usar en SQLAlchemy
DATABASE_URL = f"mssql+pyodbc://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=no&TrustServerCertificate=yes"

# Carpta donde van a ir los archivos de BCRA.
CARPETA_ENTRADA_BCRA = os.path.join(os.path.dirname(__file__), "archivos_bcra")
