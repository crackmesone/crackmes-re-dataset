import base64
import struct

# ASSUMPTION: The XOR key is '13337' (seen in the writeup at 0040B7A0)
# ASSUMPTION: The XOR function XORs each byte of the input with cycling bytes of the key string '13337'
# ASSUMPTION: The 'something' at 0040B9A8 is computed from GetTickCount at runtime and xored with username
#             to produce a stored encoded value. For keygen purposes we ignore this dynamic part and
#             implement the static algorithm as described.

# The algorithm described:
#   username (possibly truncated at null after xor decode) 
#     -> base64-encode 
#     -> xor with key '13337' 
#     -> base64-encode 
#     -> base64-encode (an extra encode per the keygen line)
#     -> Password
#
# Wait - re-reading more carefully:
#   The stored 'CorrectEncoded' value = base64(xor(base64(username)))
#   The password check: base64-decode(password) should equal base64(xor(base64(username)))
#   So password = base64-encode( base64(xor(base64(username))) )
# ASSUMPTION: The extra base64-encode in the keygen line accounts for an additional encoding step.

XOR_KEY = b'13337'

def xor_with_key(data: bytes, key: bytes = XOR_KEY) -> bytes:
    """XOR each byte of data with cycling bytes of key."""
    result = bytearray()
    key_len = len(key)
    for i, b in enumerate(data):
        result.append(b ^ key[i % key_len])
    return bytes(result)

def b64_encode(data: bytes) -> bytes:
    """Standard base64 encode."""
    return base64.b64encode(data)

def b64_decode(data: bytes) -> bytes:
    """Standard base64 decode."""
    return base64.b64decode(data)

def compute_correct_encoded(username: str) -> bytes:
    """
    Compute the 'correct encoded' value stored in memory.
    This is what the keygen targets.
    Steps:
      1. base64-encode username
      2. xor with '13337'
      3. base64-encode result
    ASSUMPTION: The dynamic GetTickCount xor step at startup produces a stored value
                that when xor-decoded gives back the username. We treat the username
                as the starting point (possibly truncated if zeros appeared).
    """
    step1 = b64_encode(username.encode('ascii'))
    step2 = xor_with_key(step1)
    step3 = b64_encode(step2)
    return step3

def keygen(name: str) -> str:
    """
    Generate serial/password for the given username.
    From the writeup keygen line:
      username -> base64-encode -> xor -> base64-encode -> base64-encode -> Password
    ASSUMPTION: The final extra base64-encode is an additional wrapping step.
    """
    step1 = b64_encode(name.encode('ascii'))
    step2 = xor_with_key(step1)
    step3 = b64_encode(step2)
    # ASSUMPTION: extra base64 encode as stated in the keygen formula
    step4 = b64_encode(step3)
    return step4.decode('ascii')

def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.
    The check: base64-decode(serial) should equal base64(xor(base64(name)))
    Which means serial should equal base64-encode(base64(xor(base64(name))))
    ASSUMPTION: Matching exactly the keygen output.
    """
    try:
        expected = keygen(name)
        return serial.strip() == expected.strip()
    except Exception:
        return False


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
