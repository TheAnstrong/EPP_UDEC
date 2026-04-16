# logic/delivery_logic.py
from database.connection import obtener_conexion

def registrar_entrega_completa(id_empleado, id_usuario, lista_productos, observaciones=""):
    """
    Registra una entrega de varios EPP a un empleado.
    lista_productos debe ser una lista de tuplas: [(id_epp, cantidad), ...]
    """
    if not lista_productos:
        return False, "No hay productos seleccionados para entregar."

    try:
        with obtener_conexion() as db:
            cursor = db.cursor()
            # --- PASO 1: VALIDAR STOCK TOTAL ANTES DE EMPEZAR ---
            for id_epp, cantidad in lista_productos:
                cursor.execute("""
                    SELECT i.cantidad_disponible, e.nombre_epp
                    FROM Inventario i
                    JOIN Elemento_EPP e ON i.id_epp = e.id_epp
                    WHERE i.id_epp = ?""", (id_epp,))
                res = cursor.fetchone()
                if not res:
                    return False, "Producto no encontrado."
                if res['cantidad_disponible'] < cantidad:
                    # Ahora devolvemos el NOMBRE en lugar del ID
                    return False, f"Stock insuficiente para: {res['nombre_epp']}. (Disponible: {res['cantidad_disponible']})"

            # --- PASO 2: CREAR CABECERA DE ENTREGA ---
            query_cabecera = """
                INSERT INTO Entrega_EPP (id_empleado, id_usuario, fecha_entrega, observaciones)
                VALUES (?, ?, date('now'), ?)
            """
            cursor.execute(query_cabecera, (id_empleado, id_usuario, observaciones))
            id_entrega = cursor.lastrowid

            # --- PASO 3 Y 4: DETALLE Y ACTUALIZACIÓN DE STOCK ---
            for id_epp, cantidad in lista_productos:
                # Insertar detalle
                query_detalle = "INSERT INTO Detalle_Entrega (id_entrega, id_epp, cantidad) VALUES (?, ?, ?)"
                cursor.execute(query_detalle, (id_entrega, id_epp, cantidad))
                
                # Restar del inventario
                query_update_stock = """
                    UPDATE Inventario 
                    SET cantidad_disponible = cantidad_disponible - ?, 
                        fecha_actualizacion = date('now')
                    WHERE id_epp = ?
                """
                cursor.execute(query_update_stock, (cantidad, id_epp))

            return True, "Entrega registrada y stock actualizado correctamente."

    except Exception as e:
        # El context manager 'with' hará el rollback automáticamente si hay error
        return False, f"Error crítico en la transacción: {e}"