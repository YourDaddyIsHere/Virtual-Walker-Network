import sys
sys.path.append(".")
import os
import os.path
BASE = os.path.dirname(os.path.abspath(__file__))
import signal
if sys.platform == "darwin":
    # Workaround for annoying MacOS Sierra bug: https://bugs.python.org/issue27126
    # As fix, we are using pysqlite2 so we can supply our own version of sqlite3.
    import pysqlite2.dbapi2 as sqlite3
else:
    import sqlite3
from hashlib import sha256
from configobj import ConfigObj
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import networkx as nx
from Node_Database import NodeDatabase,Node
from HalfBlockDatabase import HalfBlockDatabase,HalfBlock
from crypto import ECCrypto
import os
from subprocess import call,Popen, PIPE,check_output
from easywalker.easywalker import EasyWalker
import traceback
from easywalker.Message import Message
from Neighbor import Neighbor
import socket
import time

class Slave(DatagramProtocol):
    def __init__(self):
        self.config_task = ConfigObj(os.path.join(BASE, 'task.conf'))
        self.start_node = int(self.config_task["start_node"])
        self.end_node = int(self.config_task["end_node"])
        print self.start_node
        self.Graph = nx.read_gpickle(os.path.join(BASE, 'topo.gpickle'))
        self.walkers=[]
        self.node_database = NodeDatabase()
        self.block_database = HalfBlockDatabase()
        self.nodes = self.node_database.get_node_between(start_index=self.start_node,end_index=self.end_node)
        self.reactor = reactor
        self.manager_port = int(self.config_task["manager_port"])
        self.listening_port=self.reactor.listenUDP(self.manager_port, self)
        #self.neighbor_list=[]
        #for node in self.nodes:
            #print node.id
        print("start to create a walker...")
        for i in range(self.start_node,self.end_node+1):
            #create each walker and add neighbors and blocks to them
            #1.add neighbors
            neighbor_list=[]
            node = self.nodes[(i-self.start_node)]
            node_public_key = node.public_key
            #get all incoming and outgoing edge of this node
            in_edges = self.Graph.in_edges(nbunch=node_public_key,data=True)
            out_edges = self.Graph.out_edges(nbunch=node_public_key,data=True)
            member_dict = dict()
            #calculating down load by incoming edge
            print("creating blocks")
            for edge in in_edges:
                #print edge
                if edge[0] not in member_dict:
                    attribute_dict = dict()
                    attribute_dict["down"] = int(edge[2]["weight"])
                    attribute_dict["up"] = 0
                    member_dict[edge[0]] = attribute_dict
                else:
                    member_dict[edge[0]]["down"] = member_dict[edge[0]]["down"] = int(edge[2]["weight"])

            #calculate upload by outgoing edge
            for edge in out_edges:
                if edge[1] not in member_dict:
                    attribute_dict["down"] = 0
                    attribute_dict["up"] =  int(edge[2]["weight"])
                    member_dict[edge[1]] = attribute_dict
                else:
                    member_dict[edge[1]]["up"] = member_dict[edge[1]]["up"] = int(edge[2]["weight"])

            #print member_dict
            sequence_number=1
            previous_hash = '0'*32
            blocks=[]
            for member in member_dict:
                block = HalfBlock()
                block.link_public_key = member
                block.public_key=node_public_key
                block.link_sequence_number = 0
                block.sequence_number = sequence_number
                block.previous_hash = previous_hash
                block.up = member_dict[member]["up"]
                block.down = member_dict[member]["down"]
                crypto = ECCrypto()
                key = crypto.key_from_private_bin(node.private_key)
                #print(repr(node.private_key))
                block.sign(key=key)
                #print(repr(block.signature))
                #self.block_database.add_block(block,commit=False)
                blocks.append(block)
                sequence_number = sequence_number+1
                previous_hash = block.hash
            try:
                self.block_database.add_blocks(blocks,commit=False)
                if i%100==0:
                    print("commit")
                    self.block_database.commit()
            except:
                pass

            #now createing neighbor list
            print("creating neighbor list")
            for edge in in_edges:
                node = self.node_database.get_node_by_public_key(public_key=edge[0])
                neighbor = (str(node.ip),int(node.port))
                if neighbor not in neighbor_list:
                    neighbor_list.append(neighbor)

            for edge in out_edges:
                node = self.node_database.get_node_by_public_key(public_key=edge[1])
                neighbor = (str(node.ip),int(node.port))
                if neighbor not in neighbor_list:
                    neighbor_list.append(neighbor)

            print("start easy walker instance")
            #now let's start the easywalker
            try:
                walker = EasyWalker(manager=self,public_key=node_public_key,private_key=node.private_key,neighbor_list=neighbor_list,ip=node.ip,port=(i-self.start_node)+10000)
                print("walker created")
                self.walkers.append(walker)
            except Exception as e:
                traceback.print_exc(e)
                output = check_output(["lsof","-t","-i:"+str(10000+(i-self.start_node))])
                #script="-i :"+str(10000+(i-self.start_node))
                #process = Popen(["lsof","-t",script], stdout=PIPE)
                #(output, err) = process.communicate()
                #exit_code = process.wait()
                print output
                call(["kill", str(output.strip())])
                time.sleep(3)
                try:
                    #if we fail again...so be it
                    walker = EasyWalker(manager=self,public_key=node_public_key,private_key=node.private_key,neighbor_list=neighbor_list,ip=node.ip,port=(i-self.start_node)+10000)
                except:
                    pass
                print("port release and walker started")
                self.walkers.append(walker)
        self.block_database.commit()
        #p = Popen(["ansible","-i","Output","hosts","-a","sh tryConfigObj/run.sh"]) # something long running
        #p2=Popen(["ansible","-i","Output","hosts","-a","python tryConfigObj/oneprint.py"])
        self.reactor.run()







    def startProtocol(self):
        print("protocol started")
    def stopProtocol(self):
        os.kill(os.getppid(), signal.SIGHUP)

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


    def on_introduction_request(self,packet,addr,neighbor_to_introduce,walker):
        """
        1.decode a introduction request
        2.introduce a neighbor we known to the requester
        3.send a puncture request to the neighbor we introduce in step 2
        """
        """
        message_request = Message(packet=packet)
        message_request.decode_introduction_request()
        self.global_time = message_request.global_time
        requester_neighbor = Neighbor(message_request.source_private_address,addr,identity = message_request.sender_identity)
        self.neighbor_group.add_neighbor_to_incoming_list(requester_neighbor)
        #do public_address_vote
        self.public_address_vote(message_request.destination_address,addr)
        #we don't have codes to determine whether the candidate is within our lan, so we use wan address.
        #candidate_request = Wcandidate(message_request.source_lan_address,message_request.source_wan_address)
        neighbor_to_introduce = self.neighbor_group.get_neighbor_to_introduce(requester_neighbor)
        if neighbor_to_introduce!=None:
            introduced_private_address = neighbor_to_introduce.get_private_address()
            introduced_public_address = neighbor_to_introduce.get_public_address()
        else:
            introduced_private_address=("0.0.0.0",0)
            introduced_public_address=("0.0.0.0",0)
        message_response = Message(neighbor_discovery=self,identifier=message_request.identifier,destination_address=addr,source_private_address =self.private_address,source_public_address=self.public_address,
                                   private_introduction_address=introduced_private_address,public_introduction_address=introduced_public_address)
        message_response.encode_introduction_response()
        #now it is time to create puncture request
        if neighbor_to_introduce!=None:
            message_puncture_request = Message(neighbor_discovery=self,source_private_address=message_request.source_private_address,source_public_address=message_request.source_public_address,
                                               private_address_to_puncture=message_request.source_private_address,public_address_to_puncture=addr)
            message_puncture_request.encode_puncture_request()
            #send one puncture request to private ip and one puncture request to public ip
            self.transport.write(message_puncture_request.packet,neighbor_to_introduce.get_public_address())
            self.transport.write(message_puncture_request.packet,neighbor_to_introduce.get_public_address())
        self.transport.write(message_response.packet,addr)
        """

        message_request = Message(packet=packet)
        message_request.decode_introduction_request()
        requester_neighbor = Neighbor(message_request.source_private_address,addr,identity = message_request.sender_identity)
        introduced_private_address = neighbor_to_introduce
        introduced_public_address = neighbor_to_introduce
        message_response = Message(neighbor_discovery=walker,identifier=message_request.identifier,destination_address=addr,source_private_address =walker.private_address,source_public_address=walker.public_address,
                                   private_introduction_address=introduced_private_address,public_introduction_address=introduced_public_address)
        message_response.encode_introduction_response()
        message_puncture_request = Message(neighbor_discovery=walker,source_private_address=message_request.source_private_address,source_public_address=message_request.source_public_address,
                                               private_address_to_puncture=message_request.source_private_address,public_address_to_puncture=addr)
        message_puncture_request.encode_puncture_request()
        return([(message_response.packet,addr),(message_puncture_request.packet,neighbor_to_introduce)])



    def on_introduction_response(self,packet,addr):
        """
        1.decode a introduction response
        2.do public address vote to determine our public address
        3.add the introduced neighbor to neighbor_group
        """
        message = Message(packet=packet)
        message.decode_introduction_response()
        self.global_time = message.global_time
        self.public_address_vote(message.destination_address,addr)
        message_sender=Neighbor(message.source_private_address,addr,identity = message.sender_identity)
        self.neighbor_group.add_neighbor_to_outgoing_list(message_sender)
        print("the introduced candidate is: "+ str(message.public_introduction_address))
        if message.private_introduction_address!=("0.0.0.0",0) and message.public_introduction_address!=("0.0.0.0",0):
            introduced_neighbor = Neighbor(message.private_introduction_address,message.public_introduction_address)
            self.neighbor_group.add_neighbor_to_intro_list(introduced_neighbor)
            print("new candidate has been added to intro list")
        #send a missing identity by the way
        identity = message.sender_identity
        responder_member = self.database.get_member(identity = identity)
        if responder_member is None:
            message_missing_identity = Message(neighbor_discovery=self,the_missing_identity=message.sender_identity)
            message_missing_identity.encode_missing_identity()
            self.transport.write(message_missing_identity.packet,addr)

        #identity = message.sender_identity
        member = self.database.get_member(identity = identity)
        if member is not None:
            print("the member of the introduction response is: "+str(member[0]))
            public_key = member[1]
            requested_sequence_number = self.database.get_latest_sequence_number(public_key=public_key) +1
            #message_crawl_request = Message(neighbor_discovery=self,requested_sequence_number = requested_sequence_number)
            #message_crawl_request.encode_crawl_request()
            message_crawl = Message(neighbor_discovery=self,requested_sequence_number = requested_sequence_number)
            message_crawl.encode_crawl()
            self.transport.write(message_crawl.packet,addr)
            print("crawl sent")

    def on_puncture_request(self,packet,addr,walker):
        """
        1.decode a puncture request and knows which neighbor we should send the puncture to
        2.send a puncture to both private and public address of that neighbor
        """

        """
        message_puncture_request = Message(packet=packet)
        message_puncture_request.decode_puncture_request()
        self.global_time = message_puncture_request.global_time
        private_address_to_puncture = message_puncture_request.private_address_to_puncture
        public_address_to_puncture = message_puncture_request.public_address_to_puncture
        self.public_address = self.get_majority_vote()
        print("the public addr from majority vote is:")
        print(self.public_address)
        message_puncture = Message(neighbor_discovery=self,source_private_address=self.private_address,
                                   source_public_address=self.public_address)
        message_puncture.encode_puncture()
        self.transport.write(message_puncture.packet,private_address_to_puncture)
        self.transport.write(message_puncture.packet,public_address_to_puncture)
        """

        message_puncture_request = Message(packet=packet)
        message_puncture_request.decode_puncture_request()
        self.global_time = message_puncture_request.global_time
        private_address_to_puncture = message_puncture_request.private_address_to_puncture
        public_address_to_puncture = message_puncture_request.public_address_to_puncture
        message_puncture = Message(neighbor_discovery=walker,source_private_address=walker.private_address,
                                   source_public_address=walker.public_address)
        message_puncture.encode_puncture()
        return [(message_puncture.packet,public_address_to_puncture)]



    def on_missing_identity(self,packet,addr,walker):
        """
        1.decode a missing identity
        2.send a dispersy-identity message with our public key
        """
        """
        message_missing_identity = Message(packet=packet)
        message_missing_identity.decode_missing_identity()
        self.global_time = message_missing_identity.global_time
        message_identity = Message(neighbor_discovery=self)
        message_identity.encode_identity()
        self.transport.write(message_identity.packet,addr)
        """

        message_missing_identity = Message(packet=packet)
        message_missing_identity.decode_missing_identity()
        self.global_time = message_missing_identity.global_time
        message_identity = Message(neighbor_discovery=walker)
        message_identity.encode_identity()
        return [(message_identity.packet,addr)]


    def on_identity(self,packet,addr):
        """
        1.decode a dispersy-identity message
        2.store the public key in the message to our database
        3.associate this key with the candidate
        4.move this candidate to trusted neigbhors list
        """
        message_identity=Message(packet=packet)
        message_identity.decode_identity()
        sender_identity = sha1(message_identity.key_received).digest()
        if(self.database.get_member(public_key=message_identity.key_received)==None):
            self.database.add_member(identity=sender_identity,public_key=message_identity.key_received)
            #then send a crawl request
            requested_sequence_number = self.database.get_latest_sequence_number(public_key=message_identity.key_received) +1
            message_crawl = Message(neighbor_discovery=self,requested_sequence_number = requested_sequence_number)
            message_crawl.encode_crawl()
            self.transport.write(message_crawl.packet,addr)
        self.neighbor_group.associate_neigbhor_with_public_key(public_ip=addr,identity=sender_identity,public_key = message_identity.key_received)
        self.neighbor_group.insert_trusted_neighbor(Graph=self.database.trust_graph,my_public_key=self.my_public_key)



    def on_crawl_request(self,packet,addr,public_key,walker):
        message_crawl_request = Message(packet=packet)
        message_crawl_request.decode_crawl()
        print("requested sequence number is: "+str(message_crawl_request.requested_sequence_number))
        print("the public key is: "+repr(public_key))
        #print("the type of public key in on crawl request is:")
        print type(public_key)
        blocks = self.block_database.get_blocks_since(public_key=public_key,sequence_number=int(message_crawl_request.requested_sequence_number))
        #blocks = self.block_database.get_blocks_since(public_key=public_key,sequence_number=1)
        print(blocks)
        messages_to_send = []
        for block in blocks:
            message = Message(neighbor_discovery=walker,block=block)
            print("we have following blocks to send: "+str(block.up))
            message.encode_halfblock()
            messages_to_send.append((message.packet,addr))
        return messages_to_send



    def on_crawl_response(self,packet,addr):
        """
        it is a message in old protocol, should we still support old protocol?
        """
        message_crawl_response = Message(packet=packet)
        message_crawl_response.decode_crawl_response()
        block = message_crawl_response.block
        block.show()
        #it is possible that some guys send us a send block twice due to network latency
        #but we add a block to the database without checking whether it is already in the database
        #it is time consuming to check it using SELECT ... WHERE has_requester =? 
        #if a block is already in database, the database will returns a PRIMARY KEY constraint error. It does no harm to us
        self.database.add_block(block)

    def on_halfblock(self,packet,addr):
        """
        decode a halfblock message, store the block inside to our database
        """
        message_crawl_response = Message(packet=packet)
        message_crawl_response.decode_halfblock()
        block = message_crawl_response.block
        #block.show()
        #it is possible that some guys send us a send block twice due to network latency
        #but we add a block to the database without checking whether it is already in the database
        #it is time consuming to check it using SELECT ... WHERE has_requester =? 
        #if a block is already in database, the database will returns a PRIMARY KEY constraint error. It does no harm to us
        self.database.add_block(block)



if __name__ == "__main__":
    slave=Slave()