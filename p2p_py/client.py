import sys
from PyQt4 import QtGui, QtCore
from p2p import *
import threading, Queue
from time import sleep

exitFlag = 0
threadLock = threading.Lock()

class p2pThread(threading.Thread):
    def __init__(self, threadID, name, window, queue, run_func, args=None):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.window = window
        self.exitFlag = 0
        self.run_func = run_func
        self.run_func_args = args
        self.q = queue

    def run(self):
        self.run_func(self)


def listen_run_func(threadObj):
        while not threadObj.exitFlag:
            try:
                client.handle_new_connection(client.listener)
                threadObj.window.updatePeers()
            except:
                sleep(2.5)


def recv_run_func(threadObj):
    while not threadObj.exitFlag:
        r_list, _, _ = select.select(client.peer_list, [], [], 2.5)

        for r in r_list:
            status = client.handle_recv(r)
            if len(status) == 1:
                if status[0] == 0: print 'error recving'
                else: threadObj.window.updatePeers()
            else:
                #threadObj.q.put(['recv', status[1], status[2]])
                threadObj.window.recvMsg(status)


def main():
    app = QtGui.QApplication(sys.argv)
    ex = MainWindow()

    threads = []

    msgQueue = Queue.Queue(10)

    listen_thread = p2pThread(1, 'listen', ex.form_widget, msgQueue, listen_run_func, [client.listener])
    recv_thread = p2pThread(2, 'recv', ex.form_widget, msgQueue, recv_run_func, []) 

    threads.append(listen_thread)
    threads.append(recv_thread)

    listen_thread.start()
    recv_thread.start()

    sys.exit(shutdown_f(app, threads))

def shutdown_f(app, threads):
    app.exec_()
    for t in threads:
        t.exitFlag = 1
        t.join()

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.form_widget = FormWidget(self)
        self.setCentralWidget(self.form_widget)
        self.initUI()

    def initUI(self):
        exitAction = QtGui.QAction(QtGui.QIcon('exit24.png'), 'Exit',self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        QtGui.QToolTip.setFont(QtGui.QFont('SansSerif',12))

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

        self.statusBar().showMessage('Welcome to p2p-chat!')

        self.resize(1200, 300) 
        self.move(100,200)
        self.setWindowTitle('p2p-chat')
        self.show()


class FormWidget(QtGui.QWidget):
    tags = False
    def __init__(self,parent):
        super(FormWidget, self).__init__(parent)
        self.initUI()
    def initUI(self):
        send_msg_tag = QtGui.QLabel('Enter a message:')
        self.send_msg = QtGui.QTextEdit(self)
        self.receive_msg = QtGui.QListWidget(self)
        sendBtn = QtGui.QPushButton('Send Message', self)

        self.peerlist = QtGui.QListWidget(self)

        #   self.currency = QtGui.QLCDNumber(self)

        grid = QtGui.QGridLayout()
        grid.addWidget(send_msg_tag, 1, 0)
        grid.addWidget(self.send_msg, 2, 0, 3, 5)
        grid.addWidget(sendBtn,5,0)
        grid.addWidget(self.receive_msg, 0, 5, 5, 5)
        grid.addWidget(self.peerlist, 0, 0, 1, 2)

        self.updatePeers()
        self.peerlist.setCurrentRow(0)			

        openFile = QtGui.QAction(QtGui.QIcon('open.png'), 'File', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Choose a file to publish')
        openFile.triggered.connect(self.showDialog)
		
        self.peerlist.currentItemChanged.connect(self.showConvo)

        sendBtn.clicked.connect(self.sendMsg)          	

        self.setLayout(grid)

        #self.tagSinal.connect(parent.publish)

    def updatePeers(self):
        self.peerlist.clear()
        for i in client.peers:
            if client.peers[i] == 1:
                self.peerlist.addItem(i)

    def recvMsg(self, status_packet):
        mode, ip, data = status_packet
        self.receive_msg.addItem('%s : %s'%(ip,data))

    def sendMsg(self):
        _, w_list, _ = select.select([], client.peer_list, [], 0.1)
        data = self.send_msg.toPlainText()
        self.send_msg.clear()
        client.handle_send(data, w_list) 
        self.receive_msg.addItem('%s : %s'%('me', data))

    def showConvo(self):
        pass

    def showDialog(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file')
        self.sender().parent().parent().statusBar().showMessage('Staging file: ' + fname)
    def pubButton(self):
        sender = self.sender()
        sender.parent().parent().statusBar().showMessage(sender.text() + ' process pending')



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

    main()
