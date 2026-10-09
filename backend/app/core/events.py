"""Eventos de domínio síncronos entre módulos.

Usado quando um módulo precisa reagir a algo de outro módulo sem criar dependência
circular. Exemplo: o `financeiro` publica `CobrancaPaga`; o `matricula` (que já depende
do financeiro) se inscreve e ativa a matrícula. O handler roda na MESMA transação de quem
publicou, então se ele falhar tudo é desfeito.
"""

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

Handler = Callable[[Session, Any], None]

_subscribers: dict[type, list[Handler]] = defaultdict(list)


def subscribe(event_type: type, handler: Handler) -> None:
    """Inscreve `handler` para `event_type`. Inscrever duas vezes o mesmo handler não duplica."""
    if handler not in _subscribers[event_type]:
        _subscribers[event_type].append(handler)


def publish(db: Session, event: object) -> None:
    for handler in list(_subscribers[type(event)]):
        handler(db, event)


def clear_subscribers() -> None:
    _subscribers.clear()
