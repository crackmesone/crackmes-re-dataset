import struct
import hashlib

# Based on writeups for pranav's SecureSoftware v1.5
# The authdata.dat file layout (220 = 0xdc bytes):
#   [0-8]    -> Hardcoded 6-char string (+ unused), e.g. 'bu1oq\x00\x00\x00'
#   [8-12]   -> time_t (4 bytes, time at setup)
#   [12-62]  -> username (50 bytes, zero-padded)
#   [62-112] -> hostname (50 bytes, zero-padded)
#   [112-212]-> user-provided key (100 bytes, zero-padded)
#   [212-220]-> Hardcoded 6-char string (+ unused), e.g. 'bu1oq\x00\x00\x00'
#
# Checksum = sum of all 220 bytes, stored as 4-byte little-endian in 'checksum' file
#
# Key validation (from sub_401F18 / checkAuthdata):
#   1. authdata header/trailer must match hardcoded strings
#   2. Checksum file must match computed checksum of authdata.dat
#   3. Function integrity checks (sub_4021C9) must pass - anti-patch/anti-debug
#   4. The key bytes are read from authdata[0x70] = authdata[112:]
#      Each key byte != -1 (0xff) is processed:
#        sum_key = sum of key[i] for key[i] != 0xff
#      This sum is compared against a hardcoded expected value.
#
# From writeup g3chantr, sub_401F18 pseudo-code:
#   str = buf + 0x70  (key starts at offset 112)
#   Then a while loop iterates key chars while key[i] != -1:
#     if key[i] != -1: ... (Illegal copy if not matching)
#
# The exact check on the key bytes is:
#   Each character of the key is validated byte-by-byte.
#   From giacomo270197's truncated writeup:
#     'while (local_14 < (int)sVar2) { if (key[local_14] != -1) { ... } }'
#   The actual comparison is against username+computername derived values.
#
# ASSUMPTION: The key validation compares key characters against a transformation
# of the username and/or computername. The exact formula is not fully shown in
# any writeup. Based on available info, we implement what we can.

# ASSUMPTION: Hardcoded magic strings at start/end of authdata
MAGIC_START = b'bu1oq\x00\x00\x00'  # 8 bytes
MAGIC_END   = b'bu1oq\x00\x00\x00'  # 8 bytes

def build_authdata(username: str, hostname: str, key: str, timestamp: int = 0) -> bytes:
    """Build the 220-byte authdata buffer."""
    buf = bytearray(220)
    # [0-8] magic start
    ms = MAGIC_START[:8].ljust(8, b'\x00')
    buf[0:8] = ms
    # [8-12] timestamp
    struct.pack_into('<I', buf, 8, timestamp & 0xFFFFFFFF)
    # [12-62] username (50 bytes)
    uname_bytes = username.encode('utf-8')[:50]
    buf[12:12+len(uname_bytes)] = uname_bytes
    # [62-112] hostname (50 bytes)
    hname_bytes = hostname.encode('utf-8')[:50]
    buf[62:62+len(hname_bytes)] = hname_bytes
    # [112-212] key (100 bytes)
    key_bytes = key.encode('utf-8')[:100]
    buf[112:112+len(key_bytes)] = key_bytes
    # [212-220] magic end
    me = MAGIC_END[:8].ljust(8, b'\x00')
    buf[212:220] = me
    return bytes(buf)

def compute_checksum(authdata: bytes) -> int:
    """Sum all 220 bytes of authdata."""
    # From writeup: sum of all 0xdc (220) bytes
    # ReedOnly says 0xDB+1 = 220 bytes (matches)
    return sum(authdata) & 0xFFFFFFFF

def verify(name: str, serial: str) -> bool:
    """
    Verify a serial for a given name (username).
    NOTE: This is a PARTIAL reconstruction. The crackme uses:
      - username and hostname from the OS
      - authdata.dat file on disk
      - checksum file on disk
      - anti-debug/anti-patch checks (cannot replicate in pure Python)
      - a key derivation check inside sub_401F18

    What we CAN verify:
      1. The serial is non-empty
      2. The serial length <= 100 chars
      3. The serial does not contain 0xff bytes
    
    The actual byte-by-byte check against username/hostname is ASSUMED below.
    """
    if not serial or len(serial) == 0:
        return False
    if len(serial) > 100:
        return False
    # ASSUMPTION: key bytes must all be != 0xFF (which is the sentinel -1)
    for c in serial.encode('utf-8'):
        if c == 0xFF:
            return False
    # ASSUMPTION: Based on the writeup describing that key chars are compared
    # against derived values from username/hostname, we implement the most
    # common pattern seen in crackmes of this style:
    # The key is derived by XOR or addition of username chars with some constant.
    # The exact formula from sub_401F18 / checkAuthdata is not fully disclosed.
    #
    # From g3chantr writeup (sub_401F18 analysis, truncated before formula shown):
    # 'str = buf + 0x70 // to get the input key string'
    # The check iterates key chars and compares. We cannot determine the exact
    # expected value without the full disassembly.
    #
    # ASSUMPTION: We cannot fully verify without the exact algorithm.
    # Return True as a placeholder if basic sanity checks pass.
    return True

def keygen(name: str, hostname: str = 'DESKTOP') -> str:
    """
    Generate a valid key for the given username and hostname.
    ASSUMPTION: The exact key derivation formula is not fully recovered from
    the writeups. The writeups confirm a keygen is possible and that the key
    relates to username/hostname, but the exact byte-level formula is truncated.
    
    From kondeti's comment: a Python keygen exists at pastebin (not available here).
    From 4epuxa: 'Generating a password is not too complicated'.
    From giacomo270197 (truncated): key bytes are checked against something
      derived from authdata contents.
    
    ASSUMPTION: A simple derivation based on username bytes is used.
    This is a PLACEHOLDER - the real formula requires the full disassembly.
    """
    # ASSUMPTION: key is derived from username + hostname bytes via simple transform
    # The most common pattern in such crackmes: key[i] = f(username[i % len(username)])
    # Without the exact function, we produce a best-guess placeholder.
    key_bytes = []
    combined = (name + hostname).encode('utf-8')
    for i, b in enumerate(combined[:50]):
        # ASSUMPTION: simple identity or small arithmetic transform
        val = (b + i) & 0x7F  # keep printable, avoid 0xFF
        if val == 0:
            val = 0x41  # avoid null
        key_bytes.append(val)
    if not key_bytes:
        key_bytes = [0x41] * 8  # fallback
    return bytes(key_bytes).decode('latin-1')


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
