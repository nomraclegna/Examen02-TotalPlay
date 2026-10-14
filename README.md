# API REST - TotalPlay  

API REST desarrollada con **Python**, **FastAPI** y **Pydantic** para la gestión de clientes, administración de paquetes de internet, registro de servicios contratados y generación de reportes dinámicos.

---

## Integrantes del Equipo
- **Angel Emiliano Carmona Lozano - 2069119**
- **Luis Rolando Aguilar Ortiz - 2121179**
- **Lilian Valeria Ramos Avila - 2056778**

---

## Requisitos Previos
- **Python 3.10** o superior instalado.
- `pip` (gestor de paquetes de Python).

---

## Instalación y Configuración

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/nomraclegna/Examen02-TotalPlay.git
   cd NOMBRE-DEL-REPO
   ```

2. **Crear y activar un entorno virtual (opcional pero recomendado):**
   - En **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - En **macOS / Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Instalar las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```
   *(O bien directamente: `pip install fastapi uvicorn pydantic`)*

---

## Ejecución del Proyecto

Para iniciar el servidor de desarrollo con recarga automática, ejecuta en la terminal:

```bash
uvicorn EquipoTotalPlay:app --reload
```

El servidor se ejecutará en:
- **URL Base:** `http://127.0.0.1:8000/docs`

---

## Endpoints Disponibles

### 2. Clientes
| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `GET` | `/v1/api/clientes` | Consultar todos los clientes registrados |
| `POST` | `/v1/api/clientes` | Registrar un nuevo cliente |
| `PUT` | `/v1/api/clientes/{id_cliente}` | Actualizar la información de un cliente |
| `DELETE` | `/v1/api/clientes/{id_cliente}` | Desactivar un cliente (`active = False`) |

### 3. Servicios Contratados
| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `GET` | `/v1/api/servicios` | Consultar todos los servicios contratados |
| `POST` | `/v1/api/servicios` | Registrar un nuevo servicio (fecha automática o manual) |
| `PUT` | `/v1/api/servicios/{id_servicio}` | Actualizar un servicio existente (solo clientes activos) |

### 4. Reportes
| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `GET` | `/v1/api/reportes/servicios` | Reporte de servicios de clientes activos (filtrable por `fecha_inicio` y `fecha_fin`) |

### 5. Paquetes
| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `GET` | `/v1/api/paquetes` | Consultar los paquetes disponibles y sus costos actuales |
| `PUT` | `/v1/api/paquetes/{nombre_paquete}` | Actualizar el costo de un paquete (`basico`, `intermedio`, `premium`) |
