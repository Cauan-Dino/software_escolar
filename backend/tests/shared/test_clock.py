from datetime import date

import pytest

from app.shared import clock


@pytest.mark.parametrize(
    ("start", "months", "expected"),
    [
        (date(2026, 1, 31), 1, date(2026, 2, 28)),
        (date(2028, 1, 31), 1, date(2028, 2, 29)),
        (date(2026, 11, 10), 2, date(2027, 1, 10)),
        (date(2026, 3, 15), 12, date(2027, 3, 15)),
        (date(2026, 3, 15), -3, date(2025, 12, 15)),
    ],
)
def test_add_months(start, months, expected):
    assert clock.add_months(start, months) == expected


def test_today_and_now():
    assert clock.today() == date.today()
    assert clock.now().tzinfo is not None
