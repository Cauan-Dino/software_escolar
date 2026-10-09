"""Bases para os schemas Pydantic de todos os módulos."""

from pydantic import BaseModel, ConfigDict


class InputSchema(BaseModel):
    """Base de TODO schema de entrada.

    `extra="forbid"`: campos desconhecidos (ex.: `status`, `valor`, `role` enviados por um
    cliente malicioso) fazem a requisição falhar com 422 em vez de serem aceitos em silêncio.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class OutputSchema(BaseModel):
    """Base de TODO schema de saída. Lê atributos de models (`from_attributes`)."""

    model_config = ConfigDict(from_attributes=True)
