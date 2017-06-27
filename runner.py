#import networkx as nx
#import matplotlib.pyplot as plt
import socket
from crypto import LibNaCLSK
import random
import time
import pickle
from configobj import ConfigObj
from Topology import Topology
import subprocess
from subprocess import call
from subprocess import Popen, PIPE
from Node_Database import NodeDatabase,Node
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import os
class Runner(DatagramProtocol):
    def __init__(self,config_file="config.conf"):
        self.reactor = reactor
        self.listening_port=self.reactor.listenUDP(61000, self)
        if os.path.isfile("hostlist"):
            os.remove("hostlist")
        text_file = open("hostlist", "a")
        text_file.write("[slaves]\n")
        text_file.close()
        config = ConfigObj(config_file) 
        honest_node_number = config["honest_node_number"]
        evil_node_number = config["evil_node_number"]
        attack_edge_number = config["attack_edge_number"]
        print attack_edge_number
        print honest_node_number
        print evil_node_number
        #build the topology of experiment network and store it in file
        #now you should have: topo.gpickle which stores the topology
        #and NodeDatabase.db
        topology = Topology(honest_node_number=int(honest_node_number),evil_node_number=int(evil_node_number),attack_edge_number=int(attack_edge_number))
        self.database = NodeDatabase()

        #now for each hosts, create and send them relevant files
        config_task = ConfigObj("task.conf")
        for host in config["hosts list"]:
            print host
            start_node = int(config["hosts list"][host]["start_node"])
            print("the start node is: " +str(start_node))
            end_node = int(config["hosts list"][host]["end_node"])
            print("end_node is: "+str(end_node))
            workspace = config["hosts list"][host]["workspace"]
            print("workspace is: "+ str(workspace))
            address = config["hosts list"][host]["address"]
            print("address is: "+address)
            manager_port = int(config["hosts list"][host]["manager_port"])
            key = config["hosts list"][host]["key"]
            #private_ip = config["hosts list"][host]["private_ip"]
            #print("private_ip is:"+str(private_ip))
            public_ip=config["hosts list"][host]["public_ip"]
            print("public_ip is:"+str(public_ip))
            config_task["start_node"] = start_node
            config_task["end_node"] = end_node
            config_task["manager_port"] = manager_port
            config_task.write()
            for i in range(int(start_node),int(end_node+1)):
                self.database.set_ip_and_port_by_id(ip=public_ip,port=(10000+i-start_node),id=i)
            self.database.commit()
            text_file = open("hostlist", "a")
            #text_file.write("["+host+"]\n")
            text_file.write(address+"\n")
            text_file.close()
            #copy task.conf to slave folder
            call(["cp","task.conf","slave"])
            #copy NodeDatabase.db to slave folder
            call(["cp","NodeDatabase.db","slave"])
            #copy topology file to slave folder
            call(["cp","topo.gpickle","slave"])
            call(["ssh-agent"])
            call(["ssh-add",key])
            #call(["ssh-agent"])
            #call(["ssh-add","Linux1.pem"])
            print("sending files to remote workspace")
            call(["rsync","-r","slave",workspace])
            #p = Popen(["ansible","-i","hostlist","host1","-a","python slave/Slave.py"],stdout=subprocess.PIPE)


        tracker_public_ip = config["tracker"]["public_ip"]
        tracker_port = config["tracker"]["port"]
        tracker_address = config["tracker"]["address"]
        tracker_workspace = config["tracker"]["workspace"]
        tracker_key = config["tracker"]["key"]
        honest_record_number = int(config["tracker"]["honest_record_number"])
        evil_record_number = int(config["tracker"]["evil_record_number"])
        honest_range = (1,honest_record_number)
        evil_range = (int(honest_node_number)+1,int(honest_node_number)+evil_record_number)
        #create a conf file for tracker
        config_tracker = ConfigObj("tracker.conf")
        config_tracker["public_ip"]=tracker_public_ip
        config_tracker["port"] = tracker_port
        config_tracker["tracker_address"]=tracker_address
        config_tracker["honest_range"]=honest_range
        config_tracker["evil_range"]=evil_range
        config_tracker.write()
        text_file = open("hostlist", "a",0)
        text_file.write("[tracker]\n")
        text_file.write(tracker_address+"\n")
        #copy tracker.conf to tracker folder
        print("sending files to tracker machine")
        call(["cp","tracker.conf","tracker"])
        call(["cp","tracker.conf","activewalker"])
        call(["cp","NodeDatabase.db","tracker"])
        call(["ssh-agent"])
        call(["ssh-add",tracker_key])
        call(["rsync","-r","tracker",tracker_workspace])

        #process_slave = Popen(["ansible","-i","hostlist","slaves","-a","python slave/Slave.py"],stdout=subprocess.PIPE)
        #process_tracker = Popen(["ansible","-i","hostlist","tracker","-a","python tracker/tracker_manager.py"],stdout=subprocess.PIPE)
        print("tracker process started")
        self.reactor.run()



    
    #experiment intialization, e.g. sending neccessary files to slave node
    def deployment(self):
        pass
    #runs experiment
    def running(self):
        pass
    #collect data after experiment
    def collecting(self):
        pass

    def startProtocol(self):
        pass
    def stopProtocol(self):
        #os.kill(os.getppid(), signal.SIGHUP)
        config = ConfigObj("config.conf")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        for host in config["hosts list"]:
            public_ip=config["hosts list"][host]["public_ip"]
            manager_port = int(config["hosts list"][host]["manager_port"])
            self.transport.write("stopexperiment",(public_ip,manager_port))
        tracker_ip = config["tracker"]["public_ip"]
        tracker_port = int(config["tracker"]["port"])
        self.transport.write("stopexperiment",(tracker_ip,tracker_port))

    def datagramReceived(self, data, addr):
        """
        built-in function of twisted.internet.protocol.DatagramProtocol.
        will be call whenever a UDP packet comes in
        """
        print("received data from" +str(addr))










if __name__ == "__main__":
    runner = Runner()
    print("run completed")
