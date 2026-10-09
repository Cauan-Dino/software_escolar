import pytest
from pydantic import BaseModel, ValidationError

from app.shared.cpf import CPF, format_cpf, is_valid_cpf, mask_cpf, normalize_cpf


class Pessoa(BaseModel):
    cpf: CPF


@pytest.mark.parametrize("cpf", ["529.982.247-25", "52998224725", "111.444.777-35"])
def test_valid_cpfs(cpf):
    assert is_valid_cpf(cpf)


@pytest.mark.parametrize("cpf", ["111.111.111-11", "123.456.789-00", "1234", "", "abc"])
def test_invalid_cpfs(cpf):
    assert not is_valid_cpf(cpf)


def test_mask_hides_first_and_last_digits():
    assert mask_cpf("52998224725") == "***.982.247-**"
    assert mask_cpf(None) is None
    assert mask_cpf("123") == "***"


def test_normalize_and_format():
    assert normalize_cpf("529.982.247-25") == "52998224725"
    assert format_cpf("52998224725") == "529.982.247-25"


def test_pydantic_type_normalizes_and_validates():
    assert Pessoa(cpf="529.982.247-25").cpf == "52998224725"
    with pytest.raises(ValidationError):
        Pessoa(cpf="000.000.000-00")


def test_masked_cpf_type_masks_on_output():
    from app.shared.cpf import MaskedCPF

    class Item(BaseModel):
        cpf: MaskedCPF

    assert Item(cpf="52998224725").cpf == "***.982.247-**"
    assert Item(cpf=None).cpf is None
