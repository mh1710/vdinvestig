import os
import sys
import re
import logging
from typing import Dict, Any, List, Optional
import httpx

# Ensure vendor/sniff-cross is importable
vendor_sniff_cross = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "vendor", "sniff-cross"))
if vendor_sniff_cross not in sys.path:
    sys.path.insert(0, vendor_sniff_cross)

try:
    from sniff_cross import get_cnpj_data as sniff_cross_get_cnpj
except ImportError:
    sniff_cross_get_cnpj = None

logger = logging.getLogger("cnpj_service")

def clean_cnpj(cnpj: str) -> str:
    """Removes all non-digit characters from CNPJ."""
    return re.sub(r"\D", "", cnpj or "")

def validate_cnpj(cnpj: str) -> bool:
    """Validates 14-digit CNPJ format."""
    cleaned = clean_cnpj(cnpj)
    return len(cleaned) == 14 and cleaned.isdigit()

def format_cnpj(cnpj: str) -> str:
    """Formats CNPJ as XX.XXX.XXX/XXXX-XX."""
    cleaned = clean_cnpj(cnpj)
    if len(cleaned) != 14:
        return cnpj
    return f"{cleaned[:2]}.{cleaned[2:5]}.{cleaned[5:8]}/{cleaned[8:12]}-{cleaned[12:]}"

def fetch_cnpj_data(cnpj: str) -> Dict[str, Any]:
    """
    Fetches real live company data via SniffCross module with fallbacks.
    1. SniffCross (BrasilAPI direct core)
    2. CNPJ.ws (https://publica.cnpj.ws/cnpj/{cnpj})
    3. MinhaReceita (https://minhareceita.org/{cnpj})
    """
    cleaned = clean_cnpj(cnpj)
    if not validate_cnpj(cleaned):
        raise ValueError(f"CNPJ inválido: '{cnpj}'. Deve possuir 14 dígitos.")

    errors = []

    # Attempt 1: Direct SniffCross module call
    if sniff_cross_get_cnpj:
        try:
            raw_sniff_data = sniff_cross_get_cnpj(cleaned)
            if raw_sniff_data and isinstance(raw_sniff_data, dict):
                return _normalize_brasilapi(raw_sniff_data, source="SniffCross (BrasilAPI)")
            errors.append("SniffCross returned empty or 404 response")
        except Exception as e:
            errors.append(f"SniffCross error: {str(e)}")

    # Attempt 2: BrasilAPI Direct HTTP
    try:
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cleaned}"
        with httpx.Client(timeout=8.0, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return _normalize_brasilapi(data, source="BrasilAPI")
            else:
                errors.append(f"BrasilAPI status {resp.status_code}")
    except Exception as e:
        errors.append(f"BrasilAPI error: {str(e)}")

    # Attempt 3: CNPJ.ws
    try:
        url = f"https://publica.cnpj.ws/cnpj/{cleaned}"
        with httpx.Client(timeout=8.0, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return _normalize_cnpjws(data)
            else:
                errors.append(f"CNPJ.ws status {resp.status_code}")
    except Exception as e:
        errors.append(f"CNPJ.ws error: {str(e)}")

    # Attempt 4: MinhaReceita
    try:
        url = f"https://minhareceita.org/{cleaned}"
        with httpx.Client(timeout=8.0, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if "razao_social" in data:
                    return _normalize_minhareceita(data)
                errors.append("MinhaReceita returned error message")
            else:
                errors.append(f"MinhaReceita status {resp.status_code}")
    except Exception as e:
        errors.append(f"MinhaReceita error: {str(e)}")

    raise RuntimeError(f"Não foi possível obter dados para o CNPJ {format_cnpj(cleaned)}. Erros: {'; '.join(errors)}")


def search_company_by_name(query: str) -> List[Dict[str, Any]]:
    """
    Searches for company CNPJs by name using MinhaReceita/BrasilAPI/CNPJ lookup queries.
    """
    query_clean = query.strip()
    if not query_clean:
        return []

    if validate_cnpj(query_clean):
        try:
            data = fetch_cnpj_data(query_clean)
            return [{
                "cnpj": data["cnpj"],
                "cnpj_formatted": data["cnpj_formatted"],
                "razao_social": data["razao_social"],
                "nome_fantasia": data["nome_fantasia"],
                "uf": data.get("uf", ""),
                "municipio": data.get("municipio", ""),
                "situacao_cadastral": data.get("situacao_cadastral", "Ativa")
            }]
        except Exception:
            return []

    results = []
    try:
        url = f"https://minhareceita.org/{query_clean}"
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url)
            if resp.status_code == 200 and "razao_social" in resp.json():
                item = resp.json()
                norm = _normalize_minhareceita(item)
                results.append({
                    "cnpj": norm["cnpj"],
                    "cnpj_formatted": norm["cnpj_formatted"],
                    "razao_social": norm["razao_social"],
                    "nome_fantasia": norm["nome_fantasia"],
                    "uf": norm.get("uf", ""),
                    "municipio": norm.get("municipio", ""),
                    "situacao_cadastral": norm.get("situacao_cadastral", "Ativa")
                })
    except Exception:
        pass

    return results


def _normalize_brasilapi(data: Dict[str, Any], source: str = "BrasilAPI") -> Dict[str, Any]:
    cnpj = clean_cnpj(str(data.get("cnpj", "")))

    qsa = []
    for q in data.get("qsa", []) or []:
        qsa.append({
            "nome": q.get("nome_socio", q.get("nome", "Não informado")),
            "qualificacao": q.get("qualificacao_socio", q.get("descricao_qualificacao_socio", q.get("qualificacao", "Sócio/Administrador"))),
            "cpf_cnpj": q.get("cnpj_cpf_do_socio", q.get("cpf_cnpj_socio", "")),
            "faixa_etaria": q.get("faixa_etaria", "Não informada"),
            "data_entrada": q.get("data_entrada_sociedad", q.get("data_entrada", ""))
        })

    cnaes_secundarios = []
    for cnae in data.get("cnaes_secundarios", []) or []:
        cnaes_secundarios.append({
            "code": str(cnae.get("codigo", "")),
            "description": cnae.get("descricao", "")
        })

    atividade_principal = {
        "code": str(data.get("cnae_fiscal", "")),
        "description": data.get("cnae_fiscal_descricao", "")
    }

    capital_social = float(data.get("capital_social", 0.0) or 0.0)

    return {
        "source": source,
        "cnpj": cnpj,
        "cnpj_formatted": format_cnpj(cnpj),
        "razao_social": data.get("razao_social", ""),
        "nome_fantasia": data.get("nome_fantasia", "") or data.get("razao_social", ""),
        "situacao_cadastral": data.get("descricao_situacao_cadastral", data.get("situacao_cadastral", "Ativa")),
        "data_situacao_cadastral": data.get("data_situacao_cadastral", ""),
        "data_inicio_atividade": data.get("data_inicio_atividade", ""),
        "matriz_filial": "Matriz" if data.get("identificador_matriz_filial") == 1 else "Filial",
        "natureza_juridica": data.get("natureza_juridica", ""),
        "porte": data.get("porte", "Não informado"),
        "capital_social": capital_social,
        "capital_social_formatted": f"R$ {capital_social:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "logradouro": data.get("logradouro", ""),
        "numero": str(data.get("numero", "")),
        "complemento": data.get("complemento", ""),
        "bairro": data.get("bairro", ""),
        "municipio": data.get("municipio", ""),
        "uf": data.get("uf", ""),
        "cep": data.get("cep", ""),
        "email": data.get("email", ""),
        "ddd_telefone": f"({data.get('ddd1', '')}) {data.get('telefone1', '')}".strip() if data.get('ddd1') else "",
        "atividade_principal": atividade_principal,
        "cnaes_secundarios": cnaes_secundarios,
        "qsa": qsa
    }


def _normalize_cnpjws(data: Dict[str, Any]) -> Dict[str, Any]:
    est = data.get("estabelecimento", {}) or {}
    cnpj = clean_cnpj(str(est.get("cnpj", "")))

    qsa = []
    for q in data.get("socios", []) or []:
        qual = q.get("qualificacao_socio", {}) or {}
        qsa.append({
            "nome": q.get("nome", "Não informado"),
            "qualificacao": qual.get("descricao", "Sócio/Administrador"),
            "cpf_cnpj": q.get("cpf_cnpj_socio", ""),
            "faixa_etaria": q.get("faixa_etaria", "Não informada"),
            "data_entrada": q.get("data_entrada", "")
        })

    cnaes_secundarios = []
    for cnae in est.get("atividades_secundarias", []) or []:
        cnaes_secundarios.append({
            "code": str(cnae.get("subclasse", cnae.get("id", ""))),
            "description": cnae.get("descricao", "")
        })

    act_p = est.get("atividade_principal", {}) or {}
    atividade_principal = {
        "code": str(act_p.get("subclasse", act_p.get("id", ""))),
        "description": act_p.get("descricao", "")
    }

    capital_social = 0.0
    try:
        capital_social = float(data.get("capital_social", 0.0) or 0.0)
    except Exception:
        pass

    est_uf = est.get("estado", {})
    uf_str = est_uf.get("sigla", "") if isinstance(est_uf, dict) else str(est_uf)

    est_mun = est.get("cidade", {})
    mun_str = est_mun.get("nome", "") if isinstance(est_mun, dict) else str(est_mun)

    tel = f"({est.get('ddd1', '')}) {est.get('telefone1', '')}".strip() if est.get("ddd1") else ""

    return {
        "source": "CNPJ.ws",
        "cnpj": cnpj,
        "cnpj_formatted": format_cnpj(cnpj),
        "razao_social": data.get("razao_social", ""),
        "nome_fantasia": est.get("nome_fantasia", "") or data.get("razao_social", ""),
        "situacao_cadastral": est.get("situacao_cadastral", "Ativa"),
        "data_situacao_cadastral": est.get("data_situacao_cadastral", ""),
        "data_inicio_atividade": est.get("data_inicio_atividade", ""),
        "matriz_filial": est.get("tipo", "Matriz"),
        "natureza_juridica": data.get("natureza_juridica", {}).get("descricao", "") if isinstance(data.get("natureza_juridica"), dict) else str(data.get("natureza_juridica", "")),
        "porte": data.get("porte", {}).get("descricao", "Não informado") if isinstance(data.get("porte"), dict) else str(data.get("porte", "")),
        "capital_social": capital_social,
        "capital_social_formatted": f"R$ {capital_social:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "logradouro": est.get("logradouro", ""),
        "numero": str(est.get("numero", "")),
        "complemento": est.get("complemento", ""),
        "bairro": est.get("bairro", ""),
        "municipio": mun_str,
        "uf": uf_str,
        "cep": est.get("cep", ""),
        "email": est.get("email", ""),
        "ddd_telefone": tel,
        "atividade_principal": atividade_principal,
        "cnaes_secundarios": cnaes_secundarios,
        "qsa": qsa
    }


def _normalize_minhareceita(data: Dict[str, Any]) -> Dict[str, Any]:
    cnpj = clean_cnpj(str(data.get("cnpj", "")))

    qsa = []
    for q in data.get("qsa", []) or []:
        qsa.append({
            "nome": q.get("nome_socio", q.get("nome", "Não informado")),
            "qualificacao": q.get("qualificacao_socio", q.get("qualificacao", "Sócio/Administrador")),
            "cpf_cnpj": q.get("cnpj_cpf_do_socio", q.get("cpf_cnpj_socio", "")),
            "faixa_etaria": q.get("faixa_etaria", "Não informada"),
            "data_entrada": q.get("data_entrada_sociedade", "")
        })

    cnaes_secundarios = []
    for cnae in data.get("cnaes_secundarios", []) or []:
        cnaes_secundarios.append({
            "code": str(cnae.get("codigo", "")),
            "description": cnae.get("descricao", "")
        })

    atividade_principal = {
        "code": str(data.get("cnae_fiscal", "")),
        "description": data.get("cnae_fiscal_descricao", "")
    }

    capital_social = float(data.get("capital_social", 0.0) or 0.0)

    return {
        "source": "MinhaReceita",
        "cnpj": cnpj,
        "cnpj_formatted": format_cnpj(cnpj),
        "razao_social": data.get("razao_social", ""),
        "nome_fantasia": data.get("nome_fantasia", "") or data.get("razao_social", ""),
        "situacao_cadastral": data.get("descricao_situacao_cadastral", "Ativa"),
        "data_situacao_cadastral": data.get("data_situacao_cadastral", ""),
        "data_inicio_atividade": data.get("data_inicio_atividade", ""),
        "matriz_filial": "Matriz" if data.get("identificador_matriz_filial") == 1 else "Filial",
        "natureza_juridica": data.get("natureza_juridica", ""),
        "porte": data.get("porte", "Não informado"),
        "capital_social": capital_social,
        "capital_social_formatted": f"R$ {capital_social:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "logradouro": data.get("logradouro", ""),
        "numero": str(data.get("numero", "")),
        "complemento": data.get("complemento", ""),
        "bairro": data.get("bairro", ""),
        "municipio": data.get("municipio", ""),
        "uf": data.get("uf", ""),
        "cep": data.get("cep", ""),
        "email": data.get("email", ""),
        "ddd_telefone": data.get("ddd_telefone_1", data.get("ddd_telefone", "")),
        "atividade_principal": atividade_principal,
        "cnaes_secundarios": cnaes_secundarios,
        "qsa": qsa
    }
