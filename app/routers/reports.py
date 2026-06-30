from collections import defaultdict
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text

from ..database import get_db
from ..models import Remito, RemitoDetalle
from ..schemas import (
    PendientesPorDiaSchema,
    ProductoItemSchema,
    ProductoPendienteSchema,
    ProductosPendientesPorDiaSchema,
    ResponsableProductosSchema,
    RemitoSummarySchema,
)
from ..state import EstadoRemito

router = APIRouter(prefix="/reports", tags=["reports"])

PENDIENTES_FILTER = "fecha_facturacion IS NULL AND fecha_recibido IS NULL"


@router.get(
    "/pendientes-entrega",
    response_model=list[RemitoSummarySchema],
    summary="Remitos pendientes de entrega",
    description="Returns all remitos that have not been received or invoiced yet, ordered by delivery date.",
)
def pendientes_entrega(db: Session = Depends(get_db)):
    remitos = (
        db.query(Remito)
        .options(joinedload(Remito.cliente))
        .filter(Remito.fecha_facturacion.is_(None))
        .order_by(Remito.fecha_entrega.asc())
        .all()
    )
    return [RemitoSummarySchema.model_validate(r) for r in remitos]


@router.get(
    "/pendientes-por-dia",
    response_model=list[PendientesPorDiaSchema],
    summary="Remitos pendientes agrupados por día de entrega",
    description="Returns pending remitos grouped by their scheduled delivery date.",
)
def pendientes_por_dia(
    fecha_desde: Optional[datetime] = Query(None, description="Filter by fecha_entrega >= fecha_desde"),
    fecha_hasta: Optional[datetime] = Query(None, description="Filter by fecha_entrega <= fecha_hasta"),
    db: Session = Depends(get_db),
):
    query = db.query(Remito).options(joinedload(Remito.cliente))
    query = query.filter(Remito.fecha_facturacion.is_(None))
    if fecha_desde:
        query = query.filter(Remito.fecha_entrega >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Remito.fecha_entrega <= fecha_hasta)
    remitos = query.order_by(Remito.fecha_entrega.asc()).all()

    grouped: dict[str, list[RemitoSummarySchema]] = defaultdict(list)
    for r in remitos:
        fecha_key = r.fecha_entrega.strftime("%Y-%m-%d")
        grouped[fecha_key].append(RemitoSummarySchema.model_validate(r))

    result = []
    for fecha, items in sorted(grouped.items()):
        total_pendientes = 0
        total_en_preparacion = 0
        total_listo_para_entrega = 0
        total_en_camino = 0
        total_entregados = 0

        for remito in items:
            if remito.estado == EstadoRemito.CREADO:
                total_pendientes += 1
            elif remito.estado in {EstadoRemito.EN_PRODUCCION, EstadoRemito.PREPARANDO}:
                total_en_preparacion += 1
            elif remito.estado == EstadoRemito.LISTO_ENTREGAR:
                total_listo_para_entrega += 1
            elif remito.estado == EstadoRemito.EN_ENTREGA:
                total_en_camino += 1
            elif remito.estado == EstadoRemito.FACTURADO:
                total_entregados += 1

        result.append(
            PendientesPorDiaSchema(
                fecha=fecha,
                total_remitos=len(items),
                total_pendientes=total_pendientes,
                total_en_preparacion=total_en_preparacion,
                total_listo_para_entrega=total_listo_para_entrega,
                total_en_camino=total_en_camino,
                total_entregados=total_entregados,
                remitos=items,
            )
        )

    return result


@router.get(
    "/productos-pendientes-por-dia",
    response_model=list[ProductosPendientesPorDiaSchema],
    summary="Productos pendientes por día agrupados por responsable",
    description=(
        "Returns pending product quantities grouped by delivery date and then by responsable, "
        "considering only remitos that have not been received or invoiced."
    ),
)
def productos_pendientes_por_dia(
    fecha_desde: Optional[str] = Query(None, description="Filter by fecha_entrega >= fecha_desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Filter by fecha_entrega <= fecha_hasta (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    sql = text("""
        SELECT
            DATE(r.fecha_entrega) AS fecha,
            p.responsable,
            p.nombre              AS producto,
            SUM(d.cantidad - COALESCE(d.entregado, 0)) AS cantidad
        FROM costos_remitodetalles d
        JOIN costos_remitos r   ON d.remito_id = r.id
        JOIN costos_productos p ON d.producto_id = p.id
        WHERE r.fecha_facturacion IS NULL
          AND (:fecha_desde IS NULL OR DATE(r.fecha_entrega) >= :fecha_desde)
          AND (:fecha_hasta IS NULL OR DATE(r.fecha_entrega) <= :fecha_hasta)
        GROUP BY DATE(r.fecha_entrega), p.responsable, p.nombre
        ORDER BY fecha ASC, p.responsable ASC, p.nombre ASC
    """)
    rows = db.execute(sql, {"fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta}).mappings().all()

    # Group: fecha -> responsable -> productos
    by_fecha: dict[str, dict[str, list[ProductoItemSchema]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        fecha_key = str(row["fecha"])
        by_fecha[fecha_key][row["responsable"]].append(
            ProductoItemSchema(producto=row["producto"], cantidad=int(row["cantidad"]))
        )

    return [
        ProductosPendientesPorDiaSchema(
            fecha=fecha,
            responsables=[
                ResponsableProductosSchema(responsable=resp, productos=productos)
                for resp, productos in sorted(responsables.items())
            ],
        )
        for fecha, responsables in sorted(by_fecha.items())
    ]
