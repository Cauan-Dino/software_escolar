import pytest

from app.core.exceptions import RateLimitError
from app.core.rate_limit import RateLimiter


def test_blocks_after_max_calls_per_key():
    limiter = RateLimiter("teste", max_calls=2)
    limiter.hit("ip-1")
    limiter.hit("ip-1")
    with pytest.raises(RateLimitError):
        limiter.hit("ip-1")
    limiter.hit("ip-2")  # outra chave não é afetada


def test_window_expires():
    clock = [1000.0]
    limiter = RateLimiter("teste", max_calls=1, period_seconds=60, clock=lambda: clock[0])
    limiter.hit("k")
    clock[0] += 61
    limiter.hit("k")


def test_reset_all_clears_every_limiter():
    limiter = RateLimiter("teste", max_calls=1)
    limiter.hit("k")
    RateLimiter.reset_all()
    limiter.hit("k")
