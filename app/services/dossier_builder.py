from typing import Dict, Any, List
from datetime import datetime
from app.services.cnpj_service import fetch_cnpj_data, format_cnpj
from app.services.tech_osint_service import extract_domain_from_text, query_registro_br, analyze_tech_stack
from app.services.osint_brazuca_service import generate_osint_brazuca_resources

def build_sales_dossier(cnpj_or_query: str) -> Dict[str, Any]:
    """
    Synthesizes raw OSINT data from CNPJ lookup, Registro.br, Tech stack inspection,
    and OSINT-Brazuca investigative resources into a complete Commercial Sales Dossier.
    """
    # 1. Fetch CNPJ OSINT Data
    cnpj_data = fetch_cnpj_data(cnpj_or_query)

    # Extract details
    razao_social = cnpj_data.get("razao_social", "")
    nome_fantasia = cnpj_data.get("nome_fantasia", "") or razao_social
    cnpj_formatted = cnpj_data.get("cnpj_formatted", "")
    email = cnpj_data.get("email", "")

    # 2. Extract Domain and Tech OSINT
    domain = extract_domain_from_text(email) or extract_domain_from_text(nome_fantasia)

    rdap_data = {}
    tech_stack = {}
    if domain:
        rdap_data = query_registro_br(domain)
        tech_stack = analyze_tech_stack(domain)
    else:
        tech_stack = {
            "domain": "Não identificado",
            "email_provider": "Desconhecido",
            "dns_provider": "Desconhecido",
            "web_hosting": "Desconhecido",
            "detected_services": []
        }

    # 3. Decision Makers & QSA
    qsa_list = cnpj_data.get("qsa", [])
    qsa_names = [q["nome"] for q in qsa_list if q.get("nome")]

    # 4. OSINT Brazuca Resources & Dorks
    osint_brazuca = generate_osint_brazuca_resources(
        razao_social=razao_social,
        cnpj=cnpj_formatted,
        nome_fantasia=nome_fantasia,
        qsa_names=qsa_names,
        domain=domain
    )

    # 5. Generate Commercial Intelligence Insights
    commercial_insights = _generate_commercial_insights(cnpj_data, tech_stack, rdap_data)

    # 6. Assemble Final Dossier Object
    dossier = {
        "metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "lead_name": nome_fantasia or razao_social,
            "cnpj": cnpj_formatted,
            "status": "Dossiê Concluído"
        },
        "executive_summary": commercial_insights["executive_summary"],
        "company_profile": cnpj_data,
        "decision_makers": {
            "qsa": qsa_list,
            "total_socio_count": len(qsa_list),
            "key_executives": qsa_names[:5]
        },
        "digital_footprint": {
            "domain": domain or "Não cadastrado/encontrado",
            "rdap": rdap_data,
            "tech_stack": tech_stack
        },
        "osint_brazuca": osint_brazuca,
        "sales_playbook": {
            "icebreakers": commercial_insights["icebreakers"],
            "pain_points": commercial_insights["pain_points"],
            "pitch_angles": commercial_insights["pitch_angles"],
            "tech_opportunities": commercial_insights["tech_opportunities"],
            "risk_flags": commercial_insights["risk_flags"]
        }
    }

    return dossier


def _generate_commercial_insights(
    cnpj_data: Dict[str, Any],
    tech_stack: Dict[str, Any],
    rdap_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generates strategic sales arguments, icebreakers, and pain point predictions based on OSINT data.
    """
    razao = cnpj_data.get("razao_social", "")
    fantasia = cnpj_data.get("nome_fantasia", "") or razao
    porte = cnpj_data.get("porte", "Empresa")
    uf = cnpj_data.get("uf", "")
    municipio = cnpj_data.get("municipio", "")
    capital = cnpj_data.get("capital_social_formatted", "R$ 0,00")
    cnae_desc = cnpj_data.get("atividade_principal", {}).get("description", "Atividades Comerciais")
    qsa = cnpj_data.get("qsa", [])

    # Executive Summary
    summary_parts = [
        f"A **{fantasia}** ({razao}) é uma empresa de porte **{porte}** sediada em **{municipio}/{uf}**.",
        f"Atua no segmento de **{cnae_desc}**, com capital social declarado de **{capital}**."
    ]
    if qsa:
        socio_names = ", ".join([s["nome"].title() for s in qsa[:2]])
        summary_parts.append(f"O quadro societário principal inclui **{socio_names}**.")

    if tech_stack.get("detected_services"):
        techs = ", ".join(tech_stack["detected_services"])
        summary_parts.append(f"Stack tecnológica/ferramentas detectadas: **{techs}**.")

    executive_summary = " ".join(summary_parts)

    # Icebreakers for Sales Reps
    icebreakers = [
        f"Acompanho a expansão da {fantasia} em {municipio}/{uf} e notei a forte atuação no setor de {cnae_desc.lower()}.",
        f"Parabéns pela trajetória e estrutura consolidada em {municipio} desde a abertura da empresa."
    ]
    if qsa:
        icebreakers.append(f"Gostaria de agendar uma breve conversa estratégica direta com a diretoria/sócios ({qsa[0]['nome'].title()}).")

    # Pain Points based on CNAE and Tech Stack
    pain_points = []
    if "Google Workspace" in tech_stack.get("detected_services", []):
        pain_points.append("Otimização do ecossistema Google para maior eficiência no trabalho remoto e segurança da informação.")
    elif "Microsoft 365" in tech_stack.get("detected_services", []):
        pain_points.append("Redução de custos com licenças Microsoft e integração com ferramentas de automação comercial.")
    else:
        pain_points.append("Profissionalização de e-mails corporativos e segurança contra ataques de phishing e engenharia social.")

    if "RD Station Marketing/CRM" in tech_stack.get("detected_services", []):
        pain_points.append("Alinhamento do fluxo do RD Station com a equipe comercial para aumentar taxas de conversão de MQL para SQL.")
    else:
        pain_points.append("Necessidade de automação de prospecção outbound e CRM estruturado para aumentar o funil de vendas.")

    pain_points.append(f"Escalabilidade dos processos operacionais no setor de {cnae_desc.lower()}.")

    # Pitch Angles
    pitch_angles = [
        f"**Eficiência Financeira e ROI:** Apresentar como a solução impacta diretamente a margem de lucro para uma empresa com estrutura declarada de {capital}.",
        f"**Segurança & Governança:** Destaque para mitigação de riscos operacionais e adequação às normas de mercado no segmento de {cnae_desc.lower()}.",
        "**Aceleração de Vendas:** Como otimizar a abordagem comercial direcionando os principais tomadores de decisão mapeados no QSA."
    ]

    # Tech Opportunities
    tech_opportunities = []
    if tech_stack.get("detected_services"):
        tech_opportunities.append(f"A empresa já utiliza **{', '.join(tech_stack['detected_services'])}**, demonstrando maturidade e abertura para inovação tecnológica.")
    else:
        tech_opportunities.append("Oportunidade de introduzir modernização digital e infraestrutura de software de alta performance.")

    # Risk Flags
    risk_flags = []
    situacao = cnpj_data.get("situacao_cadastral", "Ativa")
    if situacao.lower() != "ativa":
        risk_flags.append(f"⚠️ Atenção: Situação Cadastral na Receita Federal é **{situacao}**.")
    else:
        risk_flags.append("✅ Situação Cadastral ATIVA perante a Receita Federal do Brasil.")

    if cnpj_data.get("capital_social", 0) == 0:
        risk_flags.append("ℹ️ Capital Social declarado como R$ 0,00 ou não informado no cadastro oficial.")

    return {
        "executive_summary": executive_summary,
        "icebreakers": icebreakers,
        "pain_points": pain_points,
        "pitch_angles": pitch_angles,
        "tech_opportunities": tech_opportunities,
        "risk_flags": risk_flags
    }
