# logic/report_logic.py
import csv
import matplotlib.pyplot as plt
from database.connection import obtener_conexion
from matplotlib.ticker import MaxNLocator
import codecs


def obtener_datos_consumo_por_epp():
    """Consulta cuánto se ha entregado de cada producto en total."""
    query = """
        SELECT e.nombre_epp, SUM(d.cantidad) as total
        FROM Detalle_Entrega d
        JOIN Elemento_EPP e ON d.id_epp = e.id_epp
        GROUP BY e.nombre_epp
        ORDER BY total DESC
    """
    with obtener_conexion() as db:
        cursor = db.cursor()
        cursor.execute(query)
        return cursor.fetchall()


def generar_grafica_barras(datos):
    """
    Crea una gráfica de barras con los datos obtenidos.
    'datos' es una lista de filas de la DB.
    """
    if not datos:
        print("No hay datos para graficar.")
        return

    nombres = [fila["nombre_epp"] for fila in datos]
    totales = [fila["total"] for fila in datos]

    plt.figure(figsize=(10, 6))
    plt.bar(nombres, totales, color="teal")
    plt.title("Consumo Total de Elementos de Protección (EPP)")
    plt.xlabel("Elemento")
    plt.ylabel("Cantidad Entregada")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # De momento la mostramos en una ventana de Matplotlib
    # Luego la integraremos a Tkinter
    plt.show()


def obtener_historial_avanzado(nombre="", documento="", mes="", anio=""):
    """
    Construye una consulta SQL dinámica según los campos que el usuario llene.
    """
    query = """
        SELECT e.fecha_entrega, emp.nombre || ' ' || emp.apellido AS empleado, 
               el.nombre_epp, d.cantidad, e.observaciones, emp.documento
        FROM Entrega_EPP e
        JOIN Empleado emp ON e.id_empleado = emp.id_empleado
        JOIN Detalle_Entrega d ON e.id_entrega = d.id_entrega
        JOIN Elemento_EPP el ON d.id_epp = el.id_epp
        WHERE 1=1
    """
    params = []

if nombre:
        limpio = " ".join(nombre.split())
        query += " AND (emp.nombre || ' ' || emp.apellido LIKE ?)"
        params.append(f"%{limpio}%")

    if documento:
        query += " AND emp.documento LIKE ?"
        params.append(f"%{documento}%")

    if mes:
        # SQLite permite filtrar por mes usando strftime
        query += " AND strftime('%m', e.fecha_entrega) = ?"
        params.append(mes.zfill(2))  # Asegura que sea '01' en vez de '1'

    if anio:
        query += " AND strftime('%Y', e.fecha_entrega) = ?"
        params.append(anio)

    query += " ORDER BY e.fecha_entrega DESC"

    with obtener_conexion() as db:
        cursor = db.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def exportar_a_csv(datos, nombre_archivo="reporte_entregas.csv"):
    """Exporta los datos de la tabla de historial a un archivo CSV compatible con Excel."""
    try:
        with open(nombre_archivo, mode="w", newline="", encoding="latin-1") as f:
            # --- LA MEJORA DE BUENA PRÁCTICA ---
            f.write("sep=;\n")

            escritor = csv.writer(f, delimiter=";")

            # Cabeceras
            escritores_cabeceras = [
                "Fecha",
                "Documento",
                "Empleado",
                "Elemento",
                "Cantidad",
                "Observaciones",
            ]
            escritor.writerow(escritores_cabeceras)

            # Datos
            for d in datos:
                escritor.writerow(
                    [
                        d["fecha_entrega"],
                        d["documento"],
                        d["empleado"],
                        d["nombre_epp"],
                        d["cantidad"],
                        d["observaciones"],
                    ]
                )

        return True, f"Reporte guardado como {nombre_archivo}"
    except Exception as e:
        print(f"Error técnico en exportación: {e}")
        return (
            False,
            "Error al exportar: No se pudo escribir el archivo."
            "Verifique que no esté abierto en otro programa.",
        )


def obtener_top_empleados():
    """Consulta quiénes son los 5 empleados que más EPP han solicitado."""
    query = """
        SELECT emp.nombre || ' ' || emp.apellido AS empleado, SUM(d.cantidad) as total
        FROM Detalle_Entrega d
        JOIN Entrega_EPP e ON d.id_entrega = e.id_entrega
        JOIN Empleado emp ON e.id_empleado = emp.id_empleado
        GROUP BY empleado ORDER BY total DESC LIMIT 5
    """
    with obtener_conexion() as db:
        cursor = db.cursor()
        cursor.execute(query)
        return cursor.fetchall()


def generar_dashboard_visual():
    """Genera una ventana con dos gráficos comparativos."""
    from logic.report_logic import obtener_datos_consumo_por_epp  # La que ya tenías

    datos_epp = obtener_datos_consumo_por_epp()
    datos_emp = obtener_top_empleados()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Gráfico 1: Consumo por EPP
    nombres_epp = [d["nombre_epp"] for d in datos_epp]
    totales_epp = [d["total"] for d in datos_epp]
    ax1.bar(nombres_epp, totales_epp, color="skyblue")
    ax1.set_title("Consumo por Elemento")

    # --- PARA LOS ENTEROS ---
    ax1.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Gráfico 2: Top Empleados (Circular/Pie)
    nombres_emp = [d["empleado"] for d in datos_emp]
    totales_emp = [d["total"] for d in datos_emp]

    # Función para mostrar Cantidad + Porcentaje
    def fmt_valor(pct):
        total = sum(totales_emp)
        val = int(round(pct * total / 100.0))
        return f"{val}\n({pct:.1f}%)"

    ax2.pie(
        totales_emp,
        labels=nombres_emp,
        autopct=fmt_valor,
        startangle=140,
        colors=["#ff9999", "#66b3ff", "#99ff99", "#ffcc99", "#c2c2f0"],
        pctdistance=0.65,
    )  # Aleja un poco el texto del centro para que se vea mejor
    ax2.set_title("Top 5 Empleados (Cant. Total Solicitada)")

    plt.tight_layout()
    plt.show()
