import hashlib, hmac

PRIME_ORDER = 2**256-2**32-2**9-2**8-2**7-2**6-2**4-1
N = 115792089237316195423570985008687907852837564279074904382605163141518161494337
A_COEF = 0
B_COEF = 7
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
G = (Gx,Gy)

def euclid(a, b):
    a,b = (b,a) if b > a else (a,b)
    r = a % b
    if r == 0: return b
    return euclid(b, r)

def extended_euclid(a, b, s0=1, s1=0, t0=0, t1=1):
    a,b = (b,a) if b > a else (a,b)
    r = 1
    while r > 0:
        q = a / b
        r = a - b*q
        s = s0 - q*s1
        t = t0 - q*t1
        a, b, s0, s1, t0, t1 = b, r, s1, s, t1, t
    return b, s0, t0

def modulo_inv(a, p):
    a = a%p
    gcd, s, t = extended_euclid(a, p)
    return t

def isinf(x, y):
    return x==0 and y ==0

def ec_add(p, q, P = PRIME_ORDER):
    px, py = p
    qx, qy = q

    if isinf(*p): return q
    if isinf(*q): return p

    if px == qx:
        if py != qy:
            return (0,0)
        else:
            return ec_double(p, P)
    
    m = ((py - qy) * modulo_inv(px - qx, P)) % P
    rx = (m**2 - px - qx) % P
    ry = m*(rx - px) + py
    ry = (-ry) % P
    return (rx, ry)

def ec_double(q, P = PRIME_ORDER, a = A_COEF):
    qx, qy = q

    if isinf(*q): return (0,0)
    if qy == 0: return (0,0)

    m = ((3*qx**2 + a)*modulo_inv(2*qy, P)) % P
    rx = (m**2 - 2*qx) % P
    ry = m*(rx - qx) + qy
    ry = (-ry) % P

    return (rx, ry)

def ec_multiply(n, q, P=PRIME_ORDER):
    if isinf(*q) or n == 0: return (0,0)
    if n == 1: return q
    if n < 0 or n > N: return ec_multiply(n%N, q)

    bin_n = bin(n)[2:]
    Q = (0,0)
    m = len(bin_n)
    for i in xrange(m):
        Q = ec_double(Q, P)
        if bin_n[i] == '1': 
            Q = ec_add(q, Q, P)
    return Q

#(deterministic pseudo random k: https://tools.ietf.org/html/rfc6979#section-3.2)
def deterministic_k(msghash, priv):
    V = '\x01'*32
    K = '\x00'*32
    K = hmac.new(K, V+'\x00'+priv+msghash, hashlib.sha256).digest()
    V = hmac.new(K, V, hashlib.sha256).digest()
    K = hmac.new(K, V+'\x01'+priv+msghash, hashlib.sha256).digest()
    V = hmac.new(K, V, hashlib.sha256).digest()
    K = hmac.new(K, V, hashlib.sha256).digest()
    return int(K.encode('hex'), 16)

def ec_sig(priv, msghash, G=G):
    k = deterministic_k(msghash, priv) #2**13 + 2**31 - 1 (there's a tx that uses this k. can you find it and steal my bitcoin? :P GL!)
    z = int(msghash.encode('hex'), 16)
    priv = int(priv.encode('hex'), 16)
    x1, y1 = ec_multiply(k, G)
    r = x1 % N
    s = (modulo_inv(k, N)*(z + r*priv)) % N
    return r, s

def ec_verify_sig(pub, sig, msghash, A=A_COEF, B=B_COEF, G=G, P=PRIME_ORDER):
    assert(not isinf(*pub))
    pubx, puby = pub
    print pubx, puby
    assert(puby**2 % P == (pubx**3 + A*pubx + B) % P)
    assert(isinf(*ec_multiply(N, pub)))
    r, s = sig
    assert(1 < r < N-1)
    assert(1 < s < N-1)
    z = int(msghash.encode('hex'), 16)
    s_inv = modulo_inv(s, N)
    u1 = z*s_inv % N
    u1G = ec_multiply(u1, G)
    u2 = r*s_inv % N
    u2Q = ec_multiply(u2, pub)
    x, y = ec_add(u1G, u2Q)
    assert(r == x)
    print 'sig verified'

def ec_priv2pub(priv, G=G):
    pr = int(priv.encode('hex'), 16)
    pub = ec_multiply(pr, G)
    return pub



if __name__ == '__main__':
    '''
    c = ec_double(G)
    print '###############################'
    print 'double ', c
    print 'add ', ec_add(c, G)
    print 'multiply ', ec_multiply(102, G)
    print '###############################'
    '''
    from  sha3 import sha3_256 as sha3
    h = hashlib.sha256('a message to sign').digest()
    pr = hashlib.sha256('private key').digest()

    h = sha3('a message to sign').digest()
    pr = sha3('private key').digest()
    pub = ec_priv2pub(pr)

    print 'priv:'
    print pr.encode('hex')
    print int(pr.encode('hex'), 16)

    print 'hash:'
    print h.encode('hex')
    print int(h.encode('hex'), 16)

    print 'pub:'
    print pub

    r, s = ec_sig(pr, h)
    print 'r'
    print r
    print 's'
    print s

    ec_verify_sig(pub, (r, s), h)
    quit()

    print h
    print h.encode('hex')
    print len


