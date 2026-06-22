from datetime import datetime, timezone, timedelta

from app.models import Cliente, Documento


def test_list_clientes_empty(client):
    resp = client.get("/clientes")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_clientes(client, sample_documento):
    resp = client.get("/clientes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["nom1"] == "Empresa Test"


def test_list_clientes_excludes_without_recent_documento(client, sample_cliente):
    # cliente has no documentos → must not appear
    resp = client.get("/clientes")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_clientes_excludes_old_documento(client, db, sample_cliente):
    # documento older than 4 months → cliente must not appear
    db.add(Documento(
        iddocumento=1,
        idcliente=sample_cliente.idcliente,
        fechadocumento=datetime.now(tz=timezone.utc) - timedelta(days=200),
    ))
    db.commit()

    resp = client.get("/clientes")
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_clientes_by_name(client, db):
    db.add(Cliente(idcliente=1, nom1="Panaderia Lopez", activo=1))
    db.add(Cliente(idcliente=2, nom1="Supermercado Sur", activo=1))
    db.add(Documento(iddocumento=1, idcliente=1, fechadocumento=datetime.now(tz=timezone.utc) - timedelta(days=10)))
    db.add(Documento(iddocumento=2, idcliente=2, fechadocumento=datetime.now(tz=timezone.utc) - timedelta(days=10)))
    db.commit()

    resp = client.get("/clientes?q=Lopez")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["nom1"] == "Panaderia Lopez"


def test_search_clientes_by_nom2(client, db):
    db.add(Cliente(idcliente=1, nom1="Empresa A", nom2="EA Alias", activo=1))
    db.add(Documento(iddocumento=1, idcliente=1, fechadocumento=datetime.now(tz=timezone.utc) - timedelta(days=10)))
    db.commit()

    resp = client.get("/clientes?q=Alias")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_cliente_not_found(client):
    resp = client.get("/clientes/9999")
    assert resp.status_code == 404


def test_get_cliente_by_id(client, sample_cliente):
    resp = client.get("/clientes/1")
    assert resp.status_code == 200
    assert resp.json()["idcliente"] == 1
