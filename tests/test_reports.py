from datetime import datetime, timezone, timedelta


def make_remito(cliente_id, producto_id, days_ahead=3):
    fecha = (datetime.now(tz=timezone.utc) + timedelta(days=days_ahead)).isoformat()
    return {
        "vendedor": "Test",
        "fecha_entrega": fecha,
        "cliente_id": cliente_id,
        "detalles": [{"producto_id": producto_id, "cantidad": 10}],
    }


def test_pendientes_entrega_empty(client):
    resp = client.get("/reports/pendientes-entrega")
    assert resp.status_code == 200
    assert resp.json() == []


def test_pendientes_entrega_returns_unfinished(client, sample_cliente, sample_producto):
    client.post("/remitos", json=make_remito(1, sample_producto.id))
    resp = client.get("/reports/pendientes-entrega")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_pendientes_entrega_excludes_facturado(client, sample_cliente, sample_producto):
    created = client.post("/remitos", json=make_remito(1, sample_producto.id)).json()
    rid = created["id"]
    for state in ["en_produccion", "preparando", "listo_entregar", "en_entrega", "facturado"]:
        client.patch(f"/remitos/{rid}/estado", json={"nuevo_estado": state})

    resp = client.get("/reports/pendientes-entrega")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_pendientes_por_dia_groups_correctly(client, sample_cliente, sample_producto):
    fecha_1 = (datetime.now(tz=timezone.utc) + timedelta(days=1)).isoformat()
    fecha_2 = (datetime.now(tz=timezone.utc) + timedelta(days=5)).isoformat()

    client.post("/remitos", json={**make_remito(1, sample_producto.id), "fecha_entrega": fecha_1})
    client.post("/remitos", json={**make_remito(1, sample_producto.id), "fecha_entrega": fecha_1})
    client.post("/remitos", json={**make_remito(1, sample_producto.id), "fecha_entrega": fecha_2})

    resp = client.get("/reports/pendientes-por-dia")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    totals = {d["fecha"]: d["total_remitos"] for d in data}
    fecha_1_key = fecha_1[:10]
    fecha_2_key = fecha_2[:10]
    assert totals[fecha_1_key] == 2
    assert totals[fecha_2_key] == 1


def test_productos_pendientes_por_dia_empty(client):
    resp = client.get("/reports/productos-pendientes-por-dia")
    assert resp.status_code == 200
    assert resp.json() == []
