import json
from utils import *
from tx import *
from peer import *

# some peers
peer = '198.245.63.145'
#peer = '198.245.61.126'
#peer = '190.93.243.195'
#port = 3333
#peer = '24.57.173.241'
port = 8333
#peer = '67.186.224.85'
#peer = '88.198.58.172'
#peer = '198.41.188.247'

try:
    FROM_PRIV = json.load(open('.wallet'))
except:
    print 'no wallet file.  save a private key (in json, hex) in .wallet'
    quit()

FROM_PRIV = FROM_PRIV[-1]

# tx setup
FROM_ADDR = priv2addr(FROM_PRIV.decode('hex'))
MY_PUB = addr2pub(FROM_ADDR)
TX_HASH = "" # fill this in

TO_PUB = addr2pub('') #fill this in

VALUE = 43210
MINING_FEE = 10000

ins = [[TX_HASH, FROM_ADDR]]
outs = [[TO_PUB, VALUE]]
privs = [FROM_PRIV]
tx = mk_tx(ins, outs, MINING_FEE, change_pub = MY_PUB)
txhash, s = pack_tx(tx)
s = sign_tx(txhash, tx, privs)
print 'raw tx! -----------------------------------------'
print s
print '-------------------------------------------------\n'

vers = assemble_version(peer, port)
print 'version msg %s \n'%vers.encode('hex')

sock = connect_peer(peer, port)
send(sock, vers)

recv(sock) # version
recv(sock) # verack

msg = assemble_msg('tx', s.decode('hex'))
send(sock, msg)

recv(sock) # rejection?

