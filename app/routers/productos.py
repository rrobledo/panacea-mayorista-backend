from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Producto
from ..schemas import ProductoSchema

router = APIRouter(prefix="/productos", tags=["productos"])


@router.get("", response_model=list[ProductoSchema])
def list_productos(
    q: str | None = Query(None, description="Search by product name"),
    solo_habilitados: bool = Query(True, description="Only return enabled products"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Producto)
    if solo_habilitados:
        query = query.filter(Producto.habilitado.is_(True))
    if q:
        query = query.filter(Producto.nombre.ilike(f"%{q}%"))
    return query.order_by(Producto.prioridad, Producto.nombre).offset(skip).limit(limit).all()


@router.get("/{id}", response_model=ProductoSchema)
def get_producto(id: int, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id == id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    return producto
