import re
import sys
from urllib.parse import urlparse
import os

# Domini consentiti che non devono essere contrassegnati come duplicati
ALLOWED_DOMAINS = {
    "github.com", 
    "reddit.com", 
    "robertsspaceindustries.com", 
    "discord.com",         # Eccezione per gli inviti Discord
    "docs.google.com"      # Eccezione per documenti Google Docs
}

def extract_domains(links):
    """Estrae i domini dai link (URL), ignorando protocollo e percorsi."""
    domains = set()
    for link in links:
        parsed_url = urlparse(link)
        domain = parsed_url.netloc.lower()  # Usa solo il dominio, senza protocollo o percorso
        if domain not in ALLOWED_DOMAINS:
            domains.add(domain)
    return domains

def check_new_domains(readme_domains, pr_domains):
    """Confronta i domini nuovi con quelli già presenti nel README e segnala duplicati."""
    duplicates = readme_domains & pr_domains  # Intersezione dei domini già presenti con quelli nuovi
    if duplicates:
        duplicate_domains = "\n".join(f"- {domain}" for domain in duplicates)
        print(f"DUPLICATE_DOMAINS:\n{duplicate_domains}")  # Indica i duplicati trovati
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    # Verifica l'esistenza del file README.md
    if not os.path.isfile("README.md"):
        print("Errore: README.md non trovato.")
        sys.exit(1)

    # Leggi il contenuto del README per estrarre i link già presenti
    with open("README.md", "r") as file:
        readme_content = file.read()

    # Estrai i link URL dal README
    readme_links = re.findall(r'\[.*?\]\((.*?)\)', readme_content)
    pr_links = []
    
    # Verifica l'esistenza del file pr_links.txt
    if not os.path.isfile("pr_links.txt"):
        sys.exit(0)  # Esci senza errore se non ci sono nuovi link

    # Leggi i link dalla PR
    with open("pr_links.txt", "r") as file:
        pr_content = file.read()
    pr_links.extend(re.findall(r'\[.*?\]\((.*?)\)', pr_content))

    # Estrai i domini dai link nel README e nella PR, escludendo i domini consentiti
    readme_domains = extract_domains(readme_links)
    pr_domains = extract_domains(pr_links)

    # Verifica i duplicati tra i domini
    check_new_domains(readme_domains, pr_domains)
