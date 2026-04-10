# logic/epp_logic.py
import sqlite3
from database.connection import obtener_conexion


def registrar_nuevo_epp(nombre, descripcion, categoria, talla):
    """
    Registra un EPP en el catálogo y le crea su inventario inicial en 0.
    """
    if not nombre or not categoria:
        return False, "El nombre y la categoría son obligatorios."

    try:
        with obtener_conexion() as db:
            cursor = db.cursor()

            # 1. Insertar en Elemento_EPP
            # Usamos 'Activo' por defecto como quedamos
            query_epp = """
                INSERT INTO Elemento_EPP (nombre_epp, descripcion, categoria, talla, estado)
                VALUES (?, ?, ?, ?, 'Activo')
            """
            cursor.execute(query_epp, (nombre, descripcion, categoria, talla))

            # Obtener el ID generado para este nuevo elemento
            nuevo_id = cursor.lastrowid

            # 2. Insertar automáticamente en Inventario (La "cascada")
            # Esto evita que la tabla inventario esté "suelta"
            query_inv = """
                INSERT INTO Inventario (id_epp, cantidad_disponible, fecha_actualizacion)
                VALUES (?, 0, date('now'))
            """
            cursor.execute(query_inv, (nuevo_id,))

            return True, f"Elemento '{nombre}' registrado con éxito."

    except sqlite3.IntegrityError:
        return (
            False,
            "Error: Este elemento ya podría existir o hay un problema de integridad.",
        )
    except Exception as e:
        return False, f"Error inesperado: {e}"


def listar_epp_activos():
    """Trae solo los elementos que no han sido desactivados."""
    with obtener_conexion() as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM Elemento_EPP WHERE estado = 'Activo'")
        return cursor.fetchall()


def desactivar_epp(id_epp):
    """Borrado lógico: cambia el estado a 'Inactivo'."""
    try:
        with obtener_conexion() as db:
            cursor = db.cursor()
            cursor.execute(
                "UPDATE Elemento_EPP SET estado = 'Inactivo' WHERE id_epp = ?",
                (id_epp,),
            )
            return True, "Elemento desactivado correctamente."
    except Exception as e:
        return False, f"No se pudo desactivar: {e}"


def actualizar_epp(id_epp, nombre, descripcion, categoria, talla):
    """Actualiza los datos de un elemento existente."""
    try:
        with obtener_conexion() as db:
            cursor = db.cursor()
            query = """
                UPDATE Elemento_EPP 
                SET nombre_epp = ?, descripcion = ?, categoria = ?, talla = ?
                WHERE id_epp = ?
            """
            cursor.execute(query, (nombre, descripcion, categoria, talla, id_epp))
            return True, "Elemento actualizado correctamente."
    except Exception as e:
        return False, f"Error al actualizar: {e}"
