"""Relógio da aplicação. Use `clock.today()` em vez de `date.today()` para os testes
conseguirem "congelar" a data com monkeypatch."""

import calendar
from datetime import UTC, date, datetime


def today() -> date:
    return date.today()


def now() -> datetime:
    return datetime.now(UTC)


def add_months(value: date, months: int) -> date:
    """Soma meses mantendo o dia, limitado ao último dia do mês (31/01 + 1 → 28 ou 29/02)."""
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)
