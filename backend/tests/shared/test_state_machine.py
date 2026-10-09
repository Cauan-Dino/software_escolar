from enum import StrEnum

import pytest

from app.core.exceptions import InvalidTransitionError
from app.shared.state_machine import StateMachine


class Luz(StrEnum):
    VERDE = "VERDE"
    AMARELO = "AMARELO"
    VERMELHO = "VERMELHO"


FSM = StateMachine({Luz.VERDE: {Luz.AMARELO}, Luz.AMARELO: {Luz.VERMELHO}})


def test_allowed_transition():
    assert FSM.can(Luz.VERDE, Luz.AMARELO)
    FSM.ensure(Luz.VERDE, Luz.AMARELO)


def test_forbidden_transition_raises_409_error():
    assert not FSM.can(Luz.VERDE, Luz.VERMELHO)
    with pytest.raises(InvalidTransitionError) as exc:
        FSM.ensure(Luz.VERDE, Luz.VERMELHO)
    assert exc.value.status_code == 409
    assert "VERDE" in exc.value.detail


def test_terminal_and_targets():
    assert FSM.is_terminal(Luz.VERMELHO)
    assert not FSM.is_terminal(Luz.VERDE)
    assert FSM.targets(Luz.AMARELO) == frozenset({Luz.VERMELHO})
