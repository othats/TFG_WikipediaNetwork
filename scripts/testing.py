import re, sys, os
import mwparserfromhell
from bs4 import BeautifulStoneSoup
import unicodedata

# ----- Helper Functions -----

def normalize_text(text):
    """
    Normaliza el texto eliminando acentos y convirtiéndolo a ASCII.
    """
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()

def meta_article(link):   
    """
    Returns True if the link corresponds to meta article
    (File, Category, Template, etc)
    """
    if ":" not in link:
        return False
    link_lower = link.lower()
    return link_lower.startswith('imagem:') \
           or link_lower.startswith('categoria:') \
           or link_lower.startswith('wikipédia:') \
           or link_lower.startswith('modelo:') \
           or link_lower.startswith('portal:') \
           or link_lower.startswith('livro:') \
           or link_lower.startswith('ficheiro:') \
           or link_lower.startswith('file:') \
           or link_lower.startswith('ajuda:') \
           or link_lower.startswith('predefinição:') \
           or link_lower.startswith('mediawiki:')

def internal_link(link):
    """
    Returns True if the link corresponds to internal article
    (if the link starts with a hash #)
    """
    return link.startswith('#')

def valid_link(link, title):
    """
    Performs series of clean-up steps on the link
    """
    if not link:
        return None
    
    if not (meta_article(link) or internal_link(link) or link==title):
        link = link[0].upper() + link[1:] # make sure it's first letter capital
        return link  


def extract_link(text, title):
    """
    Parses wikitext to extract the first valid link
    (first non-parenthesized, non-italicized link)
    """
    parsed = mwparserfromhell.parse(text)

    print(f"[DEBUG] extract_link: Total de nodos top-level: {len(parsed.nodes)}")

    # Filter out any Wikilink nodes that are image links
    filtered_nodes = []
    for node in parsed.nodes:
        if isinstance(node, mwparserfromhell.nodes.Wikilink):
            candidate = re.split(r'\||#', str(node.title))[0].strip()
            if meta_article(candidate):
                continue  # Skip this node entirely
        filtered_nodes.append(node)
    
    parenthesis_depth = 0

    for node in filtered_nodes:
        node_type = type(node).__name__
        print(f"[DEBUG] Processing node of type: {node_type}")

        # ignores parenthesized text by tracking when we are inside ()
        if isinstance(node, mwparserfromhell.nodes.Text):
            node_str = str(node)
            diff = node_str.count('(') - node_str.count(')')
            parenthesis_depth += diff
        elif isinstance(node, mwparserfromhell.nodes.Tag):
            # Para nodos que no son de tipo Text (por ejemplo, Tag), revisamos su contenido
            node_str = str(node)
            if '(' in node_str or ')' in node_str:
                diff = node_str.count('(') - node_str.count(')')
            # Si al procesar un nodo no-Text la profundidad es >0, se resetea para evitar bloqueos
            if parenthesis_depth > 0:
                parenthesis_depth = 0
        
        if parenthesis_depth > 0:
            print("[DEBUG] Skipping node because we are inside parentheses.")
            continue 

        # finds first link
        if isinstance(node, mwparserfromhell.nodes.Wikilink):
            print(f"[DEBUG] Found Wikilink node: {node}")
            link_candidate = re.split(r'\||#', str(node.title))[0].strip()
            print(f"[DEBUG] Extracted candidate link: '{link_candidate}'")
            valid = valid_link(link_candidate, title)
            print(f"[DEBUG] Result after valid_link: '{valid}'")
            if valid:
                return valid
    print("[DEBUG] No valid link found in text.")
    return None

def process_page(xml_line):
    """
    Processes singles flattened XML page to extract its title and first valid link
    Returns a string "title, link" if a valid link is found
    """
    soup = BeautifulStoneSoup(xml_line)
    title_tag = soup.find('title')
    text_tag = soup.find('text')

    if title_tag is None or text_tag is None:
        print("[DEBUG] Missing <title> or <text> tag.")
        return None
    
    title = title_tag.string
    text = text_tag.string

    print(f"[DEBUG] Extracted title: '{title}'")
    print(f"[DEBUG] Extracted text (first 200 chars): '{text[:200]}'")

    if meta_article(title):
        return "SKIPPED_META"
    
    normalized_text = normalize_text(text)
    if ',' in title or "{{desambiguacao" in normalized_text:
            return "SKIPPED_DESAMB"
    
    first_link = extract_link(text, title)
    if first_link:
        if meta_article(first_link):
            return None
        elif ',' in first_link:
            return "SKIPPED_DESAMB"
        else: 
            print(f"[DEBUG] First valid link found: '{first_link}'")
            return f"{title}, {first_link}"
    else: 
        print("[DEBUG] No valid link extracted from this page.")
        return None
    

# ----- Main function -----

input_file = "input/ptwiki-latest-pages-articles.pageperline.xml"
output_file = "output/network.csv"

target_title = "Tibagi"  # Cambia este valor según necesites

try:
    with open(input_file, "r", encoding="utf-8") as infile:
        found = False
        for line in infile:
            line = line.strip()
            if not line: 
                continue

            # Extraer el título sin procesar toda la página
            soup = BeautifulStoneSoup(line)
            title_tag = soup.find('title')
            if title_tag is None:
                continue
            title = title_tag.string.strip()

            # Si el título contiene la subcadena deseada, procesamos la página
            if target_title.lower() in title.lower():
                print(f"=== Processing page with title containing '{target_title}': {title} ===")
                result = process_page(line)
                if result:
                    print("Result:", result)
                else:
                    sys.stderr.write("Page without link: " + f"{line[13:40]}...\n")
                found = True
                # Si queremos probar sólo la primera página que coincida, descomentamos el break
                break
        
        if not found:
            print(f"No se encontró ninguna página cuyo título contenga '{target_title}'.")
except Exception as e:
    sys.stderr.write(f"Error opening file {input_file}: {str(e)}\n")

print("=== Testing Complete ===")
