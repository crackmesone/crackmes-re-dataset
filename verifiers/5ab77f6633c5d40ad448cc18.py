import re

def name_hash(name: str) -> int:
    """Compute the name algo value as described in the writeups.
    algo = 0
    for i, ch in enumerate(name):
        algo = (algo + ord(ch)) * i
    Then take al (low byte), then remainder mod 15.
    Returns (al_value, remainder) where remainder is the key checksum target.
    """
    algo = 0
    for i, ch in enumerate(name):
        algo = (algo + ord(ch)) * i
    al = algo & 0xFF
    remainder = al % 15
    return al, remainder


def count_odd_shifts(value: int) -> int:
    """Count the number of times al is odd after repeated shr eax,1.
    This matches the assembly loop:
        shr eax, 1
        test al, 1
        if al & 1: inc ecx
        if eax != 0: loop
    """
    ecx = 0
    eax = value & 0xFFFFFFFF
    # ASSUMPTION: ecx starts at 0 (confirmed by xor ecx,ecx before serial loop)
    while True:
        eax = (eax >> 1) & 0xFFFFFFFF
        if eax & 1:
            ecx += 1
        if eax == 0:
            break
    return ecx


def serial_parts_to_combined(s1: str, s2: str, s3: str, s4: str):
    """Convert 4 hex serial parts (each 4 hex digits) to combined values.
    The program reads the 4 boxes and calls a hex-string-to-int function (call 00401000)
    then combines:
      combined1 = (box1_val << 16) | box4_val   -> [ebp-14]
      combined2 = (box3_val << 16) | box2_val   -> [ebp-10]
    ASSUMPTION: call 00401000 converts the hex string to integer, masked with 0xFFFF.
    """
    def hex_str_to_int(s):
        s = s.strip()
        try:
            return int(s, 16) & 0xFFFF
        except ValueError:
            return 0

    v1 = hex_str_to_int(s1)
    v2 = hex_str_to_int(s2)
    v3 = hex_str_to_int(s3)
    v4 = hex_str_to_int(s4)

    combined1 = ((v1 << 16) | v4) & 0xFFFFFFFF
    combined2 = ((v3 << 16) | v2) & 0xFFFFFFFF
    return combined1, combined2


def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair.
    Serial format: XXXX-YYYY-ZZZZ-WWWW (4 groups of 4 hex digits separated by dashes)
    """
    # Parse serial
    parts = serial.strip().split('-')
    if len(parts) != 4:
        return False
    if any(len(p) != 4 for p in parts):
        return False

    s1, s2, s3, s4 = parts

    # Step 1: compute name hash
    al_val, target = name_hash(name)

    # The serial is rejected if target == 0 (remainder is 0 mod 15 means name hash divisible by 15)
    # From writeup: 'test esi, esi / jbe 004012CE' means if esi==0 it's bad
    if target == 0:
        return False

    # Step 2: combine serial parts
    combined1, combined2 = serial_parts_to_combined(s1, s2, s3, s4)

    # Step 3: xor the two combined values
    xored = (combined1 ^ combined2) & 0xFFFFFFFF

    # Step 4: count odd bits after shifts
    serial_checksum = count_odd_shifts(xored)

    # Step 5: compare serial_checksum with target
    return serial_checksum == target


def keygen(name: str) -> str:
    """Generate a valid serial for the given name.
    Strategy: pick combined1 = seed XOR combined2 such that count_odd_shifts gives target.
    We need to find a 32-bit value X such that count_odd_shifts(X) == target.
    Then set combined1 = combined2 ^ X, and decompose back to serial parts.
    """
    al_val, target = name_hash(name)
    if target == 0:
        raise ValueError("No serial exists for this name (hash divisible by 15). Try another name.")

    # From OorjaHalT's table: for target T, seed = (1 << T) - 1 (all-ones pattern)
    # This gives exactly T odd values when shifted.
    # Verify: for seed = (2^T - 1), the value has T '1' bits in positions 0..T-1.
    # Shifting right repeatedly: first T shifts expose those bits one by one as al&1.
    # ASSUMPTION: using seed = (2^target - 1) as the XOR value between combined1 and combined2
    seed = (1 << target) - 1

    # Choose combined2 = 0x00000000, combined1 = seed
    # But we need to ensure parts are valid 4-hex-digit values
    combined1 = seed & 0xFFFFFFFF
    combined2 = 0x00000000

    # Decompose combined1 = (box1 << 16) | box4
    box1 = (combined1 >> 16) & 0xFFFF
    box4 = combined1 & 0xFFFF
    # Decompose combined2 = (box3 << 16) | box2
    box3 = (combined2 >> 16) & 0xFFFF
    box2 = combined2 & 0xFFFF

    serial = '%04X-%04X-%04X-%04X' % (box1, box2, box3, box4)
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
