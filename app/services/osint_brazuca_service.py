import urllib.parse
from typing import Dict, Any, List

def generate_osint_brazuca_resources(
    razao_social: str,
    cnpj: str,
    nome_fantasia: str = "",
    qsa_names: List[str] = None,
    domain: str = None
) -> Dict[str, Any]:
    """
    Generates OSINT Brazuca methodology links, search dorks, and investigative direct queries
    organized by OSINT-Brazuca categories:
    - Processos & Jurídico (Jusbrasil, Escavador, PJe)
    - Transparência & Sancionados (Portal da Transparência, CEIS, CNEP, TCU)
    - Reputação & Consumidor (Reclame Aqui, Consumidor.gov)
    - Diários Oficiais & Juntas (Jucesp, Dou, Jusbrasil Diários)
    - Redes Sociais & Decisores (LinkedIn, Instagram, Google Dorks)
    - Vazamentos & Documentos (Google Filetypes, Pastebin, GitHub)
    """
    qsa_names = qsa_names or []

    # Encoded parameters
    rs_enc = urllib.parse.quote(f'"{razao_social}"')
    nf_enc = urllib.parse.quote(f'"{nome_fantasia}"') if nome_fantasia else rs_enc
    cnpj_raw = cnpj.replace(".", "").replace("/", "").replace("-", "")
    cnpj_fmt = f"{cnpj_raw[:2]}.{cnpj_raw[2:5]}.{cnpj_raw[5:8]}/{cnpj_raw[8:12]}-{cnpj_raw[12:]}" if len(cnpj_raw) == 14 else cnpj_raw
    cnpj_enc = urllib.parse.quote(f'"{cnpj_fmt}" OR "{cnpj_raw}"')

    # Main search terms
    main_term = f'"{razao_social}" OR "{nome_fantasia}"' if nome_fantasia and nome_fantasia != razao_social else f'"{razao_social}"'
    main_term_enc = urllib.parse.quote(main_term)

    categories = []

    # 1. Processos Judicial & Execuções (Jusbrasil / Escavador)
    categories.append({
        "id": "juridico",
        "title": "⚖️ Processos & Contencioso Jurídico",
        "description": "Busca em tribunais, processos trabalhistas, cíveis e execuções fiscais.",
        "resources": [
            {
                "name": "Jusbrasil - Busca da Empresa",
                "url": f"https://www.jusbrasil.com.br/busca?q={main_term_enc}",
                "tag": "Jusbrasil",
                "notes": "Verifique processos ativos, reclamações trabalhistas e passivos judiciais."
            },
            {
                "name": "Escavador - Perfil e Processos",
                "url": f"https://www.escavador.com/busca?q={main_term_enc}",
                "tag": "Escavador",
                "notes": "Pesquisa unificada em Diários Oficiais e Tribunais de Justiça."
            },
            {
                "name": "Jusbrasil - CNPJ",
                "url": f"https://www.jusbrasil.com.br/busca?q={cnpj_enc}",
                "tag": "CNPJ Direct",
                "notes": "Citações diretas do CNPJ da empresa em decisões judiciais."
            }
        ]
    })

    # Add decision maker Jusbrasil searches
    for socio in qsa_names[:3]:
        socio_enc = urllib.parse.quote(f'"{socio}"')
        categories[0]["resources"].append({
            "name": f"Jusbrasil - Sócios/Diretores ({socio})",
            "url": f"https://www.jusbrasil.com.br/busca?q={socio_enc}",
            "tag": "Sócio OSINT",
            "notes": "Verificação de processos no nome pessoal do sócio/administrador."
        })

    # 2. Portal da Transparência & Sanções Públicas (CEIS / CNEP / TCU)
    categories.append({
        "id": "transparencia",
        "title": "🏛️ Transparência, Licitações & Sanções",
        "description": "Consulta de impedimentos de licitar, sanções administrativas e contratos públicos.",
        "resources": [
            {
                "name": "Portal da Transparência - CEIS / CNEP / Sanções",
                "url": f"https://portaldatransparencia.gov.br/busca?termo={cnpj_raw}",
                "tag": "Gov.br",
                "notes": "Consulte se a empresa possui sanções vigentes ou inidoneidade."
            },
            {
                "name": "TCU - Certidão de Inabilitados e Inidôneos",
                "url": "https://contas.tcu.gov.br/certidao/Web/Certidao/SolicitarCertidao.faces",
                "tag": "TCU",
                "notes": "Validação de inabilitação perante o Tribunal de Contas da União."
            },
            {
                "name": "Portal da Transparência - Contratos Públicos",
                "url": f"https://portaldatransparencia.gov.br/despesas/empresa?consulta={cnpj_raw}",
                "tag": "Licitante",
                "notes": "Identifique se o lead vende para o governo e o volume de repasses públicos."
            }
        ]
    })

    # 3. Reputação & Reclamações de Clientes (Reclame Aqui / Consumidor.gov)
    categories.append({
        "id": "reputacao",
        "title": "💬 Reputação, Reclame Aqui & Satisfação do Cliente",
        "description": "Análise da imagem da empresa, dores de clientes e falhas no atendimento.",
        "resources": [
            {
                "name": "Reclame Aqui - Busca do Lead",
                "url": f"https://www.google.com/search?q={urllib.parse.quote('site:reclameaqui.com.br ' + main_term)}",
                "tag": "Reclame Aqui",
                "notes": "Avaliação de índice de solução, nota de atendimento e principais queixas."
            },
            {
                "name": "Consumidor.gov.br",
                "url": f"https://www.consumidor.gov.br/pages/empresa/pesquisar?nome={main_term_enc}",
                "tag": "Senacon",
                "notes": "Base de reclamações registradas na Secretaria Nacional do Consumidor."
            },
            {
                "name": "Google Maps & Avaliações",
                "url": f"https://www.google.com/maps/search/{main_term_enc}",
                "tag": "Google Reviews",
                "notes": "Feedback direto de clientes em lojas e sedes físicas."
            }
        ]
    })

    # 4. Diários Oficiais e Juntas Comerciais
    categories.append({
        "id": "diarios",
        "title": "📜 Diários Oficiais & Juntas Comerciais",
        "description": "Publicações corporativas, atuações em licitações e alterações contratuais.",
        "resources": [
            {
                "name": "Diário Oficial da União (IN.gov.br)",
                "url": f"https://www.in.gov.br/consulta/-/buscar/dou?q={cnpj_enc}",
                "tag": "DOU Direct",
                "notes": "Busca em atas, editais e extratos publicados no DOU."
            },
            {
                "name": "Google Dork - Diários Oficiais Estaduais",
                "url": f"https://www.google.com/search?q={urllib.parse.quote('("diario oficial" OR "diário oficial") ' + main_term)}",
                "tag": "Google Dork",
                "notes": "Identifique publicações de balanços, licenças ambientais e atos oficiais."
            }
        ]
    })

    # 5. Redes Sociais, Decisores & Vagas de Emprego (LinkedIn / Instagram)
    social_resources = [
        {
            "name": "LinkedIn - Página da Empresa",
            "url": f"https://www.google.com/search?q={urllib.parse.quote('site:linkedin.com/company ' + main_term)}",
            "tag": "LinkedIn Company",
            "notes": "Análise do tamanho do time, vagas abertas e organograma."
        },
        {
            "name": "LinkedIn - Decisores & C-Levels",
            "url": f"https://www.google.com/search?q={urllib.parse.quote('site:linkedin.com/in ("CEO" OR "Diretor" OR "Gerente" OR "Sócio" OR "Founder") AND "' + (nome_fantasia or razao_social) + '"')}",
            "tag": "Executive Search",
            "notes": "Mapeamento direto dos executivos e tomar dores comerciais."
        },
        {
            "name": "Glassdoor / Catho - Vagas e Cultura",
            "url": f"https://www.google.com/search?q={urllib.parse.quote('site:glassdoor.com.br OR site:catho.com.br ' + main_term)}",
            "tag": "HR OSINT",
            "notes": "Avaliações internas de funcionários e áreas em expansão."
        }
    ]

    for socio in qsa_names[:3]:
        socio_enc = urllib.parse.quote(f'site:linkedin.com/in "{socio}"')
        social_resources.append({
            "name": f"LinkedIn Direct - Executivo ({socio})",
            "url": f"https://www.google.com/search?q={socio_enc}",
            "tag": "Sócio LinkedIn",
            "notes": "Perfil profissional direto do decisor da empresa."
        })

    categories.append({
        "id": "social",
        "title": "👥 Mapeamento de Decisores & Presença Digital",
        "description": "Identificação de tomadores de decisão no LinkedIn e mídias sociais.",
        "resources": social_resources
    })

    # 6. Vazamentos de Documentos & Google Dorks Avançados (OSINT-Brazuca style)
    leak_resources = [
        {
            "name": "Google Dork - PDFs e Apresentações Comerciais",
            "url": f"https://www.google.com/search?q={urllib.parse.quote('filetype:pdf OR filetype:pptx ("proposta" OR "tabela" OR "relatorio" OR "apresentacao") ' + main_term)}",
            "tag": "File Dork",
            "notes": "Descubra apresentações, propostas e catálogos públicos vazados no Google."
        },
        {
            "name": "Google Dork - Balanços & Planilhas Excel",
            "url": f"https://www.google.com/search?q={urllib.parse.quote('filetype:xls OR filetype:xlsx OR filetype:csv ' + main_term)}",
            "tag": "Excel Dork",
            "notes": "Arquivos de dados ou dados financeiros indexados publicamente."
        }
    ]

    if domain:
        leak_resources.append({
            "name": f"GitHub - Código Fonte e Chaves ({domain})",
            "url": f"https://github.com/search?q={urllib.parse.quote(domain)}&type=code",
            "tag": "GitHub Code",
            "notes": "Verificação de reputação técnica e possíveis dados do domínio em repositórios abertos."
        })

    categories.append({
        "id": "dorks",
        "title": "🔍 Google Dorks Avançados & Mídia Investigativa",
        "description": "Filtros avançados para localizar documentos internos, propostas e histórico.",
        "resources": leak_resources
    })

    return {
        "categories": categories,
        "summary": {
            "total_categories": len(categories),
            "total_links": sum(len(c["resources"]) for c in categories)
        }
    }
