import pytest
from app.services.cnpj_service import clean_cnpj, validate_cnpj, format_cnpj, fetch_cnpj_data

def test_clean_cnpj():
    assert clean_cnpj("00.000.000/0001-91") == "00000000000191"
    assert clean_cnpj(" 12.345.678/0001-95 ") == "12345678000195"

def test_validate_cnpj():
    assert validate_cnpj("00000000000191") is True
    assert validate_cnpj("00.000.000/0001-91") is True
    assert validate_cnpj("1234") is False
    assert validate_cnpj("0000000000019A") is False

def test_format_cnpj():
    assert format_cnpj("00000000000191") == "00.000.000/0001-91"
    assert format_cnpj("00.000.000/0001-91") == "00.000.000/0001-91"

def test_fetch_cnpj_data_valid():
    data = fetch_cnpj_data("00000000000191")
    assert data["cnpj"] == "00000000000191"
    assert "BANCO DO BRASIL" in data["razao_social"].upper()
    assert len(data["qsa"]) > 0
    assert data["capital_social"] > 0
