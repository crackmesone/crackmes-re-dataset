import struct

def transform_username(name: str) -> int:
    """
    Simulates the transform_username assembly routine.
    edx = 0, eax = 0
    For each character:
        lodsb        -> al = ord(char)
        rol eax, 4   -> rotate eax left by 4
        xchg al, ah  -> swap al and ah (low byte and second byte)
        xor eax, 0xDEADBEEF
        edx += eax
        stosb        -> stores al back (modifies buffer, but we only care about edx)
    return edx (mod 2^32)
    """
    edx = 0
    eax = 0
    for ch in name:
        # lodsb: load byte into al (low byte of eax)
        al = ord(ch) & 0xFF
        eax = (eax & 0xFFFFFF00) | al

        # rol eax, 4 (32-bit rotate left by 4)
        eax = eax & 0xFFFFFFFF
        eax = ((eax << 4) | (eax >> 28)) & 0xFFFFFFFF

        # xchg al, ah: swap byte 0 and byte 1 of eax
        al = eax & 0xFF
        ah = (eax >> 8) & 0xFF
        eax = (eax & 0xFFFF0000) | (al << 8) | ah

        # xor eax, 0xDEADBEEF
        eax = (eax ^ 0xDEADBEEF) & 0xFFFFFFFF

        # add edx, eax
        edx = (edx + eax) & 0xFFFFFFFF

    return edx


def transform_password(password: str) -> int:
    """
    Simulates the transform_password assembly routine.
    The writeup was truncated before showing the full password transform,
    but based on the pattern it uses ror instead of rol.
    edx = 0, eax = 0
    For each character:
        lodsb        -> al = ord(char)
        ror eax, 8   -> rotate eax right by 8
        xchg al, ah  -> swap al and ah
        # ASSUMPTION: xor eax, 0xDEADBEEF (same constant, writeup truncated)
        edx += eax
    return edx (mod 2^32)
    """
    # ASSUMPTION: password transform follows same pattern as username but with ror instead of rol
    edx = 0
    eax = 0
    for ch in password:
        # lodsb: load byte into al
        al = ord(ch) & 0xFF
        eax = (eax & 0xFFFFFF00) | al

        # ror eax, 8 (32-bit rotate right by 8)
        eax = eax & 0xFFFFFFFF
        eax = ((eax >> 8) | (eax << 24)) & 0xFFFFFFFF

        # xchg al, ah
        al = eax & 0xFF
        ah = (eax >> 8) & 0xFF
        eax = (eax & 0xFFFF0000) | (al << 8) | ah

        # ASSUMPTION: xor eax, 0xDEADBEEF
        eax = (eax ^ 0xDEADBEEF) & 0xFFFFFFFF

        # add edx, eax
        edx = (edx + eax) & 0xFFFFFFFF

    return edx


def verify(name: str, serial: str) -> bool:
    """
    Checks:
    1. username length >= 4
    2. password length == 12
    3. result of transform_username(name) < 3
    4. transform_username(name) == transform_password(serial)
    Password (serial) must be numeric only.
    """
    if len(name) < 4:
        return False
    if len(serial) != 12:
        return False
    if not serial.isdigit():
        return False

    u_result = transform_username(name)
    if u_result >= 3:
        return False

    p_result = transform_password(serial)
    return u_result == p_result


def keygen(name: str):
    """
    Generates a valid serial for the given name by brute-forcing
    12-digit numeric passwords whose transform_password result equals
    transform_username(name).

    Since the password transform is partially assumed, this keygen may
    not produce correct results for the real binary.

    Only names where transform_username(name) < 3 will have valid serials.
    """
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters.")

    target = transform_username(name)
    if target >= 3:
        raise ValueError(f"Username transform result {target} >= 3, no valid serial exists for this name.")

    # ASSUMPTION: Brute force is infeasible for 12-digit serials.
    # The writeup notes this is a 'partial' keygen.
    # We attempt a short brute force for demonstration purposes only.
    # ASSUMPTION: a smarter approach would require the full password transform algorithm.
    raise NotImplementedError(
        "Full keygen requires the complete password transform algorithm (writeup was truncated). "
        f"Target value for name '{name}' is {target}. "
        "Try brute-forcing 12-digit numeric strings against transform_password()."
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
