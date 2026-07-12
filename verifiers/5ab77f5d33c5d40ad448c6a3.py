# CruddMe 3.0 serial check reconstruction
# Based on partial writeup - the loop was truncated before completion
# The writeup shows the beginning of the serial check algorithm

def _compute_name_hash(name: str) -> int:
    """
    Reconstructed from the assembly loop:
        lea ebx, ds:403494h       ; ebx -> name buffer
        movzx ecx, byte_40355C    ; ecx = len
        xor edi, edi              ; edi = 0
    loop_4018B1:
        movzx eax, byte ptr [ebx] ; eax = current char
        mul ecx                   ; eax = eax * ecx
        add edi, eax              ; edi += eax * ecx
        inc ebx                   ; next char
        dec ecx                   ; decrement counter
        cmp ecx, 0
        (loop condition - assumed jnz loop_4018B1)
    """
    # ASSUMPTION: loop continues while ecx != 0 (jnz back to loop_4018B1)
    # ASSUMPTION: ecx starts at len and decrements, so last char is multiplied by 1
    # ASSUMPTION: result is stored in edi as a 32-bit value
    name_bytes = name.encode('ascii', errors='replace')
    n = len(name_bytes)
    ecx = n
    edi = 0
    for i, ch in enumerate(name_bytes):
        eax = ch  # movzx eax, byte ptr [ebx]
        eax = (eax * ecx) & 0xFFFFFFFF  # mul ecx (32-bit)
        edi = (edi + eax) & 0xFFFFFFFF  # add edi, eax
        ecx -= 1  # dec ecx
        if ecx == 0:
            break
    return edi


def _format_serial(value: int) -> str:
    """
    ASSUMPTION: The serial is the decimal or hex string representation of the hash.
    The writeup was truncated before showing how the computed value is compared
    to the entered serial. Common patterns: decimal string, hex string, or
    grouped with dashes.
    """
    # ASSUMPTION: serial is decimal representation of the 32-bit hash
    return str(value)


def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair for CruddMe 3.0.
    WARNING: Algorithm is only partially recovered - the writeup was truncated
    before showing how the hash is compared to the serial.
    """
    if not name:
        return False
    # ASSUMPTION: max name length is 0x12 (18) chars based on GetWindowTextA call
    name = name[:18]
    computed = _compute_name_hash(name)
    # ASSUMPTION: serial is compared as decimal string of computed hash
    try:
        serial_stripped = serial.strip()
        return int(serial_stripped) == computed
    except ValueError:
        pass
    # ASSUMPTION alternative: hex comparison
    try:
        return int(serial_stripped, 16) == computed
    except ValueError:
        return False


def keygen(name: str) -> str:
    """
    Generate a serial for the given name.
    ASSUMPTION: serial is decimal string of hash value.
    """
    name = name[:18]  # ASSUMPTION: max 18 chars
    computed = _compute_name_hash(name)
    return _format_serial(computed)



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
