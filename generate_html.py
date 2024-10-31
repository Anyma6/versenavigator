import re
import requests
from bs4 import BeautifulSoup
from markdown import markdown
from pathlib import Path
from urllib.parse import urljoin, urlparse

def get_metadata(url):
    """Recupera titolo, favicon, descrizione e dominio del link, con valori di fallback."""
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Titolo: se manca, usa l'URL completo
        title = soup.title.string.strip() if soup.title else url

        # Favicon: risolvi favicon in URL assoluto
        icon_link = soup.find("link", rel="icon") or soup.find("link", rel="shortcut icon")
        favicon_url = urljoin(url, icon_link['href']) if icon_link else urljoin(url, "/favicon.ico")

        # Descrizione: lascia vuoto se mancante
        meta_description = soup.find("meta", attrs={"name": "description"}) or \
                           soup.find("meta", attrs={"property": "og:description"})
        description = meta_description['content'].strip() if meta_description else ""

        # Dominio
        domain = urlparse(url).netloc

        return favicon_url, title, description, domain
    except Exception as e:
        print(f"Error fetching metadata from {url}: {e}")
        return "/favicon.ico", url, "", urlparse(url).netloc

def convert_links_to_html(readme_path, output_path):
    """Converte i link in HTML con favicon, titolo, descrizione e dominio; mantiene il resto in Markdown."""
    
    # CSS per uno stile scuro con margini aumentati
    css_content = """
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
            line-height: 1.6;
            color: #ffffff;
            background-color: #000000;  /* Sfondo nero */
            display: flex;
            justify-content: center;
            padding: 40px 20px;
        }
        .content {
            max-width: 1000px; /* Aumentato per dare più spazio */
            width: 100%;
            margin: auto;
        }
        h1, h2, h3, h4 {
            color: #ffffff;
            font-weight: 600;
            border-bottom: 1px solid #444c56;
            padding-bottom: 0.3em;
        }
        a {
            color: #58a6ff; /* Colore blu chiaro per i link */
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        p {
            margin: 1em 0;
        }
        img {
            vertical-align: middle;
            margin-right: 8px;
        }
        .link-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            margin-bottom: 1em;
        }
        .link-preview {
            margin-bottom: 1em;
            padding: 8px;
            border: 1px solid #444c56;
            border-radius: 6px;
            display: flex;
            align-items: center;
            background-color: #222222; /* Colore di sfondo per i link */
            width: calc(50% - 20px);  /* Aumentato per il margine */
        }
        .link-preview img {
            width: 16px;
            height: 16px;
        }
        .link-preview div {
            margin-left: 10px;
        }
        .link-preview-title {
            font-weight: bold;
            color: #58a6ff;
        }
        .link-preview-description {
            font-size: small;
            color: #c9d1d9;
        }
        .link-preview-domain {
            font-size: smaller;
            color: #c9d1d9;
            margin-top: 2px;
        }
    </style>
    """
    
    with open(readme_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Contenuto HTML iniziale
    html_content = f"<html><head>{css_content}</head><body><div class='content'>\n"

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        url_match = re.match(r'^\s*(https?://[^\s]+)\s*$', line)
        
        if url_match:
            url = url_match.group(1)
            favicon, title, description, domain = get_metadata(url)

            # Crea un div per il link
            html_line = (f'<div class="link-preview">'
                         f'<img src="{favicon}" alt="favicon">'
                         f'<div>'
                         f'<a href="{url}" target="_blank" class="link-preview-title">{title}</a><br>'
                         f'<span class="link-preview-description">{description}</span><br>'
                         f'<span class="link-preview-domain">{domain}</span>'
                         f'</div>'
                         f'</div>')

            # Controlla se c'è un secondo link sulla riga successiva
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                next_url_match = re.match(r'^\s*(https?://[^\s]+)\s*$', next_line)
                if next_url_match:
                    next_url = next_url_match.group(1)
                    favicon_next, title_next, description_next, domain_next = get_metadata(next_url)
                    html_line += (f'<div class="link-preview">'
                                   f'<img src="{favicon_next}" alt="favicon">'
                                   f'<div>'
                                   f'<a href="{next_url}" target="_blank" class="link-preview-title">{title_next}</a><br>'
                                   f'<span class="link-preview-description">{description_next}</span><br>'
                                   f'<span class="link-preview-domain">{domain_next}</span>'
                                   f'</div>'
                                   f'</div>')

                    # Incrementa l'indice di lettura per saltare il secondo link
                    i += 1  # Skip the next line since we've processed it

            # Aggiungi il contenitore di link alla pagina HTML
            html_content += f'<div class="link-container">{html_line}</div>\n'
        
        else:
            # Converte il Markdown in HTML per tutte le altre righe
            html_content += markdown(line)

        # Incrementa l'indice per passare alla riga successiva
        i += 1

    html_content += "</div></body></html>"
    
    # Salva l'output come HTML
    output_path.write_text(html_content, encoding='utf-8')

# Percorsi per input e output
readme_path = Path("README.md")
output_dir = Path("docs")
output_dir.mkdir(exist_ok=True)
output_html_path = output_dir / "index.html"

# Esegui la conversione
convert_links_to_html(readme_path, output_html_path)
