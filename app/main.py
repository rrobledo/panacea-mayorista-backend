# Panacea Mayorista Backend
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from .routers import clientes, productos, remitos, reports

app = FastAPI(
    title="Panacea Mayorista — Notas de Pedido API",
    description=(
        "REST API para registro y seguimiento de notas de pedido (remitos). "
        "Permite crear remitos, avanzar su estado a través del ciclo de producción, "
        "y consultar pendientes de entrega."
    ),
    version="1.0.0",
    contact={"name": "Panacea Mayorista", "email": "raul.osvaldo.robledo@gmail.com"},
    license_info={"name": "Proprietary"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=500, content={"detail": "Database error occurred"})


app.include_router(clientes.router)
app.include_router(productos.router)
app.include_router(remitos.router)
app.include_router(reports.router)


@app.get("/", include_in_schema=False)
def root():
    return {"message": "Panacea Mayorista API v1.0.0 — visit /docs for documentation"}


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
