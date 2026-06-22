from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator
from .state import EstadoRemito, derive_estado


# ─── Cliente ───────────────────────────────────────────────────────────────────

class ClienteBase(BaseModel):
    idcliente: int
    nom1: Optional[str] = None
    nom2: Optional[str] = None
    cuit: Optional[str] = None
    direccion: Optional[str] = None
    localidad: Optional[str] = None
    provincia: Optional[str] = None
    tel1: Optional[str] = None
    celular: Optional[str] = None
    email1: Optional[str] = None
    personacontacto: Optional[str] = None
    activo: Optional[int] = None


class ClienteSchema(ClienteBase):
    model_config = ConfigDict(from_attributes=True)


# ─── Producto ──────────────────────────────────────────────────────────────────

class ProductoBase(BaseModel):
    id: int
    codigo: str
    nombre: str
    precio_actual: float
    unidad_medida: str
    categoria: str
    is_producto: bool
    habilitado: bool
    prioridad: int


class ProductoSchema(ProductoBase):
    model_config = ConfigDict(from_attributes=True)


# ─── RemitoDetalle ─────────────────────────────────────────────────────────────

class RemitoDetalleCreate(BaseModel):
    producto_id: int
    cantidad: int
    observaciones: Optional[str] = None


class RemitoDetalleSchema(BaseModel):
    id: int
    producto_id: int
    cantidad: int
    entregado: Optional[int] = None
    observaciones: Optional[str] = None
    producto: Optional[ProductoSchema] = None

    model_config = ConfigDict(from_attributes=True)


# ─── Remito ────────────────────────────────────────────────────────────────────

class RemitoCreate(BaseModel):
    vendedor: str
    observaciones: Optional[str] = None
    fecha_entrega: datetime
    cliente_id: int
    detalles: list[RemitoDetalleCreate]


class RemitoUpdate(BaseModel):
    vendedor: Optional[str] = None
    observaciones: Optional[str] = None
    fecha_entrega: Optional[datetime] = None
    detalles: Optional[list[RemitoDetalleCreate]] = None


class EstadoTransitionRequest(BaseModel):
    nuevo_estado: EstadoRemito


class RemitoSummarySchema(BaseModel):
    id: int
    vendedor: str
    observaciones: Optional[str] = None
    fecha_carga: datetime
    fecha_entrega: datetime
    fecha_preparacion: Optional[datetime] = None
    fecha_listo: Optional[datetime] = None
    fecha_despacho: Optional[datetime] = None
    fecha_recibido: Optional[datetime] = None
    fecha_facturacion: Optional[datetime] = None
    cliente_id: int
    estado: EstadoRemito = EstadoRemito.CREADO
    cliente: Optional[ClienteSchema] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def compute_estado(self) -> "RemitoSummarySchema":
        if self.fecha_facturacion is not None:
            self.estado = EstadoRemito.FACTURADO
        elif self.fecha_recibido is not None:
            self.estado = EstadoRemito.EN_ENTREGA
        elif self.fecha_despacho is not None:
            self.estado = EstadoRemito.LISTO_ENTREGAR
        elif self.fecha_listo is not None:
            self.estado = EstadoRemito.PREPARANDO
        elif self.fecha_preparacion is not None:
            self.estado = EstadoRemito.EN_PRODUCCION
        else:
            self.estado = EstadoRemito.CREADO
        return self


class RemitoDetailSchema(RemitoSummarySchema):
    detalles: list[RemitoDetalleSchema] = []


# ─── Reports ───────────────────────────────────────────────────────────────────

class PendientesPorDiaSchema(BaseModel):
    fecha: str
    total_remitos: int
    total_pendientes: int
    total_en_preparacion: int
    total_listo_para_entrega: int
    total_en_camino: int
    total_entregados: int
    remitos: list[RemitoSummarySchema]


class ProductoPendienteSchema(BaseModel):
    fecha: str
    producto_id: int
    codigo: str
    nombre: str
    unidad_medida: str
    cantidad_pendiente: int


class ProductoItemSchema(BaseModel):
    producto: str
    cantidad: int


class ResponsableProductosSchema(BaseModel):
    responsable: str
    productos: list[ProductoItemSchema]


class ProductosPendientesPorDiaSchema(BaseModel):
    fecha: str
    responsables: list[ResponsableProductosSchema]
