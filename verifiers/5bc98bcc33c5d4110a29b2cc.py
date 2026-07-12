# Reverse-engineered serial validation from 'undebuggable' crackme
# Based on static analysis writeup showing parent/child process interactions
# and three encrypted code blocks (check1, check2, check3).
#
# The writeup describes three password checks performed on the input.
# The full disassembly of each check block was truncated, so some details
# are filled in based on common patterns and partial information from the writeup.
#
# ASSUMPTION: The password/serial is read as 0x20 (32) bytes from stdin.
# ASSUMPTION: check1 verifies some property of the serial (e.g., length/charset check).
# ASSUMPTION: check2 verifies another property (e.g., a hash or arithmetic check).
# ASSUMPTION: check3 verifies a third property.
# The exact check algorithms are NOT fully described in the truncated writeup.
#
# What IS known from the writeup:
# - Input is read via syscall read(0, buf, 0x20) -- 32 bytes max
# - Three separate encrypted code blocks (check1_code, check2_code, check3_code)
#   are XOR-decrypted with 0x55 and executed in shared memory
# - The decrypted initial block sets up a message queue (key=0x1337),
#   shared memory (key=1337 decimal), and calls three sub-checks
# - If all checks pass, the program reads/prints a 'flag' file
#
# Since the check disassemblies were truncated and not fully described,
# we cannot implement the real check. This is a partial recovery.

def xor_decrypt(data: bytes, key: int = 0x55) -> bytes:
    """XOR-decrypt a code block as done by transfer_code()."""
    return bytes([b ^ key for b in data])


# ASSUMPTION: The three checks operate on a 32-byte serial string.
# ASSUMPTION: Based on typical keygen challenges of this style, the checks
# might verify: (1) character set, (2) a checksum/sum, (3) a hash or transform.
# None of these can be confirmed from the truncated writeup.

def check1(serial: bytes) -> bool:
    # ASSUMPTION: check1 verifies the serial has exactly 0x20 bytes
    # and possibly that each byte is printable ASCII.
    if len(serial) != 0x20:
        return False
    for b in serial:
        if b < 0x20 or b > 0x7e:
            return False
    return True


def check2(serial: bytes) -> bool:
    # ASSUMPTION: check2 performs some arithmetic check on the serial.
    # Without the full disassembly this cannot be determined.
    # Placeholder: always returns True.
    # ASSUMPTION: unknown check
    return True


def check3(serial: bytes) -> bool:
    # ASSUMPTION: check3 performs another check on the serial.
    # Without the full disassembly this cannot be determined.
    # Placeholder: always returns True.
    # ASSUMPTION: unknown check
    return True


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial for the given name.
    NOTE: The crackme appears to only take a single password/serial input
    (no separate name field is described in the writeup).
    'name' is ignored here per the writeup description.
    """
    # ASSUMPTION: serial is encoded as ASCII/latin-1
    try:
        serial_bytes = serial.encode('latin-1')
    except Exception:
        return False

    # Pad or truncate to 0x20 bytes as the program reads 0x20 bytes
    serial_bytes = serial_bytes[:0x20].ljust(0x20, b'\x00')

    return check1(serial_bytes) and check2(serial_bytes) and check3(serial_bytes)


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    ASSUMPTION: Since check2 and check3 are unknown, this only satisfies
    the known constraints (length=32, printable ASCII).
    """
    # ASSUMPTION: any 32 printable ASCII characters might work if
    # check2 and check3 have no further constraints.
    serial = 'A' * 0x20
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
