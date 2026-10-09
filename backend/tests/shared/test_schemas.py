import pytest
from pydantic import ValidationError

from app.shared.schemas import InputSchema, OutputSchema


class Entrada(InputSchema):
    nome: str


class Saida(OutputSchema):
    nome: str


def test_input_schema_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        Entrada.model_validate({"nome": "Ana", "status": "ATIVA"})


def test_input_schema_strips_whitespace():
    assert Entrada(nome="  Ana  ").nome == "Ana"


def test_output_schema_reads_attributes():
    class Obj:
        nome = "Bia"

    assert Saida.model_validate(Obj()).nome == "Bia"
