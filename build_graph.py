import requests
import os
import tomllib
from os import system
import networkx as nx
from tqdm import tqdm
import string
import numpy as np
import random

def download_registry():
    url = "https://github.com/JuliaRegistries/General/archive/refs/heads/master.zip"
    response = requests.get(url)
    with open("registry.zip", "wb") as f:
        f.write(response.content)
    system("unzip -o registry.zip -d .")


def get_dependencies_package(package):
    letter = package[0].upper()
    fname = f"General-master/{letter}/{package}/Deps.toml"
    deps = []
    if os.path.isfile(fname):
        with open(fname, "rb") as f:
            deps_toml = tomllib.load(f)
        for version in deps_toml:
            deps.extend(deps_toml[version].keys())
    return list(set(deps))

def get_repo_package(package):
    letter = package[0].upper()
    fname = f"General-master/{letter}/{package}/Package.toml"
    if os.path.isfile(fname):
        with open(fname, "rb") as f:
            toml_package = tomllib.load(f)
        if "repo" in toml_package:
            return toml_package["repo"]
    return None


def get_dependencies():
    dependencies = {}
    for letter in tqdm(string.ascii_uppercase):
        letter_path = f"General-master/{letter}"
        if os.path.isdir(letter_path):
            for package in os.listdir(letter_path):
                package_path = f"{letter_path}/{package}"
                if os.path.isdir(package_path):
                    dependencies[package] = get_dependencies_package(package)
    return dependencies

def build_graph(dependencies):
    non_std = dependencies.keys()
    G = nx.DiGraph()
    for pkg, deps in dependencies.items():
        for dep in deps:
            if dep in non_std:
                G.add_edge(pkg, dep)
    G = page_rank(G, scale=1000)
    for node in G.nodes():
        G.nodes[node]['label'] = node
        nodecolor = {"r": 0, "g": 0, "b": 0, "a": 1}
        G.nodes[node]['viz'] = {"size":2+G.in_degree(node)*0.01, "position":{"x":random.random(), "y":random.random(), "z":0.0}, "color":nodecolor}
        G.nodes[node]['color'] = nodecolor
        G.nodes[node]['repo'] = get_repo_package(node)
    return G



def page_rank(G, scale=1):
    pr_dict = nx.pagerank(G)
    pr = np.array(list(pr_dict.values()))
    pr = pr-np.min(pr)
    pr = pr/np.max(pr)* scale
    nodes = np.array(list(pr_dict.keys()))
    pr_dict = dict(zip(nodes, pr))
    nx.set_node_attributes(G, pr_dict, 'pagerank')
    return G


def update_readme():
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    readme_path = "README.MD"
    with open(readme_path, "a") as f:
        f.write(f"\n\n_Last updated: {current_date}_\n")

dependencies = get_dependencies()
G = build_graph(dependencies)
print(len(G.nodes))
remove = [node for node, degree in G.in_degree() if degree < 2]
G.remove_nodes_from(remove)
remove = [node for node, degree in G.degree() if degree < 1]
G.remove_nodes_from(remove)
print(len(G.nodes))
nx.write_gexf(G, "graph.gexf")
update_readme()
