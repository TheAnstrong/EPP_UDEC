import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from logic.epp_logic import registrar_nuevo_epp, listar_epp_activos, actualizar_epp
from logic.employee_logic import (
    registrar_empleado,
    listar_empleados_activos,
    actualizar_empleado,
    cambiar_estado_empleado,
)
from logic.report_logic import obtener_historial_avanzado
from database.connection import realizar_backup_inteligente
from logic.inventory_logic import obtener_stock_critico
from PIL import Image, ImageTk
import os
import sys

L_FONDO = "#ACCBB1"  # Blanco udec (limpio)
L_VERDE = "#33743C"  # Para marcos y divisiones
L_AZUL = "#cfe2ff"  # Verde bosque (no se si usarlo)
L_ROJO = "#ffcfcf"  # Verde bosque (no se si usarlo)
L_ROSA = "#ffcccb"  # Rosa
L_AMARILLO = "#FBD574"  # Dorado
L_NARANJA = "#FFCC80"  # Dorado
L_TEXTO = "#212529"  # Gris casi negro


def resolver_ruta(ruta_relativa):
    """Obtiene la ruta absoluta al recurso, funciona para dev y para PyInstaller."""
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, ruta_relativa)


class AppEPP:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de EPP - Universidad")
        self.root.geometry("600x300")
        self.root.configure(bg=L_FONDO)

        # --- CONTENEDOR DEL TÍTULO (Logo + Texto) ---
        frame_titulo = tk.Frame(root, bg=L_FONDO)
        frame_titulo.pack(pady=20)
        try:
            # USAMOS resolver_ruta para encontrar el logo
            ruta_logo = resolver_ruta("assets/udec_logo.png")
            img_original = Image.open(ruta_logo)
            # ... (Resto de tu código de redimensionar igual) ...
            img_resized = img_original.resize((40, 60), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img_resized)
            lbl_logo = tk.Label(frame_titulo, image=self.logo_img, bg=L_FONDO)
            lbl_logo.pack(side="left", padx=10)
        except Exception as e:
            print(f"No se pudo cargar el logo: {e}")

        # Label para el Texto (al lado del logo)
        label_titulo = tk.Label(
            frame_titulo,
            text="Panel de Control EPP",
            font=("Arial", 22, "bold"),
            bg=L_FONDO,
            fg=L_TEXTO,  # Un color gris oscuro elegante
        )
        label_titulo.pack(side="left")

        # --- Contenedor de Botones ---
        frame_botones = tk.Frame(root)
        frame_botones.pack(pady=10)
        frame_botones.configure(bg=L_FONDO)

        # Botones del Menú
        tk.Button(
            frame_botones,
            text="📦 Gestión de Inventario",
            width=25,
            height=2,
            command=self.abrir_inventario,
        ).grid(row=0, column=0, padx=10, pady=10)

        tk.Button(
            frame_botones,
            text="👥 Gestión de Personal",
            width=25,
            height=2,
            command=self.abrir_personal,
        ).grid(row=0, column=1, padx=10, pady=10)

        tk.Button(
            frame_botones,
            text="🤝 Realizar Entrega",
            width=25,
            height=2,
            bg=L_AMARILLO,
            command=self.abrir_entrega,
        ).grid(row=1, column=0, padx=10, pady=10)

        tk.Button(
            frame_botones,
            text="📊 Ver Estadísticas",
            width=25,
            height=2,
            bg=L_AZUL,
            command=self.abrir_reportes,
        ).grid(row=1, column=1, padx=10, pady=10)

        self.v_inventario = None
        self.v_personal = None
        self.v_entrega = None
        self.v_reportes = None

        self.root.iconbitmap("logo.ico")

        # En el __init__ de AppEPP

        criticos = obtener_stock_critico(5)
        if criticos:
            nombres = ", ".join([c["nombre_epp"] for c in criticos])
            messagebox.showwarning(
                "⚠️ Alerta de Stock",
                f"Los siguientes productos se están agotando: {nombres}",
                parent=self.root,
            )

        # --- FUNCIONES DE VALIDACIÓN (Dentro de la clase AppEPP) ---
        def solo_numeros(char):
            """Retorna True si el carácter es un dígito o está vacío."""
            return char.isdigit() or char == ""

        def solo_letras(char):
            """Retorna True si el carácter es letra, espacio o está vacío."""
            # Permitimos letras (incluyendo acentos y ñ) y espacios
            return char.isalpha() or char.isspace() or char == ""

        # Registrar las funciones en Tkinter para que las reconozca como validadores
        self.valida_num = root.register(solo_numeros)
        self.valida_let = root.register(solo_letras)

    # --- Funciones para abrir ventanas ---
    def abrir_entrega(self):
        if self.v_entrega is not None and self.v_entrega.winfo_exists():
            self.v_entrega.lift()
            self.v_entrega.focus_force()

            return

        self.v_entrega = tk.Toplevel(self.root)
        ventana_ent = self.v_entrega
        ventana_ent.title("Realizar Entrega de EPP")
        ventana_ent.geometry("600x500")
        ventana_ent.configure(bg=L_FONDO)

        # --- SELECCIÓN DE EMPLEADO ---
        tk.Label(
            ventana_ent,
            text="1. Seleccione Empleado:",
            font=("Arial", 10, "bold"),
            bg=L_FONDO,
        ).pack(pady=5)

        emps = listar_empleados_activos()
        # Formateamos para el combo: "Nombre Apellido (Documento)"
        lista_nombres_emp = [
            f"{e['nombre']} {e['apellido']} ({e['documento']})" for e in emps
        ]
        # Guardamos los IDs en el mismo orden
        ids_emp = [e["id_empleado"] for e in emps]

        combo_emp = ttk.Combobox(
            ventana_ent, values=lista_nombres_emp, width=50, state="readonly"
        )
        combo_emp.pack(pady=5)
        combo_emp.set("Seleccione un empleado")

        # --- SELECCIÓN DE PRODUCTO ---
        tk.Label(
            ventana_ent,
            text="2. Seleccione Elemento y Cantidad:",
            font=("Arial", 10, "bold"),
            bg=L_FONDO,
        ).pack(pady=5)
        frame_prod = tk.Frame(ventana_ent)
        frame_prod.pack()
        frame_prod.configure(bg=L_FONDO)

        productos = listar_epp_activos()
        lista_nombres_prod = [f"{p['nombre_epp']} - {p['talla']}" for p in productos]
        ids_prod = [p["id_epp"] for p in productos]

        combo_prod = ttk.Combobox(
            frame_prod, values=lista_nombres_prod, width=30, state="readonly"
        )
        combo_prod.pack(side="left", padx=5)
        combo_prod.set("Seleccione un producto")

        ent_cant = tk.Entry(frame_prod, width=5)
        ent_cant.insert(0, "1")
        ent_cant.pack(side="left", padx=5)

        # --- LISTA TEMPORAL (Carrito) ---
        lista_para_entrega = []  # Aquí guardaremos [(id_epp, cantidad, nombre), ...]

        tk.Label(ventana_ent, text="Resumen de Entrega:", bg=L_FONDO).pack(pady=10)
        tabla_temp = ttk.Treeview(
            ventana_ent, columns=("nom", "cant"), show="headings", height=5
        )
        tabla_temp.heading("nom", text="📦 Producto")
        tabla_temp.heading("cant", text="🔢 Cantidad")
        tabla_temp.column("nom", anchor="center")
        tabla_temp.column("cant", anchor="center")
        tabla_temp.pack(fill="x", padx=50)

        def agregar_al_carrito():
            idx = combo_prod.current()
            if idx < 0:
                messagebox.showwarning("Atención", "Seleccione un producto.")
                return

            id_e = ids_prod[idx]
            nombre = lista_nombres_prod[idx]

            try:
                cantidad = int(ent_cant.get())
                if cantidad <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Atención", "Ingrese una cantidad válida.")
                return

            # (Validación de stock que ya tienes...)
            from logic.inventory_logic import consultar_stock_actual

            disponible = consultar_stock_actual(id_e)

            if cantidad > disponible:
                messagebox.showerror("Sin Stock", f"Solo hay {disponible} disponibles.")
                return

            # GUARDAMOS: Ahora guardamos una tupla (id, cantidad)
            # El índice en la tabla coincidirá con el índice en esta lista
            lista_para_entrega.append((id_e, cantidad))

            tabla_temp.insert("", "end", values=(nombre, cantidad))

            # Limpiar para el siguiente
            ent_cant.delete(0, tk.END)
            ent_cant.insert(0, "1")

        # --- (Debajo de la tabla_temp en tu código) ---

        def quitar_del_carrito():
            seleccion = tabla_temp.selection()
            if not seleccion:
                messagebox.showwarning(
                    "Atención",
                    "Seleccione un producto de la tabla para quitarlo.",
                    parent=ventana_ent,
                )
                return

            # Obtener el índice de la fila seleccionada
            item_index = tabla_temp.index(seleccion[0])

            # 1. Eliminar del arreglo lógico (lista_para_entrega)
            lista_para_entrega.pop(item_index)

            # 2. Eliminar de la vista (Treeview)
            tabla_temp.delete(seleccion[0])

        # Frame para botones de acción rápida
        frame_acciones_carrito = tk.Frame(ventana_ent, bg=L_FONDO)
        frame_acciones_carrito.pack(pady=5)

        tk.Button(
            frame_acciones_carrito,
            text="➕ Agregar Producto",
            command=agregar_al_carrito,
            bg=L_AZUL,
            width=20,
        ).pack(side="left", padx=5)

        tk.Button(
            frame_acciones_carrito,
            text="❌ Quitar Seleccionado",
            command=quitar_del_carrito,
            bg=L_ROJO,
            width=20,
        ).pack(side="left", padx=5)

        # --- CAMPO DE OBSERVACIONES ---
        tk.Label(
            ventana_ent,
            text="3. Observaciones / Motivo de Entrega:",
            font=("Arial", 9),
            bg=L_FONDO,
        ).pack(pady=(10, 0))

        ent_obs = tk.Entry(ventana_ent, width=60)
        ent_obs.pack(pady=5, padx=50)
        placeholder = "Entrega de dotación estándar"
        ent_obs.insert(0, placeholder)

        # --- BOTÓN FINAL ACTUALIZADO ---
        def procesar_final():
            emp_idx = combo_emp.current()
            observacion_final = ent_obs.get().strip()  # Capturamos el texto

            if emp_idx < 0 or not lista_para_entrega:
                messagebox.showwarning(
                    "Atención", "Seleccione empleado y al menos un producto."
                )
                return

            id_empleado = ids_emp[emp_idx]
            from logic.delivery_logic import registrar_entrega_completa

            # Pasamos 'observacion_final' en lugar del texto genérico que teníamos antes
            exito, msj = registrar_entrega_completa(
                id_empleado, 1, lista_para_entrega, observacion_final
            )

            if exito:
                # --- LIMPIEZA TOTAL PARA NUEVA ENTREGA ---
                combo_emp.set("Seleccione un empleado")
                combo_prod.set("Seleccione un producto")
                ent_cant.delete(0, tk.END)
                ent_cant.insert(0, "1")
                ent_obs.delete(0, tk.END)
                # Vaciar la lista lógica y la tabla visual
                lista_para_entrega.clear()
                for item in tabla_temp.get_children():
                    tabla_temp.delete(item)
                messagebox.showinfo(
                    "Éxito",
                    "¡Entrega registrada y stock actualizado!",
                    parent=ventana_ent,
                )
            else:
                messagebox.showerror("Error", msj)

        tk.Button(
            ventana_ent,
            text="🚀 REGISTRAR ENTREGA FINAL",
            font=("Arial", 12, "bold"),
            bg=L_AMARILLO,
            fg="black",
            height=2,
            command=procesar_final,
        ).pack(pady=20)

    def abrir_reportes(self):
        if self.v_reportes is not None and self.v_reportes.winfo_exists():
            self.v_reportes.lift()
            self.v_reportes.focus_force()
            return

        self.v_reportes = tk.Toplevel(self.root)
        ventana_rep = self.v_reportes
        ventana_rep.title("Historial de Entregas y Auditoría")
        ventana_rep.geometry("1000x600")
        ventana_rep.configure(bg=L_FONDO)

        # --- PANEL DE FILTROS ---
        frame_filtros = tk.LabelFrame(
            ventana_rep, text=" Filtros de Búsqueda ", padx=10, pady=10, bg=L_FONDO
        )
        frame_filtros.pack(fill="x", padx=20, pady=10)

        fields = [
            ("Nombre / Apellido:", 0, 0, "letras"),
            ("Documento:", 0, 2, "numeros"),
        ]

        entries = {}

        for label, r, c, tipo in fields:
            tk.Label(frame_filtros, text=label, bg=L_FONDO).grid(row=r, column=c)

            en = tk.Entry(frame_filtros, width=15)
            en.grid(row=r, column=c + 1, padx=5)

            # VALIDACIÓN
            if tipo == "numeros":
                en.config(validate="key", validatecommand=(self.valida_num, "%S"))
            elif tipo == "letras":
                en.config(validate="key", validatecommand=(self.valida_let, "%S"))

            entries[label] = en

        ent_nom = entries["Nombre / Apellido:"]
        ent_doc = entries["Documento:"]

        # Mes (Combo)
        tk.Label(frame_filtros, text="Mes:", bg=L_FONDO).grid(row=0, column=4)
        combo_mes = ttk.Combobox(
            frame_filtros,
            values=[
                "",
                "01",
                "02",
                "03",
                "04",
                "05",
                "06",
                "07",
                "08",
                "09",
                "10",
                "11",
                "12",
            ],
            width=5,
        )
        combo_mes.grid(row=0, column=5, padx=5)

        # Año
        tk.Label(frame_filtros, text="Año:", bg=L_FONDO).grid(row=0, column=6)
        ent_anio = tk.Entry(frame_filtros, width=8)
        ent_anio.insert(0, "2026")
        ent_anio.grid(row=0, column=7, padx=5)

        # --- TABLA (Igual que antes pero con columna Documento) ---
        columnas = ("doc", "empleado", "epp", "motivo", "cant", "fecha")
        anchos = {"cant": 70, "motivo": 200}
        tabla_hist = ttk.Treeview(ventana_rep, columns=columnas, show="headings")
        tabla_hist.heading("doc", text="Documento")
        tabla_hist.heading("empleado", text="Empleado")
        tabla_hist.heading("epp", text="Elemento")
        tabla_hist.heading("motivo", text="Motivo")
        tabla_hist.heading("cant", text="Cantidad")
        tabla_hist.heading("fecha", text="Fecha")

        for col in columnas:
            tabla_hist.column(col, anchor="center", width=anchos.get(col, 120))
        tabla_hist.pack(fill="both", expand=True, padx=20)

        def ejecutar_busqueda():
            for item in tabla_hist.get_children():
                tabla_hist.delete(item)

            # Llamamos a la lógica con todos los campos
            datos = obtener_historial_avanzado(
                ent_nom.get(), ent_doc.get(), combo_mes.get(), ent_anio.get()
            )

            for d in datos:
                tabla_hist.insert(
                    "",
                    "end",
                    values=(
                        d["documento"],
                        d["empleado"],
                        d["nombre_epp"],
                        d["observaciones"],
                        d["cantidad"],
                        d["fecha_entrega"],
                    ),
                )

        def limpiar_filtros():
            # 1. Borrar el contenido de los Entry
            ent_nom.delete(0, tk.END)
            ent_doc.delete(0, tk.END)
            ent_anio.delete(0, tk.END)
            ent_anio.insert(0, "2026")  # Valor por defecto

            # 2. Resetear el Combobox
            combo_mes.set("")

            # 3. Recargar la tabla completa
            ejecutar_busqueda()

        tk.Button(
            frame_filtros,
            text="🔍 Buscar",
            command=ejecutar_busqueda,
            bg=L_AZUL,
            width=15,
        ).grid(row=0, column=8, padx=10)

        # Botón de Limpiar (Columna 9)
        btn_limpiar = tk.Button(
            frame_filtros,
            text="🧹 Limpiar",
            command=limpiar_filtros,
            bg=L_ROJO,
            width=12,
        )
        btn_limpiar.grid(row=0, column=9, padx=5)

        ejecutar_busqueda()  # Cargar todo al inicio

        # ... dentro de abrir_reportes (al final, después de la tabla) ...

        frame_acciones = tk.Frame(ventana_rep)
        frame_acciones.pack(pady=15)
        frame_acciones.configure(bg=L_FONDO)

        def clic_exportar():
            from logic.report_logic import obtener_historial_avanzado, exportar_a_csv

            # Obtenemos los datos que están actualmente filtrados en la pantalla
            datos = obtener_historial_avanzado(
                ent_nom.get(), ent_doc.get(), combo_mes.get(), ent_anio.get()
            )
            exito, msj = exportar_a_csv(datos)
            if exito:
                messagebox.showinfo("Exportación", msj)
            else:
                messagebox.showerror("Error", msj)

        tk.Button(
            frame_acciones,
            text="📥 Exportar a Excel (CSV)",
            bg=L_AMARILLO,
            fg="black",
            command=clic_exportar,
            width=25,
        ).pack(side="left", padx=10)

        def clic_graficos():
            from logic.report_logic import generar_dashboard_visual

            generar_dashboard_visual()

        tk.Button(
            frame_acciones,
            text="📊 Ver Dashboard Visual",
            bg=L_AZUL,
            fg="black",
            command=clic_graficos,
            width=25,
        ).pack(side="left", padx=10)

    # ---------------------------------------------------------------
    def abrir_inventario(self):
        # Verificación de seguridad para no duplicar ventanas
        if hasattr(self, "v_inv") and self.v_inv.winfo_exists():
            self.v_inv.lift()
            self.v_inv.focus_force()
            return

        self.v_inv = tk.Toplevel(self.root)
        self.v_inv.title("Gestión de Inventario y Catálogo")
        self.v_inv.geometry("650x600")
        self.v_inv.configure(bg=L_FONDO)

        self.id_seleccionado = None

        # --- SECCIÓN 1: FORMULARIO (Catálogo) ---
        frame_nuevo = tk.LabelFrame(
            self.v_inv, text=" Datos del Elemento ", padx=10, pady=10, bg=L_FONDO
        )
        frame_nuevo.pack(fill="x", padx=20, pady=10)

        fields = [
            ("Nombre:", 0, 0, "letras"),
            ("Categoría:", 0, 2, "letras"),
        ]

        entries = {}

        for label, r, c, tipo in fields:
            lbl = tk.Label(frame_nuevo, text=label, bg=L_FONDO)
            lbl.grid(row=r, column=c, sticky="e")

            en = tk.Entry(frame_nuevo)
            en.grid(row=r, column=c + 1, padx=5, pady=2)

            if tipo == "numeros":
                en.config(validate="key", validatecommand=(self.valida_num, "%S"))
            elif tipo == "letras":
                en.config(validate="key", validatecommand=(self.valida_let, "%S"))

            entries[label] = en

        ent_nombre = entries["Nombre:"]
        ent_cat = entries["Categoría:"]

        tk.Label(frame_nuevo, text="Talla:", bg=L_FONDO).grid(
            row=1, column=0, sticky="e"
        )
        ent_talla = tk.Entry(frame_nuevo)
        ent_talla.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(frame_nuevo, text="Descripción:", bg=L_FONDO).grid(
            row=1, column=2, sticky="e"
        )
        ent_desc = tk.Entry(frame_nuevo)
        ent_desc.grid(row=1, column=3, padx=5, pady=2)

        def limpiar_campos():
            ent_nombre.delete(0, tk.END)
            ent_cat.delete(0, tk.END)
            ent_talla.delete(0, tk.END)
            ent_desc.delete(0, tk.END)
            self.id_seleccionado = None
            btn_guardar.config(text="💾 Guardar Nuevo", bg=L_AZUL)

        def guardar_cambios():
            nombre, cat, talla, desc = (
                ent_nombre.get(),
                ent_cat.get(),
                ent_talla.get(),
                ent_desc.get(),
            )
            if self.id_seleccionado:
                exito, msj = actualizar_epp(
                    self.id_seleccionado, nombre, desc, cat, talla
                )
            else:
                exito, msj = registrar_nuevo_epp(nombre, desc, cat, talla)

            if exito:
                messagebox.showinfo("Éxito", msj, parent=self.v_inv)
                limpiar_campos()
                actualizar_tabla()
            else:
                messagebox.showerror("Error", msj, parent=self.v_inv)

        btn_guardar = tk.Button(
            frame_nuevo, text="💾 Guardar Nuevo", command=guardar_cambios, bg=L_AZUL
        )
        btn_guardar.grid(row=0, column=4, padx=10, rowspan=2, sticky="nsew")
        tk.Button(
            frame_nuevo, text="🧹 Limpiar", bg=L_ROJO, command=limpiar_campos
        ).grid(row=0, column=5, rowspan=2, sticky="nsew")

        # --- SECCIÓN 2: TABLA CON ALERTAS VISUALES ---
        frame_tabla = tk.LabelFrame(
            self.v_inv,
            text=" Inventario Actual (Naranja = Stock Bajo, Rojo = Sin Stock) ",
            padx=10,
            pady=10,
            bg=L_FONDO,
        )
        frame_tabla.pack(fill="both", expand=True, padx=20, pady=5)

        columnas = ("id", "nombre", "categoria", "descripcion", "talla", "stock")
        tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")

        colores_tags = {
            "bajo_stock": L_NARANJA,
            "sin_stock": L_ROSA,
        }

        for tag, color in colores_tags.items():
            tabla.tag_configure(tag, background=color)

        cabeceras = ["ID", "Nombre", "Categoría", "Descripción", "Talla", "Stock"]

        anchos = {"ID": 50, "Descripción": 160, "Talla": 80, "Stock": 50}

        for col, head in zip(columnas, cabeceras, strict=True):
            tabla.heading(col, text=head)
            tabla.column(col, width=anchos.get(head, 100), anchor="center")
        tabla.pack(fill="both", expand=True)

        # --- SECCIÓN 3: CARGA DE STOCK (Mercancía Entrante) ---
        frame_carga = tk.LabelFrame(
            self.v_inv,
            text=" 📦 Cargar Nueva Mercancía (Entrada de Almacén) ",
            padx=10,
            pady=10,
            bg=L_FONDO,
        )
        frame_carga.pack(fill="x", padx=20, pady=10)

        tk.Label(frame_carga, text="Item Seleccionado:", bg=L_FONDO).grid(
            row=0, column=0
        )
        lbl_item_nombre = tk.Label(
            frame_carga,
            text="Ninguno",
            font=("Arial", 10, "bold"),
            fg="blue",
            bg=L_FONDO,
        )
        lbl_item_nombre.grid(row=0, column=1, padx=10)

        tk.Label(frame_carga, text="Cantidad a SUMAR:", bg=L_FONDO).grid(
            row=0, column=2
        )
        ent_cantidad = tk.Entry(frame_carga, width=10)
        ent_cantidad.grid(row=0, column=3, padx=10)

        def ejecutar_carga():
            if not self.id_seleccionado:
                messagebox.showwarning(
                    "Atención",
                    "Selecciona un producto de la tabla primero.",
                    parent=self.v_inv,
                )
                return

            try:
                cantidad = int(ent_cantidad.get())
                from logic.inventory_logic import cargar_stock_epp

                exito, msj = cargar_stock_epp(self.id_seleccionado, cantidad)

                if exito:
                    messagebox.showinfo("Éxito", msj, parent=self.v_inv)
                    ent_cantidad.delete(0, tk.END)
                    actualizar_tabla()
                else:
                    messagebox.showerror("Error", msj, parent=self.v_inv)
            except ValueError:
                messagebox.showerror(
                    "Error", "Ingresa un número válido.", parent=self.v_inv
                )

        btn_cargar = tk.Button(
            frame_carga,
            text="➕ Agregar al Stock",
            command=ejecutar_carga,
            bg="#ADD8E6",
        )
        btn_cargar.grid(row=0, column=4, padx=20)

        # --- FUNCIONES DE SOPORTE ---
        def actualizar_tabla():
            for item in tabla.get_children():
                tabla.delete(item)

            from logic.epp_logic import listar_epp_activos
            from logic.inventory_logic import consultar_stock_actual

            elementos = listar_epp_activos()
            for e in elementos:
                stock = consultar_stock_actual(e["id_epp"])

                tag = (
                    "sin_stock"
                    if stock <= 0
                    else "bajo_stock"
                    if stock <= 5
                    else "normal"
                )

                tabla.insert(
                    "",
                    "end",
                    values=(
                        e["id_epp"],
                        e["nombre_epp"],
                        e["categoria"],
                        e["descripcion"],
                        e["talla"],
                        stock,
                    ),
                    tags=(tag,),
                )

        def seleccionar_fila(event):
            seleccion = tabla.selection()
            if not seleccion:
                return

            # Obtener valores (0:ID, 1:Nombre, 2:Cat, 3:Desc, 4:Talla, 5:Stock)
            item = tabla.item(seleccion[0])["values"]
            self.id_seleccionado = item[0]

            # 1. Llenar los campos del formulario superior
            ent_nombre.delete(0, tk.END)
            ent_nombre.insert(0, item[1])

            ent_cat.delete(0, tk.END)
            ent_cat.insert(0, item[2])

            ent_desc.delete(0, tk.END)
            ent_desc.insert(0, item[3])

            ent_talla.delete(0, tk.END)
            ent_talla.insert(0, item[4])

            # 2. Actualizar visuales
            btn_guardar.config(text="🔄 Actualizar", bg=L_AMARILLO)
            lbl_item_nombre.config(text=f"{item[1]} (ID: {item[0]})")

        tabla.bind("<<TreeviewSelect>>", seleccionar_fila)
        actualizar_tabla()

    # ---------------------------------------------------------------
    def abrir_personal(self):
        if self.v_personal is not None and self.v_personal.winfo_exists():
            self.v_personal.lift()
            self.v_personal.focus_force()
            return

        self.v_personal = tk.Toplevel(self.root)

        ventana_pers = self.v_personal
        ventana_pers.title("Gestión de Personal (Trabajadores)")
        ventana_pers.geometry("850x550")
        ventana_pers.configure(bg=L_FONDO)

        self.id_emp_sel = None

        # --- FORMULARIO ---
        frame_form = tk.LabelFrame(
            ventana_pers, text=" Datos del Trabajador ", padx=10, pady=10, bg=L_FONDO
        )
        frame_form.pack(fill="x", padx=20, pady=10)

        fields = [
            ("Nombre:", 0, 0, "letras"),
            ("Apellido:", 0, 2, "letras"),
            ("Documento:", 1, 0, "numeros"),
            ("Cargo:", 1, 2, "letras"),
            ("Área:", 2, 0, "letras"),
        ]
        entries = {}
        for label, r, c, tipo in fields:
            lbl = tk.Label(frame_form, text=label, bg=L_FONDO)
            lbl.grid(row=r, column=c, sticky="e")
            en = tk.Entry(frame_form)
            en.grid(row=r, column=c + 1, padx=5, pady=2)
            # --- APLICAR LA VALIDACIÓN ---
            if tipo == "numeros":
                # %S es el carácter que se está intentando insertar
                en.config(validate="key", validatecommand=(self.valida_num, "%S"))
            elif tipo == "letras":
                en.config(validate="key", validatecommand=(self.valida_let, "%S"))
            entries[label] = en

        def limpiar_emp():
            for en in entries.values():
                en.delete(0, tk.END)
            self.id_emp_sel = None
            btn_save.config(text="👤 Registrar Nuevo", bg=L_AZUL)
            tabla_act.selection_remove(tabla_act.selection())
            tabla_inac.selection_remove(tabla_inac.selection())

        def guardar_emp():

            d = {k: v.get() for k, v in entries.items()}
            if self.id_emp_sel:
                exito, msj = actualizar_empleado(
                    self.id_emp_sel,
                    d["Nombre:"],
                    d["Apellido:"],
                    d["Documento:"],
                    d["Cargo:"],
                    d["Área:"],
                )
            else:
                exito, msj = registrar_empleado(
                    d["Nombre:"],
                    d["Apellido:"],
                    d["Documento:"],
                    d["Cargo:"],
                    d["Área:"],
                    "2026-01-01",
                )  # Fecha ejemplo

            if exito:
                messagebox.showinfo("Ok", msj)
                limpiar_emp()
                actualizar_tablas_emp()
            else:
                messagebox.showerror("Error", msj)

        # --- BOTONES DE ACCIÓN ---
        # Botón de Guardar/Actualizar (Ocupa la columna 4)
        btn_save = tk.Button(
            frame_form,
            text="👤 Registrar Nuevo",
            command=guardar_emp,
            bg=L_AZUL,
            width=15,
        )
        btn_save.grid(row=0, column=4, rowspan=2, padx=5, pady=5, sticky="nsew")

        # Botón de Limpiar Selección (Ocupa la columna 5)
        btn_limpiar = tk.Button(
            frame_form, text="🧹 Limpiar Campos", command=limpiar_emp, bg=L_ROJO
        )
        btn_limpiar.grid(row=0, column=5, rowspan=2, padx=5, pady=5, sticky="nsew")

        # --- TABLA ACTIVOS ---
        tk.Label(
            ventana_pers, text="Personal Activo", font=("Arial", 10, "bold"), bg=L_FONDO
        ).pack(pady=(10, 5))

        columnas_act = ("id", "nom", "ape", "doc", "car", "area")
        cabeceras_act = ("ID", "Nombre", "Apellido", "Doc", "Cargo", "Área")

        tabla_act = ttk.Treeview(
            ventana_pers,
            columns=columnas_act,
            show="headings",
            height=8,
        )

        for col, head in zip(columnas_act, cabeceras_act, strict=True):
            tabla_act.heading(col, text=head)
            # El anchor="center" es el que hace la magia de centrar el texto
            tabla_act.column(col, width=100, anchor="center")

        tabla_act.pack(fill="x", padx=20)

        # --- TABLA INACTIVOS (Con Apellido y Cargo añadidos) ---
        tk.Label(
            ventana_pers,
            text="Personal Deshabilitado (Haga clic para reactivar)",
            font=("Arial", 10, "italic"),
            fg="#7f8c8d",  # Un gris para que se note que son inactivos
            bg=L_FONDO,
        ).pack(pady=(15, 0))

        # Añadimos 'ape' y 'car' a las columnas
        columnas_inac = ("id", "nom", "ape", "doc", "car")
        cabeceras_inac = ("ID", "Nombre", "Apellido", "Doc", "Cargo")

        tabla_inac = ttk.Treeview(
            ventana_pers, columns=columnas_inac, show="headings", height=4
        )

        for col, head in zip(columnas_inac, cabeceras_inac, strict=True):
            tabla_inac.heading(col, text=head)
            tabla_inac.column(col, width=100, anchor="center")  # También centradas

        tabla_inac.pack(fill="x", padx=20)

        def actualizar_tablas_emp():
            for t in [tabla_act, tabla_inac]:
                for item in t.get_children():
                    t.delete(item)

            from logic.employee_logic import listar_empleados_activos

            # Activos
            for e in listar_empleados_activos():
                tabla_act.insert(
                    "",
                    "end",
                    values=(
                        e["id_empleado"],
                        e["nombre"],
                        e["apellido"],
                        e["documento"],
                        e["cargo"],
                        e["area"],
                    ),
                )
            # Inactivos (Consulta rápida aquí mismo para no crear otro archivo)
            from database.connection import obtener_conexion

            with obtener_conexion() as db:
                cursor = db.cursor()
                cursor.execute("SELECT * FROM Empleado WHERE estado = 'Inactivo'")
                for e in cursor.fetchall():
                    tabla_inac.insert(
                        "",
                        "end",
                        values=(
                            e["id_empleado"],
                            e["nombre"],
                            e["apellido"],
                            e["documento"],
                            e["cargo"],
                        ),
                    )

        def sel_act(event):
            seleccion = tabla_act.selection()
            if not seleccion:
                return
            item = tabla_act.item(tabla_act.selection()[0])["values"]
            self.id_emp_sel = item[0]
            # Cargar campos
            for (lbl, en), val in zip(
                entries.items(),
                [item[1], item[2], item[3], item[4], item[5]],
                strict=True,
            ):
                en.delete(0, tk.END)
                en.insert(0, val)
            btn_save.config(text="🔄 Actualizar", bg=L_AMARILLO)

        def sel_inac(event):
            seleccion = tabla_inac.selection()
            if not seleccion:
                return

            # Solo tomamos el ID para poder reactivarlo
            item = tabla_inac.item(seleccion[0])["values"]
            self.id_emp_sel = item[0]
            # Limpiar los campos de arriba para que no se confunda con una edición
            btn_save.config(text="👤 Registrar Nuevo", bg=L_AZUL)

        # Botones de estado
        def toggle_estado(estado):
            if not self.id_emp_sel:
                return

            cambiar_estado_empleado(self.id_emp_sel, estado)
            limpiar_emp()
            actualizar_tablas_emp()

        frame_acc = tk.Frame(ventana_pers)
        frame_acc.pack(pady=5)
        frame_acc.configure(bg=L_FONDO)
        tk.Button(
            frame_acc,
            text="🚫 Desactivar Seleccionado",
            command=lambda: toggle_estado("Inactivo"),
            bg=L_ROJO,
        ).pack(side="left", padx=5)
        tk.Button(
            frame_acc,
            text="✅ Re-Activar",
            command=lambda: toggle_estado("Activo"),
            bg=L_AZUL,
        ).pack(side="left", padx=5)

        tabla_act.bind("<<TreeviewSelect>>", sel_act)
        # Para reactivar desde la tabla de abajo
        tabla_inac.bind("<<TreeviewSelect>>", sel_inac)

        actualizar_tablas_emp()


class LoginVentana:
    def __init__(self, root):
        self.root = root
        self.root.title("Acceso al Sistema - UDEC")
        self.root.geometry(
            "420x480"
        )  # Aumenté un poco el alto para que quepa todo bien
        self.root.eval("tk::PlaceWindow . center")
        self.root.configure(bg=L_FONDO)

        # --- SECCIÓN DEL LOGO (ARRIBA) ---
        try:
            ruta_logo = resolver_ruta("assets/udec_logo.png")
            img_original = Image.open(ruta_logo)

            # Redimensionar (ajusta el 40, 60 si lo quieres más grande o pequeño)
            img_resized = img_original.resize((100, 150), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img_resized)

            lbl_logo = tk.Label(self.root, image=self.logo_img, bg=L_FONDO)
            lbl_logo.pack(pady=(35, 0))
        except Exception as e:
            print(f"No se pudo cargar el logo: {e}")

        # --- SECCIÓN DEL TÍTULO (DEBAJO) ---
        tk.Label(
            self.root, text="CONTROL DE ACCESO", font=("Arial", 12, "bold"), bg=L_FONDO
        ).pack(pady=(40, 20))  # Espacio pequeño arriba para separarlo del logo

        tk.Label(root, text="Usuario:", bg=L_FONDO).pack()
        self.ent_user = tk.Entry(root)
        self.ent_user.pack(pady=5)

        tk.Label(root, text="Contraseña:", bg=L_FONDO).pack()
        self.ent_pass = tk.Entry(root, show="*")  # Ocultar caracteres
        self.ent_pass.pack(pady=5)

        tk.Button(
            root,
            text="Entrar",
            command=self.intentar_login,
            bg=L_AZUL,
            fg="black",
            width=15,
        ).pack(pady=32)
        self.root.iconbitmap("logo.ico")

    def intentar_login(self):
        realizar_backup_inteligente()
        from logic.auth_logic import verificar_credenciales

        user = self.ent_user.get()
        pw = self.ent_pass.get()

        exito, id_u, nombre = verificar_credenciales(user, pw)

        if exito:
            root_actual = self.root
            for widget in root_actual.winfo_children():
                widget.destroy()

            # RECONFIGURAR TAMAÑO PARA EL MENÚ PRINCIPAL
            root_actual.geometry("600x400")
            AppEPP(root_actual)
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")


if __name__ == "__main__":
    root = tk.Tk()
    login = LoginVentana(root)
    root.mainloop()

# # Skip login
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = AppEPP(root)
#     root.mainloop()
