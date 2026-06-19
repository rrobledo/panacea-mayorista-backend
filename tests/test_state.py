from datetime import datetime, timezone
from app.state import EstadoRemito, derive_estado, VALID_TRANSITIONS


class FakeRemito:
    def __init__(self, **kwargs):
        self.fecha_preparacion = None
        self.fecha_listo = None
        self.fecha_despacho = None
        self.fecha_recibido = None
        self.fecha_facturacion = None
        for k, v in kwargs.items():
            setattr(self, k, v)


NOW = datetime.now(tz=timezone.utc)


def test_estado_creado():
    r = FakeRemito()
    assert derive_estado(r) == EstadoRemito.CREADO


def test_estado_en_produccion():
    r = FakeRemito(fecha_preparacion=NOW)
    assert derive_estado(r) == EstadoRemito.EN_PRODUCCION


def test_estado_preparando():
    r = FakeRemito(fecha_preparacion=NOW, fecha_listo=NOW)
    assert derive_estado(r) == EstadoRemito.PREPARANDO


def test_estado_listo_entregar():
    r = FakeRemito(fecha_preparacion=NOW, fecha_listo=NOW, fecha_despacho=NOW)
    assert derive_estado(r) == EstadoRemito.LISTO_ENTREGAR


def test_estado_en_entrega():
    r = FakeRemito(fecha_preparacion=NOW, fecha_listo=NOW, fecha_despacho=NOW, fecha_recibido=NOW)
    assert derive_estado(r) == EstadoRemito.EN_ENTREGA


def test_estado_facturado():
    r = FakeRemito(fecha_facturacion=NOW)
    assert derive_estado(r) == EstadoRemito.FACTURADO


def test_facturado_overrides_all():
    r = FakeRemito(
        fecha_preparacion=NOW,
        fecha_listo=NOW,
        fecha_despacho=NOW,
        fecha_recibido=NOW,
        fecha_facturacion=NOW,
    )
    assert derive_estado(r) == EstadoRemito.FACTURADO


def test_valid_transitions_chain():
    expected_chain = [
        EstadoRemito.CREADO,
        EstadoRemito.EN_PRODUCCION,
        EstadoRemito.PREPARANDO,
        EstadoRemito.LISTO_ENTREGAR,
        EstadoRemito.EN_ENTREGA,
        EstadoRemito.FACTURADO,
    ]
    for i in range(len(expected_chain) - 1):
        assert VALID_TRANSITIONS[expected_chain[i]] == expected_chain[i + 1]


def test_facturado_has_no_transition():
    assert EstadoRemito.FACTURADO not in VALID_TRANSITIONS
