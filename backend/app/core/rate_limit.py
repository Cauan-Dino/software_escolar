"""Rate limit simples em memória (janela deslizante).

Suficiente para o MVP com um único processo da API. Com vários workers/réplicas,
troque o armazenamento por Redis mantendo a mesma interface (`hit`/`reset`).
"""

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from app.core.exceptions import RateLimitError


class RateLimiter:
    _instances: list["RateLimiter"] = []  # noqa: RUF012

    def __init__(
        self,
        name: str,
        max_calls: int,
        period_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.name = name
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        RateLimiter._instances.append(self)

    def hit(self, key: str) -> None:
        """Registra uma chamada para `key`; levanta RateLimitError se o limite estourou."""
        now = self._clock()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= self.period_seconds:
                hits.popleft()
            if len(hits) >= self.max_calls:
                raise RateLimitError()
            hits.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    @classmethod
    def reset_all(cls) -> None:
        for limiter in cls._instances:
            limiter.reset()
