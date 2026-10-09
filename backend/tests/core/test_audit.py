from datetime import date
from decimal import Decimal
from enum import StrEnum

from app.core.audit import AuditLog, list_audit_logs, record_audit, snapshot
from app.core.roles import Role
from tests.helpers import current_user


class Cor(StrEnum):
    AZUL = "AZUL"


class Coisa:
    valor = Decimal("10.50")
    dia = date(2026, 3, 1)
    cor = Cor.AZUL
    nome = "x"


def test_snapshot_serializes_decimal_date_and_enum():
    assert snapshot(Coisa(), ["valor", "dia", "cor", "nome"]) == {
        "valor": "10.50",
        "dia": "2026-03-01",
        "cor": "AZUL",
        "nome": "x",
    }


def test_record_audit_persists_actor_and_states(db):
    entry = record_audit(
        db,
        actor=current_user(Role.ADMIN, user_id=5),
        action="bolsa.conceder",
        entity="bolsa",
        entity_id=10,
        before=None,
        after={"percentual": Decimal("50.00")},
    )
    stored = db.get(AuditLog, entry.id)
    assert stored is not None
    assert stored.actor_user_id == 5
    assert stored.actor_role == "ADMIN"
    assert stored.entity_id == "10"
    assert stored.after == {"percentual": "50.00"}


def test_record_audit_without_actor_is_system(db):
    entry = record_audit(db, actor=None, action="x", entity="cobranca", entity_id=1)
    assert entry.actor_role == "SISTEMA"
    assert entry.actor_user_id is None


def test_list_audit_logs_filters_by_entity(db):
    record_audit(db, actor=None, action="a", entity="matricula", entity_id=1)
    record_audit(db, actor=None, action="b", entity="cobranca", entity_id=1)
    rows, total = list_audit_logs(db, entity="matricula")
    assert total == 1
    assert rows[0].action == "a"


def test_audit_endpoint_requires_admin(client, headers_for):
    assert client.get("/api/v1/auditoria").status_code == 401
    forbidden = client.get("/api/v1/auditoria", headers=headers_for(Role.SECRETARIA))
    assert forbidden.status_code == 403


def test_audit_endpoint_lists_for_admin(client, db, headers_for):
    record_audit(db, actor=None, action="farda.ajuste", entity="estoque_farda", entity_id=3)
    response = client.get(
        "/api/v1/auditoria", params={"entity": "estoque_farda"}, headers=headers_for(Role.ADMIN)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["action"] == "farda.ajuste"
