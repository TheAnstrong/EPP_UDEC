# logic/auth_logic.py
from database.connection import obtener_conexion


def verificar_credenciales(usuario, contrasena):
    """
    Busca al usuario en la DB y verifica que la contraseña sea correcta.
    """
    query = "SELECT id_usuario, nombre FROM Usuario WHERE nombre = ? AND contrasena = ?"

    with obtener_conexion() as db:
        cursor = db.cursor()
        cursor.execute(query, (usuario, contrasena))
        resultado = cursor.fetchone()

        if resultado:
            return True, resultado["id_usuario"], resultado["nombre"]
        return False, None, None
