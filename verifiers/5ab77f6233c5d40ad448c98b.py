# NOTE: This is a PARTIAL reconstruction. The crackme involves several complex steps:
# 1. Encrypt the username into the first 16 bytes of a keyfile
# 2. Generate a 128-bit hash from the username (Ruby Hash algorithm)
# 3. Generate and execute polymorphic (reversed) x86 code
# 4. Generate and execute polymorphic MMX code
# 5. MM7 loop computation
# 6. 'last8' loop computation
# 7. TEA decode MMX
# 8. Write all results to 'kwasek.htb'
#
# Steps 3, 4, 5, 6, 7 depend on unshown include files (reversed.inc fully,
# ruby_hash.inc, tea_mmx.inc) and runtime-generated polymorphic code.
# Only step 1 (name encryption) is fully deterministic from the writeup.
# All other steps are marked ASSUMPTION or left as stubs.

import struct

# ---------------------------------------------------------------------------
# Step 1: Encrypt username into first 16 bytes of keyfile
# The code copies uname (up to 16 bytes / 4 dwords) into fd1,
# then iterates edi from fd1+12 down to fd1+0 (13 bytes = 13 iterations),
# each iteration: load dword at [edi], XOR with 0x012E4B8C, bswap, store, dec edi
# ---------------------------------------------------------------------------

def encrypt_name_part1(name: str) -> bytes:
    """Encrypt username into 16-byte fd1 block."""
    # Pad/truncate name to 16 bytes
    name_bytes = name.encode('ascii', errors='replace')[:16]
    name_bytes = name_bytes.ljust(16, b'\x00')

    # Copy into fd1 as a bytearray
    fd1 = bytearray(name_bytes)

    # edi starts at offset 12 (byte index), iterates 13 times, decrementing byte-by-byte
    # Each iteration reads a DWORD at [edi], XOR 0x012E4B8C, bswap, store
    # edi goes: 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0  (13 values)
    edi = 12
    for _ in range(13):
        if edi + 4 <= 16:
            val = struct.unpack_from('<I', fd1, edi)[0]
        else:
            # partial dword at end - pad with zeros
            chunk = bytes(fd1[edi:]) + b'\x00' * (4 - (16 - edi))
            val = struct.unpack('<I', chunk)[0]
        val ^= 0x012E4B8C
        # bswap = reverse bytes
        val = int.from_bytes(val.to_bytes(4, 'little'), 'big')
        if edi + 4 <= 16:
            struct.pack_into('>I', fd1, edi, val)  # stored big-endian after bswap
            # Actually bswap then store back: the store is mov [edi], eax which is little-endian
            # After bswap, eax bytes are reversed; storing LE means the reversed bytes go in order
            # Re-do: bswap on a LE-read value means byte-reverse the 4 bytes
            pass
        edi -= 1

    return bytes(fd1)


def encrypt_name_part1_correct(name: str) -> bytes:
    """Corrected: each step reads LE dword, XORs, bswaps (byte-reverses), stores LE."""
    name_bytes = name.encode('ascii', errors='replace')[:16]
    name_bytes = name_bytes.ljust(16, b'\x00')
    fd1 = bytearray(name_bytes)

    edi = 12  # byte offset
    for _ in range(13):
        # Read 4 bytes little-endian (may wrap, clamp)
        end = min(edi + 4, 16)
        chunk = fd1[edi:end] + bytearray(4 - (end - edi))
        val = struct.unpack('<I', bytes(chunk))[0]
        val ^= 0x012E4B8C
        # bswap: reverse the 4 bytes
        bswapped = struct.pack('<I', val)[::-1]  # byte-reverse
        # store back
        length = end - edi
        fd1[edi:end] = bswapped[:length]
        edi -= 1
    return bytes(fd1)


# ---------------------------------------------------------------------------
# Step 2: Ruby Hash (128-bit hash of username)
# ASSUMPTION: Ruby Hash algorithm is not shown. We stub it.
# The keygen calls it twice with edx=2 decrement, ecx=16, producing 16 bytes.
# ---------------------------------------------------------------------------

def ruby_hash(data: bytes, length: int) -> bytes:
    # ASSUMPTION: Ruby Hash algorithm unknown; stubbed with a placeholder
    # Real implementation would follow the ruby_hash.inc include
    import hashlib
    # ASSUMPTION: using SHA-1 as a stand-in, truncated to 8 bytes per call
    h = hashlib.sha1(data[:length]).digest()
    return h[:8]


def compute_uname_hash(name: str) -> bytes:
    """Compute 16-byte hash of username (two 8-byte Ruby Hash calls)."""
    name_bytes = name.encode('ascii', errors='replace')[:16]
    name_bytes = name_bytes.ljust(16, b'\x00')
    # ASSUMPTION: two calls to Ruby_Hash, each producing 8 bytes
    h1 = ruby_hash(name_bytes, 16)
    h2 = ruby_hash(name_bytes, 16)  # ASSUMPTION: same input, different output somehow
    return h1 + h2


# ---------------------------------------------------------------------------
# Steps 3-7: Polymorphic code execution, MMX loops, TEA decode
# These are entirely unknown without the include files and runtime codegen.
# ASSUMPTION: fd2 (24 bytes), fd3 (64 bytes), fd4 (8 bytes), fd5 (8 bytes), fd6 (8 bytes)
# are all zeroed as placeholders.
# ---------------------------------------------------------------------------

def compute_fd2(uname_hash: bytes) -> bytes:
    # ASSUMPTION: result of executing reversed polymorphic code on check2 string
    # check2 = 'Polymorphis by Kwasek :)' (24 bytes)
    # Unknown transformation
    return b'\x00' * 24


def compute_fd3(uname_hash: bytes) -> bytes:
    # ASSUMPTION: result of executing reversed MMX polymorphic code on check_mmx string
    return b'\x00' * 64


def compute_fd4(uname_hash: bytes) -> bytes:
    # ASSUMPTION: TEA decode result
    return b'\x00' * 8


def compute_fd5() -> bytes:
    # MM7 loop: psubd mm7, [MM7String] repeated 2688 times
    # MM7String = 'Witam wszystkich' (only first 8 bytes used)
    # mm7 starts at 0, loop subtracts the qword 2688 times
    mm7_string = b'Witam ws'  # first 8 bytes of 'Witam wszystkich'
    # treat as two 32-bit integers (little-endian) for psubd (packed subtract dword)
    lo = struct.unpack('<I', mm7_string[0:4])[0]
    hi = struct.unpack('<I', mm7_string[4:8])[0]
    # psubd subtracts packed dwords, mm7 starts at 0
    # mm7_lo = 0 - lo*2688, mm7_hi = 0 - hi*2688, with 32-bit wrap
    result_lo = (-lo * 2688) & 0xFFFFFFFF
    result_hi = (-hi * 2688) & 0xFFFFFFFF
    return struct.pack('<II', result_lo, result_hi)


def compute_fd6(uname_hash: bytes) -> bytes:
    # 8 bytes from uname_hash[8:16] processed by last8_reversed 586 times
    # ASSUMPTION: last8_reversed is unknown
    buf = bytearray(uname_hash[8:16])
    # ASSUMPTION: no transformation (stub)
    return bytes(buf)


# ---------------------------------------------------------------------------
# Keyfile assembly: 128 bytes total written to 'kwasek.htb'
# Layout from the code:
#   fd1: 16 bytes (encrypted name)
#   fd2: 24 bytes (poly result)
#   fd3: 64 bytes (poly mmx result)  -- but 16 dwords = 64 bytes
#   fd4:  8 bytes (TEA)
#   fd5:  8 bytes (MM7)
#   fd6:  8 bytes (last8)
# Total = 16+24+64+8+8+8 = 128 bytes
# ---------------------------------------------------------------------------

def keygen(name: str) -> bytes:
    """Generate the 128-byte keyfile content for 'kwasek.htb'."""
    uname_hash = compute_uname_hash(name)

    fd1 = encrypt_name_part1_correct(name)
    fd2 = compute_fd2(uname_hash)
    fd3 = compute_fd3(uname_hash)
    fd4 = compute_fd4(uname_hash)
    fd5 = compute_fd5()
    fd6 = compute_fd6(uname_hash)

    keyfile = fd1 + fd2 + fd3 + fd4 + fd5 + fd6
    assert len(keyfile) == 128, f"Expected 128 bytes, got {len(keyfile)}"
    return keyfile


def verify(name: str, serial: str) -> bool:
    """
    'serial' here represents the hex-encoded keyfile content.
    ASSUMPTION: verification means the keyfile matches expected output.
    Only fd1 and fd5 are computed correctly; others are stubs.
    """
    try:
        provided = bytes.fromhex(serial)
    except Exception:
        return False
    expected = keygen(name)
    # Only check fd1 (bytes 0-15) and fd5 (bytes 104-111) as those are deterministic
    return provided[:16] == expected[:16] and provided[104:112] == expected[104:112]



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
