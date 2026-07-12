import struct
from ctypes import c_uint32

# 3-Way block cipher implementation
STRT_E = 0x0b0b
STRT_D = 0xb1b1
NMBR = 11

def u32(x):
    return x & 0xFFFFFFFF

def mu(a):
    b = [0, 0, 0]
    for i in range(32):
        b[0] = u32(b[0] << 1)
        b[1] = u32(b[1] << 1)
        b[2] = u32(b[2] << 1)
        if a[0] & 1: b[2] |= 1
        if a[1] & 1: b[1] |= 1
        if a[2] & 1: b[0] |= 1
        a[0] = u32(a[0] >> 1)
        a[1] = u32(a[1] >> 1)
        a[2] = u32(a[2] >> 1)
    a[0] = b[0]; a[1] = b[1]; a[2] = b[2]

def gamma(a):
    b = [0, 0, 0]
    b[0] = u32(a[0] ^ (a[1] | (~a[2])))
    b[1] = u32(a[1] ^ (a[2] | (~a[0])))
    b[2] = u32(a[2] ^ (a[0] | (~a[1])))
    a[0] = b[0]; a[1] = b[1]; a[2] = b[2]

def theta(a):
    b = [0, 0, 0]
    b[0] = u32(a[0] ^ (a[0]>>16) ^ (u32(a[1]<<16)) ^
               (a[1]>>16) ^ (u32(a[2]<<16)) ^
               (a[1]>>24) ^ (u32(a[2]<<8)) ^
               (a[2]>>8)  ^ (u32(a[0]<<24)) ^
               (a[2]>>16) ^ (u32(a[0]<<16)) ^
               (a[2]>>24) ^ (u32(a[0]<<8)))
    b[1] = u32(a[1] ^ (a[1]>>16) ^ (u32(a[2]<<16)) ^
               (a[2]>>16) ^ (u32(a[0]<<16)) ^
               (a[2]>>24) ^ (u32(a[0]<<8)) ^
               (a[0]>>8)  ^ (u32(a[1]<<24)) ^
               (a[0]>>16) ^ (u32(a[1]<<16)) ^
               (a[0]>>24) ^ (u32(a[1]<<8)))
    b[2] = u32(a[2] ^ (a[2]>>16) ^ (u32(a[0]<<16)) ^
               (a[0]>>16) ^ (u32(a[1]<<16)) ^
               (a[0]>>24) ^ (u32(a[1]<<8)) ^
               (a[1]>>8)  ^ (u32(a[2]<<24)) ^
               (a[1]>>16) ^ (u32(a[2]<<16)) ^
               (a[1]>>24) ^ (u32(a[2]<<8)))
    a[0] = b[0]; a[1] = b[1]; a[2] = b[2]

def pi_1(a):
    a[0] = u32((a[0]>>10) ^ (u32(a[0]<<22)))
    a[2] = u32((u32(a[2]<<1)) ^ (a[2]>>31))

def pi_2(a):
    a[0] = u32((u32(a[0]<<1)) ^ (a[0]>>31))
    a[2] = u32((a[2]>>10) ^ (u32(a[2]<<22)))

def rho(a):
    theta(a)
    pi_1(a)
    gamma(a)
    pi_2(a)

def rndcon_gen(strt):
    rtab = []
    for i in range(NMBR+1):
        rtab.append(u32(strt))
        strt = u32(strt << 1)
        if strt & 0x10000:
            strt ^= 0x11011
    return rtab

def threeway_encrypt(a, k):
    # a and k are lists of 3 uint32
    rcon = rndcon_gen(STRT_E)
    for i in range(NMBR):
        a[0] = u32(a[0] ^ k[0] ^ (u32(rcon[i] << 16)))
        a[1] = u32(a[1] ^ k[1])
        a[2] = u32(a[2] ^ k[2] ^ rcon[i])
        rho(a)
    a[0] = u32(a[0] ^ k[0] ^ (u32(rcon[NMBR] << 16)))
    a[1] = u32(a[1] ^ k[1])
    a[2] = u32(a[2] ^ k[2] ^ rcon[NMBR])
    theta(a)

def threeway_decrypt(a, k):
    ki = [k[0], k[1], k[2]]
    theta(ki)
    mu(ki)
    rcon = rndcon_gen(STRT_D)
    mu(a)
    for i in range(NMBR):
        a[0] = u32(a[0] ^ ki[0] ^ (u32(rcon[i] << 16)))
        a[1] = u32(a[1] ^ ki[1])
        a[2] = u32(a[2] ^ ki[2] ^ rcon[i])
        rho(a)
    a[0] = u32(a[0] ^ ki[0] ^ (u32(rcon[NMBR] << 16)))
    a[1] = u32(a[1] ^ ki[1])
    a[2] = u32(a[2] ^ ki[2] ^ rcon[NMBR])
    theta(a)
    mu(a)

# ASSUMPTION: GetHashUserIdFromCrackme and GetMessageFromCrackme are not
# described in detail in the writeup. The following are placeholder stubs.
# The keygen.cpp shows the overall flow:
#   key = hash_of_userid(userid)
#   msg = message_from_name_company(name, company)
#   serial = encrypt(msg, key)
# Verification: decrypt(serial, key) == msg_from_name_company(name, company)

def get_hash_userid(userid):
    # ASSUMPTION: unknown hash function applied to userid (24 chars)
    # Placeholder: simple byte packing
    uid = userid.encode('latin-1')[:24]
    while len(uid) < 24:
        uid += b'\x00'
    k0 = struct.unpack('>I', uid[0:4])[0]
    k1 = struct.unpack('>I', uid[8:12])[0]
    k2 = struct.unpack('>I', uid[16:20])[0]
    return [k0, k1, k2]

def get_message_from_name_company(name, company):
    # ASSUMPTION: unknown function combining name and company into 96-bit msg
    # Placeholder: simple byte packing of first chars
    n = name.encode('latin-1')[:16]
    c = company.encode('latin-1')[:16]
    combined = (n + b'\x00'*16)[:16] + (c + b'\x00'*16)[:8]
    m0 = struct.unpack('>I', combined[0:4])[0]
    m1 = struct.unpack('>I', combined[4:8])[0]
    m2 = struct.unpack('>I', combined[8:12])[0]
    return [m0, m1, m2]

def keygen(name, company='', userid='000000000000000000000000'):
    """
    Generate a serial for the given name, company, userid.
    Serial format: XXXXXXXX-XXXXXXXX-XXXXXXXX
    """
    key = get_hash_userid(userid)
    msg = get_message_from_name_company(name, company)
    cipher = [msg[0], msg[1], msg[2]]
    threeway_encrypt(cipher, key)
    return '%08X-%08X-%08X' % (cipher[0], cipher[1], cipher[2])

def verify(name, serial, company='', userid='000000000000000000000000'):
    """
    Verify serial against name/company/userid.
    Crackme computes D(serial, key) and compares to plaintext msg.
    """
    parts = serial.replace('-', ' ').split()
    if len(parts) != 3:
        return False
    try:
        s = [int(p, 16) for p in parts]
    except ValueError:
        return False
    key = get_hash_userid(userid)
    msg = get_message_from_name_company(name, company)
    decrypted = [s[0], s[1], s[2]]
    threeway_decrypt(decrypted, key)
    return decrypted[0] == msg[0] and decrypted[1] == msg[1] and decrypted[2] == msg[2]


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
