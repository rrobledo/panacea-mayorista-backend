from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database import get_db
from ..models import Cliente
from ..schemas import ClienteSchema

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("", response_model=list[ClienteSchema])
def list_clientes(
    q: str | None = Query(None, description="Search by name (nom1 or nom2)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Cliente)
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
