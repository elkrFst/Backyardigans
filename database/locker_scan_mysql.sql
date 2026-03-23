-- Script para crear la base de datos y tablas en MySQL/MariaDB (XAMPP)

CREATE DATABASE IF NOT EXISTS locker_scan;
USE locker_scan;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_usuario VARCHAR(50) UNIQUE NOT NULL,
    contraseña VARCHAR(255) NOT NULL,
    rol ENUM('usuario', 'administrador') NOT NULL
);

CREATE TABLE IF NOT EXISTS imagenes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    fecha_hora DATETIME NOT NULL,
    imagen LONGBLOB,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
