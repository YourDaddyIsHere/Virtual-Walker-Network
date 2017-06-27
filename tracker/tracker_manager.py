import sys
if sys.platform == "darwin":
    # Workaround for annoying MacOS Sierra bug: https://bugs.python.org/issue27126
    # As fix, we are using pysqlite2 so we can supply our own version of sqlite3.
    import pysqlite2.dbapi2 as sqlite3
else:
    import sqlite3
from configobj import ConfigObj
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import networkx as nx
from Node_Database import NodeDatabase,Node
#from crypto import ECCrypto
import os
from tracker.neighbor_discovery import NeighborDiscover
from tracker.Neighbor import Neighbor
from tracker.Neighbor_group import NeighborGroup
BASE = os.path.dirname(os.path.abspath(__file__))
#from subprocess import call,Popen, PIPE
#from easywalker.easywalker import EasyWalker
#import traceback
#from easywalker.Message import Message
#from Neighbor import Neighbor

class TrackerManager(DatagramProtocol):
    def __init__(self):
        self.reactor = reactor
        self.listening_port=self.reactor.listenUDP(61000, self)
        text_file = open(os.path.join(BASE, 'managerstarted'), "a")
        text_file.write("it starts")
        config = ConfigObj(os.path.join(BASE, 'tracker.conf'))
        self.tracker_port = int(config["port"])
        print("run tracker in port: "+ str(self.tracker_port))
        self.honest_range = config["honest_range"]
        print self.honest_range
        self.evil_range = config["evil_range"]
        print self.evil_range
        #self.honest_record_number = int(config["honest_record_number"])
        #self.evil_record_number = int(config["evil_record_number"])
        print self.tracker_port
        #print self.honest_record_number
        #print self.evil_record_number

        self.node_database = NodeDatabase()
        honest_nodes = self.node_database.get_node_between(start_index=int(self.honest_range[0]),end_index=int(self.honest_range[1]))
        evil_nodes = self.node_database.get_node_between(start_index=int(self.evil_range[0]),end_index=int(self.evil_range[1]))

        neighbor_group = NeighborGroup()
        neighbor_group.tracker=[]
        for node in honest_nodes:
            #print (node.ip,node.port)
            neighbor = Neighbor((str(node.ip),int(node.port)),(str(node.ip),int(node.port)))
            neighbor_group.tracker.append(neighbor)
        for node in evil_nodes:
            #print (node.ip,node.port)
            neighbor = Neighbor((str(node.ip),int(node.port)),(str(node.ip),int(node.port)))
            neighbor_group.tracker.append(neighbor)
        for neighbor in neighbor_group.tracker:
            print neighbor.get_public_address()
        self.tracker = NeighborDiscover(port=self.tracker_port,is_tracker=True,neighbor_group=neighbor_group)
        self.reactor.run()


    def datagramReceived(self, data, addr):
        """
        built-in function of twisted.internet.protocol.DatagramProtocol.
        will be call whenever a UDP packet comes in
        """
        print("received data from" +str(addr))
        if data=="stopexperiment":
            print("receive stop signal")
            self.reactor.stop()
        #now we receive a UDP datagram, call decode_message to decode it
        #self.handle_message(data,addr)

    def startProtocol(self):
        pass
    def stopProtocol(self):
        os.kill(os.getppid(), signal.SIGHUP)










if __name__ == "__main__":
    trackermanager=TrackerManager()