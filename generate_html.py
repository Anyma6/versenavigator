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
    
    # CSS per imitare lo stile GitHub con margini simili a VerseNavigator
    css_content = """
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
            line-height: 1.6;
            color: #24292e;
            background-color: #ffffff;
            display: flex;
            justify-content: center;
            padding: 40px 20px;
        }
        .content {
            max-width: 860px;
            width: 100%;
            margin: auto;
        }
        h1, h2, h3, h4 {
            color: #24292e;
            font-weight: 600;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }
        a {
            color: #0366d6;
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
        .link-preview {
            margin-bottom: 1em;
            padding: 8px;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            display: flex;
            align-items: center;
            background-color: #f6f8fa;
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
            color: #0366d6;
        }
        .link-preview-description {
            font-size: small;
            color: #586069;
        }
        .link-preview-domain {
            font-size: smaller;
            color: #586069;
            margin-top: 2px;
        }
    </style>
    """
    
    with open(readme_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Contenuto HTML iniziale
    html_content = f"<html><head>{css_content}</head><body><div class='content'>\n"
    
    # Converti ogni riga
    for line in lines:
        # Riconosci link singoli su righe isolate
        url_match = re.match(r'^\s*(https?://[^\s]+)\s*$', line)
        if url_match:
            url = url_match.group(1)
            favicon, title, description, domain = get_metadata(url)
            
            # Formatta il link in HTML con favicon, titolo, descrizione e dominio
            html_line = (f'<div class="link-preview">'
                         f'<img src="{favicon}" alt="favicon">'
                         f'<div>'
                         f'<a href="{url}" target="_blank" class="link-preview-title">{title}</a><br>'
                         f'<span class="link-preview-description">{description}</span><br>'
                         f'<span class="link-preview-domain">{domain}</span>'
                         f'</div>'
                         f'</div>\n')
            html_content += html_line
        else:
            # Converte il Markdown in HTML per tutte le altre righe
            html_content += markdown(line)

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
