import mwxml
import bz2
import re
from xml.sax.saxutils import unescape
import sys

def process_page(page):
    """
    Procesa una página del dump usando mwxml.
    Si la página es una redirección, extrae el título y el destino de la redirección,
    aplica algunas transformaciones y lo imprime en formato "titulo\tredireccion".
    """
    # Verifica si la página es una redirección
    if page.redirect:
        title = page.title

        # La librería mwxml provee directamente el objeto redirect
        redirect_title = page.redirect.title

        # Opcional: realizar transformaciones similares a las del script original
        # Eliminar posibles anclajes si existieran (esto dependerá de cómo se procese el dump)
        redirect_title = re.sub(r'\#.*', '', redirect_title)
        redirect_title = re.sub('_', ' ', redirect_title)
        if redirect_title:
            redirect_title = redirect_title[0].upper() + redirect_title[1:]

        output = title + "\t" + redirect_title
        output_unescaped = unescape(output, {"&apos;": "'", "&quot;": '"'})
        print(output_unescaped.encode('utf-8').decode('utf-8'))
    else:
        # Si no es una redirección, se puede ignorar o procesar de otra forma
        pass

def main():
    dump_file = "enwiki-latest-pages-articles.xml.bz2"  # ruta al dump
    with bz2.open(dump_file, "rb") as f:
        dump = mwxml.Dump.from_file(f)
        for i, page in enumerate(dump):
            try:
                process_page(page)
            except Exception as e:
                sys.stderr.write(f"Error processing page {page.title if page.title else 'Unknown'}: {str(e)}\n")
            # Opcional: imprimir progreso cada cierta cantidad de páginas
            if i % 10000 == 0 and i > 0:
                sys.stderr.write(f"Processed {i} pages...\n")

if __name__ == "__main__":
    main()
