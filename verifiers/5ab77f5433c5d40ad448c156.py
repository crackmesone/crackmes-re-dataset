import hashlib
import struct

def verify(name: str, serial: str) -> bool:
    """Check if serial matches the expected value for name."""
    if len(name) <= 6:
        return False
    if len(name) >= 30:
        return False
    expected = keygen(name)
    return serial.upper() == expected.upper()


def keygen(name: str) -> str:
    """
    Generate the serial for a given name.

    Algorithm (from the C++ keygen writeup):
    1. Compute SHA-256 of the name.
    2. Extract the 8 32-bit words H[0]..H[7] from the SHA-256 state
       (these are the big-endian words as stored internally after the digest).
    3. Compute:
         dwPart2 = H[6] + H[4] + H[2] + H[0]   (all mod 2^32)
         dwPart1 = H[7] + H[5] + H[3] + H[1]   (all mod 2^32)
    4. Serial = "%08X%08X" % (dwPart1, dwPart2)

    Note: The C++ code uses 'long' (signed 32-bit on x86 Windows) for intermediate
    arithmetic but the final printf uses %08X which just prints the low 32 bits,
    so we take values mod 2^32.
    """
    if len(name) <= 6 or len(name) >= 30:
        raise ValueError("Name must be between 7 and 29 characters (inclusive).")

    # Compute standard SHA-256
    digest = hashlib.sha256(name.encode('latin-1')).digest()

    # Unpack as 8 big-endian 32-bit unsigned integers (this is the standard SHA-256 output)
    H = list(struct.unpack('>8I', digest))

    # From the C++ keygen:
    #   edx = H[6]; eax = H[4]; ebx = H[2]; ecx = H[0]
    #   edx += eax; eax = H[7]; edx += ebx; ebx = H[5]
    #   edx += ecx; ecx = H[1]
    #   dwPart2 = edx   => H[6]+H[4]+H[2]+H[0]
    #
    #   edx = H[3]
    #   eax += ebx; eax += edx; eax += ecx
    #   => eax = H[7]+H[5]+H[3]+H[1]
    #   dwPart1 (eax) = H[7]+H[5]+H[3]+H[1]
    #
    # printf("%08X%08X", eax, dwPart2)

    MASK = 0xFFFFFFFF

    dwPart2 = (H[6] + H[4] + H[2] + H[0]) & MASK
    dwPart1 = (H[7] + H[5] + H[3] + H[1]) & MASK

    serial = "%08X%08X" % (dwPart1, dwPart2)
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
