from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from random import shuffle
from crypto import ECCrypto
from hashlib import sha1
#an easywalker is a cutting corner walker which never take step
#easywalker doesn't has its own message handler, multiple walkers share the message handlers of one manager
class EasyWalker(DatagramProtocol):
    def __init__(self,public_key,private_key,manager,ip,port = 25000,neighbor_list=[]):
        self.manager = manager
        self.private_address = (str(ip),int(port))
        self.public_address = (str(ip),int(port))
        self.master_key = "3081a7301006072a8648ce3d020106052b8104002703819200040503dac58c19267f12cb0cf667e480816cd2574acae" \
                     "5293b59d7c3da32e02b4747f7e2e9e9c880d2e5e2ba8b7fcc9892cb39b797ef98483ffd58739ed20990f8e3df7d1ec5" \
                     "a7ad2c0338dc206c4383a943e3e2c682ac4b585880929a947ffd50057b575fc30ec88eada3ce6484e5e4d6fdf41984c" \
                     "d1e51aaacc5f9a51bcc8393aea1f786fc47cbf994cb1339f706df4a"
        self.master_key_hex = self.master_key.decode("HEX")
        self.neighbor_list = neighbor_list
        self.reactor = reactor
        self.listening_port=self.reactor.listenUDP(port, self)
        self.my_public_key=public_key
        self.dispersy_version = "\x00"
        self.community_version = "\x01"
        #abandom name "prefix", use "header" to replace
        
        self.crypto = ECCrypto()
        self.my_key = self.crypto.key_from_private_bin(private_key)
        #self.my_identity = self.crypto.key_to_hash(self.my_key.pub())
        self.my_identity=sha1(self.my_public_key).digest()
        self.key = self.crypto.key_from_public_bin(self.master_key_hex)
        self.master_identity = self.crypto.key_to_hash(self.key.pub())
        self.global_time = 0
        self.start_header = self.dispersy_version+self.community_version+self.master_identity
        print(self.neighbor_list)
        print("walker running in port "+str(port))


        
    def startProtocol(self):
        pass
    def stopProtocol(self):
        pass

    def datagramReceived(self, data, addr):
        """
        built-in function of twisted.internet.protocol.DatagramProtocol.
        will be call whenever a UDP packet comes in
        """
        print("received data from" +str(addr))
        #now we receive a UDP datagram, call decode_message to decode it
        self.handle_message(data,addr)

    def handle_message(self,packet,addr):
        #call different message handler according to its message_type
        #TODO:we should ask for public key of other members here
        message_type = ord(packet[22])
        #logger.info("message id is:"+str(message_type))
        print("message id is:"+str(message_type))
        if message_type == 247:
            print("here is a missing-identity message")
            messages_to_send=self.manager.on_missing_identity(packet,addr,walker=self)
            self.send_messages(messages_to_send)
        if message_type == 245:
            print("here is a introduction-response")
            #easy walker don't care about introduction response
            #self.manager.on_introduction_response(packet,addr,neighbor_to_introduce)
        if message_type == 246:
            print("here is a introduction-request")
            shuffle(self.neighbor_list)
            neighbor_to_introduce = self.neighbor_list[0]
            #neighbor_to_introduce=("127.0.0.1",self.public_address[1])
            #for experiment use, we return our self
            messages_to_send=self.manager.on_introduction_request(packet,addr,neighbor_to_introduce,walker=self)
            self.send_messages(messages_to_send)
        if message_type == 250:
            print("here is a puncture request")
            messages_to_send=self.manager.on_puncture_request(packet,addr,walker=self)
            self.send_messages(messages_to_send)
        if message_type == 249:
            print("here is a puncture")
        if message_type == 248:
            print("here is an dispersy-identity")
            #easywalker don't care dispersy-identity
            #self.manager.on_identity(packet,addr)
        if message_type == 1:
            print ("here is a halfblock message")
            #easy walker never crawl, so it doesn't care about crawl response
            #self.manager.on_halfblock(packet,addr)
        if message_type == 2:
            print("here is a crawl(request)")
            messages_to_send=self.manager.on_crawl_request(packet,addr,public_key=self.my_public_key,walker=self)
            self.send_messages(messages_to_send)
        #if message_type == 3:
            #print("here is a crawl_response")
            #self.on_crawl_response(packet,addr)
        #if message_type == 4:
            #print("here is a crawl_resume.............................................................:D")
            #self.on_crawl_resume(packet,addr)

    def send_messages(self,messages_to_send):
        #print type(messages_to_send)
        print messages_to_send
        for message in messages_to_send:
            self.transport.write(message[0],message[1])


