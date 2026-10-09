from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.shared.pagination import Page, Pagination


def make_client() -> TestClient:
    mini = FastAPI()

    @mini.get("/itens", response_model=Page[int])
    def itens(page: Pagination) -> Page[int]:
        dados = list(range(10))
        return Page[int](
            items=dados[page.offset : page.offset + page.limit],
            total=len(dados),
            limit=page.limit,
            offset=page.offset,
        )

    return TestClient(mini)


def test_default_page():
    body = make_client().get("/itens").json()
    assert body == {"items": list(range(10)), "total": 10, "limit": 50, "offset": 0}


def test_custom_page():
    body = make_client().get("/itens", params={"limit": 3, "offset": 6}).json()
    assert body["items"] == [6, 7, 8]


def test_limit_is_bounded():
    assert make_client().get("/itens", params={"limit": 1000}).status_code == 422
