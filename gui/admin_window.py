import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, simpledialog
from gui.styles import colores, fuentes
from database.mysql_face_storage import MySQLFaceStorage
from PIL import Image, ImageTk
import io
import os
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

class AdminWindow(tk.Toplevel):
    def __init__(self, parent, db_storage, callback_actualizar):
        super().__init__(parent)
        self.title("Administración")
        self.geometry("600x400")
        self.configure(bg=colores["fondo"])
        self.storage = db_storage
        self.callback = callback_actualizar

        # Notebook para tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab Usuarios
        self.frame_usuarios = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_usuarios, text="Usuarios")

        self.lista_usuarios = tk.Listbox(self.frame_usuarios, font=fuentes["normal"], bg="white", selectmode=tk.SINGLE)
        self.lista_usuarios.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.lista_usuarios.bind('<Double-Button-1>', self.on_usuario_doble_click)

        frame_botones_usuarios = ttk.Frame(self.frame_usuarios)
        frame_botones_usuarios.pack(pady=5)

        ttk.Button(frame_botones_usuarios, text="Agregar usuario", command=self.agregar_usuario,
                   style='Primary.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(frame_botones_usuarios, text="Agregar admin", command=self.agregar_admin,
                   style='Primary.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(frame_botones_usuarios, text="Eliminar", command=self.eliminar_usuario,
                   style='Secondary.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(frame_botones_usuarios, text="Renombrar", command=self.renombrar_usuario,
                   style='Secondary.TButton').pack(side=tk.LEFT, padx=4)

        # Tab Lockers
        self.frame_lockers = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_lockers, text="Lockers")

        self.lista_lockers = tk.Listbox(self.frame_lockers, font=fuentes["normal"], bg="white", selectmode=tk.SINGLE)
        self.lista_lockers.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.lista_lockers.bind('<Double-Button-1>', self.on_locker_doble_click)

        frame_botones_lockers = ttk.Frame(self.frame_lockers)
        frame_botones_lockers.pack(pady=5)

        ttk.Button(frame_botones_lockers, text="Liberar locker", command=self.liberar_locker,
                   style='Secondary.TButton').pack(side=tk.LEFT, padx=4)

        ttk.Button(self, text="Cerrar", command=self.destroy,
                   style='Secondary.TButton').pack(pady=5)

        self.usuarios = []
        self.lockers = []
        self.cargar_usuarios()
        self.cargar_lockers()

    def cargar_usuarios(self):
        self.lista_usuarios.delete(0, tk.END)
        self.usuarios = self.storage.listar_usuarios_detallados()
        for u in self.usuarios:
            self.lista_usuarios.insert(tk.END, f"{u['nombre_usuario']} ({u['rol']})")

    def cargar_lockers(self):
        self.lista_lockers.delete(0, tk.END)
        self.lockers = self.storage.listar_lockers()
        for l in self.lockers:
            usuario = l['usuario'] if l['usuario'] else "Libre"
            self.lista_lockers.insert(tk.END, f"Locker {l['locker']} - {usuario} ({l['estado']})")

    def agregar_usuario(self):
        nombre = simpledialog.askstring("Agregar usuario", "Nombre de usuario:", parent=self)
        if not nombre:
            return
        contraseña = simpledialog.askstring("Agregar usuario", "Contraseña:", show='*', parent=self)
        if contraseña is None:
            return
        try:
            self.storage.guardar_usuario(nombre, contraseña, 'usuario')
            messagebox.showinfo("Usuario creado", f"Usuario {nombre} creado con éxito")
            self.cargar_usuarios()
            self.callback()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear usuario: {e}")

    def eliminar_usuario(self):
        seleccion = self.lista_usuarios.curselection()
        if not seleccion:
            messagebox.showwarning("Seleccione", "Debe seleccionar un usuario")
            return
        idx = seleccion[0]
        usuario = self.usuarios[idx]
        if messagebox.askyesno("Confirmar", f"¿Eliminar usuario {usuario['nombre_usuario']}?"):
            self.storage.eliminar_usuario(usuario['nombre_usuario'])
            self.cargar_usuarios()
            self.cargar_lockers()
            self.callback()

    def liberar_locker(self):
        seleccion = self.lista_lockers.curselection()
        if not seleccion:
            messagebox.showwarning("Seleccione", "Debe seleccionar un locker")
            return
        idx = seleccion[0]
        locker = self.lockers[idx]
        if locker['estado'] == 'libre':
            messagebox.showinfo("Ya libre", "El locker ya está libre")
            return
        if messagebox.askyesno("Confirmar", f"¿Liberar locker {locker['locker']}?"):
            self.storage.liberar_locker(locker['locker'])
            self.cargar_lockers()
            self.callback()

    def on_locker_doble_click(self, event):
        seleccion = self.lista_lockers.curselection()
        if not seleccion:
            return
        idx = seleccion[0]
        locker = self.lockers[idx]
        if locker['usuario']:
            usuario = self.storage.obtener_usuario_por_nombre(locker['usuario'])
            if usuario:
                imagen_bytes = self.storage.obtener_imagen_por_usuario(usuario['id'])
                if imagen_bytes:
                    top = tk.Toplevel(self)
                    top.title(f"Foto de {locker['usuario']} - Locker {locker['locker']}")
                    top.geometry('360x360')

                    imagen = Image.open(io.BytesIO(imagen_bytes))
                    imagen.thumbnail((340, 340), Image.ANTIALIAS)
                    foto = ImageTk.PhotoImage(imagen)
                    label = tk.Label(top, image=foto)
                    label.image = foto
                    label.pack(padx=10, pady=10)
                else:
                    messagebox.showinfo("Imagen", "No hay foto asociada para este usuario")
            else:
                messagebox.showinfo("Usuario", "Usuario no encontrado")
        else:
            messagebox.showinfo("Locker libre", "Este locker está libre")

    def agregar_admin(self):
        nombre = simpledialog.askstring("Nuevo admin", "Nombre de usuario:", parent=self)
        if not nombre:
            return
        contraseña = simpledialog.askstring("Nuevo admin", "Contraseña:", show='*', parent=self)
        if not contraseña:
            return
        try:
            self.storage.guardar_usuario(nombre, contraseña, 'administrador')
            messagebox.showinfo("Admin agregado", f"Administrador {nombre} creado")
            self.cargar_usuarios()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def renombrar_usuario(self):
        seleccion = self.lista_usuarios.curselection()
        if not seleccion:
            messagebox.showwarning("Seleccione", "Debe seleccionar un usuario")
            return
        idx = seleccion[0]
        usuario = self.usuarios[idx]
        nombre_nuevo = simpledialog.askstring("Renombrar", "Nuevo nombre de usuario:", parent=self)
        if not nombre_nuevo:
            return
        try:
            self.storage.renombrar_usuario(usuario['nombre_usuario'], nombre_nuevo)
            self.cargar_usuarios()
            self.cargar_lockers()
            self.callback()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_usuario_doble_click(self, event):
        seleccion = self.lista_usuarios.curselection()
        if not seleccion:
            return
        idx = seleccion[0]
        usuario = self.usuarios[idx]
        imagen_bytes = self.storage.obtener_imagen_por_usuario(usuario['id'])
        if not imagen_bytes:
            messagebox.showinfo("Imagen", "No hay foto asociada para este usuario")
            return

        top = tk.Toplevel(self)
        top.title(f"Foto de {usuario['nombre_usuario']}")
        top.geometry('360x360')

        imagen = Image.open(io.BytesIO(imagen_bytes))
        imagen.thumbnail((340, 340), Image.ANTIALIAS)
        foto = ImageTk.PhotoImage(imagen)
        label = tk.Label(top, image=foto)
        label.image = foto
        label.pack(padx=10, pady=10)