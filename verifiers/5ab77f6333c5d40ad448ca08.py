# Substitutions Keygenme by MR.HAANDI - Partial Reconstruction
# Based on writeup by s3Rious (22/09/2013)
# The writeup was truncated, so portions of the algorithm are reconstructed
# from the assembly fragments visible.

# From the writeup:
# memcpy( &s1, "Are you tricked?", 16 );
# memcpy( &s2, "YES!", 4 );
#
# Then a loop starting at 0040119F iterates over a buffer at 0x438C50
# ESI = &b_438c50 (negated: esi = -b_438c50 used as counter/offset trick)
# EDX = i = 0 (loop counter)
# MOVZX EBX, BYTE PTR DS:[EDX+438C50]  => load byte from buffer
# XOR ... (truncated)
#
# The crackme is called "substitutions" suggesting a substitution cipher
# is applied to either the name or serial.

# ASSUMPTION: The algorithm reads the username from a dialog edit control,
# applies some transformation (substitution/XOR based), and compares
# against the serial entered.

# ASSUMPTION: Based on the name 'substitutions' and the assembly showing
# a byte-by-byte loop with XOR operations over a buffer at 438C50,
# the serial is likely derived from the name via a substitution table
# or XOR with a key derived from the strings "Are you tricked?" and "YES!".

# Known constants from writeup:
S1 = b"Are you tricked?"
S2 = b"YES!"


def _transform_byte(b, index):
    """ASSUMPTION: XOR-based substitution seen in assembly fragment.
    The exact operation after MOVZX EBX was truncated.
    Using XOR with S1 cyclically as a guess."""
    # ASSUMPTION: XOR with S1 cyclically
    return b ^ S1[index % len(S1)]


def _transform_name(name: str) -> bytes:
    """ASSUMPTION: Name bytes are transformed via substitution table."""
    name_bytes = name.encode('utf-16-le')  # ASSUMPTION: wide char (DialogBoxParamW used)
    result = bytearray()
    for i, b in enumerate(name_bytes):
        result.append(_transform_byte(b, i))
    return bytes(result)


def verify(name: str, serial: str) -> bool:
    """ASSUMPTION: Serial is the hex-encoded transformed name,
    or some derivative. This is a guess since the writeup was truncated."""
    # ASSUMPTION: serial is compared against transformed name bytes as hex string
    try:
        transformed = _transform_name(name)
        expected = transformed.hex().upper()
        return serial.strip().upper() == expected
    except Exception:
        return False


def keygen(name: str) -> str:
    """Generate a serial for the given name.
    ASSUMPTION: Serial = hex of XOR(name_utf16le, 'Are you tricked?' cyclically)"""
    transformed = _transform_name(name)
    return transformed.hex().upper()



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
