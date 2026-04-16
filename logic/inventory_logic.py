# logic/inventory_logic.py
from database.connection import obtener_conexion


def cargar_stock_epp(id_epp, cantidad_a_sumar):
    """
    Suma una cantidad al stock existente de un elemento.
    Se usa cuando llega un pedido nuevo de implementos.
    """
    if cantidad_a_sumar <= 0:
        return False, "La cantidad debe ser mayor a 0."

    try:
        with obtener_conexion() as db:
            cursor = db.cursor()

            # 1. Actualizamos la cantidad sumando a la actual
            # Usamos date('now') para la fecha_actualizacion
            query = """
                UPDATE Inventario 
                SET cantidad_disponible = cantidad_disponible + ?, 
                    fecha_actualizacion = date('now')
                WHERE id_epp = ?
            """
            cursor.execute(query, (cantidad_a_sumar, id_epp))

            if cursor.rowcount == 0:
                return False, "No se encontró el registro de inventario para este EPP."

            return True, f"Se cargaron {cantidad_a_sumar} unidades con éxito."

    except Exception as e:
        return False, f"Error al cargar stock: {e}"


def consultar_stock_actual(id_epp):
    """Devuelve la cantidad disponible de un elemento específico."""
    with obtener_conexion() as db:
        cursor = db.cursor()
        cursor.execute(
            "SELECT cantidad_disponible FROM Inventario WHERE id_epp = ?", (id_epp,)
        )
        resultado = cursor.fetchone()
        return resultado["cantidad_disponible"] if resultado else 0


def obtener_stock_critico(limite):
    """Retorna los productos que tienen menos unidades que el límite."""
    query = """
        SELECT e.nombre_epp, i.cantidad_disponible 
        FROM Inventario i 
        JOIN Elemento_EPP e ON i.id_epp = e.id_epp 
        WHERE i.cantidad_disponible <= ?
    """
    with obtener_conexion() as db:
        cursor = db.cursor()
        cursor.execute(query, (limite,))
        return cursor.fetchall()
