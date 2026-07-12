import zlib

# Full keygen recovered from solution writeup by simonzack
# Algorithm: Tower of Hanoi on fractal triangle representation

def coord2v(c):
    '''get vertices at triangle coordinates'''
    currV = [0, 1, 2]
    for i in range(len(c) - 1):
        _c = c[i]
        if _c == 0:
            currV = [currV[0], currV[2], currV[1]]
        elif _c == 1:
            currV = [currV[2], currV[1], currV[0]]
        elif _c == 2:
            currV = [currV[1], currV[0], currV[2]]
    return currV

def coord2pos(c):
    '''convert triangle coordinates to position, e.g. 0,1,1 --> 220'''
    res = []
    currV = [0, 1, 2]
    for _c in c:
        res.append(currV[_c])
        if _c == 0:
            currV = [currV[0], currV[2], currV[1]]
        elif _c == 1:
            currV = [currV[2], currV[1], currV[0]]
        elif _c == 2:
            currV = [currV[1], currV[0], currV[2]]
    return res[::-1]

def pos2coord(p):
    '''convert position to triangle coordinates, e.g. 220 --> 0,1,1'''
    res = []
    currV = [0, 1, 2]
    for _p in p[::-1]:
        _c = currV.index(_p)
        res.append(_c)
        if _c == 0:
            currV = [currV[0], currV[2], currV[1]]
        elif _c == 1:
            currV = [currV[2], currV[1], currV[0]]
        elif _c == 2:
            currV = [currV[1], currV[0], currV[2]]
    return res

def findPath(p, storeChange=False):
    '''finds the shortest path from p to the bottom-left vertex'''
    c = pos2coord(p)
    res = []
    currV = coord2v(c)
    while True:
        if not storeChange:
            res.append(coord2pos(c))
        i = len(c) - 1
        o_c = None
        while True:
            if c[i] == 0:
                o_c = 0
                c[i] = 1
                break
            elif c[i] == 2:
                o_c = 2
                c[i] = 1
                break
            elif c[i] == 1:
                i -= 1
                if i == -1:
                    break
                _c = c[i]
                if _c == 0:
                    currV = [currV[0], currV[2], currV[1]]
                elif _c == 1:
                    currV = [currV[2], currV[1], currV[0]]
                elif _c == 2:
                    currV = [currV[1], currV[0], currV[2]]
        if i == -1:
            break
        if storeChange:
            if o_c == 0:
                res.append((currV[0], currV[1]))
            elif o_c == 2:
                res.append((currV[2], currV[1]))
        if i + 1 < len(c):
            currV = [currV[2], currV[1], currV[0]]
            for j in range(i + 1, len(c) - 1):
                if o_c == 0:
                    currV = [currV[0], currV[2], currV[1]]
                elif o_c == 2:
                    currV = [currV[1], currV[0], currV[2]]
            for j in range(i + 1, len(c)):
                if o_c == 0:
                    c[j] = 0
                elif o_c == 2:
                    c[j] = 2
    return res

def c_j_rand(n):
    return ((n * 0x343FD) + 0x269EC3) & 0xFFFFFFFF

def hashName(name):
    '''Hash the name string (bytes) using djb2-like algorithm, then post-process'''
    if isinstance(name, str):
        name = name.encode()
    res = 0x1505
    for c in name:
        res = (res * 0x1003F) & 0xFFFFFFFF
        res = (res + c) & 0xFFFFFFFF
    h = 0xFFFFFFFF
    while h > 0x4546B3DA:
        res = c_j_rand(res)
        h = ((res >> 0x10) & 0x7FFF) << 0x10
        res = c_j_rand(res)
        h |= (res >> 0x10) & 0x7FFF
    return h

def toBase3(n):
    res = []
    while n > 0:
        res.append(n % 3)
        n //= 3
    return res[::-1]

def keyNum2alphabet(n):
    if n <= 9:
        return ord('0') + n
    else:
        return ord('A') + n - 10

def genKey(name):
    if isinstance(name, str):
        name = name.encode()
    p = toBase3(hashName(name))
    p = p[::-1]
    xchgPairs = findPath(p, True)
    key = bytearray()
    xchgPairIndex = [
        (0, 1),
        (0, 2),
        (1, 0),
        (1, 2),
        (2, 0),
        (2, 1),
    ]
    for i in range(0, len(xchgPairs), 2):
        n1 = xchgPairIndex.index(xchgPairs[i])
        if i + 1 < len(xchgPairs):
            n2 = xchgPairIndex.index(xchgPairs[i + 1])
        else:
            n2 = 0
        key.append(keyNum2alphabet(n1 + n2 * 6))
    data = zlib.compress(key)
    # return raw deflate data (strip zlib header 2 bytes and adler32 checksum 4 bytes)
    data = data[2:-4]
    cKey = ''.join('{:02X}'.format(c) for c in data)
    return cKey

def keygen(name):
    '''Generate serial for the given name'''
    return genKey(name)

def verify(name, serial):
    '''Verify name/serial pair by regenerating and comparing'''
    expected = genKey(name)
    return serial.upper() == expected.upper()


# ===== standardized CLI (auto-added) =====
def _cli_norm(_x):
    if isinstance(_x, bytes):
        return _x.hex()
    if isinstance(_x, (list, tuple)):
        return " ".join(_cli_norm(_i) for _i in _x)
    return str(_x)


def _cli_main():
    import sys
    _SAMPLE = ['alice', 'bob', 'Kevin', 'test123', 'admin', 'crackme', 'john_doe', 'w1nner', 'root', 'dragon']
    argv = sys.argv[1:]
    mode = argv[0] if argv else ""
    if mode == "keygen":
        n = 0
        for _nm in _SAMPLE:
            _s = None
            for _call in (lambda: keygen(_nm), lambda: keygen()):
                try:
                    _s = _call()
                    break
                except TypeError:
                    continue
                except Exception:
                    _s = None
                    break
            if _s is None:
                continue
            _sv = _cli_norm(_s)
            print(_nm, _sv)
            n += 1
            if n >= 10:
                break
    elif mode == "verify":
        try:
            print("1" if verify(*argv[1:]) else "0")
        except Exception:
            print("0")
    else:
        sys.stderr.write("usage: {} {{keygen|verify <args>}}\n".format(sys.argv[0]))
        sys.exit(2)


if __name__ == "__main__":
    _cli_main()
