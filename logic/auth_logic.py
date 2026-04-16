# logic/auth_logic.py
import hashlib
from database.connection import obtener_conexion

def encriptar_contrasena(contrasena):
    """Convierte una cadena de texto en un hash SHA-256."""
    return hashlib.sha256(contrasena.encode()).hexdigest()

def verificar_credenciales(usuario, contrasena):
    """
    Verifica las credenciales comparando el hash de la contraseña ingresada
    con el hash almacenado en la base de datos.
    """
    # Encriptamos la contraseña que ingresó el usuario para poder compararla
    pass_encriptada = encriptar_contrasena(contrasena)
    query = "SELECT id_usuario, nombre FROM Usuario WHERE nombre = ? AND contrasena = ?"

    with obtener_conexion() as db:
        cursor = db.cursor()
        cursor.execute(query, (usuario, pass_encriptada))
        resultado = cursor.fetchone()

        if resultado:
            return True, resultado["id_usuario"], resultado["nombre"]
        return False, None, None

# Anti SQL Injection
# Cuando usamos un '?' en una consulta se ve como [ WHERE id_epp = ____ ]
# Lo que hace que el dato llegue como [ 5 ] y no como 5

# Lo cual evita que hagan una conulta tipo:
# WHERE usuario = 'admin' AND password = '' OR 1=1'
# Lo cual haria que la base muestre todos los datos

# Sino como:
# WHERE usuario = 'admin' AND password = ['' OR 1=1']
