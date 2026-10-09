"""Máquina de estados genérica: centraliza quais transições de status são permitidas.

MATRICULA_FSM = StateMachine({StatusMatricula.PRE_MATRICULA: {StatusMatricula.EM_ANALISE}})
MATRICULA_FSM.ensure(atual, novo)   # levanta InvalidTransitionError (HTTP 409) se inválida
"""

from collections.abc import Mapping, Set
from enum import Enum

from app.core.exceptions import InvalidTransitionError


class StateMachine[S: Enum]:
    def __init__(self, transitions: Mapping[S, Set[S]]) -> None:
        self._transitions = {state: frozenset(targets) for state, targets in transitions.items()}

    def can(self, current: S, target: S) -> bool:
        return target in self._transitions.get(current, frozenset())

    def ensure(self, current: S, target: S) -> None:
        if not self.can(current, target):
            raise InvalidTransitionError(
                f"Não é possível mudar o status de {current.value} para {target.value}."
            )

    def targets(self, current: S) -> frozenset[S]:
        return self._transitions.get(current, frozenset())

    def is_terminal(self, state: S) -> bool:
        return not self._transitions.get(state)
