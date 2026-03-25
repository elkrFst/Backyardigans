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

        # Asegurar la tabla de accesos para registrar cada evento de apertura
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accesos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario_id INT NULL,
                nombre_usuario VARCHAR(50),
                estado ENUM('concedido','denegado','sin_rostro') NOT NULL,
                fecha_hora DATETIME NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
            """
        )
        self.conn.commit()

    def guardar_usuario(self, nombre_usuario, contraseña, rol='usuario'):
        # Evitar duplicados de nombre de usuario
        self.cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario=%s", (nombre_usuario,))
        if self.cursor.fetchone():
            raise ValueError(f"El usuario '{nombre_usuario}' ya existe")

        sql = "INSERT INTO usuarios (nombre_usuario, contraseña, rol) VALUES (%s, %s, %s)"
        self.cursor.execute(sql, (nombre_usuario, contraseña, rol))
        self.conn.commit()
        return self.cursor.lastrowid

    def guardar_imagen(self, usuario_id, imagen_bytes):
        # Usar NOW() del servidor MySQL para consistencia de zona horaria
        sql = "INSERT INTO imagenes (usuario_id, fecha_hora, imagen) VALUES (%s, NOW(), %s)"
        self.cursor.execute(sql, (usuario_id, imagen_bytes))
        self.conn.commit()
        return self.cursor.lastrowid

    def guardar_acceso(self, usuario_id, nombre_usuario, estado):
        # Usar NOW() del servidor MySQL para evitar desincronización de zonas horarias
        sql = "INSERT INTO accesos (usuario_id, nombre_usuario, estado, fecha_hora) VALUES (%s, %s, %s, NOW())"
        self.cursor.execute(sql, (usuario_id, nombre_usuario, estado))
        self.conn.commit()
        return self.cursor.lastrowid

    def obtener_usuario_por_nombre(self, nombre_usuario):
        self.cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario=%s", (nombre_usuario,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def contar_accesos_hoy(self):
        # Usar CURDATE() en servidor para tomar la fecha del propio MySQL
        sql = "SELECT COUNT(*) FROM accesos WHERE DATE(fecha_hora) = CURDATE()"
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]

    def contar_accesos_por_periodo(self, periodo):
        # Usar SQL puro para evitar desincronización de zonas horarias
        if periodo == 'dia':
            sql = "SELECT COUNT(*) FROM accesos WHERE DATE(fecha_hora) = CURDATE()"
        elif periodo == 'semana':
            sql = "SELECT COUNT(*) FROM accesos WHERE YEARWEEK(fecha_hora) = YEARWEEK(CURDATE())"
        elif periodo == 'mes':
            sql = "SELECT COUNT(*) FROM accesos WHERE YEAR(fecha_hora) = YEAR(CURDATE()) AND MONTH(fecha_hora) = MONTH(CURDATE())"
        elif periodo == 'anio':
            sql = "SELECT COUNT(*) FROM accesos WHERE YEAR(fecha_hora) = YEAR(CURDATE())"
        else:
            return 0

        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]

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

    def contar_usuarios_registrados_hoy(self):
        """Cuenta los usuarios que registraron imagen hoy."""
        sql = "SELECT COUNT(DISTINCT usuario_id) FROM imagenes WHERE DATE(fecha_hora) = CURDATE()"
        self.cursor.execute(sql)
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
