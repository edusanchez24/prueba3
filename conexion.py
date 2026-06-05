#Instalar librerias pymongo --py -m pip install pymongo
#Instalar librerias dotenv --py -m pip install dotenv

import os
import urllib.parse
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar las variables desde el archivo .env
load_dotenv()

def obtener_db():
    """
    Gestiona la conexión parametrizada a MongoDB Atlas.
    Retorna el objeto de la base de datos si la conexión es exitosa.
    """
    # 1. Recuperar credenciales del archivo .env
    user = os.getenv("MONGODB_USER")
    password = os.getenv("MONGODB_PASS")
    host = os.getenv("MONGODB_HOST")
    db_name = os.getenv("MONGODB_DB")

    # 2. Codificar credenciales (seguridad para caracteres especiales)
    user_enc = urllib.parse.quote_plus(user)
    pass_enc = urllib.parse.quote_plus(password)

    # 3. Construir el string de conexión dinámico
    uri = f"mongodb+srv://{user_enc}:{pass_enc}@{host}/?retryWrites=true&w=majority"

    try:
        # Intentar conectar al clúster
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)

        # Forzar una prueba de conexión (ping)
        client.admin.command('ping')
        
        print(f"Conexión modular exitosa a la base de datos: {db_name}")
        return client[db_name]

    except Exception as e:
        print(f"Error al conectar a MongoDB: {e}")
        return None

# Bloque de prueba (solo se ejecuta si corres este archivo directamente)
if __name__ == "__main__":
    db = obtener_db()
    if db is not None:
        print("Módulo de conexión verificado y listo.")