"""Séries e segmentos atendidos pela escola (usados por turmas, matrícula, materiais...)."""

from enum import StrEnum


class Segmento(StrEnum):
    INFANTIL = "INFANTIL"
    FUNDAMENTAL = "FUNDAMENTAL"


class Serie(StrEnum):
    MATERNAL_1 = "MATERNAL_1"
    MATERNAL_2 = "MATERNAL_2"
    INFANTIL_1 = "INFANTIL_1"
    INFANTIL_2 = "INFANTIL_2"
    ANO_1 = "ANO_1"
    ANO_2 = "ANO_2"
    ANO_3 = "ANO_3"
    ANO_4 = "ANO_4"
    ANO_5 = "ANO_5"

    @property
    def label(self) -> str:
        return SERIE_LABELS[self]

    @property
    def segmento(self) -> Segmento:
        return segmento_da_serie(self)


SERIE_LABELS: dict[Serie, str] = {
    Serie.MATERNAL_1: "Maternal 1",
    Serie.MATERNAL_2: "Maternal 2",
    Serie.INFANTIL_1: "Infantil 1",
    Serie.INFANTIL_2: "Infantil 2",
    Serie.ANO_1: "1º ano",
    Serie.ANO_2: "2º ano",
    Serie.ANO_3: "3º ano",
    Serie.ANO_4: "4º ano",
    Serie.ANO_5: "5º ano",
}

_INFANTIL = {Serie.MATERNAL_1, Serie.MATERNAL_2, Serie.INFANTIL_1, Serie.INFANTIL_2}


def segmento_da_serie(serie: Serie) -> Segmento:
    return Segmento.INFANTIL if serie in _INFANTIL else Segmento.FUNDAMENTAL


class Turno(StrEnum):
    MANHA = "MANHA"
    TARDE = "TARDE"
    INTEGRAL = "INTEGRAL"
