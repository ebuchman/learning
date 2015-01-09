import urllib2
import json
import os
import time
import hashlib
sha256 = hashlib.sha256
from ec import ec_priv2pub


base_url = "http://blockchain.info"

# useful functions

def rip160(tohash):
    ripemd160 = hashlib.new('ripemd160')
    ripemd160.update(tohash)
    return ripemd160.digest()


# get tx info from blockchain.info
def get_tx_json(txhash):
    url = os.path.join(base_url, 'rawtx', txhash)
    req = urllib2.Request(url)
    return json.load(urllib2.urlopen(req))

def get_prev_output_index(txjson, from_addr):
    outs = txjson['out']
    #find output index
    inds =  [outs[i]['n'] for i in xrange(len(outs)) if outs[i]['addr'] == from_addr][0]
    return inds

def get_input_sum(txjson, out_i):
    outs = txjson['out']
    return outs[int(out_i)]['value']

def get_scriptPubKey(txjson, n):
    if not str(type(n)) in ('int'):
        n = int(n)
    return txjson['out'][n]['script']

def int_to_padded_hex(n, nbytes, endian=1):
    hexd = "%02x"%n
    padded = "0"*(nbytes*2 - len(hexd)) + hexd
    return switchEndian(padded) if endian else padded

# DER encoding for signature
def der_sig(r, s):
    renc, senc = "%02x"%r, "%02x"%s
    if r >= 2**255: renc = '00'+renc
    if s >= 2**255: senc = '00'+senc
    renc = '02'+'%02x'%(len(renc)/2)+renc
    senc = '02'+'%02x'%(len(senc)/2)+senc
    return '30'+'%02x'%(len(renc+senc)/2)+renc+senc

# swap byte order (txhash should be little endian...)
def switchEndian(hexstring, be = 0):
    if be == 0:
        return hexstring.decode('hex')[::-1].encode('hex')
    else:
        return hexstring[::-1]

def get_codec(base):
    if base == 58:
        return '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    elif base == 256:
        return ''.join([chr(i) for i in xrange(256)])
    elif base == 2:
        return '01'
    elif base == 16:
        return '0123456789abcdef'

def decode(string, base):
    codec = get_codec(base)
    result = 0

    while len(string)>0:
        result *= base
        result += codec.find(string[0])
        string = string[1:]
    return result

def encode(n, base):
    codec = get_codec(base)
    result = ''
    while n > 0:
        m = n % base
        n = n / base
        result = codec[m]+result
    return result

def addr2pub(addr):
    deco = decode(addr, 58)
    hexd = int2hex(deco)
    return hexd[:-8]

def int2hex(integer):
    h = '%02x'%integer
    if len(h)%2 != 0:
        h = '0'+h
    return h

def be2int(be):
    if len(be) == 0: return ''
    h = be.encode('hex')
    return int(h, 16)

def int2be(integer):
    h = int2hex(integer)
    return h.decode('hex')

def priv2pub(priv):
    pub = ec_priv2pub(priv)
    pubkey = '04' + int2hex(pub[0]) + int2hex(pub[1]) # pubkey prefaced with '04' byte
    return pubkey

def priv2addr(priv):
    pubkey = priv2pub(priv)
    pub160 = rip160(sha256(pubkey.decode('hex')).digest()).encode('hex')
    pubV = '00' + pub160
    check = sha256(sha256(pubV.decode('hex')).digest()).digest()[:4].encode('hex')
    pubch = pubV+check
    addr = encode(decode(pubch.decode('hex'), 256), 58)
    return '1'+addr
    

