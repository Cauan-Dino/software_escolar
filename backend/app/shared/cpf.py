"""Validação, normalização e mascaramento de CPF (LGPD: listagens só mostram CPF mascarado)."""

import re
from typing import Annotated

from pydantic import AfterValidator


def normalize_cpf(value: str) -> str:
    return re.sub(r"\D", "", value)


def is_valid_cpf(value: str) -> bool:
    cpf = normalize_cpf(value)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for size in (9, 10):
        total = sum(int(cpf[i]) * (size + 1 - i) for i in range(size))
        digit = (total * 10) % 11 % 10
        if digit != int(cpf[size]):
            return False
    return True


def mask_cpf(value: str | None) -> str | None:
    """'12345678909' → '***.456.789-**'."""
    if not value:
        return value
    cpf = normalize_cpf(value)
    if len(cpf) != 11:
        return "***"
    return f"***.{cpf[3:6]}.{cpf[6:9]}-**"


def format_cpf(value: str) -> str:
    cpf = normalize_cpf(value)
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def _validate(value: str) -> str:
    if not is_valid_cpf(value):
        raise ValueError("CPF inválido")
    return normalize_cpf(value)


CPF = Annotated[str, AfterValidator(_validate)]
"""Tipo Pydantic: aceita CPF com ou sem pontuação, valida os dígitos e guarda só números."""


MaskedCPF = Annotated[str | None, AfterValidator(mask_cpf)]
"""Tipo Pydantic para SAÍDAS de listagem: o CPF é sempre devolvido mascarado (LGPD)."""
