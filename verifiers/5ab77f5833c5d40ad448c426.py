import struct

def float_to_bytes(f):
    """Pack a float64 into 8 bytes and return low 4 bytes and high 4 bytes."""
    b = struct.pack('<d', f)
    lo = struct.unpack('<I', b[0:4])[0]
    hi = struct.unpack('<I', b[4:8])[0]
    return lo, hi

def int_to_float_hi(n):
    """Get the high 4 bytes of the IEEE 754 double representation of integer n."""
    # FILD loads integer n into ST(0), FSTP stores as double
    lo, hi = float_to_bytes(float(n))
    return lo, hi

def required_name_len():
    # From disassembly:
    # cmp dword ptr [ebp-5C], 40240000
    # je LOOSER  --> so name length must NOT produce high dword 0x40240000
    # 0x40240000 as high dword of double means:
    # struct.pack('>I', 0x40240000) + b'\x00\x00\x00\x00' -> let's find which integer gives high=0x40240000
    # double with high=0x40240000, low=0: 0x4024000000000000
    bad_val = struct.unpack('<d', struct.pack('<II', 0x00000000, 0x40240000))[0]
    # bad_val = 10.0, so name length of 10 is BAD (jumps to looser)
    # Actually re-reading: 'equal? LOOSER!' means len==10 is BAD
    # ASSUMPTION: name length must not be 10
    return int(bad_val)  # returns 10

def required_code_len():
    # From disassembly:
    # cmp dword ptr [ebp-5C], 40100000
    # je go on  --> so code length MUST produce high dword 0x40100000
    # 0x40100000 as high dword: 0x4010000000000000
    good_val = struct.unpack('<d', struct.pack('<II', 0x00000000, 0x40100000))[0]
    # good_val = 4.0, so code length must be 4
    return int(good_val)  # returns 4

# Verify the length-based checks from the disassembly
BAD_NAME_LEN = required_name_len()   # 10 - name must NOT be this length
REQUIRED_CODE_LEN = required_code_len()  # 4 - code MUST be this length

# ASSUMPTION: The writeup was truncated and only reveals the length checks fully.
# The name check: name length must not equal 10 (jump to looser if equal).
# The code check: code length must equal 4 (jump forward if equal).
# Further serial arithmetic/checks beyond length are NOT recoverable from truncated text.
# The 'special' field check is also unknown.

def _check_name_len(name):
    n = len(name)
    lo, hi = int_to_float_hi(n)
    # cmp lo with 0 (edi=0): must be 0 for a whole integer length
    # cmp hi with 0x40240000: if equal -> looser
    if lo != 0:
        # ASSUMPTION: non-zero low bytes means the cmp falls through to jne branch (not looser)
        pass
    if lo == 0 and hi == 0x40240000:
        return False  # name length == 10, loseer
    return True

def _check_code_len(code):
    n = len(code)
    lo, hi = int_to_float_hi(n)
    if lo == 0 and hi == 0x40100000:
        return True  # code length == 4, proceed
    return False

def verify(name, serial, special=''):
    """
    Verify name/serial/special against the crackme algorithm.
    WARNING: Only the length checks are recovered. The actual serial arithmetic
    beyond these checks is unknown due to truncated writeup.
    """
    # Check 1: name length must not be 10
    if not _check_name_len(name):
        return False
    # Check 2: code (serial) length must be 4
    if not _check_code_len(serial):
        return False
    # ASSUMPTION: Additional checks on serial digits/arithmetic exist but are
    # not recoverable from the truncated writeup. We cannot fully validate here.
    # ASSUMPTION: The 'special' field has additional checks not described.
    return True  # Length checks pass; further checks unknown

def keygen(name):
    """
    Generate a candidate serial for the given name.
    Only length constraints are known: name != 10 chars, serial = 4 chars.
    ASSUMPTION: The actual serial value computation is unknown (writeup truncated).
    Returns a 4-character placeholder that satisfies the length check.
    """
    if len(name) == 10:
        raise ValueError('Name must not be exactly 10 characters long.')
    # ASSUMPTION: Any 4-char serial passes the length gate; real arithmetic unknown.
    return '1234'


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
