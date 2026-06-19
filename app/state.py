from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Remito


class EstadoRemito(str, Enum):
    CREADO = "creado"
    EN_PRODUCCION = "en_produccion"
    PREPARANDO = "preparando"
    LISTO_ENTREGAR = "listo_entregar"
    EN_ENTREGA = "en_entrega"
    FACTURADO = "facturado"


class EstadoRemitoFilter(str, Enum):
    PENDIENTE = "Pendiente"
    EN_PREPARACION = "En Preparacion"
    LISTO_PARA_ENTREGA = "Listo Para Entrega"
    EN_CAMINO = "En Camino"
    ENTREGADO = "Entregado"


VALID_TRANSITIONS: dict[EstadoRemito, EstadoRemito] = {
    EstadoRemito.CREADO: EstadoRemito.EN_PRODUCCION,
    EstadoRemito.EN_PRODUCCION: EstadoRemito.PREPARANDO,
    EstadoRemito.PREPARANDO: EstadoRemito.LISTO_ENTREGAR,
    EstadoRemito.LISTO_ENTREGAR: EstadoRemito.EN_ENTREGA,
    EstadoRemito.EN_ENTREGA: EstadoRemito.FACTURADO,
}

STATE_TIMESTAMP_MAP: dict[EstadoRemito, str] = {
    EstadoRemito.EN_PRODUCCION: "fecha_preparacion",
    EstadoRemito.PREPARANDO: "fecha_listo",
    EstadoRemito.LISTO_ENTREGAR: "fecha_despacho",
    EstadoRemito.EN_ENTREGA: "fecha_recibido",
    EstadoRemito.FACTURADO: "fecha_facturacion",
}


def derive_estado(remito: "Remito") -> EstadoRemito:
    if remito.fecha_facturacion is not None:
        return EstadoRemito.FACTURADO
    if remito.fecha_recibido is not None:
        return EstadoRemito.EN_ENTREGA
    if remito.fecha_despacho is not None:
        return EstadoRemito.LISTO_ENTREGAR
    if remito.fecha_listo is not None:
        return EstadoRemito.PREPARANDO
    if remito.fecha_preparacion is not None:
        return EstadoRemito.EN_PRODUCCION
    return EstadoRemito.CREADO
