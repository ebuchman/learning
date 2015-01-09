# this is simply the barebones needed for a bitcoin tx, with awful programming practices, but everything explicitly laid out in capital letters.

import urllib2
import json
import os
from hashlib import sha256
from ec import *

ripemd160 = hashlib.new('ripemd160')

base_url = "http://blockchain.info"

# useful functions

# get tx info from blockchain.info
def get_tx_json(txhash):
    url = os.path.join(base_url, 'rawtx', txhash)
    req = urllib2.Request(url)
    return json.load(urllib2.urlopen(req))

def get_prev_output_index(txjson, from_addr):
    outs = txjson['out']
    #find output index
    return [outs[i]['n'] for i in xrange(len(outs)) if outs[i]['addr'] == from_addr][0]

def get_scriptPubKey(txjson, n):
    if not str(type(n)) in ('int'):
        n = int(n)
    return txjson['out'][n]['script']

# defaults to little endian
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

# swap byte order (txhash should be little endian)
def switchEndian(hexstring):
    return hexstring.decode('hex')[::-1].encode('hex')

def decode58(string):
    codec = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    result = 0
    while len(string) > 0:
        result *= 58
        result += codec.find(string[0])
        string = string[1:]
    return result


# tx setup
FROM_ADDR = ""
FROM_PRIV = ""
TX_HASH = ""

TO_PUB = decode58('')
TO_PUB = "%02x"%TO_PUB
TO_PUB = TO_PUB[:-8] # dont include checksum

txjson = get_tx_json(TX_HASH)

# tx contents
VERSION = int_to_padded_hex(1, 4) # n, nbytes

INPUT_COUNT = int_to_padded_hex(1, 1)
PREV_OUTPUT_INDEX = get_prev_output_index(txjson, FROM_ADDR)
SCRIPT_SIG = get_scriptPubKey(txjson, PREV_OUTPUT_INDEX) # this is convention ... (replaced later by real script)
PREV_OUTPUT_INDEX = int_to_padded_hex(PREV_OUTPUT_INDEX, 4)
SCRIPT_SIG_LENGTH = int_to_padded_hex(len(SCRIPT_SIG)/2, 1)
SEQUENCE = "ffffffff" # fixed, everywhere

OUTPUT_COUNT = int_to_padded_hex(1, 1)
OUTPUT_VALUE = int_to_padded_hex(321, 8)
SCRIPT_PUBKEY = '76'+'a9'+int_to_padded_hex(len(TO_PUB)/2, 1)+TO_PUB +'88'+'aC' # op codes: 76 = OP_DUP, A9 = OP_HASH160, 88 = OP_EQUALVERIFY, AC = OP_CHECKSIG 
SCRIPT_PUBKEY_LENGTH = int_to_padded_hex(len(SCRIPT_PUBKEY)/2, 1)

BLOCK_LOCK_TIME = int_to_padded_hex(0, 4)
HASH_CODE_TYPE = int_to_padded_hex(1, 4)

TX_HASH = switchEndian(TX_HASH)

# tx before signing:
s = VERSION+INPUT_COUNT+TX_HASH+PREV_OUTPUT_INDEX+SCRIPT_SIG_LENGTH+SCRIPT_SIG+SEQUENCE+OUTPUT_COUNT+OUTPUT_VALUE+SCRIPT_PUBKEY_LENGTH+SCRIPT_PUBKEY+BLOCK_LOCK_TIME+HASH_CODE_TYPE

txhash = sha256(sha256(s.decode('hex')).digest()).digest().encode('hex')

# signing
priv = FROM_PRIV
pub = ec_priv2pub(priv.decode('hex'))
pubkey = '04' + '%02x%02x'%(pub[0], pub[1]) # pubkey prefaced with '04' byte

r,s = ec_sig(priv.decode('hex'), txhash.decode('hex'))
sigDER = der_sig(r,s)+'01' # sig suffixed with HASHCODE (01 = HASH_ALL)

scriptSIG = int_to_padded_hex(len(sigDER)/2, 1) + sigDER + int_to_padded_hex(len(pubkey)/2, 1) + pubkey

SCRIPT_SIG_LENGTH = int_to_padded_hex(len(scriptSIG)/2, 1)
SCRIPT_SIG = scriptSIG

# so final SCRIPT_SIG contains the script (op codes, including address we are trying to spend from) and the pubkey, which must be matched to the address we are trying to spend from, and sig verified

print '####'
# final tx
s = VERSION+INPUT_COUNT+TX_HASH+PREV_OUTPUT_INDEX+SCRIPT_SIG_LENGTH+SCRIPT_SIG+SEQUENCE+OUTPUT_COUNT+OUTPUT_VALUE+SCRIPT_PUBKEY_LENGTH+SCRIPT_PUBKEY+BLOCK_LOCK_TIME
print s
print '######'
