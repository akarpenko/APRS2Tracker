# Code based on: http://code.google.com/p/pyaprs/source/browse/trunk

import socket, select, time

APPLICATION = 'spacenear.us'
VERSION = '1.0'
USER = 'VA3NAT'

class APRSClient:
    def __init__(self, packetHandler, host, adjunct='', port=10152):
        self.aprsHost = host
        self.aprsPort = port
        self.aprsAdjunct = adjunct
        self.packetHandler = packetHandler
        self.timeout = 10
        self.pollInterval = 0.1
        self.socketBuffer = ''
    
    def start(self):
        self.__connect()
        self.run()
    
    def run(self):
        while True:
            try:
                readReady, writeReady, inError = select.select([self.socket], [], [], self.timeout)
                if self.socket in readReady:
                    try:
                        self.__handleData()
                    except:
                        raise
                        print 'Error handling data'
                time.sleep(self.pollInterval)
            except (KeyboardInterrupt, SystemExit):
                print "Exit requested"
                return
    
    def __connect(self):
        print 'Connecting to %s:%d' % (self.aprsHost, self.aprsPort)
        self.socket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)
        self.socket.connect((self.aprsHost, self.aprsPort))
        if not self.__aprsLogin():
            raise Error
        return True
    
    def __aprsLogin(self):
        h = self.socket.recv(200)
        print 'Received: %s' % h.strip()
        if not h.startswith('# javAPRSSrvr 3'):
            print 'Not a known APRSIS Server'
            return False
        connStr = 'user %s pass -1 vers %s %s %s\r\n' % (USER, APPLICATION, VERSION, self.aprsAdjunct)
        self.socket.send(connStr)
        print 'Sent: %s' % connStr.strip()
        d = self.socket.recv(200)
        print 'Received: %s' % d.strip()
        if d.startswith('# logresp %s unverified' % USER):
            print 'APRS-IS Login Successful'
            return True
        else:
            print 'APRS-IS Login Failed'
            return False
    
    def __handleData(self):
        try:
            data = self.socket.recv(200)
        except:
            print 'Connection Error'
            self.__connect()
            return False
        self.socketBuffer += data
        if self.socketBuffer.endswith('\r\n'):
            lines = self.socketBuffer.strip().split('\r\n')
            self.socketBuffer = ''
        else:
            lines = self.socketBuffer.split('\r\n')
            self.socketBuffer = lines.pop(-1)
            
        for line in lines:
            self.packetHandler(line.strip())
            

class APRSTestHandler:
    def __init__(self):
        pass
        
    def packetHandler(self, packet):
        print 'APRS Packet: %s' % packet
        
def run():
    handler = APRSTestHandler()
    client = APRSClient(handler.packetHandler, 'aprsnz.aprs2.net', 'filter b/KE7MK-*')
    client.start()

if __name__=='__main__':
    run()