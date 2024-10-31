import re
import requests
import json
from bs4 import BeautifulSoup
from markdown import markdown
from pathlib import Path
from urllib.parse import urljoin, urlparse

def get_metadata(url, cache):
    """Fetch title, favicon, description, and domain with caching and reduced timeout."""
    if url in cache:
        return cache[url]

    try:
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        title = soup.title.string.strip() if soup.title else url
        icon_link = soup.find("link", rel="icon") or soup.find("link", rel="shortcut icon")
        favicon_url = urljoin(url, icon_link['href']) if icon_link else urljoin(url, "/favicon.ico")
        meta_description = soup.find("meta", attrs={"name": "description"}) or \
                           soup.find("meta", attrs={"property": "og:description"})
        description = meta_description['content'].strip() if meta_description else ""
        domain = urlparse(url).netloc

        cache[url] = (favicon_url, title, description, domain)
        return cache[url]
    except Exception as e:
        print(f"Error fetching metadata from {url}: {e}")
        return "/favicon.ico", url, "", urlparse(url).netloc

def convert_links_to_html(readme_path, output_path):
    """Convert isolated links to dark-themed HTML with responsive, 2-column layout and caching."""
    
    css_content = """
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
            line-height: 1.6;
            color: #e1e4e8;
            background-color: #0d1117;
            display: flex;
            justify-content: center;
            padding: 20px;
            margin: 0;
        }
        .content {
            max-width: 860px;
            width: 100%;
            margin: auto;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h1, h2, h3, h4 {
            color: #c9d1d9;
            font-weight: 600;
            border-bottom: 1px solid #30363d;
            padding-bottom: 0.3em;
        }
        a {
            color: #58a6ff;
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
            gap: 16px;
            width: 100%;
        }
        .link-preview {
            flex: 1 1 calc(50% - 8px); /* Ensure two items per row on wide screens */
            padding: 10px;
            border: 1px solid #30363d;
            border-radius: 6px;
            display: flex;
            align-items: center;
            background-color: #161b22;
            box-sizing: border-box;
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
            color: #8b949e;
        }
        .link-preview-domain {
            font-size: smaller;
            color: #8b949e;
            margin-top: 2px;
        }
        @media (max-width: 600px) {
            .link-preview {
                flex: 1 1 100%;
            }
        }
    </style>
    """
    
    # Load or create metadata cache
    cache_path = Path("metadata_cache.json")
    if cache_path.is_file():
        with open(cache_path, "r") as f:
            cache = json.load(f)
    else:
        cache = {}

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
            favicon, title, description, domain = get_metadata(url, cache)
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
                favicon, title, description, domain = get_metadata(url, cache)
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

            html_content += "</div>\n"  # Chiude la coppia o il singolo link
            link_container_opened = False
        else:
            if link_container_opened:
                html_content += "</div>\n"  # Chiudi il contenitore dei link
                link_container_opened = False
            html_content += markdown(line)  # Converti e aggiungi testo Markdown

    if link_container_opened:
        html_content += "</div>\n"  # Chiudi il contenitore dei link, se aperto
    html_content += "</div></body></html>"

    output_path.write_text(html_content, encoding='utf-8')

    # Salva la cache aggiornata
    with open(cache_path, "w") as f:
        json.dump(cache, f)

# Percorsi per input e output
readme_path = Path("README.md")
output_dir = Path("docs")
output_dir.mkdir(exist_ok=True)
output_html_path = output_dir / "index.html"

convert_links_to_html(readme_path, output_html_path)
