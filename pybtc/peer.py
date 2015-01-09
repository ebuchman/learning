import socket
import time
import struct
from hashlib import sha256
from utils import *

MAGIC_VALUE = 'd9b4bef9'

def crop_msg(msg, n):
    return msg[:n], msg[n:]

'''
var int
------------------------------------------------------
value           size        format
------------------------------------------------------
<0xfd           1           uint8
<=0xffff        3           0xfd followed by uint16
<=0xffffffff    5           0xfe followed by uint32
-               9           0xff followed by uint64
-------------------------------------------------------
var str
-------------------------------------------------------
size        name        type
?           length      var_int
?           string      char[]

'''
def crop_msg_var_int(msg):
    first, msg = crop_msg(msg, 1)
    first = first.encode('hex')
    if first == 'ff':
        return crop_msg(msg,8)
    elif first == 'fe':
        return crop_msg(msg,4)
    elif first == 'fd':
        return crop_msg(msg,2)
    else:
        return first.decode('hex'), msg

def crop_msg_var_str(msg):
    length, msg = crop_msg_var_int(msg)
    return crop_msg(msg, be2int(length))

'''
general message structure
-------------------------------------
size        name            type
-------------------------------------
4           magic           uint32
12          command         char[12]
4           length          uint32
4           checksum        uint32
?           payload         uchar[]

'''

def decode_msg(msg):
    magic, msg = crop_msg(msg, 4)
    command, msg = crop_msg(msg, 12)
    length, msg = crop_msg(msg, 4)
    checksum, msg = crop_msg(msg, 4)
    payload = msg

    print 'general msg decode:'
    print 'magic: \t', magic.encode('hex')
    print 'command: \t',command
    print 'payload length: \t', be2int(switchEndian(length, be=1))
    print 'checksum: \t', checksum.encode('hex')
    print 'payload: \t', payload.encode('hex')

    if 'version' in command:
        decode_version(payload)
    elif 'reject' in command:
        decode_reject(payload)

    print ''
    
def assemble_msg(command, payload, magic=MAGIC_VALUE):
    magic = switchEndian(magic).decode('hex')
    #command = switchEndian(('\x00'*(12 - len(command)) + command).encode('hex')).decode('hex')
    command = command + '\x00'*(12 - len(command))
    l = int_to_padded_hex(len(payload), 4).decode('hex')
    checksum = sha256(sha256(payload).digest()).digest()[:4]
    ret =  magic + command + l + checksum + payload
    return ret


'''
inet structure
------------------------------------
size        name            type
-------------------------------------
4           time            int32    // exclude in version msg
8           services        uint64
16          ipv6/4          char[16]
2           port            uint16
'''

def net_addr(addr, port, vers=0):
    if vers == 0:
        timestamp = int_to_padded_hex(time.time(), 4).decode('hex')
    else:
        timestamp = ''
    services = int_to_padded_hex(1, 8).decode('hex')
    ip = ('00'*10 + 'ff'*2).decode('hex') + ''.join(map(chr, map(int, addr.split('.'))))
    port = int_to_padded_hex(port, 2, endian=0).decode('hex')
    return timestamp+services+ip+port
    
def decode_net_addr(payload, vers=0):
    if vers == 0:
        timestamp, payload = crop_msg(payload, 4)
    services, payload = crop_msg(payload, 8)
    ip, payload = crop_msg(payload, 16)
    port = payload

    ip = [int(ip[i].encode('hex'), 16) for i in xrange(-4, 0)]
    return be2int(services[::-1]), ip, be2int(port)

'''
version message
------------------------------------
size        name            type
-------------------------------------
4           version         int32
8           services        uint64
8           timestamp       int64
26          to_addr         net_addr
26          from_addr       net_addr
8           nonce           uint64
?           user_agent      var_str
4           start_height    int32
1           relay           bool
'''

def decode_version(payload):
    version, payload = crop_msg(payload, 4)
    services, payload = crop_msg(payload, 8)
    timestamp, payload = crop_msg(payload, 8)
    to_addr, payload = crop_msg(payload, 26)
    from_addr, payload = crop_msg(payload, 26)
    nonce, payload = crop_msg(payload, 8)
    user_agent, payload = crop_msg_var_str(payload)
    start_height, payload = crop_msg(payload, 4)
    relay = payload

    print 'version decode'
    print 'version: \t', be2int(switchEndian(version, be=1))
    print 'services: \t', be2int(switchEndian(services, be=1))
    print 'timestamp: \t', be2int(switchEndian(timestamp, be=1))
    print 'to addr: \t', decode_net_addr(to_addr)
    print 'from addr: \t', decode_net_addr(from_addr)
    print 'nonce: \t', be2int(nonce[::-1])
    print 'user agent: \t', user_agent
    print 'start height: \t', start_height[::-1].encode('hex')
    print 'relay: \t', relay.encode('hex')
    print ''

def assemble_version(rec_ip, rec_port):
    version = int_to_padded_hex(70002, 4).decode('hex')
    services = int_to_padded_hex(1, 8).decode('hex')
    timestamp = int_to_padded_hex(int(time.time()), 8).decode('hex')
    addr_me = net_addr('108.168.13.13', 8333, vers=1)
    addr_you = net_addr(rec_ip, rec_port, vers=1)
    nonce = int_to_padded_hex(2**31 + 1, 8).decode('hex')
    sub_version_num = '\x00'# utils.varstr('')
    start_height = int_to_padded_hex(0, 4).decode('hex')
    relay = '\x00'

    payload = version + services + timestamp + addr_me + addr_you + nonce + sub_version_num + start_height + relay

    return assemble_msg('version', payload)

def assemble_version2(rec_ip, rec_port):
    version = 60002
    services = 1
    timestamp = int(time.time())
    addr_me = net_addr("108.168.13.13", 8333, vers=1)
    addr_you = net_addr(rec_ip,rec_port, vers=1)
    nonce = 2**31 + 1 #random.getrandbits(64)
    sub_version_num = '' #utils.varstr('')
    start_height = 0
     
    payload = struct.pack('<LQQ26s26sQsL', version, services, timestamp, addr_me,
    addr_you, nonce, sub_version_num, start_height) 

    print payload.encode('hex')

'''
reject message
-----------------------------------
size        name            type
------------------------------------
?           message         var_str
1           ccode           char
?           reason          var_str
'''
def decode_reject(payload):
    msg, payload = crop_msg_var_str(payload)
    ccode, payload = crop_msg(payload, 1)
    reason =  payload 

    print 'reject message'
    print 'msg rejected: \t', msg
    print 'ccode: \t', ccode.encode('hex')
    print 'reason: \t', reason.encode('hex'), reason
    print ''

'''
peer connectivity
'''

def connect_peer(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.connect((ip, port))
        print 'connected to peer %s:%d\n'%(ip, port)
    except:
        print 'could not connect to %s:%d\n'%(ip, port)
        sock = None
    return sock

def send(sock, msg):
    sent = sock.send(msg)
    print 'sent %d bytes\n'%sent

def recv(sock):
    recv = sock.recv(1000)
    print 'received %d bytes: %s \n'%(len(recv), recv.encode('hex'))
    decode_msg(recv)




