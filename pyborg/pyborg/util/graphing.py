import json
import logging

import networkx as nx
import matplotlib.pyplot as plt
from networkx.readwrite import json_graph

logger = logging.getLogger(__name__)


def networkx_demo(pyb, graphics=False, export=False, dot=True, limit=70):
    G = nx.Graph()
    print(pyb)
    for counter, word in enumerate(pyb.words.keys()):
        if counter >= limit:
            break
        G.add_node(word)
        for p in pyb.words[word]:
            print(p)
            try:
                G.add_edge(word, pyb.lines[p["hash"]][0])
            except KeyError:
                G.add_edge(word, pyb.lines[p["hashval"]][0])
    logger.debug(G)

    if dot:
        nx.nx_agraph.write_dot(G, "graph_demo.dot")
    if graphics:
        nx.draw(G)
        plt.show()
    if export:
        data = json_graph.node_link_data(G)
        s = json.dumps(data)
        return s
    return G
