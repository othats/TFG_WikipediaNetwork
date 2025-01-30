# imports 
from pipeline import get_first_link
import csv 
import os
import re

# file paths 
idx_file = "../data/input/ptwiki-20250101-pages-articles-multistream-index.txt"
nodes = "../data/output/id_page.csv"
edges = "../data/output/source_target.csv"

# parameters 
max_iter = 100

# function to get the starting id
def get_id(path):
    if os.path.exists(path) and os.stat(path).st_size > 0:
        with open(path, 'r') as f:
            return sum(1 for _ in f) 
    return 1 

if not os.path.exists(nodes):
    with open(nodes, 'w', newline='') as nodes_out:
        writer = csv.writer(nodes_out)
        writer.writerow(["ID", "label"]) 

if not os.path.exists(edges):
    with open(edges, 'w', newline='') as edges_out:
        writer = csv.writer(edges_out)
        writer.writerow(["source", "target"]) 

# initialization
pages_visited = {}
current_id = get_id(nodes)

with open(nodes, 'r') as nodes_file:
    node_reader = csv.reader(nodes_file)
    next(node_reader) 
    for row in node_reader:
        pages_visited[row[1]] = int(row[0])

with open(nodes, 'a', newline='') as nodes_out, open(edges, 'a', newline='') as edges_out:
    node_writer = csv.writer(nodes_out)
    edge_writer = csv.writer(edges_out)

    with open(idx_file, 'r') as f:
        for line in f: 
            parts = line.strip().split(':')

            if len(parts) == 3:
                _, _, title = parts
                page_title = re.sub(r' ', '_', title)

                if page_title in pages_visited:
                    continue

                print(f"next page: {page_title}")

                pages_visited[page_title] = current_id
                node_writer.writerow([current_id, page_title])
                current_id += 1
            
                current_page = page_title
                source_id = pages_visited[current_page]

                i = 0
                while i<max_iter:
                    try: 
                        next_link = get_first_link(current_page)["title"]
                        if next_link: 
                            next_page = re.sub(r' ', '_', next_link)
                            
                            if next_page:
                                if next_page in pages_visited:
                                    target_id = pages_visited[next_page]
                                    edge_writer.writerow([source_id, target_id])
                                    print("loop found")
                                    break

                                pages_visited[next_page] = current_id
                                target_id = current_id
                                node_writer.writerow([current_id, next_page])
                                print(f"new page discovered: {current_page}")
                                current_id += 1

                                edge_writer.writerow([source_id, target_id])

                                current_page = next_page
                                source_id = target_id
                                i += 1
                            else:
                                break
                    except Exception as e:
                        print(f"Error processing {current_page}: {e}")
                        break
