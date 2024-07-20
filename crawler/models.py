from crawler.helpers import extract_domain

class Node:
    def __init__(self, url, depth):
        self.url = url
        self.depth = depth
        self.visited = False
        self.edges = []
        self.title = ""
        self.text = ""

    def add_edge(self, node):
        self.edges.append(node)

class WebGraph:
    def __init__(self, name, root_url, max_depth):
        self.root_url = root_url
        self.name = name
        self.domain = extract_domain(root_url)
        self.max_depth = max_depth
        self.nodes = {}

    def add_node(self, url, depth):
        if url not in self.nodes:
            self.nodes[url] = Node(url, depth)
        return self.nodes[url]

    def add_edge(self, from_url, to_url):
        if from_url in self.nodes and to_url in self.nodes:
            from_node = self.nodes[from_url]
            to_node = self.nodes[to_url]
            from_node.add_edge(to_node)

    def get_node(self, url):
        return self.nodes.get(url)

    def __str__(self):
        return '\n'.join(f"{node.url} (Depth: {node.depth})" for node in self.nodes.values())
