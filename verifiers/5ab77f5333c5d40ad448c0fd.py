import math
import decimal

def compute_serial(name: str) -> str:
    # Step 1: Build hex string from ASCII values of each character
    text2 = ""
    for ch in name:
        num2 = ord(ch)
        # Format as uppercase hex without '0x' prefix
        hex_str = format(num2, 'X')
        text2 += hex_str

    # Step 2: Reverse the hex string
    text4 = text2[::-1]

    # Step 3: Truncate to 9 characters if longer
    if len(text4) > 9:
        text4 = text4[:9]

    # Step 4: Convert to integer (decimal parse - will fail if hex chars A-F present)
    value2 = int(text4)  # This is a decimal parse, so text4 must be all digits 0-9

    # Step 5: Raise name length to the power of 3
    value3 = float(len(name)) ** 3.0

    # Step 6: Multiply and round
    d = decimal.Decimal(value2)
    d2 = round(d * decimal.Decimal(value3), 0)

    return str(int(d2))


def verify(name: str, serial: str) -> bool:
    if len(name) < 4:
        return False
    if len(serial) < 1:
        return False

    # Serial must be parseable as a double
    try:
        float(serial)
    except ValueError:
        return False

    try:
        expected = compute_serial(name)
    except Exception:
        # Some names cause exceptions (e.g., names whose reversed hex contains A-F)
        return False

    # Compare as decimals (matching the .NET Convert.ToDecimal(Convert.ToDouble(...)) comparison)
    try:
        return decimal.Decimal(serial.strip()) == decimal.Decimal(expected)
    except Exception:
        return False


def keygen(name: str) -> str:
    """
    Generate the serial for a given name.
    Raises ValueError if the name is invalid or produces hex chars in the reversed string.
    """
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters")
    try:
        return compute_serial(name)
    except Exception as ex:
        raise ValueError(f"Name not valid (likely contains hex chars A-F in reversed string): {ex}")



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
