import tkinter as tk
from tkinter import messagebox
from tkinter import ttk  # Para tablas y combobox modernos
from logic.epp_logic import registrar_nuevo_epp, listar_epp_activos, actualizar_epp
from logic.employee_logic import (
    registrar_empleado,
    listar_empleados_activos,
    desactivar_empleado,
    actualizar_empleado,
    cambiar_estado_empleado,
)
from logic.report_logic import obtener_historial_avanzado
from database.connection import realizar_backup_inteligente


class AppEPP:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de EPP - Universidad")
        self.root.geometry("600x300")

        # --- Título ---
        label_titulo = tk.Label(
            root, text="Panel de Control EPP", font=("Arial", 20, "bold")
        )
        label_titulo.pack(pady=20)

        # --- Contenedor de Botones ---
        frame_botones = tk.Frame(root)
        frame_botones.pack(pady=10)

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
            bg="#d1ffcf",
            command=self.abrir_entrega,
        ).grid(row=1, column=0, padx=10, pady=10)

        tk.Button(
            frame_botones,
            text="📊 Ver Estadísticas",
            width=25,
            height=2,
            bg="#cfe2ff",
            command=self.abrir_reportes,
        ).grid(row=1, column=1, padx=10, pady=10)

        self.v_inventario = None
        self.v_personal = None
        self.v_entrega = None
        self.v_reportes = None

        self.root.iconbitmap("logo.ico")

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

        # --- SELECCIÓN DE EMPLEADO ---
        tk.Label(
            ventana_ent, text="1. Seleccione Empleado:", font=("Arial", 10, "bold")
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
        ).pack(pady=5)
        frame_prod = tk.Frame(ventana_ent)
        frame_prod.pack()

        from logic.epp_logic import listar_epp_activos

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

        tk.Label(ventana_ent, text="Resumen de Entrega:").pack(pady=10)
        tabla_temp = ttk.Treeview(
            ventana_ent, columns=("nom", "cant"), show="headings", height=5
        )
        tabla_temp.heading("nom", text="Producto")
        tabla_temp.heading("cant", text="Cantidad")
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

            # NUEVO: Consultar stock disponible antes de agregar a la lista
            from logic.inventory_logic import consultar_stock_actual

            disponible = consultar_stock_actual(id_e)

            if cantidad > disponible:
                messagebox.showerror(
                    "Sin Stock",
                    f"No puedes agregar {cantidad} unidades de {nombre}.\nSolo hay {disponible} disponibles.",
                )
                return

            # Si pasa el filtro, lo agregamos
            lista_para_entrega.append((id_e, cantidad))
            tabla_temp.insert("", "end", values=(nombre, cantidad))
            ent_cant.delete(0, tk.END)
            ent_cant.insert(0, "1")

        tk.Button(
            ventana_ent, text="➕ Agregar", command=agregar_al_carrito, bg="#eee"
        ).pack(pady=5)

        # --- BOTÓN FINAL ---
        def procesar_final():
            emp_idx = combo_emp.current()
            if emp_idx < 0 or not lista_para_entrega:
                messagebox.showwarning(
                    "Atención", "Seleccione empleado y al menos un producto."
                )
                return

            id_empleado = ids_emp[emp_idx]
            from logic.delivery_logic import registrar_entrega_completa

            # Usamos el id_usuario=1 por defecto (Administrador)
            exito, msj = registrar_entrega_completa(
                id_empleado, 1, lista_para_entrega, "Entrega desde interfaz"
            )

            if exito:
                messagebox.showinfo("Éxito", msj, parent=ventana_ent)
                ventana_ent.destroy()  # Cerramos al terminar
            else:
                messagebox.showerror("Error", msj)

        tk.Button(
            ventana_ent,
            text="🚀 REGISTRAR ENTREGA FINAL",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
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

        # --- PANEL DE FILTROS ---
        frame_filtros = tk.LabelFrame(
            ventana_rep, text=" Filtros de Búsqueda ", padx=10, pady=10
        )
        frame_filtros.pack(fill="x", padx=20, pady=10)

        # Nombre / Apellido
        tk.Label(frame_filtros, text="Nombre:").grid(row=0, column=0)
        ent_nom = tk.Entry(frame_filtros, width=15)
        ent_nom.grid(row=0, column=1, padx=5)

        # Documento
        tk.Label(frame_filtros, text="Documento:").grid(row=0, column=2)
        ent_doc = tk.Entry(frame_filtros, width=15)
        ent_doc.grid(row=0, column=3, padx=5)

        # Mes (Combo)
        tk.Label(frame_filtros, text="Mes:").grid(row=0, column=4)
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
        tk.Label(frame_filtros, text="Año:").grid(row=0, column=6)
        ent_anio = tk.Entry(frame_filtros, width=8)
        ent_anio.insert(0, "2026")
        ent_anio.grid(row=0, column=7, padx=5)

        # --- TABLA (Igual que antes pero con columna Documento) ---
        columnas = ("doc", "empleado", "epp", "cant", "fecha")
        tabla_hist = ttk.Treeview(ventana_rep, columns=columnas, show="headings")
        tabla_hist.heading("doc", text="Documento")
        tabla_hist.heading("empleado", text="Empleado")
        tabla_hist.heading("epp", text="Elemento")
        tabla_hist.heading("cant", text="Cant")
        tabla_hist.heading("fecha", text="Fecha")
        for col in columnas:
            tabla_hist.column(col, anchor="center")
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
            bg="#ddd",
            width=15,
        ).grid(row=0, column=8, padx=10)

        # Botón de Limpiar (Columna 9)
        btn_limpiar = tk.Button(
            frame_filtros,
            text="🧹 Limpiar",
            command=limpiar_filtros,
            bg="#f0f0f0",
            width=12,
        )
        btn_limpiar.grid(row=0, column=9, padx=5)

        ejecutar_busqueda()  # Cargar todo al inicio

        # ... dentro de abrir_reportes (al final, después de la tabla) ...

        frame_acciones = tk.Frame(ventana_rep)
        frame_acciones.pack(pady=15)

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
            bg="#228b22",
            fg="white",
            command=clic_exportar,
            width=25,
        ).pack(side="left", padx=10)

        def clic_graficos():
            from logic.report_logic import generar_dashboard_visual

            generar_dashboard_visual()

        tk.Button(
            frame_acciones,
            text="📊 Ver Dashboard Visual",
            bg="#00008b",
            fg="white",
            command=clic_graficos,
            width=25,
        ).pack(side="left", padx=10)

    def abrir_inventario(self):
        # Verificación de seguridad para no duplicar ventanas
        if hasattr(self, "v_inv") and self.v_inv.winfo_exists():
            self.v_inv.lift()
            self.v_inv.focus_force()
            return

        self.v_inv = tk.Toplevel(self.root)
        self.v_inv.title("Gestión de Inventario y Catálogo")
        self.v_inv.geometry("800x600")

        self.id_seleccionado = None

        # --- SECCIÓN 1: FORMULARIO ---
        frame_nuevo = tk.LabelFrame(
            self.v_inv, text=" Datos del Elemento ", padx=10, pady=10
        )
        frame_nuevo.pack(fill="x", padx=20, pady=10)

        # Campos (Nombre, Categoría, Talla, Descripción)
        tk.Label(frame_nuevo, text="Nombre:").grid(row=0, column=0, sticky="e")
        ent_nombre = tk.Entry(frame_nuevo)
        ent_nombre.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(frame_nuevo, text="Categoría:").grid(row=0, column=2, sticky="e")
        ent_cat = tk.Entry(frame_nuevo)
        ent_cat.grid(row=0, column=3, padx=5, pady=2)

        tk.Label(frame_nuevo, text="Talla:").grid(row=1, column=0, sticky="e")
        ent_talla = tk.Entry(frame_nuevo)
        ent_talla.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(frame_nuevo, text="Descripción:").grid(row=1, column=2, sticky="e")
        ent_desc = tk.Entry(frame_nuevo)
        ent_desc.grid(row=1, column=3, padx=5, pady=2)

        def limpiar_campos():
            ent_nombre.delete(0, tk.END)
            ent_cat.delete(0, tk.END)
            ent_talla.delete(0, tk.END)
            ent_desc.delete(0, tk.END)
            self.id_seleccionado = None
            btn_guardar.config(text="💾 Guardar Nuevo", bg="#98fb98")

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
            frame_nuevo, text="💾 Guardar Nuevo", command=guardar_cambios, bg="#98fb98"
        )
        btn_guardar.grid(row=0, column=4, padx=10, rowspan=2, sticky="nsew")
        tk.Button(frame_nuevo, text="Limpiar", command=limpiar_campos).grid(
            row=0, column=5, rowspan=2, sticky="nsew"
        )

        # --- SECCIÓN 2: TABLA ---
        frame_tabla = tk.LabelFrame(
            self.v_inv, text=" Inventario Actual ", padx=10, pady=10
        )
        frame_tabla.pack(fill="both", expand=True, padx=20, pady=10)

        columnas = ("id", "nombre", "categoria", "descripcion", "talla", "stock")
        tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        cabeceras = ["ID", "Nombre", "Categoría", "Descripción", "Talla", "Stock"]
        for col, head in zip(columnas, cabeceras):
            tabla.heading(col, text=head)
            tabla.column(col, width=100, anchor="center")
        tabla.pack(fill="both", expand=True)

        def actualizar_tabla():
            for item in tabla.get_children():
                tabla.delete(item)
            elementos = listar_epp_activos()
            from logic.inventory_logic import consultar_stock_actual

            for e in elementos:
                stock = consultar_stock_actual(e["id_epp"])
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
                )

        def al_seleccionar_fila(event):
            seleccion = tabla.selection()
            if not seleccion:
                return
            valores = tabla.item(seleccion[0])["values"]
            self.id_seleccionado = valores[0]
            ent_nombre.delete(0, tk.END)
            ent_nombre.insert(0, valores[1])
            ent_cat.delete(0, tk.END)
            ent_cat.insert(0, valores[2])
            ent_desc.delete(0, tk.END)
            ent_desc.insert(0, valores[3])
            ent_talla.delete(0, tk.END)
            ent_talla.insert(0, valores[4])
            btn_guardar.config(text="🔄 Actualizar Item", bg="#ffd700")

        tabla.bind("<<TreeviewSelect>>", al_seleccionar_fila)
        actualizar_tabla()

    def abrir_personal(self):
        if self.v_personal is not None and self.v_personal.winfo_exists():
            self.v_personal.lift()
            self.v_personal.focus_force()
            return

        self.v_personal = tk.Toplevel(self.root)

        ventana_pers = self.v_personal
        ventana_pers.title("Gestión de Personal (Trabajadores)")
        ventana_pers.geometry("850x550")

        self.id_emp_sel = None

        # --- FORMULARIO ---
        frame_form = tk.LabelFrame(
            ventana_pers, text=" Datos del Trabajador ", padx=10, pady=10
        )
        frame_form.pack(fill="x", padx=20, pady=10)

        fields = [
            ("Nombre:", 0, 0),
            ("Apellido:", 0, 2),
            ("Documento:", 1, 0),
            ("Cargo:", 1, 2),
            ("Área:", 2, 0),
        ]
        entries = {}
        for label, r, c in fields:
            tk.Label(frame_form, text=label).grid(row=r, column=c, sticky="e")
            en = tk.Entry(frame_form)
            en.grid(row=r, column=c + 1, padx=5, pady=2)
            entries[label] = en

        def limpiar_emp():
            for en in entries.values():
                en.delete(0, tk.END)
            self.id_emp_sel = None
            btn_save.config(text="👤 Registrar Nuevo", bg="#98fb98")

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

        btn_save = tk.Button(
            frame_form, text="👤 Registrar Nuevo", command=guardar_emp, bg="#98fb98"
        )
        btn_save.grid(row=0, column=4, rowspan=2, padx=10, sticky="nsew")

        # --- TABLA ACTIVOS ---
        tk.Label(
            ventana_pers, text="Personal Activo", font=("Arial", 10, "bold")
        ).pack()
        tabla_act = ttk.Treeview(
            ventana_pers,
            columns=("id", "nom", "ape", "doc", "car", "area"),
            show="headings",
            height=8,
        )
        for col, head in zip(
            ("id", "nom", "ape", "doc", "car", "area"),
            ("ID", "Nombre", "Apellido", "Doc", "Cargo", "Area"),
        ):
            tabla_act.heading(col, text=head)
            tabla_act.column(col, width=100)
        tabla_act.pack(fill="x", padx=20)

        # --- TABLA INACTIVOS ---
        tk.Label(
            ventana_pers,
            text="Personal Deshabilitado",
            font=("Arial", 10, "italic"),
            fg="gray",
        ).pack(pady=(10, 0))
        tabla_inac = ttk.Treeview(
            ventana_pers, columns=("id", "nom", "doc"), show="headings", height=4
        )
        for col, head in zip(("id", "nom", "doc"), ("ID", "Nombre", "Doc")):
            tabla_inac.heading(col, text=head)
            tabla_inac.column(col, width=100)
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
                            e["nombre"] + " " + e["apellido"],
                            e["documento"],
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
                entries.items(), [item[1], item[2], item[3], item[4], item[5]]
            ):
                en.delete(0, tk.END)
                en.insert(0, val)
            btn_save.config(text="🔄 Actualizar", bg="#ffd700")

        def sel_inac(event):
            seleccion = tabla_inac.selection()
            if not seleccion:
                return

            # Solo tomamos el ID para poder reactivarlo
            item = tabla_inac.item(seleccion[0])["values"]
            self.id_emp_sel = item[0]
            # Opcional: limpiar los campos de arriba para que no se confunda con una edición
            btn_save.config(text="👤 Registrar Nuevo", bg="#98fb98")

        # Botones de estado
        def toggle_estado(estado):
            if not self.id_emp_sel:
                return

            cambiar_estado_empleado(self.id_emp_sel, estado)
            limpiar_emp()
            actualizar_tablas_emp()

        frame_acc = tk.Frame(ventana_pers)
        frame_acc.pack(pady=5)
        tk.Button(
            frame_acc,
            text="🚫 Desactivar Seleccionado",
            command=lambda: toggle_estado("Inactivo"),
            bg="#ffcccb",
        ).pack(side="left", padx=5)
        tk.Button(
            frame_acc,
            text="✅ Re-Activar",
            command=lambda: toggle_estado("Activo"),
            bg="#ccffcc",
        ).pack(side="left", padx=5)

        tabla_act.bind("<<TreeviewSelect>>", sel_act)
        # Para reactivar desde la tabla de abajo
        tabla_inac.bind("<<TreeviewSelect>>", sel_inac)

        actualizar_tablas_emp()


class LoginVentana:
    def __init__(self, root):
        self.root = root
        self.root.title("Acceso al Sistema - UDEC")
        self.root.geometry("350x250")
        self.root.eval("tk::PlaceWindow . center")  # Centrar ventana

        tk.Label(root, text="🛡️ CONTROL DE ACCESO", font=("Arial", 14, "bold")).pack(
            pady=20
        )

        tk.Label(root, text="Usuario:").pack()
        self.ent_user = tk.Entry(root)
        self.ent_user.pack(pady=5)

        tk.Label(root, text="Contraseña:").pack()
        self.ent_pass = tk.Entry(root, show="*")  # Ocultar caracteres
        self.ent_pass.pack(pady=5)

        tk.Button(
            root,
            text="Entrar",
            command=self.intentar_login,
            bg="#4CAF50",
            fg="white",
            width=15,
        ).pack(pady=20)
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
            app = AppEPP(root_actual)
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")


if __name__ == "__main__":
    root = tk.Tk()
    login = LoginVentana(root)
    root.mainloop()
