from conexion import obtener_db

# Obtenemos la instancia de la base de datos
db = obtener_db()

# ==========================================
# 1. BÚSQUEDAS CON EXPRESIONES REGULARES
# ==========================================

def buscar_invitados_por_texto(texto_buscado):
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
        print(f"Error al buscar invitados con regex: {e}")
        return []

def buscar_eventos_por_nombre(texto_buscado):
    if db is None: return []
    try:
        filtro = {"nombre": {"$regex": texto_buscado, "$options": "i"}}
        return list(db.eventos.find(filtro))
    except Exception as e:
        print(f"Error al buscar eventos por nombre: {e}")
        return []


# ==========================================
# 2. BÚSQUEDAS EN SUBDOCUMENTOS (ARREGLOS)
# ==========================================

def buscar_eventos_por_rut_invitado(rut_buscado):
    if db is None: return []
    try:
        # La notación de punto "invitados.rut" entra automáticamente al arreglo
        filtro = {"invitados.rut": rut_buscado}
        return list(db.eventos.find(filtro))
    except Exception as e:
        print(f"Error al buscar eventos por RUT del invitado: {e}")
        return []

def buscar_eventos_por_estado_invitado(estado_buscado):
    if db is None: return []
    try:
        filtro = {"invitados.estado": estado_buscado}
        return list(db.eventos.find(filtro))
    except Exception as e:
        print(f"Error al buscar eventos por estado de invitado: {e}")
        return []

# ==========================================
# 3. AGREGACIONES AVANZADAS ($lookup)
# ==========================================

def obtener_detalles_evento_con_invitados(codigo_evento):
    if db is None: return None
    try:
        pipeline = [
            #$match - Filtracion de eventos
            {"$match": {"codigo": codigo_evento}},
            {"$unwind": "$invitados"},
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
                    # Se arma nueva lista "invitados_completos" fusionando datos de ambas colecciones
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
        
        resultado = list(db.eventos.aggregate(pipeline))
        
        if resultado:
            return resultado[0]
        else:
            return None
            
    except Exception as e:
        print(f"Error en la agregación: {e}")
        return None   

# ==========================================
# 4. CREAR (INSERT / $push)
# ==========================================


def crear_evento(codigo, nombre, fecha, lugar, categoria):
    """C: CREATE - Inserta un nuevo documento en la colección 'eventos'"""
    if db is None: return False
    try:
        nuevo_evento = {
            "codigo": codigo,
            "nombre": nombre,
            "fecha": fecha,
            "lugar": lugar,
            "categoria": categoria,
            "invitados": [] # Nace con una lista de invitados vacía
        }
        resultado = db.eventos.insert_one(nuevo_evento)
        return resultado.inserted_id is not None
    except Exception as e:
        print(f"❌ Error al crear evento: {e}")
        return False

def agregar_invitado_a_evento(codigo_evento, rut_invitado, estado):
    """
    U: UPDATE ($push) - Agrega un nuevo subdocumento a la lista 'invitados' de un evento.
    """
    if db is None: return False
    try:
        nuevo_invitado = {
            "rut": rut_invitado,
            "estado": estado,
            "checkin": False
        }
        resultado = db.eventos.update_one(
            {"codigo": codigo_evento},
            {"$push": {"invitados": nuevo_invitado}}
        )
        return resultado.modified_count > 0
    except Exception as e:
        print(f"❌ Error al agregar invitado: {e}")
        return False



# ==========================================
# 4. LEER (Mostrar los datos)
# ==========================================

def obtener_todos_los_eventos():
    """R: READ - Trae todos los documentos de la colección 'eventos'."""
    if db is None: return []
    try:
        # Convertimos el cursor a lista
        return list(db.eventos.find())
    except Exception as e:
        print(f"❌ Error al obtener todos los eventos: {e}")
        return []

# ==========================================
# 5. ACTUALIZAR (UPDATE / Operador Posicional $)
# ==========================================

def actualizar_estado_invitado(codigo_evento, rut_invitado, nuevo_estado):
    """
    U: UPDATE con $ - Busca un evento y un RUT específico dentro del arreglo, 
    y actualiza solo el estado de ESE invitado usando el operador posicional ($).
    """
    if db is None: return False
    try:
        resultado = db.eventos.update_one(
            # Filtramos el evento y el invitado específico
            {"codigo": codigo_evento, "invitados.rut": rut_invitado},
            # El símbolo $ representa el índice exacto donde se encontró el RUT
            {"$set": {"invitados.$.estado": nuevo_estado}} 
        )
        return resultado.modified_count > 0
    except Exception as e:
        print(f"❌ Error al actualizar estado: {e}")
        return False


# ==========================================
# 6. ELIMINAR (DELETE / $pull)
# ==========================================

def eliminar_invitado_de_evento(codigo_evento, rut_invitado):
    """
    D: DELETE en arreglo ($pull) - Remueve un subdocumento específico de la lista.
    """
    if db is None: return False
    try:
        resultado = db.eventos.update_one(
            {"codigo": codigo_evento},
            {"$pull": {"invitados": {"rut": rut_invitado}}}
        )
        return resultado.modified_count > 0
    except Exception as e:
        print(f"❌ Error al eliminar invitado: {e}")
        return False

def eliminar_evento_completo(codigo_evento):
    """D: DELETE - Elimina un documento completo de la colección."""
    if db is None: return False
    try:
        resultado = db.eventos.delete_one({"codigo": codigo_evento})
        return resultado.deleted_count > 0
    except Exception as e:
        print(f"❌ Error al eliminar evento: {e}")
        return False

