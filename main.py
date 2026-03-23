#!/usr/bin/env python3
import sys
import os

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import App
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()