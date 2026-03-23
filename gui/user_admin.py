import tkinter as tk
import tkinter.ttk as ttk
from tkinter import simpledialog, messagebox
from gui.styles import colores, fuentes
from database.mysql_face_storage import MySQLFaceStorage


class UserAdminWindow(tk.Toplevel):
    def __init__(self, parent, db_config=None):
        super().__init__(parent)
        self.title("Administración de Usuarios")
        self.geometry("500x350")
        self.configure(bg=colores["fondo"])

        # Conectar almacenamiento (usar configuración por defecto si no se pasa)
        cfg = db_config or {}
        self.storage = MySQLFaceStorage(**cfg)

        # Solicitar credenciales de administrador
        usuario = simpledialog.askstring("Usuario", "Usuario administrador:", parent=self)
        contraseña = simpledialog.askstring("Contraseña", "Contraseña:", show='*', parent=self)
        if not usuario or not contraseña:
            messagebox.showerror("Acceso denegado", "Credenciales requeridas")
            self.destroy()
            return

        auth = None
        try:
            auth = self.storage.autenticar_usuario(usuario, contraseña)
        except Exception as e:
            messagebox.showerror("Error", f"Error al autenticar: {e}")
            self.destroy()
            return

        if not auth or auth.get('rol') not in ('administrador', 'admin'):
            messagebox.showerror("Acceso denegado", "Credenciales inválidas o no es administrador")
            self.destroy()
            return

        # Contenido: lista y botones
        self.lista = tk.Listbox(self, font=fuentes['normal'], bg='white')
        self.lista.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        frame = ttk.Frame(self)
        frame.pack(pady=5)
        ttk.Button(frame, text="Refrescar", command=self.cargar_lista, style='Small.TButton').pack(side='left', padx=4)
        ttk.Button(frame, text="Agregar", command=self.agregar, style='Primary.TButton').pack(side='left', padx=4)
        ttk.Button(frame, text="Eliminar", command=self.eliminar, style='Secondary.TButton').pack(side='left', padx=4)
        ttk.Button(frame, text="Cerrar", command=self.destroy, style='Secondary.TButton').pack(side='left', padx=4)

        self.cargar_lista()

    def cargar_lista(self):
        try:
            usuarios = self.storage.listar_usuarios_detallados()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo listar usuarios: {e}")
            usuarios = []
        self.lista.delete(0, tk.END)
        for u in usuarios:
            self.lista.insert(tk.END, f"{u['nombre_usuario']}  ({u['rol']})")

    def agregar(self):
        nombre = simpledialog.askstring("Nuevo usuario", "Nombre de usuario:", parent=self)
        if not nombre:
            return
        contraseña = simpledialog.askstring("Contraseña", "Contraseña:", show='*', parent=self)
        if contraseña is None:
            return
        rol = simpledialog.askstring("Rol", "Rol (administrador/usuario):", initialvalue='usuario', parent=self)
        if not rol:
            rol = 'usuario'
        try:
            uid = self.storage.guardar_usuario(nombre, contraseña, rol)
            messagebox.showinfo("Creado", f"Usuario creado con id {uid}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear usuario: {e}")
        self.cargar_lista()

    def eliminar(self):
        sel = self.lista.curselection()
        if not sel:
            messagebox.showwarning("Seleccione", "Seleccione un usuario para eliminar")
            return
        texto = self.lista.get(sel[0])
        nombre = texto.split()[0]
        if messagebox.askyesno("Confirmar", f"¿Eliminar usuario {nombre}?"):
            try:
                filas = self.storage.eliminar_usuario(nombre)
                if filas:
                    messagebox.showinfo("Eliminado", f"Usuario {nombre} eliminado")
                else:
                    messagebox.showwarning("No encontrado", "Usuario no encontrado o ya eliminado")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar: {e}")
            self.cargar_lista()
