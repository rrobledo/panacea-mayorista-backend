from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text

from ..database import get_db
from ..models import Remito, RemitoDetalle
from ..schemas import PendientesPorDiaSchema, ProductoPendienteSchema, RemitoSummarySchema

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
        .filter(Remito.fecha_facturacion.is_(None), Remito.fecha_recibido.is_(None))
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
def pendientes_por_dia(db: Session = Depends(get_db)):
    remitos = (
        db.query(Remito)
        .options(joinedload(Remito.cliente))
        .filter(Remito.fecha_facturacion.is_(None), Remito.fecha_recibido.is_(None))
        .order_by(Remito.fecha_entrega.asc())
        .all()
    )

    grouped: dict[str, list] = defaultdict(list)
    for r in remitos:
        fecha_key = r.fecha_entrega.strftime("%Y-%m-%d")
        grouped[fecha_key].append(RemitoSummarySchema.model_validate(r))

    return [
        PendientesPorDiaSchema(fecha=fecha, total_remitos=len(items), remitos=items)
        for fecha, items in sorted(grouped.items())
    ]


@router.get(
    "/productos-pendientes-por-dia",
    response_model=list[ProductoPendienteSchema],
    summary="Productos pendientes por día",
    description=(
        "Returns the total pending quantity of each product grouped by delivery date, "
        "considering only remitos that have not been received or invoiced."
    ),
)
def productos_pendientes_por_dia(db: Session = Depends(get_db)):
    sql = text("""
        SELECT
            DATE(r.fecha_entrega) AS fecha,
            p.id                  AS producto_id,
            p.codigo,
            p.nombre,
            p.unidad_medida,
            SUM(d.cantidad - COALESCE(d.entregado, 0)) AS cantidad_pendiente
        FROM costos_remitodetalles d
        JOIN costos_remitos r   ON d.remito_id = r.id
        JOIN costos_productos p ON d.producto_id = p.id
        WHERE r.fecha_facturacion IS NULL
          AND r.fecha_recibido IS NULL
        GROUP BY DATE(r.fecha_entrega), p.id, p.codigo, p.nombre, p.unidad_medida
        ORDER BY fecha ASC, p.nombre ASC
    """)
    rows = db.execute(sql).mappings().all()
    return [
        ProductoPendienteSchema(
            fecha=str(row["fecha"]),
            producto_id=row["producto_id"],
            codigo=row["codigo"],
            nombre=row["nombre"],
            unidad_medida=row["unidad_medida"],
            cantidad_pendiente=int(row["cantidad_pendiente"]),
        )
        for row in rows
    ]
