from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date

app = FastAPI(
    title="API REST - TotalPlay",
    description="Gestión de clientes, paquetes y consumo de servicios de internet",
    version="1.0.0"
)

clientes = []
consumos = []

paquetes = {
    "basico": 400.00,
    "intermedio": 500.00,
    "premium": 600.00
}


@app.exception_handler(HTTPException)
def manejar_errores_http(request: Request, exc: HTTPException):
    mensaje = f"Error: {exc.detail}"
    print(mensaje)
    return PlainTextResponse(content=mensaje, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
def manejar_errores_pydantic(request: Request, exc: RequestValidationError):
    error = exc.errors()[0]
    campo = error["loc"][-1]
    tipo = error["type"]

    if "json" in tipo:
        mensaje = (
            "Error: Formato inválido. Si intentaste escribir letras en un campo numérico "
            "(como costo o ID), recuerda que solo se aceptan números."
        )
    elif "missing" in tipo:
        mensaje = f"Error: El campo '{campo}' es obligatorio y no fue enviado."
    elif campo == "costo":
        if "gt" in tipo or "ge" in tipo or "greater" in tipo:
            mensaje = "Error: El precio del paquete no puede ser negativo ni cero."
        else:
            mensaje = "Error: El precio del paquete es inválido. Solo se aceptan números válidos (no letras ni vacíos)."
    elif campo in ("id_cliente", "id_servicio"):
        if "gt" in tipo or "ge" in tipo or "greater" in tipo:
            mensaje = f"Error: El '{campo}' no puede ser negativo ni cero (debe ser mayor a 0)."
        else:
            mensaje = f"Error: El '{campo}' es inválido. Solo se aceptan números enteros (no letras ni vacíos)."
    elif campo in ("fecha_registro", "fecha_inicio", "fecha_fin"):
        mensaje = f"Error: La fecha en '{campo}' no es válida. Usa el formato YYYY-MM-DD (ej. 2026-10-13)."
    elif campo == "active":
        mensaje = "Error: El campo 'active' solo acepta valores booleanos (true o false)."
    else:
        mensaje = f"Error: El valor ingresado en el campo '{campo}' no es válido."

    print(mensaje)
    return PlainTextResponse(content=mensaje, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


def limpiar_y_validar_nombre(valor: str) -> str:
    nombre_limpio = " ".join(valor.split())

    if not nombre_limpio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre del cliente no puede estar vacío."
        )

    if len(nombre_limpio) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre del cliente debe contener al menos 2 letras."
        )

    if not nombre_limpio.replace(" ", "").isalpha():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre del cliente solo puede contener letras y espacios (sin números ni símbolos)."
        )

    return nombre_limpio.title()


def limpiar_y_validar_direccion(valor: str) -> str:
    direccion_limpia = " ".join(valor.split())

    if not direccion_limpia:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La dirección del cliente no puede estar vacía."
        )

    if len(direccion_limpia) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La dirección debe tener al menos 5 caracteres válidos."
        )

    if not any(caracter.isalpha() for caracter in direccion_limpia):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La dirección debe contener el nombre de la calle o colonia (letras)."
        )

    return direccion_limpia.title()


def limpiar_y_validar_paquete(valor: str) -> str:
    paquete_normalizado = (
        valor.strip()
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )

    if not paquete_normalizado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre del paquete no puede estar vacío."
        )

    if paquete_normalizado not in paquetes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El paquete '{valor}' no es válido. Los paquetes disponibles son: basico, intermedio, premium."
        )

    return paquete_normalizado


def limpiar_y_validar_fecha(valor: Optional[str], generar_actual_si_vacio: bool = True) -> Optional[str]:
    if valor is None or valor.strip() == "" or valor.strip().lower() == "string":
        if generar_actual_si_vacio:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return None

    texto = valor.strip().replace("T", " ").replace("Z", "")
    if "." in texto:
        texto = texto.split(".")[0]

    for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            fecha_obj = datetime.strptime(texto, formato)
            if formato == "%Y-%m-%d":
                ahora = datetime.now()
                fecha_obj = fecha_obj.replace(hour=ahora.hour, minute=ahora.minute, second=ahora.second)
            return fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Formato de fecha inválido. Usa 'YYYY-MM-DD HH:MM:SS' (ej. 2026-10-13 14:30:00) o 'YYYY-MM-DD'."
    )


class ClienteCreate(BaseModel):
    nombre_cliente: str = Field(..., example="Juan Carlos Pérez", description="Nombre completo del cliente (solo letras)")
    direccion: str = Field(..., example="Av. Universidad 500", description="Dirección del domicilio del cliente")
    active: bool = Field(default=True, example=True, description="Estado inicial del cliente (True = activo)")

class ClienteUpdate(BaseModel):
    nombre_cliente: Optional[str] = Field(default=None, example="Juan Carlos Pérez", description="Nuevo nombre del cliente (opcional)")
    direccion: Optional[str] = Field(default=None, example="Calle Hidalgo 120", description="Nueva dirección del cliente (opcional)")
    active: Optional[bool] = Field(default=None, example=True, description="Permite reactivar o cambiar el estado del cliente")

class ServicioCreate(BaseModel):
    id_cliente: int = Field(..., gt=0, example=1, description="ID del cliente que contrata el servicio")
    paquete: str = Field(
        ...,
        example="basico",
        description="Paquete válido: basico, intermedio o premium (acepta mayúsculas y acentos)"
    )
    fecha_registro: Optional[str] = Field(
        default=None,
        example="2026-10-13 14:30:00",
        description="Fecha y hora opcional (YYYY-MM-DD HH:MM:SS o YYYY-MM-DD). Si se deja vacío o null, usa la fecha y hora actual."
    )

class ServicioUpdate(BaseModel):
    paquete: str = Field(
        ...,
        example="premium",
        description="Nuevo paquete válido: basico, intermedio o premium (acepta mayúsculas y acentos)"
    )
    fecha_registro: Optional[str] = Field(
        default=None,
        example="2026-10-13 16:00:00",
        description="Nueva fecha y hora opcional (YYYY-MM-DD HH:MM:SS o YYYY-MM-DD). Si se deja vacío o null, conserva la que ya tenía."
    )

class PaqueteUpdate(BaseModel):
    costo: float = Field(..., gt=0, example=550.00, description="Nuevo costo del paquete (debe ser mayor a 0)")


def obtener_cliente_por_id(id_cliente: int):
    for cliente in clientes:
        if cliente["id_cliente"] == id_cliente:
            return cliente
    return None

def obtener_servicio_por_id(id_servicio: int):
    for servicio in consumos:
        if servicio["id_servicio"] == id_servicio:
            return servicio
    return None

def obtener_servicio_por_cliente(id_cliente: int):
    for servicio in consumos:
        if servicio["id_cliente"] == id_cliente:
            return servicio
    return None


@app.get("/v1/api/clientes", status_code=status.HTTP_200_OK, tags=["2. Clientes"])
def consultar_clientes():
    return {
        "success": True,
        "total_clientes": len(clientes),
        "clientes": clientes
    }

@app.post("/v1/api/clientes", status_code=status.HTTP_201_CREATED, tags=["2. Clientes"])
def registrar_cliente(datos: ClienteCreate):
    nombre_formateado = limpiar_y_validar_nombre(datos.nombre_cliente)
    direccion_formateada = limpiar_y_validar_direccion(datos.direccion)

    for c in clientes:
        if c["nombre_cliente"] == nombre_formateado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El cliente '{nombre_formateado}' ya se encuentra registrado con el ID {c['id_cliente']}."
            )

    nuevo_cliente = {
        "id_cliente": len(clientes) + 1,
        "nombre_cliente": nombre_formateado,
        "direccion": direccion_formateada,
        "active": datos.active
    }
    clientes.append(nuevo_cliente)

    return {
        "success": True,
        "mensaje": "Cliente registrado exitosamente.",
        "cliente": nuevo_cliente
    }

@app.put("/v1/api/clientes/{id_cliente}", status_code=status.HTTP_200_OK, tags=["2. Clientes"])
def actualizar_cliente(id_cliente: int, datos: ClienteUpdate):
    if id_cliente <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ID del cliente no puede ser negativo ni cero."
        )

    cliente = obtener_cliente_por_id(id_cliente)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El cliente con ID {id_cliente} no existe."
        )

    if datos.nombre_cliente is None and datos.direccion is None and datos.active is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes enviar al menos un dato para actualizar (nombre_cliente, direccion o active)."
        )

    if datos.nombre_cliente is not None:
        nuevo_nombre = limpiar_y_validar_nombre(datos.nombre_cliente)
        for c in clientes:
            if c["nombre_cliente"] == nuevo_nombre and c["id_cliente"] != id_cliente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe otro cliente registrado con el nombre '{nuevo_nombre}'."
                )
        cliente["nombre_cliente"] = nuevo_nombre

    if datos.direccion is not None:
        cliente["direccion"] = limpiar_y_validar_direccion(datos.direccion)

    if datos.active is not None:
        cliente["active"] = datos.active

    return {
        "success": True,
        "mensaje": "Información del cliente actualizada.",
        "cliente": cliente
    }

@app.delete("/v1/api/clientes/{id_cliente}", status_code=status.HTTP_200_OK, tags=["2. Clientes"])
def desactivar_cliente(id_cliente: int):
    if id_cliente <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ID del cliente no puede ser negativo ni cero."
        )

    cliente = obtener_cliente_por_id(id_cliente)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El cliente con ID {id_cliente} no existe."
        )

    if not cliente["active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El cliente con ID {id_cliente} ya se encontraba desactivado."
        )

    cliente["active"] = False

    return {
        "success": True,
        "mensaje": f"El cliente con ID {id_cliente} ha sido desactivado (active = False).",
        "cliente": cliente
    }


@app.post("/v1/api/servicios", status_code=status.HTTP_201_CREATED, tags=["3. Servicios Contratados"])
def registrar_servicio(datos: ServicioCreate):
    cliente = obtener_cliente_por_id(datos.id_cliente)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el cliente con ID {datos.id_cliente}."
        )

    if not cliente["active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El cliente con ID {datos.id_cliente} está inactivo y no puede contratar servicios."
        )

    servicio_existente = obtener_servicio_por_cliente(datos.id_cliente)
    if servicio_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El cliente con ID {datos.id_cliente} ya tiene un servicio contratado "
                f"(id_servicio: {servicio_existente['id_servicio']}, paquete: '{servicio_existente['paquete']}'). "
                f"Solo puede modificarse mediante PUT /v1/api/servicios/{servicio_existente['id_servicio']}."
            )
        )

    paquete_validado = limpiar_y_validar_paquete(datos.paquete)

    fecha_limpia = limpiar_y_validar_fecha(datos.fecha_registro, generar_actual_si_vacio=True)

    nuevo_servicio = {
        "id_servicio": len(consumos) + 1,
        "id_cliente": datos.id_cliente,
        "paquete": paquete_validado,
        "fecha_registro": fecha_limpia
    }
    consumos.append(nuevo_servicio)

    return {
        "success": True,
        "mensaje": "Servicio registrado exitosamente.",
        "servicio": nuevo_servicio
    }

@app.get("/v1/api/servicios", status_code=status.HTTP_200_OK, tags=["3. Servicios Contratados"])
def consultar_servicios():
    return {
        "success": True,
        "total_servicios": len(consumos),
        "servicios": consumos
    }

@app.put("/v1/api/servicios/{id_servicio}", status_code=status.HTTP_200_OK, tags=["3. Servicios Contratados"])
def actualizar_servicio(id_servicio: int, datos: ServicioUpdate):
    if id_servicio <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ID del servicio no puede ser negativo ni cero."
        )

    servicio = obtener_servicio_por_id(id_servicio)
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El servicio con ID {id_servicio} no existe."
        )

    cliente = obtener_cliente_por_id(servicio["id_cliente"])
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El cliente asociado (ID {servicio['id_cliente']}) no existe."
        )

    if not cliente["active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede actualizar este servicio porque el cliente se encuentra inactivo."
        )

    paquete_validado = limpiar_y_validar_paquete(datos.paquete)

    nueva_fecha = limpiar_y_validar_fecha(datos.fecha_registro, generar_actual_si_vacio=False)

    servicio["paquete"] = paquete_validado
    if nueva_fecha is not None:
        servicio["fecha_registro"] = nueva_fecha

    return {
        "success": True,
        "mensaje": "Servicio actualizado correctamente.",
        "servicio": servicio
    }


@app.get("/v1/api/reportes/servicios", status_code=status.HTTP_200_OK, tags=["4. Reportes"])
def generar_reporte_servicios(
    fecha_inicio: Optional[date] = Query(default=None, description="Fecha inicial (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(default=None, description="Fecha final (YYYY-MM-DD)")
):
    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha_inicio no puede ser posterior a la fecha_fin."
        )

    reporte_detallado = []

    for servicio in consumos:
        cliente = obtener_cliente_por_id(servicio["id_cliente"])

        if not cliente or not cliente["active"]:
            continue

        fecha_del_servicio = datetime.strptime(servicio["fecha_registro"], "%Y-%m-%d %H:%M:%S").date()

        if fecha_inicio and fecha_del_servicio < fecha_inicio:
            continue
        if fecha_fin and fecha_del_servicio > fecha_fin:
            continue

        nombre_paquete = servicio["paquete"]
        costo_actual = paquetes.get(nombre_paquete, 0.0)

        reporte_detallado.append({
            "id_servicio": servicio["id_servicio"],
            "paquete": nombre_paquete,
            "fecha_registro": servicio["fecha_registro"],
            "costo_paquete": costo_actual,
            "cliente": {
                "id_cliente": cliente["id_cliente"],
                "nombre_cliente": cliente["nombre_cliente"],
                "direccion": cliente["direccion"],
                "active": cliente["active"]
            }
        })

    return {
        "success": True,
        "total_registros": len(reporte_detallado),
        "filtros": {
            "fecha_inicio": fecha_inicio.strftime("%Y-%m-%d") if fecha_inicio else None,
            "fecha_fin": fecha_fin.strftime("%Y-%m-%d") if fecha_fin else None
        },
        "reporte": reporte_detallado
    }


@app.get("/v1/api/paquetes", status_code=status.HTTP_200_OK, tags=["5. Paquetes"])
def consultar_paquetes():
    return {
        "success": True,
        "paquetes": paquetes
    }

@app.put("/v1/api/paquetes/{nombre_paquete}", status_code=status.HTTP_200_OK, tags=["5. Paquetes"])
def actualizar_costo_paquete(
    nombre_paquete: str,
    datos: PaqueteUpdate
):
    paquete_validado = limpiar_y_validar_paquete(nombre_paquete)

    costo_anterior = paquetes[paquete_validado]
    paquetes[paquete_validado] = round(datos.costo, 2)

    return {
        "success": True,
        "mensaje": f"El costo del paquete '{paquete_validado}' se actualizó correctamente.",
        "paquete": paquete_validado,
        "costo_anterior": costo_anterior,
        "costo_nuevo": paquetes[paquete_validado]
    }