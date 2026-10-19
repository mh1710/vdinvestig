import pytest
from app.services.dossier_builder import build_sales_dossier
from app.services.osint_brazuca_service import generate_osint_brazuca_resources
from app.services.tech_osint_service import extract_domain_from_text, analyze_tech_stack

def test_extract_domain():
    assert extract_domain_from_text("contato@empresa.com.br") == "empresa.com.br"
    assert extract_domain_from_text("https://www.meusite.com.br/page") == "meusite.com.br"
    assert extract_domain_from_text("user@gmail.com") is None

def test_generate_osint_brazuca_resources():
    res = generate_osint_brazuca_resources(
        razao_social="EMPRESA EXEMPLO LTDA",
        cnpj="12.345.678/0001-95",
        nome_fantasia="EXEMPLO TECH",
        qsa_names=["JOAO SILVA", "MARIA SANTOS"],
        domain="exemplo.com.br"
    )
    assert res["summary"]["total_categories"] > 0
    assert res["summary"]["total_sources_indexed"] > 500
    assert res["summary"]["total_links_generated"] > 10

def test_build_sales_dossier():
    dossier = build_sales_dossier("00000000000191")
    assert dossier["metadata"]["cnpj"] == "00.000.000/0001-91"
    assert "executive_summary" in dossier
    assert len(dossier["sales_playbook"]["icebreakers"]) > 0
    assert len(dossier["sales_playbook"]["pain_points"]) > 0
    assert "osint_brazuca" in dossier
