import os
import sys
import csv
from collections import deque

# ----- Helper Functions -----

class ArticleDictionary: 
    def __init__(self):
        self.article_to_idx = {}
        self.idx_to_article = {}
        self.next_idx = 0

    def idx_for_article(self, article):
        """
        Returns the index for the article, if it doesn't exist yet, it assigns one
        """
        if article not in self.article_to_idx:
            self.article_to_idx[article] = self.next_idx
            self.idx_to_article[self.next_idx] = article
            self.next_idx += 1
        return self.article_to_idx[article]
    
def parse_network(filename, article_dict):
    """
    Reads the csv file and constructs a graph.
    Returns set of nodes (articles) and dictionary of edges 
    """
    nodes = set()
    edges = {}
  
    total_size = os.path.getsize(filename)
    last_percent = 0

    with open(filename, 'r', encoding="utf-8") as f:
        
        header = f.readline() # first line is useless  

        while True:
            line = f.readline()
            if not line: 
                break

            line = line.strip()
            if not line:
                continue 

            cols = line.split(", ")
            
            if len(cols) < 2:
                continue

            # construct the graph backwards (second column as origin, first as target)
            source = cols[1]
            target = cols[0]

            source_idx = article_dict.idx_for_article(source)
            target_idx = article_dict.idx_for_article(target)

            nodes.add(source_idx)
            nodes.add(target_idx)
            
            if source_idx in edges:
                if target_idx not in edges[source_idx]:
                    edges[source_idx].append(target_idx)
            else: 
                edges[source_idx] = [target_idx]

            # progress calculation
            current_position = f.tell() 
            percent = int((current_position / total_size) * 100)
            if percent > last_percent:
                last_percent = percent
                print(f"Progress: {percent}%", end="\r", flush=True)

    return nodes, edges

def bfs(start_article, nodes, edges, article_dict):
    """
    Performs breadth first search from "Filosofía"
    Prints the distance from each article to Philosophy
    """
    boundary = deque()
    visited = set()
    unvisited = set(nodes)

    start_idx = article_dict.article_to_idx[start_article]

    boundary.append(start_idx)
    visited.add(start_idx)
    unvisited.discard(start_idx)

    distance = 0
    with open(output_file, "w", encoding="utf-8") as outfile:

        # header
        outfile.write("article, distance\n")
        
        while boundary:
            frontier = deque()
            for node in boundary:
                outfile.write(f"{article_dict.idx_to_article[node]}, {distance}\n")
                
                visited.add(node)
                unvisited.discard(node)

                for neighbor in edges.get(node, []):
                    if neighbor in unvisited:
                        frontier.append(neighbor)

            #sys.stderr.write(f"distance={distance} frontier size={len(frontier)} visited={len(visited)} unvisited={len(unvisited)}\n")
            distance += 1
            boundary = frontier
    print(f"Number of unvisited articles: {len(unvisited)}")

# ----- Main function -----


start_article = "Filosofia"
input_file = "output/network.csv"
output_file = "output/distances.txt"

article_dict = ArticleDictionary()
print("\nConverting to dictionary: ")
nodes, edges = parse_network(input_file, article_dict)

print("\nPerforming BFS: ")
bfs(start_article, nodes, edges, article_dict)