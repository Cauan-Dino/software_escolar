from collections import defaultdict
from dataclasses import dataclass
from typing import cast

import pytest
from sqlalchemy.orm import Session

from app.core import events


@dataclass
class AlgoAconteceu:
    valor: int


FAKE_DB = cast(Session, object())


@pytest.fixture
def clean_bus(monkeypatch):
    monkeypatch.setattr(events, "_subscribers", defaultdict(list))


@pytest.mark.usefixtures("clean_bus")
def test_publish_calls_subscribed_handlers_with_session_and_event():
    received = []
    events.subscribe(AlgoAconteceu, lambda db, ev: received.append((db, ev.valor)))
    events.publish(FAKE_DB, AlgoAconteceu(42))
    assert received == [(FAKE_DB, 42)]


@pytest.mark.usefixtures("clean_bus")
def test_subscribing_same_handler_twice_does_not_duplicate():
    received = []

    def handler(db, ev):
        received.append(ev)

    events.subscribe(AlgoAconteceu, handler)
    events.subscribe(AlgoAconteceu, handler)
    events.publish(FAKE_DB, AlgoAconteceu(1))
    assert len(received) == 1


@pytest.mark.usefixtures("clean_bus")
def test_publish_without_subscribers_is_noop_and_clear_removes_handlers():
    events.publish(FAKE_DB, AlgoAconteceu(1))
    events.subscribe(AlgoAconteceu, lambda db, ev: None)
    events.clear_subscribers()
    assert not events._subscribers
