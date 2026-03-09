import tkinter as tk
import random

class DinoGame:
    """Mini juego estilo dinosaurio de Chrome en un canvas pequeño."""
    def __init__(self, parent):
        self.canvas = tk.Canvas(parent, width=150, height=60, bg="black", highlightthickness=0)
        self.canvas.place(x=10, y=10)
        self.parent = parent
        self.dino = self.canvas.create_rectangle(10, 42, 25, 60, fill="white")
        self.obstacles = []
        self.gravity = 1.2
        self.vel_y = 0
        self.jumping = False
        parent.bind("<space>", self.jump)
        self._rand = random
        self.animate()

    def jump(self, event=None):
        if not self.jumping:
            self.vel_y = -15
            self.jumping = True

    def animate(self):
        # movimiento vertical del dino
        self.vel_y += self.gravity
        self.canvas.move(self.dino, 0, self.vel_y)
        coords = self.canvas.coords(self.dino)
        if coords[3] >= 60:
            self.canvas.move(self.dino, 0, 60 - coords[3])
            self.vel_y = 0
            self.jumping = False

        # generar obstáculos con probabilidad
        if not self.obstacles or self.canvas.coords(self.obstacles[-1])[0] < 120:
            if self._rand.random() < 0.03:
                obs = self.canvas.create_rectangle(150, 45, 160, 60, fill="green")
                self.obstacles.append(obs)

        # mover obstáculos y detectar colisiones
        for obs in list(self.obstacles):
            self.canvas.move(obs, -5, 0)
            x1, y1, x2, y2 = self.canvas.coords(obs)
            if x2 < 0:
                self.canvas.delete(obs)
                self.obstacles.remove(obs)
            else:
                if self._collision(self.canvas.bbox(self.dino), (x1, y1, x2, y2)):
                    # reiniciar juego
                    for o in self.obstacles:
                        self.canvas.delete(o)
                    self.obstacles.clear()
                    break
        self.canvas.after(50, self.animate)

    def _collision(self, box1, box2):
        if not box1 or not box2:
            return False
        x1, y1, x2, y2 = box1
        a1, b1, a2, b2 = box2
        return not (x2 < a1 or x1 > a2 or y2 < b1 or y1 > b2)
