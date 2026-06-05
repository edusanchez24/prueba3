import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Importamos las funciones que creamos en nuestro "cerebro"
import crud

# Variable global para el visor de resultados
txt_resultados = None

# ==========================================
# FUNCIONES DE RENDERIZADO (MOSTRAR DATOS)
# ==========================================

def mostrar_en_visor(texto):
    """Limpia el visor e inserta el nuevo texto."""
    txt_resultados.config(state="normal")
    txt_resultados.delete("1.0", tk.END)
    txt_resultados.insert(tk.END, texto)
    txt_resultados.config(state="disabled")

def renderizar_lista(lista, tipo="Documentos"):
    """Formatea listas de diccionarios (Eventos o Invitados) para que se lean bien."""
    if not lista:
        mostrar_en_visor(f"📭 No se encontraron {tipo} con los criterios ingresados.")
        return

    texto_final = f"--- Se encontraron {len(lista)} resultados ---\n\n"
    for doc in lista:
        for clave, valor in doc.items():
            # Si el valor es una lista (ej. subdocumento invitados), lo mostramos resumido
            if isinstance(valor, list):
                texto_final += f"  {clave.capitalize()}: [{len(valor)} registros anidados]\n"
            else:
                texto_final += f"  {clave.capitalize()}: {valor}\n"
        texto_final += "-" * 40 + "\n"
    
    mostrar_en_visor(texto_final)

def renderizar_lookup(evento):
    """Formateo especial para el resultado de la agregación $lookup."""
    if not evento:
        mostrar_en_visor("📭 No se encontró el evento o no se pudo realizar el cruce.")
        return

    texto_final = "🌟 RESULTADO DE AGREGACIÓN ($lookup) 🌟\n"
    texto_final += "=" * 50 + "\n"
    texto_final += f"Código: {evento.get('codigo')}\n"
    texto_final += f"Evento: {evento.get('nombre')}\n"
    texto_final += f"Fecha: {evento.get('fecha')} | Lugar: {evento.get('lugar')}\n\n"
    
    texto_final += "👥 INVITADOS (Datos cruzados entre colecciones):\n"
    for inv in evento.get("invitados_completos", []):
        texto_final += f"  - {inv.get('nombre', 'Sin nombre')} ({inv.get('correo', '')})\n"
        texto_final += f"    Empresa: {inv.get('empresa', 'N/A')}\n"
        texto_final += f"    Estado en evento: {inv.get('estado_evento')} | Check-in: {inv.get('checkin')}\n"
        texto_final += "  " + "." * 30 + "\n"
        
    mostrar_en_visor(texto_final)

# ==========================================
# FUNCIONES QUE CONECTAN BOTONES CON CRUD.PY
# ==========================================

def cmd_buscar_invitados_regex():
    texto = ent_regex_invitado.get().strip()
    if not texto:
        messagebox.showwarning("Atención", "Escriba un texto para buscar.")
        return
    resultados = crud.buscar_invitados_por_texto(texto)
    renderizar_lista(resultados, "Invitados")

def cmd_buscar_eventos_regex():
    texto = ent_regex_evento.get().strip()
    if not texto:
        messagebox.showwarning("Atención", "Escriba el nombre del evento.")
        return
    resultados = crud.buscar_eventos_por_nombre(texto)
    renderizar_lista(resultados, "Eventos")

def cmd_buscar_por_rut():
    rut = ent_sub_rut.get().strip()
    if not rut:
        messagebox.showwarning("Atención", "Escriba un RUT.")
        return
    resultados = crud.buscar_eventos_por_rut_invitado(rut)
    renderizar_lista(resultados, "Eventos")

def cmd_buscar_por_estado():
    estado = cmb_estado.get().strip()
    resultados = crud.buscar_eventos_por_estado_invitado(estado)
    renderizar_lista(resultados, "Eventos")

def cmd_ejecutar_lookup():
    codigo = ent_lookup_codigo.get().strip()
    if not codigo:
        messagebox.showwarning("Atención", "Escriba el código del evento (ej. EVT001).")
        return
    resultado = crud.obtener_detalles_evento_con_invitados(codigo)
    renderizar_lookup(resultado)

# ==========================================
# CONFIGURACIÓN DE LA VENTANA (FRONTEND)
# ==========================================
window = tk.Tk()
window.title("Panel de Control - MongoDB Advance")
window.geometry("600x750")

# --- FRAME 1: EXPRESIONES REGULARES ---
frame_regex = tk.LabelFrame(window, text=" 1. Búsquedas Simples (Expresiones Regulares - $regex) ", padx=10, pady=10)
frame_regex.pack(padx=20, pady=5, fill="x")

tk.Label(frame_regex, text="Buscar Invitado (Nombre/Correo):").grid(row=0, column=0, sticky="w", pady=2)
ent_regex_invitado = tk.Entry(frame_regex, width=25)
ent_regex_invitado.grid(row=0, column=1, padx=5)
tk.Button(frame_regex, text="Buscar", command=cmd_buscar_invitados_regex, bg="#4CAF50", fg="white").grid(row=0, column=2, sticky="ew")

tk.Label(frame_regex, text="Buscar Evento (Nombre):").grid(row=1, column=0, sticky="w", pady=2)
ent_regex_evento = tk.Entry(frame_regex, width=25)
ent_regex_evento.grid(row=1, column=1, padx=5)
tk.Button(frame_regex, text="Buscar", command=cmd_buscar_eventos_regex, bg="#4CAF50", fg="white").grid(row=1, column=2, sticky="ew")

# --- FRAME 2: SUBDOCUMENTOS ---
frame_sub = tk.LabelFrame(window, text=" 2. Búsquedas en Arreglos Anidados (Subdocumentos) ", padx=10, pady=10)
frame_sub.pack(padx=20, pady=5, fill="x")

tk.Label(frame_sub, text="Eventos donde participa RUT:").grid(row=0, column=0, sticky="w", pady=2)
ent_sub_rut = tk.Entry(frame_sub, width=25)
ent_sub_rut.grid(row=0, column=1, padx=5)
tk.Button(frame_sub, text="Buscar", command=cmd_buscar_por_rut, bg="#2196F3", fg="white").grid(row=0, column=2, sticky="ew")

tk.Label(frame_sub, text="Eventos con invitados en estado:").grid(row=1, column=0, sticky="w", pady=2)
cmb_estado = ttk.Combobox(frame_sub, values=["pendiente", "confirmado", "rechazado"], width=22)
cmb_estado.current(0)
cmb_estado.grid(row=1, column=1, padx=5)
tk.Button(frame_sub, text="Buscar", command=cmd_buscar_por_estado, bg="#2196F3", fg="white").grid(row=1, column=2, sticky="ew")

# --- FRAME 3: AGREGACIÓN $LOOKUP ---
frame_lookup = tk.LabelFrame(window, text=" 3. Agregación Compleja (JOIN con $lookup) ", padx=10, pady=10)
frame_lookup.pack(padx=20, pady=5, fill="x")

tk.Label(frame_lookup, text="Código del Evento (ej. EVT001):").grid(row=0, column=0, sticky="w", pady=2)
ent_lookup_codigo = tk.Entry(frame_lookup, width=25)
ent_lookup_codigo.grid(row=0, column=1, padx=5)
tk.Button(frame_lookup, text="⚡ Ejecutar Cruce", command=cmd_ejecutar_lookup, bg="#9C27B0", fg="white", font=("Helvetica", 9, "bold")).grid(row=0, column=2, sticky="ew")

# --- FRAME 4: VISOR DE RESULTADOS ---
frame_resultados = tk.LabelFrame(window, text=" Consola de Resultados ", padx=10, pady=5)
frame_resultados.pack(padx=20, pady=10, fill="both", expand=True)

scroll_y = tk.Scrollbar(frame_resultados)
scroll_y.pack(side="right", fill="y")

txt_resultados = tk.Text(frame_resultados, yscrollcommand=scroll_y.set, font=('Consolas', 10), bg="#2b2b2b", fg="#a9b7c6")
txt_resultados.pack(fill="both", expand=True)
scroll_y.config(command=txt_resultados.yview)
txt_resultados.config(state="disabled") # Bloqueado para que el usuario no escriba dentro

# Ajuste de columnas para que los botones se vean alineados
for frame in [frame_regex, frame_sub, frame_lookup]:
    frame.columnconfigure(2, weight=1)

window.mainloop()