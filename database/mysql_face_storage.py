import mysql.connector
from mysql.connector import Error
from datetime import datetime, timezone, timedelta

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
        fecha_hora = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
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
        # Primero obtener el ID del usuario
        self.cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario=%s", (nombre_usuario,))
        row = self.cursor.fetchone()
        if not row:
            return 0
        usuario_id = row[0]
        
        # Eliminar imágenes asociadas
        self.cursor.execute("DELETE FROM imagenes WHERE usuario_id=%s", (usuario_id,))
        
        # Eliminar usuario
        sql = "DELETE FROM usuarios WHERE nombre_usuario=%s"
        self.cursor.execute(sql, (nombre_usuario,))
        self.conn.commit()
        return self.cursor.rowcount

    def contar_usuarios_registrados(self):
        """Cuenta el total de usuarios registrados."""
        self.cursor.execute("SELECT COUNT(*) FROM usuarios")
        return self.cursor.fetchone()[0]

    def contar_accesos_hoy(self):
        """Cuenta los accesos de hoy (imágenes guardadas hoy)."""
        hoy = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        sql = "SELECT COUNT(*) FROM imagenes WHERE DATE(fecha_hora) = %s"
        self.cursor.execute(sql, (hoy,))
        return self.cursor.fetchone()[0]

    def contar_usuarios_registrados_hoy(self):
        """Cuenta los usuarios que registraron imagen hoy."""
        hoy = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        sql = "SELECT COUNT(DISTINCT usuario_id) FROM imagenes WHERE DATE(fecha_hora) = %s"
        self.cursor.execute(sql, (hoy,))
        return self.cursor.fetchone()[0]

    def contar_registros_por_periodo(self, periodo):
        """Cuenta registros por periodo: 'dia', 'semana', 'mes', 'anio'."""
        ahora = datetime.now(timezone.utc)
        if periodo == 'dia':
            fecha_inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        elif periodo == 'semana':
            fecha_inicio = ahora - timedelta(days=ahora.weekday())
            fecha_inicio = fecha_inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        elif periodo == 'mes':
            fecha_inicio = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif periodo == 'anio':
            fecha_inicio = ahora.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return 0
        
        sql = "SELECT COUNT(*) FROM imagenes WHERE fecha_hora >= %s"
        self.cursor.execute(sql, (fecha_inicio,))
        return self.cursor.fetchone()[0]

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
