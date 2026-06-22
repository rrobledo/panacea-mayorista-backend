import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Cliente, Documento, Producto, Remito, RemitoDetalle

# StaticPool: all sessions share the same in-memory SQLite connection
# schema_translate_map: public.table → main.table (SQLite default schema is "main")
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
).execution_options(schema_translate_map={"public": None})


@event.listens_for(engine.sync_engine if hasattr(engine, "sync_engine") else engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    db = TestingSessionLocal()
    try:
        db.execute(text("DELETE FROM costos_remitodetalles"))
        db.execute(text("DELETE FROM costos_remitos"))
        db.execute(text("DELETE FROM costos_productos"))
        db.execute(text("DELETE FROM documentos"))
        db.execute(text("DELETE FROM clientes"))
        db.commit()
    finally:
        db.close()


@pytest.fixture
def db():
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_cliente(db):
    c = Cliente(idcliente=1, nom1="Empresa Test", nom2="ET", activo=1, localidad="Buenos Aires")
    db.add(c)
    db.commit()
    return c


@pytest.fixture
def sample_documento(db, sample_cliente):
    from datetime import datetime, timezone, timedelta
    doc = Documento(
        iddocumento=1,
        idcliente=sample_cliente.idcliente,
        fechadocumento=datetime.now(tz=timezone.utc) - timedelta(days=30),
    )
    db.add(doc)
    db.commit()
    return doc


@pytest.fixture
def sample_producto(db):
    p = Producto(
        codigo="PROD-001",
        nombre="Producto Test",
        utilidad=0.3,
        precio_actual=100.0,
        unidad_medida="kg",
        lote_produccion=10,
        tiempo_produccion=1,
        categoria="General",
        responsable="admin",
        is_producto=True,
        habilitado=True,
        prioridad=1,
    )
    db.add(p)
    db.commit()
    return p
