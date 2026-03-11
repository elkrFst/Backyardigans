import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, simpledialog
from gui.styles import colores, fuentes
from database.face_storage import FaceStorage
import os

class AdminWindow(tk.Toplevel):
    def __init__(self, parent, face_storage, callback_actualizar):
        super().__init__(parent)
        self.title("Administración de Rostros")
        self.geometry("400x300")
        self.configure(bg=colores["fondo"])
        self.face_storage = face_storage
        self.callback = callback_actualizar

        # Contraseña
        password = simpledialog.askstring("Contraseña", "Ingrese contraseña de administrador:", show='*', parent=self)
        if password != "Admin123":
            messagebox.showerror("Acceso denegado", "Contraseña incorrecta")
            self.destroy()
            return

        # Lista de rostros
        self.lista = tk.Listbox(self, font=fuentes["normal"], bg="white", selectmode=tk.SINGLE)
        self.lista.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.cargar_lista()

        # Botones
        frame_botones = ttk.Frame(self)
        frame_botones.pack(pady=5)

        ttk.Button(frame_botones, text="Agregar", command=self.agregar,
                   style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Eliminar", command=self.eliminar,
                   style='Secondary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Renombrar", command=self.renombrar,
                   style='Secondary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botones, text="Cerrar", command=self.destroy,
                   style='Secondary.TButton').pack(side=tk.LEFT, padx=5)

    def cargar_lista(self):
        self.lista.delete(0, tk.END)
        for nombre in self.face_storage.listar():
            self.lista.insert(tk.END, nombre)

    def agregar(self):
        # Aquí podrías abrir una ventana de captura de rostro con nombre
        # Por simplicidad, abrimos un diálogo para ingresar nombre y luego capturar
        nombre = simpledialog.askstring("Nuevo rostro", "Ingrese el nombre:", parent=self)
        if nombre:
            # Llamar a la función de registro (podría reutilizarse la de app)
            # Por ahora solo informamos que debe hacerse desde el menú principal
            messagebox.showinfo("Info", "Use la opción 'Registrar Locker' del menú principal para capturar el rostro.")
            # Alternativa: abrir cámara aquí mismo (más complejo)
        self.cargar_lista()
        self.callback()

    def eliminar(self):
        seleccion = self.lista.curselection()
        if not seleccion:
            messagebox.showwarning("Seleccione", "Debe seleccionar un rostro")
            return
        nombre = self.lista.get(seleccion[0])
        if messagebox.askyesno("Confirmar", f"¿Eliminar {nombre}?"):
            self.face_storage.eliminar(nombre)
            self.cargar_lista()
            self.callback()

    def renombrar(self):
        seleccion = self.lista.curselection()
        if not seleccion:
            messagebox.showwarning("Seleccione", "Debe seleccionar un rostro")
            return
        nombre_viejo = self.lista.get(seleccion[0])
        nombre_nuevo = simpledialog.askstring("Renombrar", "Nuevo nombre (sin extensión):", parent=self)
        if nombre_nuevo:
            # Asegurar extensión .jpg
            if not nombre_nuevo.endswith('.jpg'):
                nombre_nuevo += '.jpg'
            try:
                self.face_storage.renombrar(nombre_viejo, nombre_nuevo)
                self.cargar_lista()
                self.callback()
            except Exception as e:
                messagebox.showerror("Error", str(e))