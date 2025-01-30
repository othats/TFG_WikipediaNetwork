import requests 
from bs4 import BeautifulSoup
import re

url = "https://pt.wikipedia.org/w/api.php"

params = {
    "action" : "parse",
    "format" : "json",
    "page" : "Hollywood",
    "prop" : "text"
}

response = requests.get(url, params=params)
data = response.json()

print(data)

# Extracción del contenido HTML de la respuesta
html_content = data["parse"]["text"]["*"]

# Uso de BeautifulSoup para filtrar el contenido del párrafo
soup = BeautifulSoup(html_content, "html.parser")

# Manejo de redirecciones
redirect_msg = soup.find("div", class_="redirectMsg")
if redirect_msg:
    redirect_link = redirect_msg.find("a")
    if redirect_link and redirect_link.get("href"):
        redirect_title = redirect_link.get("title")
        print(f"Redirección detectada: a {redirect_title}")
        params["page"] = redirect_title
        response = requests.get(url, params=params)
        data = response.json()
        html_content = data["parse"]["text"]["*"]
        soup = BeautifulSoup(html_content, "html.parser")

if "página de desambiguação" in soup.text:
    print("\n\n Página de desambiguación!!\n")
    links = soup.find_all("ul")
    links_2 = []
    for ul in links:
        links_2.extend(ul.find_all("a"))
    print(links_2)
    first_link = links_2[0]

else:

    paragraphs = soup.find_all("p")

    for p in paragraphs:

        if p.get("class"):
            continue

        print("\nThe paragraph includes the following information:\n\n", p)

        # Convertir el párrafo a texto para aplicar la expresión regular
        text_without_parentheses = re.sub(r'\(.*?\)', '', str(p))


        # Volver a crear un objeto BeautifulSoup con el texto limpio
        clean_paragraph = BeautifulSoup(f"{text_without_parentheses}", "html.parser")

        print("\nIf we remove the parenthesis, this is the content:\n\n", clean_paragraph)

        # Filtro para los links
        valid_links = [link for link in clean_paragraph.find_all("a") if not link.find_parent(["i", "em", "sup"])]
        
        if valid_links:
            first_link = valid_links[0]
            print("\nThis is the first valid link:\n", first_link)
            if len(valid_links) > 1:
                second_link = valid_links[1]        
            break

        print("\nThere are no links in this paragraph.\n")
    
# Crear un objeto con el título y el href del primer link válido
link_data = {
"title": first_link.get('title'),
"href": first_link.get('href')
}

print("\nThis is the first valid link with its title and hyperlink:\n", link_data)
