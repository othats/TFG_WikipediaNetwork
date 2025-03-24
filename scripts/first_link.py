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


def extract_link(text, title):
    """
    Parses wikitext to extract the first valid link
    (first non-parenthesized, non-italicized link)
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
            # Si al procesar un nodo no-Text la profundidad es >0, se resetea para evitar bloqueos
            if parenthesis_depth > 0:
                parenthesis_depth = 0
        
        if parenthesis_depth > 0:
            continue 

        # finds first link
        if isinstance(node, mwparserfromhell.nodes.Wikilink):
            link_candidate = re.split(r'\||#', str(node.title))[0].strip()
            valid = valid_link(link_candidate, title)
            if valid:
                return valid
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
        return None
    
    title = title_tag.string
    text = text_tag.string

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
            return f"{title}, {first_link}"
    else: 
        return None


# ----- Main function -----


input_file = "input/ptwiki-latest-pages-articles.pageperline.xml"
nodes_file = "output/pages.csv"
edges_file = "output/edges.csv"
error_file = "output/errors.log"

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
         open(edges_file, "w", encoding="utf-8") as edges_out:
        
        # add header to csv's
        nodes_out.write("id,page\n")
        edges_out.write("source,target\n")

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

                    parts = result.split(", ")
                    source, target = parts[0], parts[1]

                    # new page
                    if source not in node_mapping:
                        node_mapping[source] = current_id
                        nodes_out.write(f"{current_id},{source}\n")
                        current_id += 1

                    if target not in node_mapping:
                        node_mapping[target] = current_id
                        nodes_out.write(f"{current_id},{target}\n")
                        current_id += 1

                    edges_out.write(f"{node_mapping[source]},{node_mapping[target]}\n")
            
            
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