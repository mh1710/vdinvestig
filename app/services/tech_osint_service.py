import re
import socket
import logging
from typing import Dict, Any, List, Optional
import httpx
import dns.resolver

logger = logging.getLogger("tech_osint_service")

def extract_domain_from_text(text: str) -> Optional[str]:
    """Extracts a clean domain name from website URL, email, or company name."""
    if not text:
        return None

    # Try finding domain in email
    email_match = re.search(r"@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text)
    if email_match:
        domain = email_match.group(1).lower()
        if not any(free in domain for free in ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "bol.com.br", "uol.com.br"]):
            return domain

    # Try clean URL
    text_clean = text.strip().lower()
    text_clean = re.sub(r"^https?://", "", text_clean)
    text_clean = re.sub(r"^www\.", "", text_clean)
    text_clean = text_clean.split("/")[0].split(":")[0]

    if re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", text_clean):
        return text_clean

    return None

def query_registro_br(domain: str) -> Dict[str, Any]:
    """
    Queries Registro.br RDAP endpoint for .br domains.
    URL: https://rdap.registro.br/domain/{domain}
    """
    domain = domain.lower().strip()
    result = {
        "domain": domain,
        "is_br": domain.endswith(".br"),
        "registered": False,
        "status": [],
        "owner": None,
        "owner_id": None,
        "nameservers": [],
        "created_at": None,
        "updated_at": None,
        "expires_at": None,
        "contacts": []
    }

    if not domain.endswith(".br"):
        result["notes"] = "Domínio não é .br. RDAP do Registro.br é exclusivo para domínios .br."
        return result

    try:
        url = f"https://rdap.registro.br/domain/{domain}"
        with httpx.Client(timeout=8.0, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                result["registered"] = True
                result["status"] = data.get("status", [])

                # Entities / Owner
                entities = data.get("entities", [])
                for entity in entities:
                    roles = entity.get("roles", [])
                    vcard = entity.get("vcardArray", [])
                    fn = None
                    if isinstance(vcard, list) and len(vcard) > 1:
                        for field in vcard[1]:
                            if isinstance(field, list) and len(field) > 3 and field[0] == "fn":
                                fn = field[3]

                    if "registrant" in roles:
                        result["owner"] = fn or entity.get("handle")
                        result["owner_id"] = entity.get("publicIds", [{}])[0].get("identifier") if entity.get("publicIds") else None

                    result["contacts"].append({
                        "handle": entity.get("handle"),
                        "roles": roles,
                        "name": fn
                    })

                # Nameservers
                ns_list = data.get("nameservers", [])
                for ns in ns_list:
                    result["nameservers"].append(ns.get("ldhName"))

                # Events
                events = data.get("events", [])
                for ev in events:
                    action = ev.get("eventAction")
                    date = ev.get("eventDate")
                    if action == "registration":
                        result["created_at"] = date
                    elif action == "last changed":
                        result["updated_at"] = date
                    elif action == "expiration":
                        result["expires_at"] = date

            elif resp.status_code == 404:
                result["registered"] = False
                result["notes"] = "Domínio não encontrado no Registro.br (Disponível para registro)."
            else:
                result["notes"] = f"Registro.br retornou status {resp.status_code}"
    except Exception as e:
        result["notes"] = f"Erro na consulta Registro.br RDAP: {str(e)}"

    return result

def analyze_tech_stack(domain: str) -> Dict[str, Any]:
    """
    Analyzes domain DNS records (MX, NS, A, TXT) and HTTP headers
    to detect corporate tech stack (Email Provider, Hosting, CDN, CRM/Marketing).
    """
    stack = {
        "domain": domain,
        "email_provider": "Desconhecido / Próprio",
        "dns_provider": "Desconhecido",
        "web_hosting": "Desconhecido",
        "mx_records": [],
        "ns_records": [],
        "txt_records": [],
        "detected_services": []
    }

    # 1. Query DNS MX Records
    try:
        mx_answers = dns.resolver.resolve(domain, "MX")
        mx_list = [str(r.exchange).rstrip(".").lower() for r in mx_answers]
        stack["mx_records"] = mx_list

        for mx in mx_list:
            if "google" in mx or "gmail" in mx or "googlemail" in mx:
                stack["email_provider"] = "Google Workspace (Gmail Corp)"
                stack["detected_services"].append("Google Workspace")
            elif "outlook" in mx or "microsoft" in mx or "protection.outlook.com" in mx:
                stack["email_provider"] = "Microsoft 365 (Exchange Online)"
                stack["detected_services"].append("Microsoft 365")
            elif "locaweb" in mx:
                stack["email_provider"] = "Locaweb Mail"
                stack["detected_services"].append("Locaweb")
            elif "hostgator" in mx:
                stack["email_provider"] = "HostGator Webmail"
                stack["detected_services"].append("HostGator")
            elif "kinghost" in mx:
                stack["email_provider"] = "KingHost"
                stack["detected_services"].append("KingHost")
            elif "zoho" in mx:
                stack["email_provider"] = "Zoho Mail"
                stack["detected_services"].append("Zoho")
            elif "umbler" in mx:
                stack["email_provider"] = "Umbler Mail"
                stack["detected_services"].append("Umbler")
            elif "secureserver.net" in mx or "godaddy" in mx:
                stack["email_provider"] = "GoDaddy Email"
                stack["detected_services"].append("GoDaddy")
    except Exception:
        pass

    # 2. Query DNS NS Records
    try:
        ns_answers = dns.resolver.resolve(domain, "NS")
        ns_list = [str(r.target).rstrip(".").lower() for r in ns_answers]
        stack["ns_records"] = ns_list

        for ns in ns_list:
            if "cloudflare" in ns:
                stack["dns_provider"] = "Cloudflare DNS & Security"
                stack["detected_services"].append("Cloudflare")
            elif "awsdns" in ns:
                stack["dns_provider"] = "Amazon Route 53"
                stack["detected_services"].append("AWS Route 53")
            elif "azure-dns" in ns:
                stack["dns_provider"] = "Microsoft Azure DNS"
                stack["detected_services"].append("Azure DNS")
            elif "domaincontrol" in ns or "godaddy" in ns:
                stack["dns_provider"] = "GoDaddy DNS"
            elif "locaweb" in ns:
                stack["dns_provider"] = "Locaweb DNS"
            elif "registro.br" in ns:
                stack["dns_provider"] = "DNS Regulatório Registro.br"
    except Exception:
        pass

    # 3. Query DNS TXT Records (Marketing & CRM verification tags)
    try:
        txt_answers = dns.resolver.resolve(domain, "TXT")
        txt_list = [str(r).lower() for r in txt_answers]
        stack["txt_records"] = txt_list

        full_txt = " ".join(txt_list)
        if "rdstation" in full_txt or "rd-station" in full_txt:
            stack["detected_services"].append("RD Station Marketing/CRM")
        if "hubspot" in full_txt:
            stack["detected_services"].append("HubSpot CRM")
        if "salesforce" in full_txt or "pardot" in full_txt:
            stack["detected_services"].append("Salesforce / Pardot")
        if "activecampaign" in full_txt:
            stack["detected_services"].append("ActiveCampaign")
        if "mailchimp" in full_txt:
            stack["detected_services"].append("Mailchimp")
        if "zendesk" in full_txt:
            stack["detected_services"].append("Zendesk Support")
        if "pipedrive" in full_txt:
            stack["detected_services"].append("Pipedrive CRM")
        if "spf.protection.outlook.com" in full_txt and "Microsoft 365" not in stack["detected_services"]:
            stack["detected_services"].append("Microsoft 365")
        if "_spf.google.com" in full_txt and "Google Workspace" not in stack["detected_services"]:
            stack["detected_services"].append("Google Workspace")
    except Exception:
        pass

    # 4. HTTP Headers Check
    try:
        with httpx.Client(timeout=4.0, follow_redirects=True) as client:
            resp = client.get(f"https://{domain}")
            server = resp.headers.get("server", "").lower()
            powered = resp.headers.get("x-powered-by", "").lower()

            if "nginx" in server:
                stack["web_hosting"] = "Nginx Web Server"
            elif "apache" in server:
                stack["web_hosting"] = "Apache HTTP Server"
            elif "cloudflare" in server:
                stack["web_hosting"] = "Cloudflare Edge Hosting"
            elif "cloudflare-nginx" in server:
                stack["web_hosting"] = "Cloudflare / Nginx"
            elif "amazons3" in server or "cloudfront" in server:
                stack["web_hosting"] = "AWS CloudFront / S3"
            elif "litespeed" in server:
                stack["web_hosting"] = "LiteSpeed Server"

            if "wordpress" in powered or "wp" in powered:
                stack["detected_services"].append("WordPress CMS")
            elif "php" in powered:
                stack["detected_services"].append("PHP Platform")
    except Exception:
        pass

    # Remove duplicates from detected_services
    stack["detected_services"] = list(dict.fromkeys(stack["detected_services"]))

    return stack
