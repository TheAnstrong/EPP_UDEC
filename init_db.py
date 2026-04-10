import sqlite3

# 1. Conectar (si el archivo 'epp.db' no existe, se crea solo)
conexion = sqlite3.connect('database/epp.db')
cursor = conexion.cursor()

# 2. Leer el archivo .sql
with open('database/epp.sql', 'r') as archivo_sql:
    sql_script = archivo_sql.read()

# 3. Ejecutar el código SQL
try:
    cursor.executescript(sql_script)
    print("¡Base de datos creada y script ejecutado con éxito!")
except sqlite3.Error as e:
    print(f"Hubo un error: {e}")

# 4. Guardar y cerrar
conexion.commit()
conexion.close()