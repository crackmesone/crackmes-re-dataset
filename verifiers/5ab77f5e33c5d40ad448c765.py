import base64
import struct

# RSA parameters from the crackme
# n and d are hex strings used with big integer arithmetic
RSA_N = int('A72DC3F82EEDF31C710F140F8CE5FDC75D055A1FFEC93BB1', 16)
RSA_D = int('E465E216700726DCF499650CA244BFAF7148CB6D60003B1', 16)


def xorname(name_bytes):
    """XOR operation on name bytes as described in the assembly.
    Last byte >> 1 is used as XOR key, applied to all preceding bytes.
    The last byte itself is also XORed.
    """
    data = bytearray(name_bytes)
    length = len(data)
    # al = last byte >> 1
    al = (data[length - 1] >> 1) & 0xFF
    # XOR all bytes (loop from length down to 1, i.e. indices length-1 down to 0)
    # The asm: ecx = length, then loops from ecx down to 1
    # xor byte ptr[edi+ecx-1], al  => XORs data[ecx-1]
    # So it XORs ALL bytes including the last one
    for i in range(length - 1, -1, -1):
        data[i] ^= al
    return bytes(data)


def ripemd160_hash(data):
    """Compute RIPEMD-160 hash."""
    try:
        import hashlib
        h = hashlib.new('ripemd160')
        h.update(data)
        return h.digest()
    except Exception:
        # ASSUMPTION: If ripemd160 not available, raise error
        raise RuntimeError('RIPEMD-160 not available in this Python build')


def compute_serial(name: str) -> str:
    """Compute the serial for a given name."""
    if len(name) < 5:
        raise ValueError('Name must be longer than 4 characters')

    name_bytes = name.encode('latin-1')

    # Step 1: XOR the name
    xored = xorname(name_bytes)

    # Step 2: Base64 encode the XORed name
    # ASSUMPTION: Standard base64 encoding is used (Encode64 from the keygen)
    b64 = base64.b64encode(xored)

    # Step 3: RIPEMD-160 hash of the base64 string
    # The asm passes length of b64 string and the b64 string pointer
    digest = ripemd160_hash(b64)

    # Step 4: bswap each 32-bit word of the 20-byte hash
    # The asm does bswap on 5 dwords
    words = struct.unpack('<5I', digest)  # little-endian read
    bswapped = []
    for w in words:
        # bswap reverses byte order
        bswapped_word = struct.unpack('>I', struct.pack('<I', w))[0]
        bswapped.append(bswapped_word)

    # Step 5: Format as hex string: "%.8X%.8X%.8X%.8X%.8X"
    # But the asm pushes HashBuffer+16, +12, +8, +4, +0 in that order for wsprintf
    # with format "%.8X%.8X%.8X%.8X%.8X"
    # Pushed in reverse order: [4],[3],[2],[1],[0] (cdecl: last arg pushed first)
    # Actually wsprintf args: format, then arg1, arg2, ... pushed right-to-left
    # Push order: +16, +12, +8, +4, +0 means arg5=+16, arg4=+12, arg3=+8, arg2=+4, arg1=+0
    # So format is: %.8X(word0) %.8X(word1) %.8X(word2) %.8X(word3) %.8X(word4)
    hash_str = ''.join('%08X' % w for w in bswapped)

    # Step 6: RSA: C = M^D mod N
    # M is the hash integer (treated as big integer from hex string)
    M = int(hash_str, 16)
    C = pow(M, RSA_D, RSA_N)

    # Step 7: Convert C to hex string (big_cotstr)
    serial = '%X' % C
    return serial


def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair."""
    try:
        expected = compute_serial(name)
        return serial.upper() == expected.upper()
    except Exception:
        return False


def keygen(name: str) -> str:
    """Generate serial for a given name."""
    return compute_serial(name)



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
