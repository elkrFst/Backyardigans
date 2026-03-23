import os
from datetime import datetime

try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ModuleNotFoundError:
    import sqlite3
    MYSQL_AVAILABLE = False
    print("[MySQLFaceStorage] mysql-connector-python no está instalado; se usará SQLite como respaldo.")

class MySQLFaceStorage:
    def __init__(self, host='localhost', user='root', password='', database='locker_scan'):
        self.use_sqlite = not MYSQL_AVAILABLE
        if self.use_sqlite:
            self.db_path = os.path.join(os.path.dirname(__file__), 'locker_scan.db')
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._setup_sqlite()
        else:
            self.conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            self.cursor = self.conn.cursor()
            self._setup_mysql()

    def _setup_mysql(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre_usuario VARCHAR(50) UNIQUE NOT NULL,
                contraseña VARCHAR(255) NOT NULL,
                rol ENUM('usuario', 'administrador') NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS imagenes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario_id INT NOT NULL,
                fecha_hora DATETIME NOT NULL,
                imagen LONGBLOB,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS lockers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                locker_num INT UNIQUE NOT NULL,
                usuario_id INT UNIQUE,
                asignado_en DATETIME,
                estado ENUM('libre','ocupado') NOT NULL DEFAULT 'libre',
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
            )
        """)
        for n in range(1, 5):
            self.cursor.execute("INSERT IGNORE INTO lockers (locker_num, estado) VALUES (%s, 'libre')", (n,))
        self.conn.commit()

    def _setup_sqlite(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_usuario TEXT UNIQUE NOT NULL,
                contraseña TEXT NOT NULL,
                rol TEXT CHECK(rol IN ('usuario','administrador')) NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS imagenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                fecha_hora TEXT NOT NULL,
                imagen BLOB,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS lockers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                locker_num INTEGER UNIQUE NOT NULL,
                usuario_id INTEGER UNIQUE,
                asignado_en TEXT,
                estado TEXT CHECK(estado IN ('libre','ocupado')) NOT NULL DEFAULT 'libre',
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
            )
        """)
        for n in range(1, 5):
            self.cursor.execute("INSERT OR IGNORE INTO lockers (locker_num, estado) VALUES (?, 'libre')", (n,))
        self.conn.commit()


    def guardar_usuario(self, nombre_usuario, contraseña, rol='usuario'):
        if self.use_sqlite:
            sql = "INSERT INTO usuarios (nombre_usuario, contraseña, rol) VALUES (?, ?, ?)"
        else:
            sql = "INSERT INTO usuarios (nombre_usuario, contraseña, rol) VALUES (%s, %s, %s)"
        self.cursor.execute(sql, (nombre_usuario, contraseña, rol))
        self.conn.commit()
        return self.cursor.lastrowid

    def guardar_imagen(self, usuario_id, imagen_bytes):
        if self.use_sqlite:
            sql = "INSERT INTO imagenes (usuario_id, fecha_hora, imagen) VALUES (?, ?, ?)"
        else:
            sql = "INSERT INTO imagenes (usuario_id, fecha_hora, imagen) VALUES (%s, %s, %s)"
        fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(sql, (usuario_id, fecha_hora, imagen_bytes))
        self.conn.commit()
        return self.cursor.lastrowid

    def listar(self):
        """Devuelve una lista de nombres de usuario existentes en la base de datos."""
        self.cursor.execute("SELECT nombre_usuario FROM usuarios")
        return [row[0] for row in self.cursor.fetchall()]

    def listar_lockers(self):
        self.cursor.execute(
            "SELECT l.locker_num, u.nombre_usuario, l.estado FROM lockers l LEFT JOIN usuarios u ON l.usuario_id=u.id ORDER BY l.locker_num"
        )
        return [{'locker': r[0], 'usuario': r[1] if r[1] else None, 'estado': r[2]} for r in self.cursor.fetchall()]

    def locker_disponible(self):
        self.cursor.execute("SELECT locker_num FROM lockers WHERE estado='libre' ORDER BY locker_num LIMIT 1")
        row = self.cursor.fetchone()
        return row[0] if row else None

    def asignar_locker(self, usuario_id, locker_num):
        if self.use_sqlite:
            self.cursor.execute("UPDATE lockers SET usuario_id=?, estado='ocupado', asignado_en=? WHERE locker_num=?", (usuario_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), locker_num))
            if self.cursor.rowcount == 0:
                self.cursor.execute("INSERT INTO lockers (locker_num, usuario_id, estado, asignado_en) VALUES (?, ?, 'ocupado', ?)", (locker_num, usuario_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        else:
            self.cursor.execute("UPDATE lockers SET usuario_id=%s, estado='ocupado', asignado_en=NOW() WHERE locker_num=%s", (usuario_id, locker_num))
            if self.cursor.rowcount == 0:
                self.cursor.execute("INSERT INTO lockers (locker_num, usuario_id, estado, asignado_en) VALUES (%s, %s, 'ocupado', NOW())", (locker_num, usuario_id))
        self.conn.commit()

    def liberar_locker(self, locker_num):
        if self.use_sqlite:
            self.cursor.execute("UPDATE lockers SET usuario_id=NULL, estado='libre', asignado_en=NULL WHERE locker_num=?", (locker_num,))
        else:
            self.cursor.execute("UPDATE lockers SET usuario_id=NULL, estado='libre', asignado_en=NULL WHERE locker_num=%s", (locker_num,))
        self.conn.commit()

    def obtener_usuario_por_nombre(self, nombre_usuario):
        if self.use_sqlite:
            self.cursor.execute("SELECT id, nombre_usuario, rol FROM usuarios WHERE nombre_usuario=?", (nombre_usuario,))
        else:
            self.cursor.execute("SELECT id, nombre_usuario, rol FROM usuarios WHERE nombre_usuario=%s", (nombre_usuario,))
        row = self.cursor.fetchone()
        if row:
            return {'id': row[0], 'nombre_usuario': row[1], 'rol': row[2]}
        return None

    def obtener_imagen_por_usuario(self, usuario_id):
        query = "SELECT imagen FROM imagenes WHERE usuario_id=? ORDER BY fecha_hora DESC LIMIT 1" if self.use_sqlite else "SELECT imagen FROM imagenes WHERE usuario_id=%s ORDER BY fecha_hora DESC LIMIT 1"
        self.cursor.execute(query, (usuario_id,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def obtener_locker_por_usuario_id(self, usuario_id):
        if self.use_sqlite:
            self.cursor.execute("SELECT locker_num FROM lockers WHERE usuario_id=? AND estado='ocupado'", (usuario_id,))
        else:
            self.cursor.execute("SELECT locker_num FROM lockers WHERE usuario_id=%s AND estado='ocupado'", (usuario_id,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def renombrar_usuario(self, nombre_viejo, nombre_nuevo):
        if self.use_sqlite:
            self.cursor.execute("UPDATE usuarios SET nombre_usuario=? WHERE nombre_usuario=?", (nombre_nuevo, nombre_viejo))
        else:
            self.cursor.execute("UPDATE usuarios SET nombre_usuario=%s WHERE nombre_usuario=%s", (nombre_nuevo, nombre_viejo))
        if self.cursor.rowcount == 0:
            raise ValueError("Usuario no encontrado")
        self.conn.commit()

    def listar_usuarios_detallados(self):
        self.cursor.execute("SELECT id, nombre_usuario, rol FROM usuarios")
        return [{'id': row[0], 'nombre_usuario': row[1], 'rol': row[2]} for row in self.cursor.fetchall()]

    def autenticar_usuario(self, nombre_usuario, contraseña):
        if self.use_sqlite:
            sql = "SELECT id, nombre_usuario, rol FROM usuarios WHERE nombre_usuario=? AND contraseña=?"
        else:
            sql = "SELECT id, nombre_usuario, rol FROM usuarios WHERE nombre_usuario=%s AND contraseña=%s"
        self.cursor.execute(sql, (nombre_usuario, contraseña))
        row = self.cursor.fetchone()
        if row:
            return {'id': row[0], 'nombre_usuario': row[1], 'rol': row[2]}
        return None

    def eliminar_usuario(self, nombre_usuario):
        sql = "DELETE FROM usuarios WHERE nombre_usuario=?" if self.use_sqlite else "DELETE FROM usuarios WHERE nombre_usuario=%s"
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
