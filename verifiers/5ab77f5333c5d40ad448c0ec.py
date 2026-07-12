# Reverse-engineered keygen for ZaiRoN crackme1
# Based on j!m's writeup
#
# PART 1: Serial structure is XXAXXAXXA
#   where X in '0'-'9' (digits) and A in 'A'-'E'
#   The 9-char serial encodes 3 groups of (x, y, z)
#   After parsing:
#     digits 0-9 -> value 0-9  (subtract 0x30)
#     letters A-E -> value 10-14 (subtract 0x37)
#   Positions: 0=x, 1=y, 2=z, 3=x, 4=y, 5=z, 6=x, 7=y, 8=z
#   z appears at positions 2, 5, 8 (can be 'A'-'E' i.e. 10-14)
#   x,y at other positions must be digits 0-9
#
# PART 2: The writeup describes a second verification stage involving
#   4 tables (table1-table4) at various offsets, each 16 rows of 8 bytes,
#   plus a table4 at 0x401337. The serial is padded/extended to 18 chars.
#   This part was only partially described (writeup was truncated).
#   ASSUMPTION: We only implement Part 1 fully; Part 2 is marked incomplete.

def _parse_serial(serial):
    """Parse 9-char serial string into list of integer values.
    Returns list of 9 ints or None on failure."""
    if len(serial) != 9:
        return None
    values = []
    for i, ch in enumerate(serial):
        b = ord(ch)
        if i in (2, 5, 8):
            # Must be digit 0-9 or letter A-E
            if 0x30 <= b <= 0x39:
                values.append(b - 0x30)
            elif 0x41 <= b <= 0x45:
                values.append(b - 0x37)
            else:
                return None
        else:
            # Must be digit 0-9
            if 0x30 <= b <= 0x39:
                values.append(b - 0x30)
            else:
                return None
    return values


def _f(x, y):
    """f(x,y) = x + 3y + y^2 + x^2 + 2xy = (x+y)^2 + (x+y) + 2y"""
    return x + 3*y + y*y + x*x + 2*x*y


def _check_part1(serial_str, name):
    """Check Part 1 of the validation against the first 3 chars of name."""
    values = _parse_serial(serial_str)
    if values is None:
        return False
    # Only first 3 chars of name are used
    name_bytes = [ord(c) for c in name[:3]]
    if len(name_bytes) < 3:
        # ASSUMPTION: name must be at least 3 chars; pad or fail
        return False
    for group_idx in range(3):
        x = values[group_idx * 3 + 0]
        y = values[group_idx * 3 + 1]
        z = values[group_idx * 3 + 2]
        fxy = _f(x, y)
        # fxy must be even
        if fxy % 2 != 0:
            return False
        k = fxy // 2
        # k <= 18
        if k > 18:
            return False
        # The check: floor((x + 3y + y^2 + x^2 + 2xy) / 2) * 14 + z == name_char
        # Using 8-bit arithmetic (al)
        computed = ((k * 14) + z) & 0xFF
        if computed != name_bytes[group_idx]:
            return False
    return True


def verify(name, serial):
    """Verify name/serial pair.
    Part 1 is fully implemented.
    Part 2 (table-based second stage) is NOT implemented due to truncated writeup.
    ASSUMPTION: Only Part 1 is checked here; real crackme also requires Part 2.
    """
    if len(serial) < 9:
        return False
    serial9 = serial[:9]
    return _check_part1(serial9, name)


def _find_xy_for_k(k):
    """Find (x,y) with x,y in 0..9 such that f(x,y) = 2*k."""
    for x in range(10):
        for y in range(10):
            if _f(x, y) == 2 * k:
                return (x, y)
    return None


def _encode_value(v, allow_letter=False):
    """Encode an integer value back to its serial character."""
    if 0 <= v <= 9:
        return chr(v + 0x30)
    elif allow_letter and 10 <= v <= 14:
        return chr(v + 0x37)
    return None


def keygen(name):
    """Generate a valid 9-char serial for the given name (Part 1 only).
    ASSUMPTION: Part 2 second-stage table check is not implemented;
    the generated serial may not fully pass the real crackme.
    """
    if len(name) < 3:
        raise ValueError("Name must be at least 3 characters")
    serial = ''
    for i in range(3):
        C = ord(name[i])
        # z = C mod 14, k = C // 14
        k = C // 14
        z = C % 14
        if k > 18:
            raise ValueError(f"Name character '{name[i]}' (ascii {C}) too large")
        pair = _find_xy_for_k(k)
        if pair is None:
            raise ValueError(f"No valid (x,y) found for k={k}")
        x, y = pair
        xc = _encode_value(x, allow_letter=False)
        yc = _encode_value(y, allow_letter=False)
        # z at position 2/5/8 can be digit or A-E
        zc = _encode_value(z, allow_letter=True)
        if xc is None or yc is None or zc is None:
            raise ValueError(f"Cannot encode values x={x} y={y} z={z}")
        serial += xc + yc + zc
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
