import pytest

from app.shared.serie import SERIE_LABELS, Segmento, Serie, segmento_da_serie


@pytest.mark.parametrize(
    "serie", [Serie.MATERNAL_1, Serie.MATERNAL_2, Serie.INFANTIL_1, Serie.INFANTIL_2]
)
def test_infantil_series(serie):
    assert segmento_da_serie(serie) is Segmento.INFANTIL
    assert serie.segmento is Segmento.INFANTIL


@pytest.mark.parametrize("serie", [Serie.ANO_1, Serie.ANO_2, Serie.ANO_3, Serie.ANO_4, Serie.ANO_5])
def test_fundamental_series(serie):
    assert segmento_da_serie(serie) is Segmento.FUNDAMENTAL


def test_every_serie_has_label():
    assert set(SERIE_LABELS) == set(Serie)
    assert Serie.ANO_1.label == "1º ano"
