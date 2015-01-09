import socket
import time
import struct
from hashlib import sha256
from ec import ec_sig
from utils import *

# ins are [prev_hash, addr]
# outs are [pub, value]
def mk_tx(ins, outs, mining_fee, change_pub = None):
    tx = {}

    tx['version'] = version = int_to_padded_hex(1, 4)
    tx['input_count'] = input_count = int_to_padded_hex(len(ins), 1)
    tx['ins'] = []

    input_total = 0
    for i in ins:
        prev_hash, from_addr = i
        txjson = get_tx_json(prev_hash)
        prev_out_i = get_prev_output_index(txjson, from_addr)

        script_sig = get_scriptPubKey(txjson, prev_out_i) # this is convention ... (replaced later by real script)
        prev_out_i = int_to_padded_hex(prev_out_i, 4)
        script_sig_length = int_to_padded_hex(len(script_sig)/2, 1)
        sequence = "ffffffff" # fixed, everywhere
        tx['ins'].append([switchEndian(prev_hash), prev_out_i, script_sig_length, script_sig, sequence, from_addr])

        input_total += get_input_sum(txjson, int(switchEndian(prev_out_i)))

    tx['output_count'] = output_count= int_to_padded_hex(len(outs), 1)

    tx['outs'] = []
    value_total = 0
    for i in outs:
        to_pub, value = i
        out1 = int_to_padded_hex(value, 8)
        script_pubkey1 = '76'+'a9'+int_to_padded_hex(len(to_pub)/2, 1)+to_pub +'88'+'aC' # op codes: 76 = OP_DUP, A9 = OP_HASH160, 88 = OP_EQUALVERIFY, AC = OP_CHECKSIG 
        script_pubkey_length1 = int_to_padded_hex(len(script_pubkey1)/2, 1)
        tx['outs'].append([out1, script_pubkey_length1, script_pubkey1])
        value_total += value

    if change_pub:
        to_pub = change_pub
        value = input_total - value_total - mining_fee
        out1 = int_to_padded_hex(value, 8)
        script_pubkey1 = '76'+'a9'+int_to_padded_hex(len(to_pub)/2, 1)+to_pub +'88'+'aC' # op codes: 76 = OP_DUP, A9 = OP_HASH160, 88 = OP_EQUALVERIFY, AC = OP_CHECKSIG 
        script_pubkey_length1 = int_to_padded_hex(len(script_pubkey1)/2, 1)
        tx['outs'].append([out1, script_pubkey_length1, script_pubkey1])
        tx['output_count'] = int_to_padded_hex(len(outs)+1, 1)

    tx['block_lock'] = block_lock_time = int_to_padded_hex(0, 4)
    tx['hash_type'] = hash_type = int_to_padded_hex(1, 4)

    #tx['hash'] = tx_hash = switchEndian(TX_HASH)

    return tx


def pack_tx(tx, presig=1):
    s = tx['version'] + tx['input_count']
    for inp in tx['ins']:
        s += ''.join(inp[:-1])

    s += tx['output_count']
    for outp in tx['outs']:
        s += ''.join(outp)
    s += tx['block_lock']
    
    if presig:
        s += tx['hash_type']

    txhash = sha256(sha256(s.decode('hex')).digest()).digest().encode('hex')
    return txhash,s


def sign_tx(txhash, tx, privs):
    privs = [p.decode('hex') for p in privs]
    addrs = map(priv2addr, privs)
    for i in xrange(len(tx['ins'])):
        inp = tx['ins'][i]
        addr = inp[-1]
        i = addrs.index(addr)
        priv = privs[i]
        pubkey = priv2pub(priv)

        r,s = ec_sig(priv, txhash.decode('hex'))
        sigDER = der_sig(r,s)+'01' # sig suffixed with HASHCODE (01 = HASH_ALL)

        scriptsig = int_to_padded_hex(len(sigDER)/2, 1) + sigDER + int_to_padded_hex(len(pubkey)/2, 1) + pubkey
        scriptsig_length = int_to_padded_hex(len(scriptsig)/2, 1)
        inp[2] = scriptsig_length
        inp[3] = scriptsig
        tx['ins'][i] = inp
    
    txhash, s = pack_tx(tx, presig=0)
    return s


