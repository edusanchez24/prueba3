from conexion import obtener_db

# Obtenemos la instancia de la base de datos
db = obtener_db()

# ==========================================
# 1. BÚSQUEDAS CON EXPRESIONES REGULARES
# ==========================================

def buscar_invitados_por_texto(texto_buscado):
    """
    R: READ con Regex - Busca en la colección 'invitados'.
    Permite encontrar coincidencias parciales en el nombre o en el correo,
    ignorando mayúsculas y minúsculas.
    """
    if db is None: return []
    try:
        # Usamos $or para aplicar el regex a múltiples campos a la vez
        filtro = {
            "$or": [
                {"nombre": {"$regex": texto_buscado, "$options": "i"}},
                {"correo": {"$regex": texto_buscado, "$options": "i"}}
            ]
        }
        return list(db.invitados.find(filtro))
    except Exception as e:
        print(f"❌ Error al buscar invitados con regex: {e}")
        return []

def buscar_eventos_por_nombre(texto_buscado):
    """
    R: READ con Regex - Busca eventos por coincidencias en su nombre.
    """
    if db is None: return []
    try:
        filtro = {"nombre": {"$regex": texto_buscado, "$options": "i"}}
        return list(db.eventos.find(filtro))
    except Exception as e:
        print(f"❌ Error al buscar eventos por nombre: {e}")
        return []


# ==========================================
# 2. BÚSQUEDAS EN SUBDOCUMENTOS (ARREGLOS)
# ==========================================

def buscar_eventos_por_rut_invitado(rut_buscado):
    """
    R: READ en Subdocumentos - Retorna los eventos donde participa un RUT específico.
    Demuestra la capacidad de MongoDB para consultar dentro de arreglos anidados.
    """
    if db is None: return []
    try:
        # La notación de punto "invitados.rut" entra automáticamente al arreglo
        filtro = {"invitados.rut": rut_buscado}
        return list(db.eventos.find(filtro))
    except Exception as e:
        print(f"❌ Error al buscar eventos por RUT del invitado: {e}")
        return []

def buscar_eventos_por_estado_invitado(estado_buscado):
    """
    R: READ en Subdocumentos - Encuentra eventos que contengan al menos un invitado
    con un estado particular (ej: "pendiente", "rechazado").
    """
    if db is None: return []
    try:
        filtro = {"invitados.estado": estado_buscado}
        return list(db.eventos.find(filtro))
    except Exception as e:
        print(f"❌ Error al buscar eventos por estado de invitado: {e}")
        return []

# ==========================================
# 3. AGREGACIONES AVANZADAS ($lookup)
# ==========================================

def obtener_detalles_evento_con_invitados(codigo_evento):
    """
    R: READ con Agregación ($lookup) - Emula un JOIN de SQL.
    Trae un evento y cruza los RUTs de sus invitados con la colección 'invitados'
    para traer los datos completos (nombre, correo, empresa).
    """
    if db is None: return None
    try:
        pipeline = [
            # Etapa 1: $match - Filtramos para traer solo el evento que nos interesa
            {"$match": {"codigo": codigo_evento}},
            
            # Etapa 2: $unwind - Desarmamos la lista de invitados. 
            # Si el evento tiene 10 invitados, temporalmente se crean 10 documentos separados.
            {"$unwind": "$invitados"},
            
            # Etapa 3: $lookup - El cruce mágico con la otra colección
            {
                "$lookup": {
                    "from": "invitados",           # Colección con la que vamos a cruzar
                    "localField": "invitados.rut", # El campo RUT dentro del evento
                    "foreignField": "rut",         # El campo RUT en la colección invitados
                    "as": "datos_invitado"         # Nombre de la nueva lista donde se guardará el cruce
                }
            },
            
            # Etapa 4: $unwind - El $lookup devuelve una lista, la desarmamos para sacar el objeto
            {"$unwind": "$datos_invitado"},
            
            # Etapa 5: $group - Volvemos a agrupar todo en la estructura original del evento
            {
                "$group": {
                    "_id": "$_id",
                    "codigo": {"$first": "$codigo"},
                    "nombre": {"$first": "$nombre"},
                    "fecha": {"$first": "$fecha"},
                    "lugar": {"$first": "$lugar"},
                    "categoria": {"$first": "$categoria"},
                    # Armamos una nueva lista "invitados_completos" fusionando datos de ambas colecciones
                    "invitados_completos": {
                        "$push": {
                            "rut": "$invitados.rut",
                            "estado_evento": "$invitados.estado",
                            "checkin": "$invitados.checkin",
                            "nombre": "$datos_invitado.nombre",
                            "correo": "$datos_invitado.correo",
                            "empresa": "$datos_invitado.empresa",
                            "estado_cuenta": "$datos_invitado.estado"
                        }
                    }
                }
            }
        ]
        
        # Ejecutamos la agregación
        resultado = list(db.eventos.aggregate(pipeline))
        
        # Si hay resultados, retornamos el primer (y único) evento encontrado con sus invitados
        if resultado:
            return resultado[0]
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error en la agregación: {e}")
        return None   