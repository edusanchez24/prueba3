from conexion import obtener_db

db = obtener_db()

def buscar_invitados_por_texto(texto_buscado):
    if db is None: return []
    try:
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
    if db is None: return []
    try:
        filtro = {"nombre": {"$regex": texto_buscado, "$options": "i"}}
        return list(db.eventos.find(filtro))
    except Exception as e:
        print(f"❌ Error al buscar eventos por nombre: {e}")
        return []

def buscar_eventos_por_rut_invitado(rut_buscado):
    if db is None: return []
    try:
        filtro = {"invitados.rut": rut_buscado}
        return list(db.eventos.find(filtro))
    except Exception as e:
        print(f"❌ Error al buscar eventos por RUT del invitado: {e}")
        return []

def buscar_eventos_por_estado_invitado(estado_buscado):
    if db is None: return []
    try:
        filtro = {"invitados.estado": estado_buscado}
        return list(db.eventos.find(filtro))
    except Exception as e:
        print(f"❌ Error al buscar eventos por estado de invitado: {e}")
        return []

def obtener_detalles_evento_con_invitados(codigo_evento):
    if db is None: return None
    try:
        pipeline = [
            {"$match": {"codigo": codigo_evento}},
            {"$unwind": "$invitados"},
            {
                "$lookup": {
                    "from": "invitados",
                    "localField": "invitados.rut",
                    "foreignField": "rut",
                    "as": "datos_invitado"
                }
            },
            {"$unwind": "$datos_invitado"},
            {
                "$group": {
                    "_id": "$_id",
                    "codigo": {"$first": "$codigo"},
                    "nombre": {"$first": "$nombre"},
                    "fecha": {"$first": "$fecha"},
                    "lugar": {"$first": "$lugar"},
                    "categoria": {"$first": "$categoria"},
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
        return None
    except Exception as e:
        print(f"❌ Error en la agregación: {e}")
        return None

def crear_evento(codigo, nombre, fecha, lugar, categoria):
    if db is None: return False
    try:
        nuevo_evento = {
            "codigo": codigo,
            "nombre": nombre,
            "fecha": fecha,
            "lugar": lugar,
            "categoria": categoria,
            "invitados": []
        }
        resultado = db.eventos.insert_one(nuevo_evento)
        return resultado.inserted_id is not None
    except Exception as e:
        print(f"❌ Error al crear evento: {e}")
        return False

def agregar_invitado_a_evento(codigo_evento, rut_invitado, estado):
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

def actualizar_estado_invitado(codigo_evento, rut_invitado, nuevo_estado):
    if db is None: return False
    try:
        resultado = db.eventos.update_one(
            {"codigo": codigo_evento, "invitados.rut": rut_invitado},
            {"$set": {"invitados.$.estado": nuevo_estado}} 
        )
        return resultado.modified_count > 0
    except Exception as e:
        print(f"❌ Error al actualizar estado: {e}")
        return False

def eliminar_invitado_de_evento(codigo_evento, rut_invitado):
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
    if db is None: return False
    try:
        resultado = db.eventos.delete_one({"codigo": codigo_evento})
        return resultado.deleted_count > 0
    except Exception as e:
        print(f"❌ Error al eliminar evento: {e}")
        return False

def listar_eventos_basico():
    if db is None: return []
    try:
        proyeccion = {"_id": 0, "codigo": 1, "nombre": 1, "fecha": 1, "lugar": 1, "categoria": 1}
        return list(db.eventos.find({}, proyeccion))
    except Exception as e:
        print(f"❌ Error al listar eventos: {e}")
        return []

def top_3_eventos_confirmados():
    if db is None: return []
    try:
        pipeline = [
            {"$unwind": "$invitados"},
            {"$match": {"invitados.estado": "confirmado"}},
            {"$group": {
                "_id": "$nombre",
                "codigo": {"$first": "$codigo"},
                "total_confirmados": {"$sum": 1}
            }},
            {"$sort": {"total_confirmados": -1}},
            {"$limit": 3}
        ]
        return list(db.eventos.aggregate(pipeline))
    except Exception as e:
        print(f"❌ Error en Top 3: {e}")
        return []