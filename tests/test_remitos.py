from datetime import datetime, timezone, timedelta


FECHA_ENTREGA = (datetime.now(tz=timezone.utc) + timedelta(days=3)).isoformat()


def make_remito_payload(cliente_id, producto_id, fecha_entrega=None):
    return {
        "vendedor": "Juan Ventas",
        "observaciones": "Test remito",
        "fecha_entrega": fecha_entrega or FECHA_ENTREGA,
        "cliente_id": cliente_id,
        "detalles": [{"producto_id": producto_id, "cantidad": 5}],
    }


def test_create_remito(client, sample_cliente, sample_producto):
    resp = client.post("/remitos", json=make_remito_payload(1, sample_producto.id))
    assert resp.status_code == 201
    data = resp.json()
    assert data["estado"] == "creado"
    assert data["vendedor"] == "Juan Ventas"
    assert len(data["detalles"]) == 1
    assert data["detalles"][0]["cantidad"] == 5


def test_create_remito_invalid_cliente(client, sample_producto):
    resp = client.post("/remitos", json=make_remito_payload(9999, sample_producto.id))
    assert resp.status_code == 422


def test_create_remito_invalid_producto(client, sample_cliente):
    resp = client.post("/remitos", json=make_remito_payload(1, 9999))
    assert resp.status_code == 422


def test_get_remito_not_found(client):
    resp = client.get("/remitos/9999")
    assert resp.status_code == 404


def test_get_remito(client, sample_cliente, sample_producto):
    created = client.post("/remitos", json=make_remito_payload(1, sample_producto.id)).json()
    resp = client.get(f"/remitos/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_list_remitos(client, sample_cliente, sample_producto):
    client.post("/remitos", json=make_remito_payload(1, sample_producto.id))
    client.post("/remitos", json=make_remito_payload(1, sample_producto.id))
    resp = client.get("/remitos")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_remitos_filter_by_cliente(client, sample_cliente, sample_producto, db):
    from app.models import Cliente
    db.add(Cliente(idcliente=2, nom1="Otro Cliente", activo=1))
    db.commit()
    client.post("/remitos", json=make_remito_payload(1, sample_producto.id))
    client.post("/remitos", json=make_remito_payload(2, sample_producto.id))
    resp = client.get("/remitos?cliente_id=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_estado_transition_sequence(client, sample_cliente, sample_producto):
    created = client.post("/remitos", json=make_remito_payload(1, sample_producto.id)).json()
    rid = created["id"]

    transitions = [
        "en_produccion",
        "preparando",
        "listo_entregar",
        "en_entrega",
        "facturado",
    ]
    for next_state in transitions:
        resp = client.patch(f"/remitos/{rid}/estado", json={"nuevo_estado": next_state})
        assert resp.status_code == 200, f"Failed transition to {next_state}: {resp.json()}"
        assert resp.json()["estado"] == next_state


def test_invalid_estado_transition(client, sample_cliente, sample_producto):
    created = client.post("/remitos", json=make_remito_payload(1, sample_producto.id)).json()
    resp = client.patch(f"/remitos/{created['id']}/estado", json={"nuevo_estado": "facturado"})
    assert resp.status_code == 422


def test_skip_estado_transition(client, sample_cliente, sample_producto):
    created = client.post("/remitos", json=make_remito_payload(1, sample_producto.id)).json()
    resp = client.patch(f"/remitos/{created['id']}/estado", json={"nuevo_estado": "preparando"})
    assert resp.status_code == 422


def test_update_remito_in_creado(client, sample_cliente, sample_producto):
    created = client.post("/remitos", json=make_remito_payload(1, sample_producto.id)).json()
    resp = client.put(f"/remitos/{created['id']}", json={"vendedor": "Maria Ventas"})
    assert resp.status_code == 200
    assert resp.json()["vendedor"] == "Maria Ventas"


def test_update_remito_not_in_creado(client, sample_cliente, sample_producto):
    created = client.post("/remitos", json=make_remito_payload(1, sample_producto.id)).json()
    rid = created["id"]
    client.patch(f"/remitos/{rid}/estado", json={"nuevo_estado": "en_produccion"})
    resp = client.put(f"/remitos/{rid}", json={"vendedor": "Maria Ventas"})
    assert resp.status_code == 422


def test_delete_remito_in_creado(client, sample_cliente, sample_producto):
    created = client.post("/remitos", json=make_remito_payload(1, sample_producto.id)).json()
    resp = client.delete(f"/remitos/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/remitos/{created['id']}").status_code == 404


def test_delete_remito_not_in_creado(client, sample_cliente, sample_producto):
    created = client.post("/remitos", json=make_remito_payload(1, sample_producto.id)).json()
    rid = created["id"]
    client.patch(f"/remitos/{rid}/estado", json={"nuevo_estado": "en_produccion"})
    resp = client.delete(f"/remitos/{rid}")
    assert resp.status_code == 422
