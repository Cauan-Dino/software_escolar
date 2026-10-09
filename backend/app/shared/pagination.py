"""Paginação padrão das listagens: `?limit=50&offset=0` → `Page[T]`."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query
from pydantic import BaseModel


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class PageParams:
    limit: int = 50
    offset: int = 0


def _page_params(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PageParams:
    return PageParams(limit=limit, offset=offset)


Pagination = Annotated[PageParams, Depends(_page_params)]
