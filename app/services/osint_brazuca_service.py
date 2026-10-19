import os
import json
import urllib.parse
from typing import Dict, Any, List

SOURCES_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "vendor", "osint-brazuca", "data", "sources.json"
))

_cached_sources = None

def _load_osint_brazuca_sources() -> List[Dict[str, Any]]:
    global _cached_sources
    if _cached_sources is not None:
        return _cached_sources

    if os.path.exists(SOURCES_PATH):
        try:
            with open(SOURCES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                _cached_sources = data.get("sources", [])
                return _cached_sources
        except Exception:
            pass

    _cached_sources = []
    return _cached_sources

def generate_osint_brazuca_resources(
    razao_social: str,
    cnpj: str,
    nome_fantasia: str = "",
    qsa_names: List[str] = None,
    domain: str = None
) -> Dict[str, Any]:
    """
    Integrates the real OSINT-Brazuca dataset (500+ sources from vendor/osint-brazuca/data/sources.json)
    and maps matching sources based on inputs: 'cnpj', 'nome', 'cpf', 'dominio'.
    """
    qsa_names = qsa_names or []
    sources = _load_osint_brazuca_sources()

    cnpj_raw = cnpj.replace(".", "").replace("/", "").replace("-", "")
    cnpj_fmt = f"{cnpj_raw[:2]}.{cnpj_raw[2:5]}.{cnpj_raw[5:8]}/{cnpj_raw[8:12]}-{cnpj_raw[12:]}" if len(cnpj_raw) == 14 else cnpj_raw
    main_name = nome_fantasia or razao_social

    # Group matched OSINT-Brazuca dataset items by category
    categories_map: Dict[str, List[Dict[str, Any]]] = {}

    # Helper to insert into category map
    def add_res(cat_title: str, cat_desc: str, item: Dict[str, Any]):
        if cat_title not in categories_map:
            categories_map[cat_title] = []
        categories_map[cat_title].append(item)

    # 1. Parse OSINT-Brazuca dataset sources
    for src in sources:
        cat_name = src.get("categoria", "Fontes Diversas (OSINT-Brazuca)")
        src_inputs = src.get("input", [])
        src_name = src.get("nome", "Fonte OSINT")
        links = src.get("links", [])

        # Check relevance
        is_relevant = False
        notes = src.get("descricao") or f"Fonte de {cat_name} (Dataset OSINT-Brazuca)"

        for link_obj in links:
            url_template = link_obj.get("url", "")
            if not url_template:
                continue

            # Build direct target URL
            target_url = url_template
            if "cnpj" in src_inputs or "cnpj" in url_template.lower():
                target_url = target_url.replace("{cnpj}", cnpj_raw).replace("{cnpj_formatted}", cnpj_fmt)
                is_relevant = True
            elif "nome" in src_inputs or "razao_social" in url_template.lower() or "termo" in url_template.lower():
                target_url = target_url.replace("{termo}", urllib.parse.quote(main_name)).replace("{nome}", urllib.parse.quote(main_name))
                is_relevant = font_relevant = True
            elif ("dominio" in src_inputs or "domain" in url_template.lower()) and domain:
                target_url = target_url.replace("{dominio}", domain).replace("{domain}", domain)
                is_relevant = True

            if is_relevant:
                add_res(
                    cat_title=f"🇧🇷 {cat_name}",
                    cat_desc="Bases abertas e portais catalogados no projeto OSINT-Brazuca.",
                    item={
                        "name": src_name,
                        "url": target_url,
                        "tag": "OSINT-Brazuca",
                        "notes": notes
                    }
                )

    # 2. Add Specialized Commercial & Dork Resources
    main_term_enc = urllib.parse.quote(f'"{razao_social}" OR "{main_name}"') if main_name != razao_social else urllib.parse.quote(f'"{razao_social}"')
    cnpj_enc = urllib.parse.quote(f'"{cnpj_fmt}" OR "{cnpj_raw}"')

    # Legal & Processual
    add_res(
        cat_title="⚖️ Processos & Contencioso (Jusbrasil / Escavador)",
        cat_desc="Investigação de passivos judiciais, processos trabalhistas e cíveis.",
        item={
            "name": f"Jusbrasil - Busca do Lead ({main_name})",
            "url": f"https://www.jusbrasil.com.br/busca?q={main_term_enc}",
            "tag": "Jusbrasil",
            "notes": "Pesquisa unificada em tribunais de justiça e diários oficiais."
        }
    )
    add_res(
        cat_title="⚖️ Processos & Contencioso (Jusbrasil / Escavador)",
        cat_desc="Investigação de passivos judiciais, processos trabalhistas e cíveis.",
        item={
            "name": f"Jusbrasil - Citações de CNPJ ({cnpj_fmt})",
            "url": f"https://www.jusbrasil.com.br/busca?q={cnpj_enc}",
            "tag": "CNPJ Direct",
            "notes": "Mapeamento de execuções fiscais e autos de infração diretos."
        }
    )

    for socio in qsa_names[:3]:
        socio_enc = urllib.parse.quote(f'"{socio}"')
        add_res(
            cat_title="⚖️ Processos & Contencioso (Jusbrasil / Escavador)",
            cat_desc="Investigação de passivos judiciais, processos trabalhistas e cíveis.",
            item={
                "name": f"Jusbrasil - Sócio/Diretor ({socio})",
                "url": f"https://www.jusbrasil.com.br/busca?q={socio_enc}",
                "tag": "QSA OSINT",
                "notes": "Verificação de histórico jurídico pessoal do sócio/executivo."
            }
        )

    # Transparência & Licitações
    add_res(
        cat_title="🏛️ Portal da Transparência & Sanções (CEIS / CNEP / TCU)",
        cat_desc="Checagem de impedimentos de licitar, inidoneidade e repasses públicos.",
        item={
            "name": "Portal da Transparência - CEIS/CNEP/Sanções",
            "url": f"https://portaldatransparencia.gov.br/busca?termo={cnpj_raw}",
            "tag": "Gov.br",
            "notes": "Consulte registros no Cadastro de Empresas Inidôneas e Suspensas."
        }
    )

    # Executive LinkedIn Search
    for socio in qsa_names[:3]:
        socio_enc = urllib.parse.quote(f'site:linkedin.com/in "{socio}"')
        add_res(
            cat_title="👥 Decisores & Perfis Profissionais (LinkedIn)",
            cat_desc="Mapeamento de executivos e tomadores de decisão.",
            item={
                "name": f"LinkedIn Executivo - {socio}",
                "url": f"https://www.google.com/search?q={socio_enc}",
                "tag": "LinkedIn Direct",
                "notes": "Perfil no LinkedIn do tomador de decisão mapeado no QSA."
            }
        )

    # Google Dorks Avançados
    add_res(
        cat_title="🔍 Google Dorks Avançados & Documentos Vazados",
        cat_desc="Busca em PDFs, apresentações comerciais, tabelas Excel e propostas indexadas.",
        item={
            "name": "Google Dork - Propostas e Apresentações (PDF/PPT)",
            "url": f"https://www.google.com/search?q={urllib.parse.quote('filetype:pdf OR filetype:pptx ("proposta" OR "relatorio" OR "apresentacao") ' + main_name)}",
            "tag": "File Dork",
            "notes": "Pesquisa por documentos corporativos abertos no Google."
        }
    )

    # Format into response array
    categories_list = []
    for title, res_list in categories_map.items():
        categories_list.append({
            "id": title.lower().replace(" ", "-"),
            "title": title,
            "description": res_list[0]["notes"] if res_list else "",
            "resources": res_list
        })

    return {
        "categories": categories_list,
        "summary": {
            "total_categories": len(categories_list),
            "total_sources_indexed": len(sources),
            "total_links_generated": sum(len(c["resources"]) for c in categories_list)
        }
    }
