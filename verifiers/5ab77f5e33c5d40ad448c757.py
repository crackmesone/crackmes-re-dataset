import math
import struct

def first_func(name: str) -> int:
    """
    Computes the 'FirstFunc' value from the name.
    Mimics the assembly: sum chars, then multiply by 0x51EB851F (signed 64-bit),
    shift right, subtract to get result.
    """
    # sum of char values (signed bytes)
    total = 0
    for c in name:
        # treat as signed byte
        b = ord(c)
        if b >= 128:
            b -= 256
        total += b

    # imul signed 64-bit: total * 0x51EB851F
    product = total * 0x51EB851F

    # edx:eax - edx is high 32 bits
    # In Python we simulate signed 64-bit
    # product as signed 64-bit
    product_signed = product
    # sign extend to handle negatives
    if product_signed >= 2**63:
        product_signed -= 2**64
    elif product_signed < -(2**63):
        product_signed += 2**64

    # d = (product >> 32) >> 4  (arithmetic shift)
    d = product_signed >> 36  # >> 32 then >> 4

    # sum SAR 0x1F  (sign bit of sum)
    s = total >> 31

    result = d - s
    return result


def gen_char(f1: int) -> str:
    """
    Maps a computed integer value to a character in [a-z] range.
    Mirrors the assembly loop logic.
    """
    # Treat as signed 32-bit for modular arithmetic
    val = f1 & 0xFFFFFFFF
    if val >= 0x80000000:
        val -= 0x80000000  # ASSUMPTION: treat as unsigned for looping

    # Loop 1: while val <= '@'(0x40) AND val <= 'Y'(0x59): val += 0x1A
    # Assembly: if f1 > '@' OR f1 > 'Y' break, else add 0x1A
    # Condition to stay: NOT(f1 > '@') AND NOT(f1 > 'Y')
    # i.e., f1 <= 0x40 AND f1 <= 0x59  => f1 <= 0x40
    # ASSUMPTION: interpreted as: keep adding while val < 'a'(0x61)
    for _ in range(10000):
        if val > 0x40 or val > 0x59:
            break
        val += 0x1A

    # Loop 2: while 'Z'(0x5A) < val <= '`'(0x60): val += 0x1A
    for _ in range(10000):
        if val > 0x60 or val <= 0x5A:
            break
        val += 0x1A

    # Loop 3: while val > 'z'(0x7A): val -= 0x1A
    for _ in range(10000):
        if val <= 0x7A:
            break
        val -= 0x1A

    # movsx al: take low byte as signed
    byte_val = val & 0xFF
    if byte_val >= 128:
        byte_val -= 256
    return chr(byte_val & 0xFF)


def compute_serial_char(name: str, i: int) -> str:
    """
    For position i in the serial, compute the expected character.
    Based on the FPU section of the writeup.
    """
    n = len(name)
    PI = math.pi

    f2 = first_func(name)
    # f1 = f2 + name[i] (last char of name, based on 004017EB)
    # ASSUMPTION: lpName[i] here refers to name[i] where i is the serial index
    # The writeup says 'i' is the outer loop iterator for serial chars
    name_char_idx = i % n  # ASSUMPTION: wrap around name index
    f1 = f2 + ord(name[name_char_idx])

    # ch = lpName[k-1] XOR i
    # ASSUMPTION: k-1 refers to last char of name
    k = n
    ch = ord(name[k - 1]) ^ i

    # dfp = ch * pi
    dfp = ch * PI

    # dfp = dfp / (i+1)  -- j = i+1 based on 'inc eax' before fdivp
    j = i + 1
    dfp = dfp / j

    # dfp = dfp + f1
    dfp = dfp + f1

    # Convert to int using truncation toward -inf (FPU round-toward-zero with 0C00 CWR = truncate)
    import ctypes
    var1 = int(dfp)  # truncate
    f1 = var1

    # f1 = f1 - (nLen XOR 0x10)
    nLen = n
    f1 = f1 - (nLen ^ 0x10)

    # if (f1 AND 1) == 0: f1 = neg(f1) = -f1
    if (f1 & 1) == 0:
        f1 = -f1

    return gen_char(f1)


def verify(name: str, serial: str) -> bool:
    """
    Verifies that the serial is valid for the given name.
    Serial must be exactly 20 characters long.
    """
    if len(serial) != 20:
        return False
    for i in range(20):
        expected = compute_serial_char(name, i)
        if serial[i] != expected:
            return False
    return True


def keygen(name: str) -> str:
    """
    Generates a valid serial for the given name.
    """
    serial = ''
    for i in range(20):
        serial += compute_serial_char(name, i)
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
