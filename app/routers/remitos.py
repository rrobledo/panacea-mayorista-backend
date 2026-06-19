from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from ..database import get_db
from ..models import Cliente, Producto, Remito, RemitoDetalle
from ..schemas import (
    EstadoTransitionRequest,
    RemitoCreate,
    RemitoDetailSchema,
    RemitoSummarySchema,
    RemitoUpdate,
)
from ..state import (
    EstadoRemito,
    STATE_TIMESTAMP_MAP,
    VALID_TRANSITIONS,
    derive_estado,
)

router = APIRouter(prefix="/remitos", tags=["remitos"])


@router.post("", response_model=RemitoDetailSchema, status_code=201)
def create_remito(payload: RemitoCreate, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.idcliente == payload.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=422, detail=f"Cliente {payload.cliente_id} not found")

    producto_ids = [d.producto_id for d in payload.detalles]
    productos = db.query(Producto).filter(Producto.id.in_(producto_ids)).all()
    found_ids = {p.id for p in productos}
    missing = set(producto_ids) - found_ids
    if missing:
        raise HTTPException(status_code=422, detail=f"Productos not found: {missing}")

    remito = Remito(
        vendedor=payload.vendedor,
        observaciones=payload.observaciones,
        fecha_carga=datetime.now(tz=timezone.utc),
        fecha_entrega=payload.fecha_entrega,
        cliente_id=payload.cliente_id,
    )
    db.add(remito)
    db.flush()

    for detalle in payload.detalles:
        db.add(RemitoDetalle(
            remito_id=remito.id,
            producto_id=detalle.producto_id,
            cantidad=detalle.cantidad,
            observaciones=detalle.observaciones,
        ))

    db.commit()
    db.refresh(remito)
    return RemitoDetailSchema.model_validate(remito)


@router.get("", response_model=list[RemitoSummarySchema])
def list_remitos(
    fecha_desde: Optional[datetime] = Query(None, description="Filter by fecha_entrega >= fecha_desde"),
    fecha_hasta: Optional[datetime] = Query(None, description="Filter by fecha_entrega <= fecha_hasta"),
    cliente_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Remito).options(joinedload(Remito.cliente))
    if fecha_desde:
        query = query.filter(Remito.fecha_entrega >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Remito.fecha_entrega <= fecha_hasta)
    if cliente_id:
        query = query.filter(Remito.cliente_id == cliente_id)
    remitos = query.order_by(Remito.fecha_entrega.desc()).offset(skip).limit(limit).all()
    return [RemitoSummarySchema.model_validate(r) for r in remitos]


@router.get("/{id}", response_model=RemitoDetailSchema)
def get_remito(id: int, db: Session = Depends(get_db)):
    remito = (
        db.query(Remito)
        .options(joinedload(Remito.cliente), joinedload(Remito.detalles).joinedload(RemitoDetalle.producto))
        .filter(Remito.id == id)
        .first()
    )
    if not remito:
        raise HTTPException(status_code=404, detail="Remito not found")
    return RemitoDetailSchema.model_validate(remito)


@router.patch("/{id}/estado", response_model=RemitoDetailSchema)
def transition_estado(id: int, payload: EstadoTransitionRequest, db: Session = Depends(get_db)):
    remito = db.query(Remito).filter(Remito.id == id).first()
    if not remito:
        raise HTTPException(status_code=404, detail="Remito not found")

    current = derive_estado(remito)
    expected_next = VALID_TRANSITIONS.get(current)

    if expected_next is None or expected_next != payload.nuevo_estado:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid transition: '{current}' → '{payload.nuevo_estado}'. Expected next state: '{expected_next}'",
        )

    timestamp_field = STATE_TIMESTAMP_MAP[payload.nuevo_estado]
    setattr(remito, timestamp_field, datetime.now(tz=timezone.utc))
    db.commit()
    db.refresh(remito)
    return RemitoDetailSchema.model_validate(remito)


@router.put("/{id}", response_model=RemitoDetailSchema)
def update_remito(id: int, payload: RemitoUpdate, db: Session = Depends(get_db)):
    remito = (
        db.query(Remito)
        .options(joinedload(Remito.detalles))
        .filter(Remito.id == id)
        .first()
    )
    if not remito:
        raise HTTPException(status_code=404, detail="Remito not found")

    current = derive_estado(remito)
    if current != EstadoRemito.CREADO:
        raise HTTPException(status_code=422, detail="Only remitos in 'creado' state can be edited")

    if payload.vendedor is not None:
        remito.vendedor = payload.vendedor
    if payload.observaciones is not None:
        remito.observaciones = payload.observaciones
    if payload.fecha_entrega is not None:
        remito.fecha_entrega = payload.fecha_entrega

    if payload.detalles is not None:
        for detalle in remito.detalles:
            db.delete(detalle)
        db.flush()
        for detalle in payload.detalles:
            db.add(RemitoDetalle(
                remito_id=remito.id,
                producto_id=detalle.producto_id,
                cantidad=detalle.cantidad,
                observaciones=detalle.observaciones,
            ))

    db.commit()
    db.refresh(remito)
    return RemitoDetailSchema.model_validate(remito)


@router.delete("/{id}", status_code=204)
def delete_remito(id: int, db: Session = Depends(get_db)):
    remito = db.query(Remito).options(joinedload(Remito.detalles)).filter(Remito.id == id).first()
    if not remito:
        raise HTTPException(status_code=404, detail="Remito not found")

    current = derive_estado(remito)
    if current != EstadoRemito.CREADO:
        raise HTTPException(status_code=422, detail="Only remitos in 'creado' state can be deleted")

    db.delete(remito)
    db.commit()
