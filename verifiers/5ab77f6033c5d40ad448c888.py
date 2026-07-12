import struct
import math

# TEA constants
TEA_DELTA = 0x9E3779B9

def tea_decrypt_block(v0, v1, key):
    """Decrypt a single 64-bit block using TEA."""
    k0, k1, k2, k3 = key
    n = 32
    total = (TEA_DELTA * n) & 0xFFFFFFFF
    for _ in range(n):
        v1 = (v1 - (((v0 << 4) + k2) ^ (v0 + total) ^ ((v0 >> 5) + k3))) & 0xFFFFFFFF
        v0 = (v0 - (((v1 << 4) + k0) ^ (v1 + total) ^ ((v1 >> 5) + k1))) & 0xFFFFFFFF
        total = (total - TEA_DELTA) & 0xFFFFFFFF
    return v0, v1

def tea_encrypt_block(v0, v1, key):
    """Encrypt a single 64-bit block using TEA."""
    k0, k1, k2, k3 = key
    total = 0
    for _ in range(32):
        total = (total + TEA_DELTA) & 0xFFFFFFFF
        v0 = (v0 + (((v1 << 4) + k0) ^ (v1 + total) ^ ((v1 >> 5) + k1))) & 0xFFFFFFFF
        v1 = (v1 + (((v0 << 4) + k2) ^ (v0 + total) ^ ((v0 >> 5) + k3))) & 0xFFFFFFFF
    return v0, v1

def ror32(val, n):
    val &= 0xFFFFFFFF
    return ((val >> n) | (val << (32 - n))) & 0xFFFFFFFF

def compute_step1(name):
    """
    Step 1: take the first 4 bytes of name as a DWORD,
    apply the transformation sequence.
    """
    # Load first DWORD from name buffer (little-endian)
    name_bytes = name.encode('ascii', errors='replace')
    # Pad to at least 4 bytes
    name_bytes = name_bytes + b'\x00' * 4
    eax = struct.unpack_from('<I', name_bytes[:4])[0]
    eax = (eax ^ 0x1337) & 0xFFFFFFFF
    eax = ror32(eax, 0x0D)
    eax = (eax + 0xBEEF) & 0xFFFFFFFF
    eax = (eax ^ 0x20066002) & 0xFFFFFFFF
    return eax

def make_tea_key(step1_val):
    """
    From the writeup:
    [407B7C] = step1_val
    [407B80] = bswap(step1_val)
    tea_initkey uses [407B7C]..[407B80] => 8 bytes = 2 DWORDs as part of key.
    ASSUMPTION: key is [step1_val, bswap(step1_val), 0, 0] (two known DWORDs, two unknown/zero)
    """
    k0 = step1_val
    k1 = struct.unpack('<I', struct.pack('>I', step1_val))[0]  # bswap
    # ASSUMPTION: remaining key words are 0
    k2 = 0
    k3 = 0
    return (k0, k1, k2, k3)

def serial_to_blocks(serial):
    """
    The serial is 40 chars long.
    The loop subtracts 8 each iteration (serial_len - 8*i == 0 after 5 iterations => 5 blocks of 8 chars).
    Each call to 004024EB processes 8 bytes of serial into a DWORD.
    ASSUMPTION: each 8-char group is interpreted as a hex string representing a 32-bit value.
    """
    blocks = []
    for i in range(5):
        chunk = serial[i*8:(i+1)*8]
        try:
            val = int(chunk, 16)
        except ValueError:
            val = 0
        blocks.append(val)
    return blocks

def blocks_to_serial(blocks):
    """Convert list of DWORDs back to 40-char hex serial."""
    return ''.join('{:08X}'.format(b) for b in blocks)

def verify(name, serial):
    """
    Verification:
    1. Name length: 1 < len(name) <= 50 (< 0x32)
    2. Serial length must be exactly 40
    3. step1 = transform(name[0:4])
    4. TEA key = [step1, bswap(step1), 0, 0]
    5. Serial is split into 5 blocks of 8 hex chars => 5 DWORDs
    6. TEA decrypt pairs of DWORDs with the key
    7. ASSUMPTION: decrypted result should contain the name (checked via lstrlen/strcmp)
    """
    if len(name) <= 1 or len(name) >= 50:
        return False
    if len(serial) != 40:
        return False

    step1 = compute_step1(name)
    key = make_tea_key(step1)

    try:
        blocks = serial_to_blocks(serial)
    except Exception:
        return False

    # Decrypt pairs: blocks[0],blocks[1] and blocks[2],blocks[3]
    # blocks[4] might be a checksum or name-length check
    # ASSUMPTION: first two pairs decrypt to name bytes, compared with lstrlen result
    decrypted = []
    for i in range(0, 4, 2):
        d0, d1 = tea_decrypt_block(blocks[i], blocks[i+1], key)
        decrypted.append(d0)
        decrypted.append(d1)

    # Reconstruct decrypted bytes
    dec_bytes = b''
    for d in decrypted:
        dec_bytes += struct.pack('<I', d)

    # ASSUMPTION: decrypted bytes should match the name (null-terminated)
    name_bytes = name.encode('ascii', errors='replace')
    dec_name = dec_bytes[:len(name_bytes)]

    # Also check block[4]: ASSUMPTION it encodes name length or step1
    # ASSUMPTION: blocks[4] == step1 ^ len(name) or similar - not enough info, skip

    return dec_name == name_bytes

def keygen(name):
    """
    Generate a valid serial for the given name.
    Serial length = 40 (5 groups of 8 hex chars).
    """
    if len(name) <= 1 or len(name) >= 50:
        raise ValueError('Name must be between 2 and 49 characters')

    step1 = compute_step1(name)
    key = make_tea_key(step1)

    # Build plaintext from name (padded to 16 bytes for 2 TEA blocks)
    name_bytes = name.encode('ascii', errors='replace')
    # Pad to 16 bytes
    plain = name_bytes[:16].ljust(16, b'\x00')

    p0, p1, p2, p3 = struct.unpack('<4I', plain)

    # Encrypt
    e0, e1 = tea_encrypt_block(p0, p1, key)
    e2, e3 = tea_encrypt_block(p2, p3, key)

    # ASSUMPTION: block[4] = step1 (or 0 - not enough info)
    e4 = step1

    serial = '{:08X}{:08X}{:08X}{:08X}{:08X}'.format(e0, e1, e2, e3, e4)
    return serial


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
