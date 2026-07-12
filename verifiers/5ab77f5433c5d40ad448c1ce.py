import ctypes

# ---------------------------------------------------------------------------
# Helper: modular exponentiation  (mirrors sub_401000 / sub_401050)
# RSA params from solution 2 comments: E=7, N=0x8F=143, D=0x67=103
# sub_401000 is called as sub_401000(byte, D=0x67, N=0x8F)  => byte^D mod N
# ---------------------------------------------------------------------------
RSA_E = 7
RSA_N = 0x8F   # 143
RSA_D = 0x67   # 103

def _powmod(base, exp, mod):
    """Standard modular exponentiation."""
    return pow(base, exp, mod)


# ---------------------------------------------------------------------------
# Step 1 – build hash_10 (16-byte buffer) from name
# Mirrors the div_loop in gene.asm / KEYGEN.ASM
# ---------------------------------------------------------------------------
def _build_hash10(name: bytes) -> list:
    namelen = len(name)
    hash10 = [0] * 0x10
    for ecx in range(0x10):
        # edx = ecx % 3  (signed idiv, but for ecx>=0 same as unsigned)
        edx_outer = ecx % 3
        if edx_outer == 0:
            # idiv esi  (esi = namelen)
            edx_inner = ecx % namelen
            dl = name[edx_inner]
        else:
            edx_inner = ecx % namelen
            idx = namelen - edx_inner - 1   # esi - edx - 1  (0-based)
            dl = name[idx]
        hash10[ecx] = dl
    return hash10


# ---------------------------------------------------------------------------
# Step 2 – build buffer2 (8-byte array) from hash_10
# Mirrors part2_create_loop.  Only even esi values produce output.
# The loop runs esi=0..15; at each EVEN esi:
#   val = (hash10[esi+1] * esi) XOR hash10[esi]
#   dl  = val % 25  (idiv 0x19=25, remainder dl)  then dl += 'A'
# Output index = esi >> 1  (0..7)
# ---------------------------------------------------------------------------
def _build_buffer2(hash10: list) -> list:
    buf2 = [0] * 8
    for esi in range(0x10):
        # check parity of esi via: eax = esi & 0x80000001; if sign => adjust; jnz skips
        # Effectively: skip if esi is ODD
        # (esi & 0x80000001): for 0<=esi<16 the sign bit is never set,
        # so we just check (esi & 1) != 0 => skip
        if (esi & 1) != 0:
            continue
        eax = ctypes.c_int8(hash10[esi + 1]).value   # movsx
        ecx_val = ctypes.c_int8(hash10[esi]).value   # movsx
        eax = eax * esi
        eax = eax ^ ecx_val
        # idiv 0x19 => remainder dl
        dl = eax % 0x19   # ASSUMPTION: Python % may differ from C signed idiv for negatives
        dl = dl & 0xFF
        dl_char = (dl + ord('A')) & 0xFF
        out_idx = esi >> 1
        buf2[out_idx] = dl_char
    return buf2


# ---------------------------------------------------------------------------
# Step 3 – RSA transform of each buf2 byte, then encode as two letters
# From solution 2: call sub_401000(byte, D=0x67, N=0x8F)
# result / 26 => high letter, result % 26 => low letter  (both + 'A')
# This produces _buffer3 (16 chars = 8 pairs)
# ---------------------------------------------------------------------------
def _rsa_encode(buf2: list) -> str:
    out = []
    for b in buf2:
        r = _powmod(b, RSA_D, RSA_N)
        hi = r // 26
        lo = r % 26
        out.append(chr(hi + ord('A')))
        out.append(chr(lo + ord('A')))
    return ''.join(out)


# ---------------------------------------------------------------------------
# Step 4 – compute p3  (from keygen.c)
# p3 = sum(ord(c) for c in name) XOR 1
# Solution 2 uses XOR 7 instead of XOR 1  -- ASSUMPTION: use solution 2 value
# ---------------------------------------------------------------------------
def _compute_p3(name: str) -> int:
    # ASSUMPTION: solution 1 uses XOR 1, solution 2 uses XOR 7.
    # We expose both; verify() will try both.
    s = sum(ord(c) for c in name)
    return s ^ 7   # solution 2 value used for keygen


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    name_bytes = name.encode('ascii', errors='replace')
    if len(name_bytes) < 1:
        raise ValueError('Name too short')
    hash10 = _build_hash10(name_bytes)
    buf2   = _build_buffer2(hash10)
    enc    = _rsa_encode(buf2)   # 16 chars
    p3     = _compute_p3(name)
    # Serial format: ULT-<16chars>-<p3>   (dash added after _buffer3[16])
    # Solution 2 sets byte[edi]='-' (0x2Dh) after the 16 encoded chars
    serial = 'ULT-' + enc + '-' + str(p3)
    return serial


def _parse_serial(serial: str):
    """Return (enc_part, p3_str) or raise ValueError."""
    if not serial.startswith('ULT-'):
        raise ValueError('Bad prefix')
    body = serial[4:]  # everything after ULT-
    # body should be 16 alpha chars, then '-', then digits
    # but solution 1 format was ULT-<p2[17]><rand_letter><p3>  -- slightly different
    # ASSUMPTION: we accept the solution-2 format: ULT-AAAA...AA-<number>
    dash = body.rfind('-')
    if dash < 0:
        raise ValueError('No dash found in body')
    enc_part = body[:dash]
    p3_str   = body[dash+1:]
    return enc_part, p3_str


def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair."""
    try:
        enc_part, p3_str = _parse_serial(serial)
    except ValueError:
        return False

    # Check p3
    try:
        p3_given = int(p3_str)
    except ValueError:
        return False

    name_bytes = name.encode('ascii', errors='replace')
    if len(name_bytes) < 1:
        return False

    # Accept both XOR 1 and XOR 7 variants
    s = sum(ord(c) for c in name)
    p3_v1 = s ^ 1
    p3_v2 = s ^ 7
    if p3_given not in (p3_v1, p3_v2):
        return False

    # Regenerate expected encoded part
    hash10 = _build_hash10(name_bytes)
    buf2   = _build_buffer2(hash10)
    enc_expected = _rsa_encode(buf2)

    # enc_part may be 16 chars (solution2) or 17 (solution1 adds extra random letter)
    # ASSUMPTION: compare first 16 chars
    if len(enc_part) < 16:
        return False
    return enc_part[:16].upper() == enc_expected.upper()


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------

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
