from __future__ import annotations

from datetime import date, datetime
from calendar import monthrange
from typing import Iterable
import uuid


MONTH_NAMES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']


def now_iso() -> str:
    return datetime.now().isoformat(timespec='seconds')


def parse_date(value: str) -> date:
    return datetime.strptime(value, '%Y-%m-%d').date()


def month_iter(start_year: int, start_month: int, end_year: int, end_month: int) -> Iterable[tuple[int, int]]:
    year, month = start_year, start_month
    while (year < end_year) or (year == end_year and month <= end_month):
        yield year, month
        month += 1
        if month > 12:
            year += 1
            month = 1


def adjust_due_date(base_date: date, year: int, month: int) -> str:
    day = min(base_date.day, monthrange(year, month)[1])
    return date(year, month, day).isoformat()


def recurrence_group() -> str:
    return uuid.uuid4().hex[:16]
