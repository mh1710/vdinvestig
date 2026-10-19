import os
import sys
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from app.services.dossier_builder import build_sales_dossier
from app.services.cnpj_service import format_cnpj

console = Console()

def main():
    parser = argparse.ArgumentParser(
        description="Dossiê OSINT de Vendas - CLI de Inteligência Comercial (SniffCross + OSINT-Brazuca)"
    )
    parser.add_argument(
        "-c", "--cnpj",
        required=True,
        help="CNPJ ou nome da empresa para investigação OSINT"
    )

    args = parser.parse_args()

    console.print(f"[bold cyan]🔍 Gerando Dossiê OSINT de Vendas para: {args.cnpj}...[/bold cyan]")

    try:
        dossier = build_sales_dossier(args.cnpj)
        meta = dossier.get("metadata", {})
        comp = dossier.get("company_profile", {})
        play = dossier.get("sales_playbook", {})
        tech = dossier.get("digital_footprint", {}).get("tech_stack", {})
        qsa = dossier.get("decision_makers", {}).get("qsa", [])

        # Header Panel (SniffCross rich formatting style)
        header_text = (
            f"[bold]Razão Social:[/bold] {comp.get('razao_social', 'N/A')}\n"
            f"[bold]Nome Fantasia:[/bold] {comp.get('nome_fantasia', 'N/A')}\n"
            f"[bold]CNPJ:[/bold] {comp.get('cnpj_formatted', meta.get('cnpj', 'N/A'))}\n"
            f"[bold]Situação Cadastral:[/bold] {comp.get('situacao_cadastral', 'Ativa')}\n"
            f"[bold]Localidade:[/bold] {comp.get('municipio', 'N/A')} - {comp.get('uf', 'N/A')}\n"
            f"[bold]Capital Social:[/bold] {comp.get('capital_social_formatted', 'R$ 0,00')}\n"
            f"[bold]Provedor de E-mail:[/bold] {tech.get('email_provider', 'Desconhecido')}"
        )
        console.print(Panel(header_text, title=f"[bold green]📋 DOSSIÊ OSINT: {comp.get('nome_fantasia') or comp.get('razao_social')}[/bold green]", expand=False))

        # Executive Summary
        console.print("\n[bold blue]📌 Resumo Executivo:[/bold blue]")
        console.print(Markdown(dossier.get("executive_summary", "")))

        # QSA Table
        if qsa:
            table = Table(title="\n👥 Quadro de Sócios e Administradores (QSA)", show_header=True, header_style="bold magenta")
            table.add_column("Nome", style="cyan")
            table.add_column("Qualificação", style="yellow")
            table.add_column("CPF/CNPJ", style="white")

            for socio in qsa:
                table.add_row(socio.get("nome", "N/A"), socio.get("qualificacao", "N/A"), socio.get("cpf_cnpj", "N/A"))

            console.print(table)

        # Sales Playbook Icebreakers & Pain Points
        console.print("\n[bold green]💡 Quebra-Gelos (Icebreakers) para Reunião:[/bold green]")
        for ice in play.get("icebreakers", []):
            console.print(f" - {ice}")

        console.print("\n[bold yellow]🔥 Dores e Desafios Previstos:[/bold yellow]")
        for pain in play.get("pain_points", []):
            console.print(f" - {pain}")

        console.print(f"\n[bold green]✅ Dossiê concluído via SniffCross & OSINT-Brazuca Engine![/bold green]\n")

    except Exception as e:
        console.print(f"[bold red]Erro ao gerar dossiê:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
