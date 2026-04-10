# logic/employee_logic.py
import sqlite3
from database.connection import obtener_conexion


def registrar_empleado(nombre, apellido, documento, cargo, area, fecha_ingreso):
    """
    Registra un nuevo trabajador en el sistema.
    """
    if not nombre or not apellido or not documento:
        return False, "Nombre, Apellido y Documento son obligatorios."

    try:
        with obtener_conexion() as db:
            cursor = db.cursor()

            query = """
                INSERT INTO Empleado (nombre, apellido, documento, cargo, area, fecha_ingreso, estado)
                VALUES (?, ?, ?, ?, ?, ?, 'Activo')
            """
            cursor.execute(
                query, (nombre, apellido, documento, cargo, area, fecha_ingreso)
            )
            return True, f"Empleado {nombre} {apellido} registrado con éxito."

    except sqlite3.IntegrityError:
        return False, "Error: Ya existe un empleado con ese número de documento."
    except Exception as e:
        return False, f"Error inesperado: {e}"


def listar_empleados_activos():
    """Trae la lista de trabajadores vigentes para asignarles EPP."""
    with obtener_conexion() as db:
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM Empleado WHERE estado = 'Activo' ORDER BY apellido ASC"
        )
        return cursor.fetchall()


def desactivar_empleado(id_empleado):
    """Cambia el estado del empleado a Inactivo (Baja laboral)."""
    try:
        with obtener_conexion() as db:
            cursor = db.cursor()
            cursor.execute(
                "UPDATE Empleado SET estado = 'Inactivo' WHERE id_empleado = ?",
                (id_empleado,),
            )
            return True, "Empleado desactivado correctamente."
    except Exception as e:
        return False, f"Error al desactivar: {e}"


def actualizar_empleado(id_empleado, nombre, apellido, documento, cargo, area):
    """Actualiza los datos básicos del trabajador."""
    try:
        with obtener_conexion() as db:
            cursor = db.cursor()
            query = """
                UPDATE Empleado 
                SET nombre = ?, apellido = ?, documento = ?, cargo = ?, area = ?
                WHERE id_empleado = ?
            """
            cursor.execute(
                query, (nombre, apellido, documento, cargo, area, id_empleado)
            )
            return True, "Datos actualizados correctamente."
    except Exception as e:
        return False, f"Error al actualizar: {e}"


def cambiar_estado_empleado(id_empleado, nuevo_estado):
    """Activa o desactiva a un empleado."""
    try:
        with obtener_conexion() as db:
            cursor = db.cursor()
            cursor.execute(
                "UPDATE Empleado SET estado = ? WHERE id_empleado = ?",
                (nuevo_estado, id_empleado),
            )
            return True, f"Empleado marcado como {nuevo_estado}."
    except Exception as e:
        return False, f"Error: {e}"
