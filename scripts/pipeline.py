import requests 
from bs4 import BeautifulSoup
import re

# Función para encontrar el primer link válido de una página
def get_first_link(page_title, timeout=5):

    url = "https://pt.wikipedia.org/w/api.php"

    params = {
        "action" : "parse",
        "format" : "json",
        "page" : page_title,
        "prop" : "text"
    }

    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
    except requests.exceptions.Timeout:
        print(f"Timeout error for page: {page_title}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request error for page: {page_title} - {e}")
        return None
    
    data = response.json()
    
    html_content = data["parse"]["text"]["*"]
    if not html_content:
        print(f"No se encontró contenido para la página: {page_title}")
        return None
    
    soup = BeautifulSoup(html_content, "html.parser")

    redirect_msg = soup.find("div", class_="redirectMsg")
    if redirect_msg:
        redirect_link = redirect_msg.find("a")
        if redirect_link and redirect_link.get("href"):
            redirect_title = redirect_link.get("title")
            params["page"] = redirect_title

            response = requests.get(url, params=params)
            data = response.json()
            html_content = data["parse"]["text"]["*"]
            soup = BeautifulSoup(html_content, "html.parser")

    if "página de desambiguação" in soup.text:
        links = soup.find_all("ul")
        links_2 = []
        for ul in links:
            links_2.extend(ul.find_all("a"))
        first_link = links_2[0]
        link_data = {
                "title": first_link.get('title'),
                "href": first_link.get('href')
            }
        return link_data

    else: 

        paragraphs = soup.find_all("p")

        for p in paragraphs:

            if p.get("class"):
                continue
                
            text_without_parentheses = re.sub(r'\(.*?\)', '', str(p))
            clean_paragraph = BeautifulSoup(f"{text_without_parentheses}", "html.parser")

            valid_links = [link for link in clean_paragraph.find_all("a") if not link.find_parent(["i", "em", "sup"])]
            
            if valid_links:
                first_link = valid_links[0]
                link_data = {
                    "title": first_link.get('title'),
                    "href": first_link.get('href')
                }
                return link_data
            
        print(f"No se encontraron enlaces válidos en la página: {page_title}")
        return None


# Función para seguir enlaces en bucle
def pipeline(start_page, max_iter=100, target_page="Filosofia"):
    
    visited_pages = set() # Para detectar bucles
    current_page = start_page
    i = 0

    while i<max_iter:
        print(f"\nIteración {i+1}: Visitando {current_page}")
        link_data = get_first_link(current_page)

        if not link_data:
            print("No se puede continuar porque no hay enlaces válidos.")
            break

        page_title = re.sub(r' ', '_', link_data["title"])

                    
        if page_title == target_page:
            print("\n¡Se encontró la página de Filosofía!")
            break
        if page_title in visited_pages:
            print(f"\nSe detectó un bucle en la navegación. {page_title} ya visitado")
            break

        visited_pages.add(page_title)
        current_page = page_title
        i += 1

    print("\nSe alcanzó el número máximo de iteraciones.")


print(get_first_link("Idade_Moderna"))