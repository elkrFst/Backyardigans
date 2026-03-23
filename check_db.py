#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.mysql_face_storage import MySQLFaceStorage

def main():
    db = MySQLFaceStorage(host='localhost', user='root', password='', database='locker_scan')
    print("Usando SQLite fallback:", db.use_sqlite)
    print("\nUsuarios:")
    usuarios = db.listar_usuarios_detallados()
    for u in usuarios:
        print(f"  {u['id']}: {u['nombre_usuario']} ({u['rol']})")

    print("\nLockers:")
    lockers = db.listar_lockers()
    for l in lockers:
        print(f"  Locker {l['locker']}: {l['usuario'] or 'Libre'} ({l['estado']})")

    db.cerrar()

if __name__ == "__main__":
    main()