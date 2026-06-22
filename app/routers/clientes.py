from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database import get_db
from ..models import Cliente, Documento
from ..schemas import ClienteSchema

router = APIRouter(prefix="/clientes", tags=["clientes"])


def _four_months_ago() -> date:
    today = date.today()
    month = today.month - 4
    year = today.year
    if month <= 0:
        month += 12
        year -= 1
    return today.replace(year=year, month=month)


@router.get("", response_model=list[ClienteSchema])
def list_clientes(
    q: str | None = Query(None, description="Search by name (nom1 or nom2)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    cutoff = _four_months_ago()
    active_subq = (
        db.query(Documento)
        .filter(Documento.idcliente == Cliente.idcliente, Documento.fechadocumento > cutoff)
        .exists()
    )
    query = db.query(Cliente).filter(active_subq)
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(Cliente.nom1.ilike(pattern), Cliente.nom2.ilike(pattern))
        )
    return query.offset(skip).limit(limit).all()


@router.get("/{idcliente}", response_model=ClienteSchema)
def get_cliente(idcliente: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.idcliente == idcliente).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente not found")
    return cliente
