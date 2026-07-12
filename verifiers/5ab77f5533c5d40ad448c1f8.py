import hashlib
import struct

# ASSUMPTION: The SHA-1 used here has a modified initial constant:
# Message_Digest[0] = 0x67453301 instead of standard 0x67452301
# This is confirmed by both solutions (sha1.c: h0init = 0x67453301L)
# We implement a custom SHA-1 with this tweak.

def _rotl32(n, x):
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF

def custom_sha1(data: bytes) -> list:
    """SHA-1 with modified initial constant h0 = 0x67453301."""
    if isinstance(data, str):
        data = data.encode('latin-1')
    
    # Modified initial values
    h0 = 0x67453301  # MODIFIED (standard is 0x67452301)
    h1 = 0xEFCDAB89
    h2 = 0x98BADCFE
    h3 = 0x10325476
    h4 = 0xC3D2E1F0
    
    msg = bytearray(data)
    orig_len = len(data) * 8
    msg.append(0x80)
    while len(msg) % 64 != 56:
        msg.append(0x00)
    msg += struct.pack('>Q', orig_len)
    
    for i in range(0, len(msg), 64):
        chunk = msg[i:i+64]
        w = list(struct.unpack('>16I', chunk))
        for j in range(16, 80):
            w.append(_rotl32(1, w[j-3] ^ w[j-8] ^ w[j-14] ^ w[j-16]))
        
        a, b, c, d, e = h0, h1, h2, h3, h4
        
        for j in range(80):
            if j < 20:
                f = (b & c) | ((~b) & d)
                k = 0x5A827999
            elif j < 40:
                f = b ^ c ^ d
                k = 0x6ED9EBA1
            elif j < 60:
                f = (b & c) | (b & d) | (c & d)
                k = 0x8F1BBCDC
            else:
                f = b ^ c ^ d
                k = 0xCA62C1D6
            
            temp = (_rotl32(5, a) + f + e + k + w[j]) & 0xFFFFFFFF
            e = d
            d = c
            c = _rotl32(30, b)
            b = a
            a = temp
        
        h0 = (h0 + a) & 0xFFFFFFFF
        h1 = (h1 + b) & 0xFFFFFFFF
        h2 = (h2 + c) & 0xFFFFFFFF
        h3 = (h3 + d) & 0xFFFFFFFF
        h4 = (h4 + e) & 0xFFFFFFFF
    
    return [h0, h1, h2, h3, h4]


def bswap(val):
    val &= 0xFFFFFFFF
    return (((val & 0x000000FF) << 24) |
            ((val & 0x0000FF00) << 8)  |
            ((val & 0x00FF0000) >> 8)  |
            ((val & 0xFF000000) >> 24))


def compute_serial(name: str) -> str:
    if len(name) < 5:
        return None
    
    # Step 1: SHA1 of name -> hashbuf (40-char hex string)
    digest1 = custom_sha1(name.encode('latin-1'))
    hashbuf = "{:08X}{:08X}{:08X}{:08X}{:08X}".format(*digest1)
    # hashbuf is 40 chars
    hashbuf = list(hashbuf.encode('latin-1'))  # work as byte array
    
    # Step 2: Calculate nvalue
    i = len(name) - 1
    n = 0
    tmp = 0
    nvalue = 0
    while i > -1:
        char_val = ord(name[i]) & 0xFF
        tmp = (tmp & 0xFFFFFF00) | char_val
        tmp = (tmp * 5 + n) & 0xFFFFFFFF
        tmp = bswap(tmp)
        nvalue = (nvalue + tmp) & 0xFFFFFFFF
        n += 1
        i -= 1
    nvalue ^= 0x12345678
    nvalue &= 0xFFFFFFFF
    
    # wsprintf with %X (uppercase hex, no leading zeros)
    nvalstr = "{:X}".format(nvalue)
    
    # Step 3: SHA1 of nvalstr -> nvaluehash, also get digest2
    digest2 = custom_sha1(nvalstr.encode('latin-1'))
    nvaluehash = "{:08X}{:08X}{:08X}{:08X}{:08X}".format(*digest2)
    
    # Step 4: Modify hashbuf by adding bytes from digest2
    # hashbuf[n] += (sha.Message_Digest[i] & 0x000000FF)
    # hashbuf[n+1] += (sha.Message_Digest[i] & 0x0000FF00) >> 8
    # hashbuf[n+2] += (sha.Message_Digest[i] & 0x00FF0000) >> 16
    # hashbuf[n+3] += (sha.Message_Digest[i] & 0xFF000000) >> 24
    # n goes 0,4,8,12,16 for i=0..4
    for idx in range(5):
        base = idx * 4
        hashbuf[base]   = (hashbuf[base]   + (digest2[idx] & 0x000000FF)) & 0xFF
        hashbuf[base+1] = (hashbuf[base+1] + ((digest2[idx] & 0x0000FF00) >> 8)) & 0xFF
        hashbuf[base+2] = (hashbuf[base+2] + ((digest2[idx] & 0x00FF0000) >> 16)) & 0xFF
        hashbuf[base+3] = (hashbuf[base+3] + ((digest2[idx] & 0xFF000000) >> 24)) & 0xFF
    
    # Step 5: SHA1 of nvaluehash with length = len(hashbuf) (40)
    # SHA1Input(&sha, nvaluehash, strlen(hashbuf))
    # strlen(hashbuf) may differ from strlen(nvaluehash)=40 if hashbuf has null bytes
    # ASSUMPTION: hashbuf after modification may contain null bytes; strlen stops at first null
    # We compute strlen of modified hashbuf
    hashbuf_strlen = 0
    for b in hashbuf:
        if b == 0:
            break
        hashbuf_strlen += 1
    
    # Input is nvaluehash bytes, length is hashbuf_strlen
    nvaluehash_bytes = nvaluehash.encode('latin-1')
    input_bytes = nvaluehash_bytes[:hashbuf_strlen]
    
    digest3 = custom_sha1(input_bytes)
    hashbuf_final = "{:08X}{:08X}{:08X}{:08X}{:08X}".format(*digest3)
    
    # Step 6: Build serial
    # for (n = 0; n < 4; n++) serial[n] = hashbuf[n];   -> first 4 chars
    # for (i = 0, n = 4; i < strlen(hashbuf); n++, i += 2) serial[n] = hashbuf[i];  -> every other char
    # serial[6] = '-'
    hf = hashbuf_final
    serial_list = []
    for n in range(4):
        serial_list.append(hf[n])
    i = 0
    while i < len(hf):
        serial_list.append(hf[i])
        i += 2
    # serial[6] = '-'
    while len(serial_list) <= 6:
        serial_list.append('\x00')
    serial_list[6] = '-'
    
    serial = ''.join(serial_list)
    return serial


def keygen(name: str) -> str:
    return compute_serial(name)


def verify(name: str, serial: str) -> bool:
    if len(name) < 5:
        return False
    expected = compute_serial(name)
    if expected is None:
        return False
    return serial == expected



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
