from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Boolean, Column, Float, ForeignKey, Integer,
    Numeric, SmallInteger, String, Text, TIMESTAMP
)
from sqlalchemy.orm import relationship
from .database import Base


class Documento(Base):
    __tablename__ = "documentos"
    __table_args__ = {"schema": "public"}

    iddocumento = Column(Integer, primary_key=True)
    idcliente = Column(Integer, ForeignKey("public.clientes.idcliente"), nullable=False)
    fechadocumento = Column(TIMESTAMP, nullable=False)


class Cliente(Base):
    __tablename__ = "clientes"
    __table_args__ = {"schema": "public"}

    idcliente = Column(Integer, primary_key=True)
    bempresa = Column(SmallInteger)
    cc = Column(SmallInteger)
    cc_bloq = Column(SmallInteger)
    nom1 = Column(String(100))
    nom2 = Column(String(100))
    cuit = Column(String(20))
    condiva = Column(SmallInteger)
    tpdoc = Column(SmallInteger)
    nrodoc = Column(String(20))
    direccion = Column(String(255))
    codpostal = Column(String(20))
    barrio = Column(String(100))
    localidad = Column(String(100))
    provincia = Column(String(50))
    actividadcomecial = Column(String(100))
    tipoest = Column(SmallInteger)
    fechainicioact = Column(TIMESTAMP)
    tel1 = Column(String(20))
    int1 = Column(String(10))
    tel2 = Column(String(20))
    celular = Column(String(20))
    email1 = Column(String(50))
    email2 = Column(String(50))
    personacontacto = Column(String(255))
    comentarios = Column(String(255))
    fechaalta = Column(TIMESTAMP)
    activo = Column(SmallInteger)
    listaprecio = Column(Integer)
    expreso = Column(String(50))
    entrega = Column(String(40))
    horario = Column(String(30))
    fechaultcompra = Column(TIMESTAMP)
    idprovincia = Column(Integer)

    remitos = relationship("Remito", back_populates="cliente")


class Producto(Base):
    __tablename__ = "costos_productos"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    codigo = Column(String(50), nullable=False)
    nombre = Column(String(250), nullable=False)
    ref_id = Column(String(250))
    utilidad = Column(Float, nullable=False)
    precio_actual = Column(Float, nullable=False)
    unidad_medida = Column(String(10), nullable=False)
    lote_produccion = Column(Integer, nullable=False)
    tiempo_produccion = Column(Integer, nullable=False)
    categoria = Column(String(250), nullable=False)
    responsable = Column(String(50), nullable=False)
    is_producto = Column(Boolean, nullable=False)
    habilitado = Column(Boolean, nullable=False)
    prioridad = Column(Integer, nullable=False)

    detalles = relationship("RemitoDetalle", back_populates="producto")


class Remito(Base):
    __tablename__ = "costos_remitos"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    observaciones = Column(String(1000))
    vendedor = Column(String(255), nullable=False)
    fecha_carga = Column(TIMESTAMP(timezone=True), nullable=False)
    fecha_entrega = Column(TIMESTAMP(timezone=True), nullable=False)
    fecha_preparacion = Column(TIMESTAMP(timezone=True))
    fecha_listo = Column(TIMESTAMP(timezone=True))
    fecha_despacho = Column(TIMESTAMP(timezone=True))
    fecha_recibido = Column(TIMESTAMP(timezone=True))
    fecha_facturacion = Column(TIMESTAMP(timezone=True))
    cliente_id = Column(Integer, ForeignKey("public.clientes.idcliente"), nullable=False)

    cliente = relationship("Cliente", back_populates="remitos")
    detalles = relationship("RemitoDetalle", back_populates="remito", cascade="all, delete-orphan")


class RemitoDetalle(Base):
    __tablename__ = "costos_remitodetalles"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    cantidad = Column(Integer, nullable=False)
    entregado = Column(Integer)
    observaciones = Column(String(1000))
    producto_id = Column(Integer, ForeignKey("public.costos_productos.id"), nullable=False)
    remito_id = Column(Integer, ForeignKey("public.costos_remitos.id"))

    producto = relationship("Producto", back_populates="detalles")
    remito = relationship("Remito", back_populates="detalles")
