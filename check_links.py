import re
import sys
from urllib.parse import urlparse
import os

# Domini consentiti che non devono essere contrassegnati come duplicati
ALLOWED_DOMAINS = {
    "github.com",
    "reddit.com",
    "robertsspaceindustries.com",
    "discord.com",
    "docs.google.com",
    "chatgpt.com"
}

def extract_domains(links):
    """Estrae i domini principali dai link, ignorando protocollo e percorsi."""
    domains = set()
    for link in links:
        parsed_url = urlparse(link)
        domain = parsed_url.netloc.lower()
        # Rimuove il prefisso 'www.' per evitare considerazioni sbagliate
        domain = domain.lstrip("www.")
        # Aggiunge solo i domini non presenti nella lista consentita
        if domain not in ALLOWED_DOMAINS:
            domains.add(domain)
    return domains

def check_new_domains(readme_domains, pr_domains):
    """Verifica la presenza di domini duplicati tra README e PR."""
    duplicates = readme_domains & pr_domains  # Usa l'intersezione per esatti
    if duplicates:
        duplicate_domains = "\n".join(f"- {domain}" for domain in duplicates)
        print(f"DUPLICATE_DOMAINS:\n{duplicate_domains}")
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    # Verifica l'esistenza del file README.md
    if not os.path.isfile("README.md"):
        print("Errore: README.md non trovato.")
        sys.exit(1)

    # Legge i link dal README
    with open("README.md", "r") as file:
        readme_content = file.read()
    readme_links = re.findall(r'\[.*?\]\((https?://.*?)\)', readme_content)

    # Verifica l'esistenza del file pr_links.txt
    if not os.path.isfile("pr_links.txt"):
        print("Nessun link PR trovato.")
        sys.exit(0)

    # Legge i link dalla PR
    with open("pr_links.txt", "r") as file:
        pr_content = file.read()
    pr_links = re.findall(r'\[.*?\]\((https?://.*?)\)', pr_content)

    # Estrae i domini dai link nel README e nella PR
    readme_domains = extract_domains(readme_links)
    pr_domains = extract_domains(pr_links)

    # Controlla per eventuali duplicati
    check_new_domains(readme_domains, pr_domains)
