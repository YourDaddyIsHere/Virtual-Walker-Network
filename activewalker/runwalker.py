import os
from neighbor_discovery import NeighborDiscover
from Neighbor_group import NeighborGroup
from Neighbor import Neighbor
from configobj import ConfigObj
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
BASE = os.path.dirname(os.path.abspath(__file__))
class walkerManager(DatagramProtocol):
    def __init__(self):
        self.reactor = reactor
        self.listening_port=self.reactor.listenUDP(63000, self)
        print("program starts")
        
        #self.walker.neighbor_group.tracker=[]
        config = ConfigObj(os.path.join(BASE, 'tracker.conf'))
        tracker_ip = config["public_ip"]
        tracker_port = int(config["port"])
        neighbor = Neighbor((tracker_ip,tracker_port),(tracker_ip,tracker_port))
        neighbor_group = NeighborGroup()
        neighbor_group.tracker = []
        neighbor_group.tracker.append(neighbor)
        #for n in self.walker.neighbor_group.tracker:
            #print n.get_public_address()
        self.walker = NeighborDiscover(neighbor_group=neighbor_group)
        self.reactor.callLater(1, self.show)
        self.reactor.run()

    def show(self):
        for n in self.walker.neighbor_group.tracker:
            print n.get_public_address()
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
        pass
        #os.kill(os.getppid(), signal.SIGHUP)

if __name__ == "__main__":
    walker_manager=walkerManager()