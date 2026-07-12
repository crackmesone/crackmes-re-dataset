import hashlib
import random as _random

# This crackme uses a .NET-style GetHashCode on the name, then performs
# big-integer arithmetic (likely ECC or RSA-like via MIRACL library).
# The keygen source shows:
#   1. Compute GetHashCode(name) - a .NET-style hash
#   2. Generate a random big integer and use it in a signature scheme
#   3. Produce a serial from the result
#
# The writeup was truncated before the full crypto algorithm was shown.
# We can only fully reconstruct GetHashCode and the hash step.
# The actual signature/verification math is NOT shown in the truncated writeup.

def _to_unicode_bytes(s):
    """Simulate .NET's UTF-16LE encoding (null byte after each char, null terminator)."""
    result = bytearray()
    for c in s:
        result.append(ord(c) & 0xFF)
        result.append(0)
    result.append(0)
    return bytes(result)

def get_hash_code(s):
    """Replicate the .NET-style GetHashCode from the keygen source."""
    unicode_bytes = _to_unicode_bytes(s)
    # Read as array of 32-bit ints (little-endian)
    import struct
    # Pad to multiple of 4
    padded = unicode_bytes + b'\x00' * (4 - len(unicode_bytes) % 4)
    num_ints = len(padded) // 4
    ints = list(struct.unpack_from('<' + 'I' * num_ints, padded))

    num  = 0x15051505
    num2 = 0x15051505

    # Use signed 32-bit arithmetic
    def to_signed32(x):
        x = x & 0xFFFFFFFF
        if x >= 0x80000000:
            x -= 0x100000000
        return x

    def to_uint32(x):
        return x & 0xFFFFFFFF

    ptr = 0  # index into ints array
    i = len(s)
    while i > 0:
        # num = (((num << 5) + num) + (num >> 0x1b)) ^ ints[ptr]
        num = to_signed32(to_signed32((to_signed32(num << 5) + num)) + to_signed32(to_uint32(num) >> 0x1b))
        num = to_signed32(num ^ to_signed32(ints[ptr]))
        if i <= 2:
            break
        num2 = to_signed32(to_signed32((to_signed32(num2 << 5) + num2)) + to_signed32(to_uint32(num2) >> 0x1b))
        num2 = to_signed32(num2 ^ to_signed32(ints[ptr + 1]))
        ptr += 2
        i -= 4

    result = to_signed32(num + to_signed32(num2 * to_signed32(0x5d588b65)))
    return result

# ASSUMPTION: The serial validation is based on an ECC or discrete-log signature
# scheme using the MIRACL library. The exact curve parameters, modulus, generator,
# and public key are embedded in the crackme binary and NOT provided in the writeup.
# Without those parameters, we cannot implement verify() or keygen() fully.

# ASSUMPTION: The serial format is likely a hex or decimal string of big-integer data.
# ASSUMPTION: The name hash (get_hash_code) feeds into the signature as the message.

def verify(name: str, serial: str) -> bool:
    """
    Stub verifier - cannot be fully implemented because the crypto parameters
    (curve/modulus, generator point, public key) from the crackme binary are
    not provided in the available writeup.
    """
    # ASSUMPTION: get_hash_code(name) is used as the message to verify
    h = get_hash_code(name)
    # ASSUMPTION: serial encodes a signature (r, s) or similar
    # Without the public key and curve parameters, we cannot verify.
    raise NotImplementedError(
        "Cannot verify: crypto parameters not available from truncated writeup. "
        f"Name hash = {h:#010x}"
    )

def keygen(name: str) -> str:
    """
    Stub keygen - cannot be fully implemented because the random big-integer
    signing math requires the private key and curve parameters from the binary.
    """
    h = get_hash_code(name)
    raise NotImplementedError(
        "Cannot generate serial: private key and curve parameters not available. "
        f"Name hash = {h:#010x}"
    )


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
