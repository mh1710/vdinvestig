import os
import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.services.cnpj_service import search_company_by_name, validate_cnpj, clean_cnpj
from app.services.dossier_builder import build_sales_dossier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dossier_app")

app = FastAPI(
    title="Dossiê OSINT de Vendas - Commercial OSINT Brasil",
    description="Aplicação de Inteligência de Fontes Abertas (OSINT) para Vendedores e SDRs realizarem pré-meeting de leads corporativos.",
    version="1.0.0"
)

# Models
class DossierRequest(BaseModel):
    query: str

class ExportMarkdownRequest(BaseModel):
    dossier: Dict[str, Any]

# API Endpoints
@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "Dossiê OSINT de Vendas"}

@app.get("/api/search/cnpj/{cnpj}")
def api_search_cnpj(cnpj: str):
    """Fetches real-time OSINT company data by CNPJ."""
    try:
        dossier = build_sales_dossier(cnpj)
        return dossier
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Erro ao buscar CNPJ {cnpj}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na extração OSINT: {str(e)}")

@app.get("/api/search/name")
def api_search_name(q: str = Query(..., min_length=2, description="Nome da empresa ou sócio")):
    """Searches for CNPJs by company or partner name."""
    try:
        results = search_company_by_name(q)
        return {"query": q, "results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Erro ao buscar por nome {q}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na busca por nome: {str(e)}")

@app.post("/api/dossier/generate")
def api_generate_dossier(payload: DossierRequest):
    """Generates complete Commercial Sales Dossier from CNPJ or Name query."""
    query_str = payload.query.strip()
    if not query_str:
        raise HTTPException(status_code=400, detail="Consulta não pode ser vazia.")

    try:
        # If query is CNPJ
        if validate_cnpj(query_str):
            return build_sales_dossier(query_str)

        # Search by name first
        search_res = search_company_by_name(query_str)
        if search_res:
            target_cnpj = search_res[0]["cnpj"]
            return build_sales_dossier(target_cnpj)

        raise HTTPException(status_code=404, detail=f"Nenhuma empresa encontrada com o termo '{query_str}'. Tente informar o CNPJ diretamente.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar dossiê para {query_str}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Falha na geração do Dossiê OSINT: {str(e)}")

@app.post("/api/dossier/export/markdown")
def api_export_markdown(payload: ExportMarkdownRequest):
    """Exports dossier data formatted as Markdown for CRM insertion (HubSpot/Salesforce)."""
    d = payload.dossier
    meta = d.get("metadata", {})
    comp = d.get("company_profile", {})
    play = d.get("sales_playbook", {})
    digital = d.get("digital_footprint", {})
    tech = digital.get("tech_stack", {})
    qsa = d.get("decision_makers", {}).get("qsa", [])

    md_lines = [
        f"# 📋 DOSSIÊ COMMERCIAL OSINT - {meta.get('lead_name', '')}",
        f"**CNPJ:** {meta.get('cnpj', '')} | **Gerado em:** {meta.get('generated_at', '')}",
        "---",
        "## 📌 Resumo Executivo",
        d.get("executive_summary", ""),
        "",
        "## 🏢 Perfil do Lead",
        f"- **Razão Social:** {comp.get('razao_social', '')}",
        f"- **Nome Fantasia:** {comp.get('nome_fantasia', '')}",
        f"- **Situação Cadastral:** {comp.get('situacao_cadastral', '')}",
        f"- **Porte:** {comp.get('porte', '')} | **Capital Social:** {comp.get('capital_social_formatted', '')}",
        f"- **Localização:** {comp.get('municipio', '')}/{comp.get('uf', '')}",
        f"- **Atividade Principal:** {comp.get('atividade_principal', {}).get('description', '')}",
        "",
        "## 👥 Quadro de Sócios e Decisores (QSA)"
    ]

    for socio in qsa:
        md_lines.append(f"- **{socio.get('nome', '')}** ({socio.get('qualificacao', '')})")

    md_lines.extend([
        "",
        "## 🌐 Presença Digital & Stack Tecnológico",
        f"- **Domínio:** {digital.get('domain', '')}",
        f"- **Serviços Detectados:** {', '.join(tech.get('detected_services', [])) or 'Nenhum serviço mapeado'}",
        f"- **Provedor de E-mail:** {tech.get('email_provider', '')}",
        "",
        "## 🎯 Playbook para Reunião de Vendas",
        "### 💡 Quebra-Gelos (Icebreakers)"
    ])
    for ice in play.get("icebreakers", []):
        md_lines.append(f"- {ice}")

    md_lines.append("\n### 🔥 Dores e Desafios Previstos")
    for pain in play.get("pain_points", []):
        md_lines.append(f"- {pain}")

    md_lines.append("\n### 🚀 Ângulos de Pitch Comercial")
    for pitch in play.get("pitch_angles", []):
        md_lines.append(f"- {pitch}")

    markdown_text = "\n".join(md_lines)
    return {"markdown": markdown_text}

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/", response_class=HTMLResponse)
def root_index():
    index_file = os.path.join(static_path, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h2>Dossiê OSINT de Vendas API Rodando</h2>")
