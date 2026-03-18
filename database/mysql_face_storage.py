import mysql.connector
from mysql.connector import Error
from datetime import datetime

class MySQLFaceStorage:
    def __init__(self, host='localhost', user='root', password='', database='backyardigans_db'):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.conn.cursor()

    def guardar_usuario(self, nombre_usuario, contraseña, rol='usuario'):
        sql = "INSERT INTO usuarios (nombre_usuario, contraseña, rol) VALUES (%s, %s, %s)"
        self.cursor.execute(sql, (nombre_usuario, contraseña, rol))
        self.conn.commit()
        return self.cursor.lastrowid

    def guardar_imagen(self, usuario_id, imagen_bytes):
        sql = "INSERT INTO imagenes (usuario_id, fecha_hora, imagen) VALUES (%s, %s, %s)"
        fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(sql, (usuario_id, fecha_hora, imagen_bytes))
        self.conn.commit()
        return self.cursor.lastrowid

    def listar(self):
        """Devuelve una lista de nombres de usuario existentes en la base de datos."""
        self.cursor.execute("SELECT nombre_usuario FROM usuarios")
        return [row[0] for row in self.cursor.fetchall()]

    def listar_usuarios_detallados(self):
        """Devuelve lista de diccionarios con id, nombre_usuario y rol."""
        self.cursor.execute("SELECT id, nombre_usuario, rol FROM usuarios")
        return [{'id': row[0], 'nombre_usuario': row[1], 'rol': row[2]} for row in self.cursor.fetchall()]

    def autenticar_usuario(self, nombre_usuario, contraseña):
        """Autentica y devuelve el usuario si coincide nombre y contraseña."""
        sql = "SELECT id, nombre_usuario, rol FROM usuarios WHERE nombre_usuario=%s AND contraseña=%s"
        self.cursor.execute(sql, (nombre_usuario, contraseña))
        row = self.cursor.fetchone()
        if row:
            return {'id': row[0], 'nombre_usuario': row[1], 'rol': row[2]}
        return None

    def eliminar_usuario(self, nombre_usuario):
        """Elimina un usuario por nombre de usuario. Devuelve número de filas afectadas."""
        sql = "DELETE FROM usuarios WHERE nombre_usuario=%s"
        self.cursor.execute(sql, (nombre_usuario,))
        self.conn.commit()
        return self.cursor.rowcount

    def cerrar(self):
        self.cursor.close()
        self.conn.close()

# Ejemplo de uso:
# storage = MySQLFaceStorage(password='tu_password')
# usuario_id = storage.guardar_usuario('admin', '1234', 'administrador')
# with open('foto.jpg', 'rb') as f:
#     imagen_bytes = f.read()
# storage.guardar_imagen(usuario_id, imagen_bytes)
# storage.cerrar()
