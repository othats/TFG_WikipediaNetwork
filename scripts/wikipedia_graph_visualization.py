import networkx as nx
import matplotlib.pyplot as plt
import csv

nodes_file = "../data/output/id_page.csv"
edges_file = "../data/output/source_target.csv"

G = nx.DiGraph()

with open(nodes_file, 'r') as nodes_f:
    node_reader = csv.reader(nodes_f)
    next(node_reader)  # Saltar el encabezado
    for row in node_reader:
        node_id = int(row[0])  # ID del nodo
        node_page = row[1]  # Nombre de la página
        G.add_node(node_id, page=node_page)  # Agregar nodo al grafo con el ID y el nombre de la página

with open(edges_file, 'r') as edges_f:
    edge_reader = csv.reader(edges_f)
    next(edge_reader)  # Saltar el encabezado
    for row in edge_reader:
        source = int(row[0])  # ID de la página origen
        target = int(row[1])  # ID de la página destino
        G.add_edge(source, target)  # Agregar arista entre los nodos

plt.figure(figsize=(12, 12))  # Tamaño de la figura
pos = nx.spring_layout(G, seed=42)  # Layout para el grafo (se puede cambiar por otros como "circular_layout")
nx.draw(G, pos, with_labels=False, node_size=500, node_color='lightblue', font_size=10, font_weight='bold', edge_color='gray')

labels = {node: G.nodes[node]['page'] for node in G.nodes}
nx.draw_networkx_labels(G, pos, labels, font_size=8)

plt.savefig("graphs/wikipedia_graph.png", format="PNG", dpi=300)

plt.title("Grafo de Enlaces de Wikipedia")
plt.show()


