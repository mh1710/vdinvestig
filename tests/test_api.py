import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_api_search_cnpj():
    response = client.get("/api/search/cnpj/00000000000191")
    assert response.status_code == 200
    data = response.json()
    assert data["company_profile"]["cnpj"] == "00000000000191"

def test_api_generate_dossier():
    response = client.post("/api/dossier/generate", json={"query": "00.000.000/0001-91"})
    assert response.status_code == 200
    data = response.json()
    assert "executive_summary" in data

def test_api_export_markdown():
    dossier_mock = {
        "metadata": {"lead_name": "TESTE", "cnpj": "00000000000191", "generated_at": "2026-01-01"},
        "executive_summary": "Resumo de teste",
        "company_profile": {"razao_social": "TESTE S.A."},
        "sales_playbook": {"icebreakers": ["Gelo 1"], "pain_points": ["Dor 1"]},
        "digital_footprint": {"domain": "teste.com.br", "tech_stack": {"detected_services": ["Google Workspace"]}},
        "decision_makers": {"qsa": [{"nome": "SOCIO 1", "qualificacao": "Diretor"}]}
    }
    response = client.post("/api/dossier/export/markdown", json={"dossier": dossier_mock})
    assert response.status_code == 200
    assert "DOSSIÊ COMMERCIAL OSINT" in response.json()["markdown"]
