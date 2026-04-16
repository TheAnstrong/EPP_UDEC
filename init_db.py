import sqlite3
from logic.auth_logic import encriptar_contrasena

# 1. Conectar (si el archivo 'epp.db' no existe, se crea solo)
conexion = sqlite3.connect('database/epp.db')
cursor = conexion.cursor()

# 2. Leer el archivo .sql
with open('database/epp.sql', 'r') as archivo_sql:
    sql_script = archivo_sql.read()

# 3. Registrar Admin
def ejecutar_registro():
    db_name = "database/epp.db"  # Recuerda usar la carpeta si ya la tienes

    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Encriptamos la contraseña '123456' antes de meterla a la lista
        pass_final = encriptar_contrasena("123456")

        # Estructura: id, nombre, email, pass_hash, nombre_usuario, estado
        datos_usuario = [
            (1, "administrador", "admin@epp.com", pass_final, "admin", "activo")
        ]

        cursor.executemany(
            "INSERT OR REPLACE INTO Usuario VALUES (?,?,?,?,?,?)", datos_usuario
        )

        conn.commit()
        print("✅ Éxito: Usuario admin creado con contraseña protegida (Hash).")

    except sqlite3.Error as e:
        print(f"❌ Error al insertar datos: {e}")
    finally:
        if conn:
            conn.close()

# 4. Ejecutar SQL
try:
    cursor.executescript(sql_script)
    print("¡Base de datos creada y script ejecutado con éxito!")
    ejecutar_registro()
except sqlite3.Error as e:
    print(f"Hubo un error: {e}")