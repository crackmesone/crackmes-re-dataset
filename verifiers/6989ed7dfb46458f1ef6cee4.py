import sys
from typing import List, Optional

# Constants extracted from multiple solution writeups
BLOB_HEX = "48d9ed8a1dff9a7bb0d1e57c15f7927388e9ddbb2dcfaa4b80e1d5b325c7a243"
DATA_HEX = "4f000000d000000051010000d201000053020000d402000055030000d603000057000000d800000059010000da0100005b020000dc0200005d030000de0300005f000000e000000061010000e201000063020000e402000065030000e603000067000000e800000069010000ea0100006b020000ec0200006d030000ee0300006f000000f000000071010000f201000073020000f402000075030000f603000077000000f800000079010000fa0100007b020000fc0200007d030000fe0300007f000000000100008101000002020000830200000403000085030000060000008700000008010000890100000a0200008b0200000c0300008d0300000e000000"

# Anti-debug constants from parent-child interaction
# Parent forces RAX = 0x9F2D38B17C6A4E5F when child hits INT3
# Child uses 0xB3E192F8A4D5C6B7 if no hardware breakpoints detected
ANTIDEBUG_CONST = 0xB3E192F8A4D5C6B7
PARENT_FORCED = 0x9F2D38B17C6A4E5F
# Effective mask = XOR of both constants
MASK = ANTIDEBUG_CONST ^ PARENT_FORCED

# LCG parameters
LCG_SEED = 0xDEADBEEF
LCG_A = 0x19660D
LCG_B = 0x3C6EF35F

# ASSUMPTION: There is ambiguity between solutions about the LCG output width and matrix structure.
# Solution 1 uses & 0x3FF (10-bit) with a 64x4x16 structure (high matrix),
# Solution 2 uses & 0xFF (8-bit) with a flat 64x64 structure.
# We implement Solution 1's approach (more detailed) as primary, but note the discrepancy.

def build_high_matrix() -> List[int]:
    """Build 4096-entry fixed matrix from LCG seeded with 0xDEADBEEF."""
    high = [0] * 4096
    u = LCG_SEED
    idx = 0
    for _ in range(0x40):          # 64 outer
        for _ in range(4):         # 4 rows
            for _ in range(16):    # 16 cols
                u = (u * LCG_A + LCG_B) & 0xFFFFFFFF
                high[idx] = u & 0x3FF
                idx += 1
    return high


def build_low_matrix(pw: bytes) -> List[int]:
    """Build 64-entry input matrix from password bytes (zero-padded to 64 bytes)."""
    low = [0] * 64
    for i in range(64):
        low[i] = pw[i] if i < len(pw) else 0
    return low


def gen_key(pw: bytes) -> List[int]:
    """
    For each n in 0..63:
      edx = sum over 4 groups j of dot(high[(n*4+j)*16:(n*4+j)*16+16], low[j*16:j*16+16]) mod 2^32
      edx = edx mod 1024
      key[n] = (data[n*4] - (edx & 0xFF)) mod 256
    """
    data = bytes.fromhex(DATA_HEX)
    high = build_high_matrix()
    low = build_low_matrix(pw)
    key = []
    for n in range(64):
        edx = 0
        for j in range(4):
            start1 = (n * 4 + j) * 16
            start2 = j * 16
            dot = 0
            for k in range(16):
                dot = (dot + high[start1 + k] * low[start2 + k]) & 0xFFFFFFFF
            edx = (edx + dot) & 0xFFFFFFFF
        edx = edx & 0x3FF
        source_byte = data[n * 4]
        key.append((source_byte - (edx & 0xFF)) & 0xFF)
    return key


def decode_blob(key: List[int]) -> bytes:
    """XOR blob with mask bytes and key to produce VM bytecode."""
    blob = bytes.fromhex(BLOB_HEX)
    mask_bytes = MASK.to_bytes(8, 'little')
    out = bytearray()
    for i, b in enumerate(blob):
        out.append(b ^ mask_bytes[i & 7] ^ key[i])
    return bytes(out)


def check_vm_success(decoded: bytes) -> bool:
    """
    Valid password => first VM instruction:
      op=0xF0, imm (bytes 3..10 little-endian) == 1
    VM instruction format: [op:1][r1:1][r2:1][imm:8] = 11 bytes
    """
    if len(decoded) < 11:
        return False
    op = decoded[0]
    imm = int.from_bytes(decoded[3:11], 'little')
    return op == 0xF0 and imm == 1


def verify(name: str, serial: str) -> bool:
    """
    Verify a password (serial) for this crackme.
    Note: The crackme only uses 'password' (serial), not a name+serial pair.
    The 'name' parameter is ignored as the crackme has no name field.
    """
    # ASSUMPTION: name is not used; only the password/serial matters.
    pw = serial.encode('latin-1')
    try:
        key = gen_key(pw)
        decoded = decode_blob(key)
        return check_vm_success(decoded)
    except Exception:
        return False


def keygen(name: str) -> str:
    """
    Generate a valid password using Z3 if available, otherwise use brute-force
    over short printable strings.
    The known-good answer from the writeup is 'y5' (length 2).
    """
    # Known solution from writeup
    known = 'y5'
    if verify(name, known):
        return known

    # Try to find via Z3 (preferred, as used by solvers)
    try:
        from z3 import Int, Solver, sat
        data = bytes.fromhex(DATA_HEX)
        blob = bytes.fromhex(BLOB_HEX)
        mask_bytes = MASK.to_bytes(8, 'little')
        high = build_high_matrix()

        # Target: decoded[0]=0xF0, decoded[3]=0x01, decoded[4..10]=0x00
        TARGET = {0: 0xF0, 3: 0x01, 4: 0x00, 5: 0x00, 6: 0x00, 7: 0x00, 8: 0x00, 9: 0x00, 10: 0x00}

        def coeff_row_low8(n: int) -> List[int]:
            """Low 8 bits of high matrix coefficients for row n."""
            row = []
            for j in range(4):
                for k in range(16):
                    row.append(high[(n * 4 + j) * 16 + k] & 0xFF)
            return row  # length 64

        def need_val(n: int, target_byte: int) -> int:
            key_n = blob[n] ^ mask_bytes[n & 7] ^ target_byte
            data_n = data[n * 4]
            return (data_n - key_n) & 0xFF

        for nvars in range(1, 65):
            s = Solver()
            xs = [Int(f'x{i}') for i in range(nvars)]
            for x in xs:
                s.add(x >= 0x20, x <= 0x7e)
            for n, tgt in TARGET.items():
                coeffs = coeff_row_low8(n)
                expr = sum(coeffs[i] * xs[i] for i in range(nvars))
                s.add(expr % 256 == need_val(n, tgt))
            if s.check() == sat:
                m = s.model()
                return ''.join(chr(m[x].as_long()) for x in xs)
        return ''
    except ImportError:
        pass

    # Fallback: brute-force short printable strings
    import itertools
    chars = [chr(c) for c in range(0x20, 0x7f)]
    for length in range(1, 5):
        for combo in itertools.product(chars, repeat=length):
            candidate = ''.join(combo)
            if verify(name, candidate):
                return candidate
    # ASSUMPTION: If nothing found, return empty string
    return ''



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
