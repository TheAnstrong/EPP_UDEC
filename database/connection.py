import sqlite3
import shutil
import os
import sys
from datetime import datetime
from contextlib import contextmanager
import glob

# Este truco detecta si el programa es un .exe o un script de Python
if getattr(sys, "frozen", False):
    # Si es un ejecutable, la carpeta base es donde está el .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Si es código normal, la carpeta base es la carpeta del proyecto
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join("database", "epp.db")


@contextmanager
def obtener_conexion():
    """
    Gestiona la conexión de forma segura.
    Asegura que se cierre siempre, incluso si hay errores.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        # ACTIVAR LLAVES FORÁNEAS (Vital para que no se corrompa la lógica)
        conn.execute("PRAGMA foreign_keys = ON;")
        # Para que los resultados sean diccionarios y no tuplas raras
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error en la base de datos: {e}")
        raise e
    finally:
        conn.close()


def realizar_backup_inteligente():
    """Crea un backup diario y mantiene solo los últimos 7."""
    if not os.path.exists("backups"):
        os.makedirs("backups")

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    origen = "database/epp.db"
    destino = f"backups/backup_{fecha_hoy}.db"

    # 1. Verificar si ya se hizo el backup de hoy
    if os.path.exists(destino):
        return  # Ya estamos respaldados por hoy, no hacemos nada

    try:
        if os.path.exists(origen):
            shutil.copy2(origen, destino)

            # 2. Limpieza: Mantener solo los últimos 7 archivos
            listado_backups = sorted(glob.glob("backups/backup_*.db"))
            while len(listado_backups) > 7:
                archivo_viejo = listado_backups.pop(0)
                os.remove(archivo_viejo)

            print(f"💾 Backup de hoy ({fecha_hoy}) generado y limpieza realizada.")
    except Exception as e:
        print(f"⚠️ Error en backup: {e}")
