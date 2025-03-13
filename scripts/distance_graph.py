import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("output/distances.csv")

distance_counts = df.groupby("distance")["article"].count().reset_index()
distance_counts.columns = ["distance", "num_nodes"]


plt.figure(figsize=(10, 6))
plt.bar(distance_counts["distance"], distance_counts["num_nodes"], color="skyblue")
plt.xlabel("Distancia a Filosofía")
plt.ylabel("Número de nodos")
plt.title("Distribución de nodos por distancia a 'Filosofía'")
plt.xticks(distance_counts["distance"])  # Si no hay muchos niveles
plt.tight_layout()


plt.savefig("output/distribution_distance_nodes.png")

