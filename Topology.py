import networkx as nx
import matplotlib.pyplot as plt
from crypto import LibNaCLSK, ECCrypto
import random
import time
import pickle
from Node_Database import NodeDatabase,Node
import os


class Topology(object):
    """
    1.specify the number of honest nodes and evil nodes
    2.create 1 honest region and 1 evil region
    3.connect them with few edges
    4.for each edge, assign a random up attribute and a down attributes
    5.for each node, assign a public key
    """
    def __init__(self,honest_node_number,evil_node_number,attack_edge_number):
        print("generating topology")
        if os.path.isfile("NodeDatabase.db"):
            os.remove("NodeDatabase.db")
        self.database = NodeDatabase()
        self.crypto = ECCrypto()
        region_honest = nx.powerlaw_cluster_graph(honest_node_number,3,0.1)
        region_evil = nx.powerlaw_cluster_graph(evil_node_number,3,0.1)
        print("topology generated")
        #setting a label for honest or evil
        #nx.set_node_attributes(region_honest, 'honest', True)
        #nx.set_node_attributes(region_evil, 'honest', False)

        #now replacing the original label with public key
        mapping_honest = dict()
        mapping_evil = dict()
        public_key_honest = dict()
        public_key_evil = dict()
        public_keys = dict()
        list_public_key_honest = []
        list_public_key_evil = []

        print("creating key dict")
        
        honest_nodes_list=[]
        evil_nodes_list=[]
        for i in range(0,honest_node_number):
            key = LibNaCLSK()
            key_bin = key.key_to_bin()
            key_pub = key.pub()
            key_pub_bin = key_pub.key_to_bin()
            #public_key_honest.append(key_pub_bin)
            #key_dict = dict()
            #key_dict["public key"] = key_pub
            #key_dict["private key"] = key
            #key_dict["public key binary"] = key_pub_bin
            #key_dict["honest"] = True
            #key_dict["id"] = i
            #key_dict["identity"] = self.crypto.key_to_hash(key_pub)
            #public_key_honest[key_pub_bin] = key_dict
            mapping_honest[i] = key_pub_bin
            list_public_key_honest.append(key_pub_bin)
            node = Node()
            node.set(public_key =key_pub_bin,private_key = key_bin,member_identity=self.crypto.key_to_hash(key_pub),honest=True)
            honest_nodes_list.append(node)
        self.database.add_nodes(honest_nodes_list)

        for i in range(0,evil_node_number):
            key = LibNaCLSK()
            key_bin = key.key_to_bin()
            key_pub = key.pub()
            key_pub_bin = key_pub.key_to_bin()
            #public_key_honest.append(key_pub_bin)
            #key_dict = dict()
            #key_dict["public key"] = key_pub
            #key_dict["private key"] = key
            #key_dict["public key binary"] = key_pub_bin
            #key_dict["honest"] = False
            #key_dict["id"] = i+honest_node_number
            #key_dict["identity"] = self.crypto.key_to_hash(key_pub)
            #public_key_evil[key_pub_bin] = key_dict
            mapping_evil[i] = key_pub_bin 
            list_public_key_evil.append(key_pub_bin)
            node=Node()
            node.set(public_key =key_pub_bin,private_key = key_bin,member_identity=self.crypto.key_to_hash(key_pub),honest=False)
            evil_nodes_list.append(node)
        self.database.add_nodes(evil_nodes_list)

        #public_keys.update(public_key_honest)
        #public_keys.update(public_key_evil)

        print("relabeling nodes")

        self.region_honest_relabel =nx.relabel_nodes(region_honest,mapping_honest)
        self.region_evil_relabel =nx.relabel_nodes(region_evil,mapping_evil)
        #self.region = nx.compose(self.region_honest_relabel,self.region_evil_relabel)
        region_honest=None
        region_evil = None

        print("creating directed graph")
        #convert the graph to directed graph
        self.honest_graph = nx.DiGraph()
        self.evil_graph = nx.DiGraph()

        for node in self.region_honest_relabel.nodes():
            self.honest_graph.add_node(node)
        for node in self.region_evil_relabel.nodes():
            self.evil_graph.add_node(node)
        nx.set_node_attributes(self.honest_graph, 'honest', True)
        nx.set_node_attributes(self.evil_graph, 'honest', False)

        for edge in self.region_honest_relabel.edges():
            self.honest_graph.add_edge(edge[0],edge[1],weight=random.randint(50,300))
            self.honest_graph.add_edge(edge[1],edge[0],weight=random.randint(50,300))

        for edge in self.region_evil_relabel.edges():
            self.evil_graph.add_edge(edge[0],edge[1],weight=random.randint(50,300))
            self.evil_graph.add_edge(edge[1],edge[0],weight=random.randint(50,300))


        self.Graph = nx.compose(self.honest_graph,self.evil_graph)


        print("adding attack edge")
        #adding attack_edges
        for i in range(0,attack_edge_number):
            public_key_victim = list_public_key_honest[random.randint(0,honest_node_number-1)]
            public_key_attacker = list_public_key_evil[random.randint(0,evil_node_number-1)]
            self.Graph.add_edge(public_key_victim,public_key_attacker,weight=random.randint(50,300))
            self.Graph.add_edge(public_key_attacker,public_key_victim,weight=random.randint(50,300))

        """
        #add up/down to each edge
        for edge in self.region.edges():
            self.region.add_edge(edge[0],edge[1],weight=random.randint(50,300))
            self.region.add_edge(edge[1],edge[0],weight=random.randint(50,300))
        """

        self.database.close()

        nx.write_gpickle(self.Graph, "topo.gpickle")
        #pickle.dump( public_keys, open( "public_keys.p", "wb" ) )


        pos = nx.shell_layout(self.Graph)

        nx.draw_networkx_nodes(self.Graph,pos,
                       nodelist=self.Graph.nodes(),
                       node_color='r',
                       node_size=20,
                       alpha=0.8)

        nx.draw_networkx_nodes(self.Graph,pos,
                       nodelist=self.evil_graph.nodes(),
                       node_color='b',
                       node_size=20,
                       alpha=0.8)


        nx.draw_networkx_edges(self.Graph,pos,
                       edgelist=self.Graph.edges(),
                       width=1,alpha=0.2,edge_color='g')

        #nx.draw_networkx_labels(self.Graph,pos,labels,font_size=16)
        #print self.evil_graph.nodes()
        #plt.show()
        #for node in self.Graph.nodes():
            #print self.Graph.node[node]["honest"]


if __name__ == "__main__":
    time_start = time.time()
    topo = Topology(honest_node_number=4000,evil_node_number=6000,attack_edge_number=20)
    time_end = time.time()
    print(time_end-time_start)


