import json
import logging

import networkx as nx
import matplotlib.pyplot as plt
from networkx.readwrite import json_graph

logger = logging.getLogger(__name__)

def networkx_demo(pyb, graphics=False, export=False):
    G = nx.Graph()
    print(pyb)

    G.add_node("fuck")

    for p in pyb.words["fuck"]:
        G.add_edge("fuck", pyb.lines[p["hashval"]][0])

    logger.info(G)

    if graphics:
        nx.draw(G)
        plt.show()
    if export:
        data = json_graph.node_link_data(G)
        s = json.dumps(data)
        return s
    return G
