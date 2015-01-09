import socket
import select
import sys
import os

class P2PClient():
    def __init__(self, port=5410, peers_file="peers.txt"):
        self.port = port 
        self.peers_file = peers_file
        self.listen_backlog = 10

        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.setblocking(0)
        self.listener.bind(('', port))

        self.listener.listen(self.listen_backlog)

        self.shutdown = False

        self.read_list = [self.listener, sys.stdin]
        self.write_list = []
        self.peer_list = []

        self.n_connected_peers = 0
        self.peers = {} # dictionary of ip:connected
        self.load_peers()

    def load_peers(self):
        if not os.path.isfile(self.peers_file):
            open(self.peers_file, "a").close()

        f = open(self.peers_file, "r")
        for line in f:
            line = line[:-1]
            self.peers[line] = 0
        f.close()

    def connect_peers(self):
        for peer in self.peers:
            con = self.peers[peer]
            if not con:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.settimeout(3)
                try:
                    s.connect((peer, self.port))
                    print 'connected to peer ', peer
                    self.n_connected_peers += 1
                    self.peers[peer] = 1
                    self.read_list.append(s)
                    self.peer_list.append(s)
                    self.write_list.append(s)
                except: 
                    print 'could not connect to ', peer
                    pass
        print self.n_connected_peers, " connected peers!"

    def handle_new_connection(self, r):
        new_fd, new_addr = r.accept()
        ip, port = new_addr
        new_fd.setblocking(0)
        self.read_list.append(new_fd)
        self.peer_list.append(new_fd)
        self.write_list.append(new_fd)
        if not ip in self.peers or not self.peers[ip] == 1:
            self.peers[ip] = 1
            f = open(self.peers_file, "a")
            f.write(ip+'\n')
            f.close()
        print 'new connection to', new_addr
        self.n_connected_peers += 1


    def handle_send(self, data, w_list):
        for w in w_list:
            e = w.send(data)

    def handle_recv(self, r):
        try:
            ip, port = r.getpeername()
            data = r.recv(100)
            if not data:
                self.handle_con_closed(r)
                return ['CLOSED']
            return [1, ip, data]
        except: 
            print 'could not recv'
        return [0]

    def handle_std_in(self, r, w_list):
        data = sys.stdin.readline()
        data = data[:-1] #remove new line character

        if data == "\q": 
            self.handle_shutdown()
        elif data == "\connect_peers":
            self.connect_peers()
        else:
            self.handle_send(data, w_list)

    def main_loop(self):
        while not self.shutdown:
            r_list, w_list, _ = select.select(self.read_list, self.write_list, [], 2.5)

            for r in r_list:
                if (r == self.listener):  
                    try:
                        self.handle_new_connection(r)
                    except: 
                        print 'could not connect'
                elif r == sys.stdin:
                    self.handle_std_in(r, w_list)
                else: 
                    status = self.handle_recv(r)
                    mode, ip, data = status
                    if mode == 1:
                        print '%s : %s'%(ip, data)

    def handle_con_closed(self, r):
        ip, port = r.getpeername()
        self.peers[ip] = 0
        self.read_list.remove(r)
        self.peer_list.remove(r)
        self.write_list.remove(r)
        r.close()
        print "connection to peer", ip,",", port, " closed"
        self.n_connected_peers -= 1


    def handle_shutdown(self):
        for r in self.read_list:
            r.close()
        for w in self.write_list:
            try:
                w.close()
            except: pass
        self.shutdown = True


if __name__ == '__main__':
    l = len(sys.argv)
    if l == 1:
       port = 5490
    elif l == 2: 
        port = int(sys.argv[1])
    else:
        print "too many arguments"
        quit()

    print 'Welcome to chatP2P'
    print 'Type \q to exit'
    print 'Type \connect_peers to try reconnecting to peers'

    client = P2PClient(port)
    client.connect_peers()
    client.main_loop()
