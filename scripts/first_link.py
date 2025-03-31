# ----- Imports -----

import re, sys, os
import mwparserfromhell
import random
from bs4 import BeautifulStoneSoup
import unicodedata

# ----- Config -----

input_file = "input/ptwiki-latest-pages-articles.pageperline.xml"
nodes_file = "output/pages.csv"
edges_first_file = "output/edges_first.csv"
edges_second_file = "output/edges_second.csv"
edges_random_file = "output/edges_random.csv"
error_file = "output/errors.log"

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
    link_lower = normalize_text(link)
    return link_lower.startswith('imagem:') \
           or link_lower.startswith('categoria:') \
           or link_lower.startswith('wikipedia:') \
           or link_lower.startswith('modelo:') \
           or link_lower.startswith('portal:') \
           or link_lower.startswith('modulo:') \
           or link_lower.startswith('livro:') \
           or link_lower.startswith('ficheiro:') \
           or link_lower.startswith('topico:') \
           or link_lower.startswith('file:') \
           or link_lower.startswith('ajuda:') \
           or link_lower.startswith('predefinicao:') \
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


def extract_links(text, title):
    """
    Parses wikitext to extract the first, second and random valid links
    (non-parenthesized, non-italicized)
    """
    parsed = mwparserfromhell.parse(text)

    # Filter out any Wikilink nodes that are image links
    filtered_nodes = []
    for node in parsed.nodes:
        if isinstance(node, mwparserfromhell.nodes.Wikilink):
            candidate = re.split(r'\||#', str(node.title))[0].strip()
            if meta_article(candidate):
                continue  # Skip this node entirely
        filtered_nodes.append(node)
    
    links = []
    parenthesis_depth = 0

    for node in filtered_nodes:

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
                parenthesis_depth += diff
            # Si al procesar un nodo no-Text la profundidad es >0, se resetea para evitar bloqueos
            if parenthesis_depth > 0:
                parenthesis_depth = 0
        

        # finds links
        elif isinstance(node, mwparserfromhell.nodes.Wikilink):
            candidate = re.split(r'\||#', str(node.title))[0].strip()
            valid = valid_link(candidate, title)
            if valid and parenthesis_depth <= 0:
                links.append(valid)

    return links

def process_page(xml_line, mode):
    """
    Processes singles flattened XML page to extract its title and first, second and random valid link
    """
    soup = BeautifulStoneSoup(xml_line)
    title_tag = soup.find('title')
    text_tag = soup.find('text')

    if title_tag is None or text_tag is None:
        return None
    
    title = title_tag.string
    text = text_tag.string

    if meta_article(title):
        return "SKIPPED_META"
    
    normalized_text = normalize_text(text)
    if ',' in title or "{{desambiguacao" in normalized_text:
        return "SKIPPED_DESAMB"
    
    links = extract_links(text, title)

    if not links: 
        return None
    
    targets = {
        "first": links[0],
        "second": links[1] if len(links) > 1 else None,
        "random": random.choice(links)
    }

    for key in targets: 
        if targets[key]:
            if meta_article(targets[key]) or ',' in targets[key]:
                targets[key] = None

    return title, targets 


# ----- Main Execution -----

err_out = open(error_file, "w", encoding="utf-8")
sys.stderr = err_out

total_size = os.path.getsize(input_file)
last_percent = 0

# Dictionary to assign ID to each visited page
node_mapping = {}
current_id = 0

try:
    with open(input_file, "r", encoding="utf-8") as infile, \
         open(nodes_file, "w", encoding="utf-8") as nodes_out, \
         open(edges_first_file, "w", encoding="utf-8") as edges_first_out, \
         open(edges_second_file, "w", encoding="utf-8") as edges_second_out, \
         open(edges_random_file, "w", encoding="utf-8") as edges_random_out:
        
        # add header to csv's
        nodes_out.write("id,page\n")
        edges_first_out.write("source,target\n")
        edges_second_out.write("source,target\n")
        edges_random_out.write("source,target\n")

        while True:
            line = infile.readline()
            if not line: 
                break

            line = line.strip()
            if not line: 
                continue

            result = process_page(line)
            if result:
                if result not in ("SKIPPED_META", "SKIPPED_DESAMB"):

                    title, targets = result

                    # new page
                    if title not in node_mapping:
                        node_mapping[title] = current_id
                        nodes_out.write(f"{current_id},{title}\n")
                        current_id += 1

                    for mode, target in targets.items():
                        if target:
                            if target not in node_mapping:
                                node_mapping[target] = current_id
                                nodes_out.write(f"{current_id},{target}\n")
                                current_id += 1

                            source_id = node_mapping[title]
                            target_id = node_mapping[target]

                            if mode == "first":
                                edges_first_out.write(f"{source_id},{target_id}\n")
                            elif mode == "second":
                                edges_second_out.write(f"{source_id},{target_id}\n")
                            elif mode == "random":
                                edges_random_out.write(f"{source_id},{target_id}\n")
            
            else:
                sys.stderr.write("Page without link: " +
                                    f"{line[13:40]}...\n")
                
            # progress calculation
            current_position = infile.tell() 
            percent = int((current_position / total_size) * 100)
            if percent > last_percent:
                last_percent = percent
                print(f"Progress: {percent}%", end="\r", flush=True)

        print("\nProcess complete!")

except Exception as e:
    sys.stderr.write(f"Error opening file {input_file}: {str(e)}\n")