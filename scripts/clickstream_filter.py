import pandas as pd

# Lectura del archivo TSV y gestión de posibles errores
data = pd.read_csv(
    "../data/input/clickstream-ptwiki-2024-10.tsv", 
    sep="\t", 
    names=["referer", "resource", "type", "n"],
    on_bad_lines="skip")

print("Filtering data. Original number of rows:", len(data))

# Filtración de datos para incluir solo interacciones internas a Wikipedia
filtered_data = data[data["type"] == "link"]

# Exportación de datos a nuevo archivo
filtered_data.to_csv("../data/output/filtered_clickstream.csv", index=False)
print("External types successfully deleted. Number of rows: ", len(filtered_data))

# Filtración de datos para incluir una sola instancia de cada página de origen
popular_links = filtered_data.drop_duplicates(subset="referer", keep="first")

# Exportación de datos a nuevo archivo 
popular_links = popular_links[["referer", "resource"]]
popular_links.to_csv("popular_outgoing_links.csv", index=False)
print("Download complete. Final number of rows:", len(popular_links))

