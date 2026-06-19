from app.models import Cliente


def test_list_clientes_empty(client):
    resp = client.get("/clientes")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_clientes(client, sample_cliente):
    resp = client.get("/clientes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["nom1"] == "Empresa Test"


def test_search_clientes_by_name(client, db):
    db.add(Cliente(idcliente=1, nom1="Panaderia Lopez", activo=1))
    db.add(Cliente(idcliente=2, nom1="Supermercado Sur", activo=1))
    db.commit()

    resp = client.get("/clientes?q=Lopez")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["nom1"] == "Panaderia Lopez"


def test_search_clientes_by_nom2(client, db):
    db.add(Cliente(idcliente=1, nom1="Empresa A", nom2="EA Alias", activo=1))
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
