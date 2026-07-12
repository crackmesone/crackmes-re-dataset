#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Keygen for keygenme#1 by tamaroth
# Reconstructed from writeup by crackmes.de (Miguel, 23.10.2010)
#
# Algorithm summary:
# 1. Get username (length must be > 3)
# 2. Compute two floating-point numbers from the username chars (first_number, second_number)
# 3. Get serial string (length must be > 3)
# 4. Decode serial: treat as base64-like encoding with charset
#    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
#    Process in 4-char chunks, each chunk yields 3 bytes:
#      n1 = ((a * 4) % 0x100) + ((b >> 4) & 0x3)
#      n2 = ((c >> 2) & 0xf) ^ ((b << 4) % 0x100)
#      n3 = ((c << 6) % 0x100) + d
# 5. The resulting byte string, when interpreted as ASCII, must match pattern: "X|Y"
#    where X and Y are numbers (using digits, '-', '.')
#    and there is exactly one '|' separator.
# 6. X and Y are loaded as floats and compared to first_number and second_number from the username.
#
# ASSUMPTION: first_number and second_number computation from username.
# The writeup says "You can see the algorithm used in my keygen" but doesn't spell it out fully.
# ASSUMPTION: Based on common crackme patterns for two numbers from a name,
# we guess:
#   first_number  = sum of ord(c) for c in name  (as float)
#   second_number = product of ord(c) for c in name  (as float)
# These are ASSUMPTIONS - the actual asm is not shown in the writeup.

CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

def char_to_idx(c):
    idx = CHARSET.find(c)
    if idx == -1:
        raise ValueError(f"Character {c!r} not in charset")
    return idx

def decode_serial_to_bytes(serial):
    """Decode serial string (base64-like) into bytes using 4->3 mapping."""
    result = []
    # Pad serial to multiple of 4
    # ASSUMPTION: serial length must be multiple of 4 or padding is ignored
    if len(serial) % 4 != 0:
        # ASSUMPTION: pad with 'A' (index 0)
        serial = serial + 'A' * (4 - len(serial) % 4)
    for i in range(0, len(serial), 4):
        chunk = serial[i:i+4]
        a = char_to_idx(chunk[0])
        b = char_to_idx(chunk[1])
        c = char_to_idx(chunk[2])
        d = char_to_idx(chunk[3])
        n1 = ((a * 4) % 0x100) + ((b >> 4) & 0x3)
        n2 = ((c >> 2) & 0xf) ^ ((b << 4) % 0x100)
        n3 = ((c << 6) % 0x100) + d
        result.extend([n1 & 0xFF, n2 & 0xFF, n3 & 0xFF])
    return bytes(result)

def parse_decoded(decoded_bytes):
    """Parse decoded bytes as ASCII string with pattern X|Y.
    Valid chars: '|', '-', '.', '0'-'9'.
    Returns (float(X), float(Y)) or None if invalid."""
    try:
        s = decoded_bytes.decode('ascii', errors='replace')
    except Exception:
        return None
    # Strip null bytes
    s = s.rstrip('\x00')
    # Validate chars
    pipe_count = 0
    for ch in s:
        if ch == '|':
            pipe_count += 1
        elif ch in '-.' or ('0' <= ch <= '9'):
            pass
        else:
            return None
    if pipe_count != 1:
        return None
    parts = s.split('|')
    if len(parts) != 2:
        return None
    try:
        n1 = float(parts[0])
        n2 = float(parts[1])
        return (n1, n2)
    except ValueError:
        return None

# ASSUMPTION: These are placeholders. The actual formulas are NOT shown in the writeup.
# Replace with the real formulas if discovered through further analysis.
def first_number(name):
    # ASSUMPTION: sum of ASCII values of name chars
    return float(sum(ord(c) for c in name))

def second_number(name):
    # ASSUMPTION: product of ASCII values of name chars
    result = 1.0
    for c in name:
        result *= ord(c)
    return result

def verify(name, serial):
    """Verify (name, serial) pair."""
    if len(name) <= 3:
        return False
    if len(serial) <= 3:
        return False
    try:
        decoded = decode_serial_to_bytes(serial)
    except ValueError:
        return False
    parsed = parse_decoded(decoded)
    if parsed is None:
        return False
    sn1, sn2 = parsed
    fn1 = first_number(name)
    fn2 = second_number(name)
    # ASSUMPTION: exact float comparison; real crackme likely uses FPU comparison
    # with some tolerance. Using a small epsilon here.
    eps = 1e-6
    return abs(sn1 - fn1) < eps and abs(sn2 - fn2) < eps

def encode_bytes_to_serial(data_bytes):
    """Encode 3 bytes back into 4 serial chars (inverse of decode).
    Given n1, n2, n3 (3 bytes), find a,b,c,d in charset such that:
      n1 = ((a*4)%256) + ((b>>4)&3)
      n2 = ((c>>2)&0xf) ^ ((b<<4)%256)
      n3 = ((c<<6)%256) + d
    ASSUMPTION: brute-force search over charset indices (0..63 each).
    """
    result = []
    for i in range(0, len(data_bytes), 3):
        chunk = data_bytes[i:i+3]
        if len(chunk) < 3:
            chunk = chunk + bytes(3 - len(chunk))  # pad with zeros
        n1, n2, n3 = chunk[0], chunk[1], chunk[2]
        found = False
        for a in range(64):
            for b in range(64):
                if ((a * 4) % 256) + ((b >> 4) & 3) == n1:
                    for c in range(64):
                        if ((c >> 2) & 0xf) ^ ((b << 4) % 256) == n2:
                            d = n3 - ((c << 6) % 256)
                            if 0 <= d <= 63:
                                result.append(CHARSET[a])
                                result.append(CHARSET[b])
                                result.append(CHARSET[c])
                                result.append(CHARSET[d])
                                found = True
                                break
                    if found:
                        break
            if found:
                break
        if not found:
            raise ValueError(f"Cannot encode bytes {chunk!r} into serial chars")
    return ''.join(result)

def keygen(name):
    """Generate a valid serial for the given name."""
    if len(name) <= 3:
        raise ValueError("Name must be longer than 3 characters")
    fn1 = first_number(name)
    fn2 = second_number(name)
    # Format the two numbers as the decoded string: "fn1|fn2"
    # ASSUMPTION: We format with enough precision but keep it short.
    # The decoded bytes must all be valid chars: '|', '-', '.', '0'-'9'
    # repr of float might use 'e' notation - avoid that
    def fmt_float(f):
        # Try integer first
        if f == int(f) and abs(f) < 1e15:
            return str(int(f))
        else:
            return f"{f:.6f}".rstrip('0').rstrip('.')
    s = f"{fmt_float(fn1)}|{fmt_float(fn2)}"
    # Validate the string contains only allowed chars
    for ch in s:
        if ch not in '|.-' and not ('0' <= ch <= '9'):
            raise ValueError(f"Float representation contains invalid char {ch!r}: {s}")
    # Encode the string as bytes
    data = s.encode('ascii')
    # Encode bytes to serial string
    serial = encode_bytes_to_serial(data)
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
