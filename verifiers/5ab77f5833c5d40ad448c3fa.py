import ctypes

# ROL (rotate left) for 32-bit integers
def rol32(value, shift):
    value = value & 0xFFFFFFFF
    shift = shift & 31
    return ((value << shift) | (value >> (32 - shift))) & 0xFFFFFFFF

# ROUND 2: Hidden edit hash check
# The hidden edit must contain a 16-char string such that after the hash
# the result equals 'xN<X.2`"' and magic == 0x125D02B2
# Two known valid hidden edit values are provided:
KNOWN_HIDDEN_EDITS = [b'aMoxywhtlkzsgGjk', b' { 7 .b~HO8_3M89']
TARGET_CODE = b'xN<X.2`"'
TARGET_MAGIC = 0x125D02B2

def check_hidden_edit(code_bytes):
    """Verify a 16-byte hidden edit value passes round 2."""
    assert len(code_bytes) == 16
    code = list(code_bytes)
    magic = 0
    result = []
    for i in range(8):
        a = code[i*2]
        b = code[i*2+1]
        magic = rol32(magic, 6)
        magic = (((a + b) * magic) ^ a) - b
        magic = magic & 0xFFFFFFFF
        # treat as signed 32-bit for subtraction then mask
        # actually magic stays as uint32 accumulator
        ch = ((((a ^ b) * 2) % 0x5E) + 0x20) & 0xFF
        result.append(ch)
    result_bytes = bytes(result)
    return result_bytes == TARGET_CODE and magic == TARGET_MAGIC

# ROUND 3: Name completion and serial verification

def complete_name(name_str):
    """Extend name to 32 characters using the given formula."""
    name = list(name_str.encode('latin-1'))
    j = len(name)
    i = 0
    while j < 32:
        # ASSUMPTION: arithmetic is done on raw byte values, result masked to byte
        val = (((name[i+1] - name[i]) ^ name[i+1]) * name[j-1]) % 0x5E + 0x20
        name.append(val & 0xFF)
        i += 1
        j += 1
    return name  # list of 32 ints

def encrypt_name(name32):
    """XOR first 16 bytes with second 16 bytes (in-place on copy)."""
    n = name32[:]
    for i in range(16):
        n[i] ^= n[i + 16]
    return n

def serial_check_constraints(serial32, i):
    """Check constraints for serial generation at position i."""
    # No spaces (0x20)
    if serial32[i] == 0x20 or serial32[i + 16] == 0x20:
        return False
    # Frequency check: no char appears more than 2 times in serial[0..i] and serial[16..16+i]
    freq = {}
    for k in range(i + 1):
        c = serial32[k]
        freq[c] = freq.get(c, 0) + 1
        if freq[c] > 2:
            return False
        c2 = serial32[k + 16]
        freq[c2] = freq.get(c2, 0) + 1
        if freq[c2] > 2:
            return False
    # No two consecutive same chars
    if i > 0:
        prev_enc = (((serial32[i-1] - serial32[i-1+16]) * 2) ^ (serial32[i-1+16] * 2)) & 0xFF
        curr_enc = (((serial32[i] - serial32[i+16]) * 2) ^ (serial32[i+16] * 2)) & 0xFF
        if curr_enc == prev_enc:
            return False
        if serial32[i+16] == serial32[i-1+16]:
            return False
    return True

def verify(name, serial):
    """
    Verify a name/serial pair against Round 3 logic.
    Round 1 (key state) and Round 2 (hidden edit) are UI-level checks
    not verifiable from name/serial alone.
    """
    if len(serial) < 32:
        return False
    # Step 1: complete name to 32 chars
    name32 = complete_name(name)
    if len(name32) < 32:
        return False
    # Step 2: encrypt name (XOR halves)
    enc_name = encrypt_name(name32)
    # Step 3: encode serial bytes
    ser = list(serial.encode('latin-1')) if isinstance(serial, str) else list(serial)
    if len(ser) < 32:
        return False
    # Check each position for constraints and compute encrypted serial
    enc_serial = [0] * 16
    for i in range(16):
        if ser[i] == 0x20 or ser[i + 16] == 0x20:
            return False
        enc_serial[i] = (((ser[i] - ser[i + 16]) * 2) ^ (ser[i + 16] * 2)) & 0xFF
    # Frequency check
    freq = [0] * 256
    for i in range(16):
        freq[ser[i]] += 1
        if freq[ser[i]] > 2:
            return False
        freq[ser[i + 16]] += 1
        if freq[ser[i + 16]] > 2:
            return False
    # Consecutive check
    for i in range(1, 16):
        if enc_serial[i] == enc_serial[i-1]:
            return False
        if ser[i + 16] == ser[i - 1 + 16]:
            return False
    # Final verification: aux must be zero
    # aux starts at 0, aux++ then aux *= (enc_serial[i] ^ (enc_name[i] & -2))
    # aux==0 only if in last iteration the XOR term is 0
    # ASSUMPTION: aux==0 means the final XOR term (enc_serial[15] ^ (enc_name[15] & 0xFE)) == 0
    # because if aux becomes 0 at the last multiply, the condition holds
    aux = 0
    for i in range(16):
        aux += 1
        aux *= (enc_serial[i] ^ (enc_name[i] & 0xFE))
        aux &= 0xFFFFFFFF  # ASSUMPTION: 32-bit arithmetic
    return aux == 0

def keygen(name):
    """Generate a 32-character serial for the given name."""
    name32 = complete_name(name)
    enc_name = encrypt_name(name32)
    serial = [0] * 33
    freq = {}
    result = [None] * 32

    for i in range(16):
        target = enc_name[i] & 0xFE  # (name[i] & -2)
        found = False
        # Try to find x, y such that:
        # enc_serial[i] = ((x - y)*2 ^ y*2) & 0xFF == target
        # From writeup: x = ((target ^ (y*2)) / 2 + y)
        # ASSUMPTION: iterate y from 0x21 to 0x7E
        for y in range(0x21, 0x7F):
            # enc = ((x-y)*2 ^ y*2), we want enc == target
            # target ^ (y*2) = (x-y)*2  =>  x = (target ^ (y*2))//2 + y
            diff = (target ^ ((y * 2) & 0xFF))
            if diff % 2 != 0:
                continue
            x = (diff // 2 + y) & 0xFF
            if x <= 0x20 or x > 0x7E:
                continue
            if freq.get(x, 0) >= 2 or freq.get(y, 0) >= 2:
                continue
            if x == 0x20 or y == 0x20:
                continue
            # Consecutive check
            if i > 0:
                prev_enc = (((result[i-1] - result[i-1+16]) * 2) ^ (result[i-1+16] * 2)) & 0xFF
                curr_enc = (((x - y) * 2) ^ (y * 2)) & 0xFF
                if curr_enc == prev_enc:
                    continue
                if y == result[i - 1 + 16]:
                    continue
            result[i] = x
            result[i + 16] = y
            freq[x] = freq.get(x, 0) + 1
            freq[y] = freq.get(y, 0) + 1
            found = True
            break
        if not found:
            # ASSUMPTION: fallback random not implemented; return None
            return None
    return bytes(result[:32]).decode('latin-1')


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
