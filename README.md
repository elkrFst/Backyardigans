# Smart Locker - Sistema de Reconocimiento Facial

Control de acceso a **4 lockers fijos** usando reconocimiento facial.

## Estructura

```
main.py           - Punto de entrada
config.py         - Configuración centralizada
core.py           - Lógica: Base de datos, Reconocimiento, Cámara
ui.py             - Interfaz gráfica (Tkinter)
requirements.txt  - Dependencias
rostros/         - Almacena rostros (máximo 4)
```

## Funcionalidades

- ✅ **4 Lockers fijos** (locker1, locker2, locker3, locker4)
- ✅ **Registro automático** - Asigna al primer locker libre (solo usuarios normales)
- ✅ **Reconocimiento facial** - Abre locker específico
- ✅ **Admin panel** - Liberar/asignar lockers específicos (admins no consumen lockers)
- ✅ **Máximo 4 rostros** - Un rostro por locker (solo para usuarios normales)
- ✅ **Separación de roles** - Admins gestionan el sistema sin ocupar lockers

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

### Flujo de Uso

1. **Admin Login**: Los administradores acceden al panel de control sin ocupar lockers
2. **Registrar Usuario**: Presiona "Registrar Nuevo Locker" → Se asigna automáticamente al primer locker libre (solo usuarios normales)
3. **Acceder**: Presiona "Abrir Locker" → Se reconoce el rostro y abre el locker correspondiente
4. **Admin Panel**: Panel de administración para liberar/asignar lockers específicos

## Configuración

Edita `config.py` para:
- Credenciales MySQL
- Resolución de cámara
- Índice de cámara (0 = integrada)
- Umbral de similitud de rostros

## Características

- ✅ Reconocimiento facial con face_recognition
- ✅ Base de datos MySQL
- ✅ Admin panel para gestión de usuarios
- ✅ Control de lockers (libre/ocupado)
- ✅ Registro de accesos
- ✅ Interfaz limpia y moderna

