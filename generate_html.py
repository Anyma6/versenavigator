import re
import logging
from bs4 import BeautifulSoup
from markdown import markdown
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests

# Configurazione logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_metadata(url):
    """Fetch title, favicon, description, and domain without caching."""
    try:
        logging.info(f"Fetching metadata for URL: {url}")
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.string.strip() if soup.title else url
        icon_link = soup.find("link", rel="icon") or soup.find("link", rel="shortcut icon")
        favicon_url = urljoin(url, icon_link['href']) if icon_link else urljoin(url, "/favicon.ico")
        meta_description = soup.find("meta", attrs={"name": "description"}) or \
                           soup.find("meta", attrs={"property": "og:description"})
        description = meta_description['content'].strip() if meta_description else ""
        domain = urlparse(url).netloc

        return favicon_url, title, description, domain
    except Exception as e:
        logging.error(f"Error fetching metadata from {url}: {e}")
        return "/favicon.ico", url, "", urlparse(url).netloc

def convert_links_to_html(readme_path, output_path):
    """Convert isolated links to dark-themed HTML with responsive, 2-column layout."""
    
    css_content = """
    <style>
        /* Dark Theme Styles */
        body {
            background-color: #121212;
            color: #e0e0e0;
            font-family: Arial, sans-serif;
            margin: 20px;
            padding: 20px;
            line-height: 1.6;
        }
        .content {
            max-width: 1200px;
            margin: auto;
        }
        .link-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
        }
        .link-preview {
            background-color: #1e1e1e;
            border-radius: 5px;
            padding: 15px;
            margin: 10px;
            flex: 0 0 calc(50% - 20px);
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.5);
            transition: background-color 0.3s;
        }
        .link-preview:hover {
            background-color: #2b2b2b;
        }
        .link-preview img {
            width: 20px;
            height: 20px;
            margin-right: 10px;
            vertical-align: middle;
        }
        .link-preview-title {
            font-size: 1.2em;
            color: #1e90ff;
            text-decoration: none;
        }
        .link-preview-description {
            font-size: 0.9em;
            color: #b0b0b0;
        }
        .link-preview-domain {
            font-size: 0.8em;
            color: #757575;
        }
    </style>
    """
    
    with open(readme_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    html_content = f"<html><head>{css_content}</head><body><div class='content'>\n"
    link_container_opened = False

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        url_match = re.match(r'^\s*(https?://[^\s]+)\s*$', line)
        
        if url_match:
            if not link_container_opened:
                html_content += "<div class='link-container'>\n"
                link_container_opened = True
            
            url = url_match.group(1)
            favicon, title, description, domain = get_metadata(url)
            html_line = (f'<div class="link-preview">'
                         f'<img src="{favicon}" alt="favicon">'
                         f'<div>'
                         f'<a href="{url}" target="_blank" class="link-preview-title">{title}</a><br>'
                         f'<span class="link-preview-description">{description}</span><br>'
                         f'<span class="link-preview-domain">{domain}</span>'
                         f'</div>'
                         f'</div>\n')

            html_content += html_line
            i += 1

            # Se il prossimo elemento è un link, raggruppa a coppie
            if i < len(lines) and re.match(r'^\s*(https?://[^\s]+)\s*$', lines[i].strip()):
                url = re.match(r'^\s*(https?://[^\s]+)\s*$', lines[i].strip()).group(1)
                favicon, title, description, domain = get_metadata(url)
                html_line = (f'<div class="link-preview">'
                             f'<img src="{favicon}" alt="favicon">'
                             f'<div>'
                             f'<a href="{url}" target="_blank" class="link-preview-title">{title}</a><br>'
                             f'<span class="link-preview-description">{description}</span><br>'
                             f'<span class="link-preview-domain">{domain}</span>'
                             f'</div>'
                             f'</div>\n')
                html_content += html_line
                i += 1  # Incrementa l'indice per il secondo link

            html_content += "</div>\n"  # Chiude il contenitore dei link
            link_container_opened = False
        else:
            if link_container_opened:
                html_content += "</div>\n"  # Chiudi il contenitore dei link
                link_container_opened = False
            html_content += markdown(line)  # Converti e aggiungi testo Markdown
            i += 1  # Incrementa l'indice per il testo non link

    if link_container_opened:
        html_content += "</div>\n"  # Chiudi il contenitore dei link, se aperto
    html_content += "</div></body></html>"

    output_path.write_text(html_content, encoding='utf-8')

# Percorsi per input e output
readme_path = Path("README.md")
output_dir = Path("docs")
output_dir.mkdir(exist_ok=True)
output_html_path = output_dir / "index.html"

convert_links_to_html(readme_path, output_html_path)
logging.info("HTML generation completed.")
