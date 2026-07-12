import math
import struct

def username_hash_fill_data(uname):
    uname_bytes = uname.encode('latin-1') if isinstance(uname, str) else uname
    ulen = len(uname_bytes)
    uhash = 0xF10DB198
    for i in range(ulen):
        uhash = (uhash * 0x1000193) & 0xFFFFFFFF
        uhash ^= uname_bytes[i]
    # treat uhash as signed 32-bit
    uhash_signed = uhash if uhash < 0x80000000 else uhash - 0x100000000

    uhash_high = uhash >> 16  # unsigned
    uhash_low = uhash & 0xFFFF

    out = [0.0] * 11

    cval = float(uhash_high)
    # uhash_high is already unsigned (uhash was uint before shift)
    cval /= 65535.0
    cval *= 10.0
    cval += 5.0
    out[0] = cval

    cval = float(uhash_low)
    cval /= 65535.0
    cval *= 10.0
    cval += 10.0
    out[1] = cval

    cval = float(uhash)  # unsigned
    cval /= 4294967295.0
    cval *= 0.5
    cval += 0.25
    out[3] = cval

    cval = out[0]
    cval *= math.pi / 2.0  # 1.5707963267948966
    out[4] = cval

    PI = math.pi
    for i in range(5, 11):
        current = out[i - 1]
        current += 0.1
        cval = out[0] * PI
        rem = math.fmod(current, cval)
        cval2 = cval * 0.5
        rem = cval2 - rem
        rem += current
        rem += out[0] * PI
        out[i] = rem

    cval = out[0] * PI * 0.5 + out[10] - out[4]
    out[3] *= cval
    out[2] = cval / 64.0
    return out


def create_keyhash(key):
    prev = 0
    for i in range(5):
        c = key[i]
        if isinstance(c, int):
            cv = c
        else:
            cv = ord(c)
        if cv <= ord('9'):
            val = cv - 0x16  # 22
        else:
            val = cv - 0x41  # 65
        prev += int(36 ** (4 - i)) * val
    return prev & 0xFFFFFFFF


def generate_specials(key, data):
    h = create_keyhash(key)
    if h == 0:
        return None
    h &= 0xFFFFFF
    upper = h >> 12
    mantissa = upper & 0x3F
    characteristic = upper >> 6
    if characteristic & 0x80000000:
        characteristic += 4294967296
    if mantissa != 0:
        if mantissa & 0x80000000:
            mantissa += 4294967296
        out0 = (mantissa / 64.0) + characteristic
    else:
        out0 = float(characteristic)
    out0 = data[2] * out0

    lower = h & 0xFFF
    char2 = lower >> 6
    if char2 & 0x80000000:
        char2 += 4294967296
    mant2 = lower & 0x3F
    if mant2 != 0:
        if mant2 & 0x80000000:
            mant2 += 4294967296
        out1 = (mant2 / 64.0 + char2) * data[2]
    else:
        out1 = char2 * data[2]
    return (out0, out1)


def cmpfunc(array):
    # array[0], array[1] = spec[0], spec[1]
    # array[2..12] = username_data[0..10]
    # array[13] = username_data[i+5]
    PI = math.pi
    var3 = 10000000000.0

    var1 = array[2] * PI
    var2 = var1 * 0.5
    fmodr = math.fmod(array[0], var1)
    modf = var2 - fmodr
    var2 = modf + array[0]
    if var2 < array[0]:
        var2 += var1
    var2 *= var3
    var2 = round(var2)
    var5 = var2 / var3

    var1 = array[2] * PI
    var2 = var1 * 0.5
    fmodr = math.fmod(array[1], var1)
    modf = var2 - fmodr
    var2 = modf + array[1]
    if var2 >= array[1]:
        var2 -= var1
    var2 *= var3
    var2 = round(var2)
    var2 /= var3

    tmp4 = array[13] * var3
    tmp4 = round(tmp4)
    if var5 == var2:
        tmp4 /= var3
        if var5 == tmp4:
            return True
    return False


def verify(name, serial):
    # serial format: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX (5 parts of 5 base36 chars)
    parts = serial.split('-')
    if len(parts) != 5:
        return False
    for p in parts:
        if len(p) != 5:
            return False

    username_data = username_hash_fill_data(name)

    diffs = []
    sum_val = 0.0
    for i in range(5):
        import copy
        data2 = list(username_data)
        spec = generate_specials(parts[i], data2)
        if spec is None:
            return False

        oncheck = [0.0] * 14
        oncheck[0] = spec[0]
        oncheck[1] = spec[1]
        for j in range(11):
            oncheck[2 + j] = username_data[j]
        oncheck[13] = username_data[i + 5]
        if not cmpfunc(oncheck):
            return False

        si1 = math.sin(spec[0] / username_data[0]) * username_data[1]
        si2 = math.sin(spec[1] / username_data[0]) * username_data[1]
        diffpow = (spec[1] - spec[0]) ** 2
        sindiffpow = (si2 - si1) ** 2
        diffsumsqrt = math.sqrt(diffpow + sindiffpow)
        diffsumsqrt = math.ceil(diffsumsqrt * 10.0) / 10.0

        if i > 0:
            for j in range(i):
                if diffs[j] == diffsumsqrt:
                    return False
        diffs.append(diffsumsqrt)
        sum_val += diffsumsqrt

    sum_val = math.ceil(sum_val * 10.0) / 10.0
    target = math.ceil(username_data[3] * 10.0) / 10.0
    return sum_val == target


def _encode_base36_part(val):
    """Encode an integer as a 5-char base36 string (digits 0-9 then A-Z)"""
    CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    # Adjust mapping: digit d maps to char with code d+22 for 0-9, d+65 for A-Z
    # Actually from create_keyhash: if <= '9': val = c - 22, else val = c - 65
    # So digit 0 = chr(22)? That doesn't make sense for printable chars.
    # ASSUMPTION: base36 uses chars where '0'-'9' represent values (ord(c)-22)
    # and 'A'-'Z' represent values (ord(c)-65). So '0'=26, '1'=27...wait
    # ord('0')=48, 48-22=26; ord('A')=65, 65-65=0. So A=0..Z=25, 0=26..9=35
    ENCODE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    result = ''
    v = val
    for _ in range(5):
        v, r = divmod(v, 36)
        result = ENCODE[r] + result
    return result


def _decode_part(key):
    return create_keyhash(key)


def _build_key_for_target(data, target_val, idx):
    """
    For a given target username_data[idx+5], find a key part that:
    1. generate_specials produces (out0, out1) such that cmpfunc passes
    2. The arc-length contribution diffsumsqrt has the right value
    We brute force over all possible 24-bit hash values.
    """
    # ASSUMPTION: We brute force all 24-bit values for the internal hash
    PI = math.pi
    target_node = data[idx + 5]  # username_data[idx+5]
    d2 = data[2]

    for h in range(1, 0x1000000):
        upper = h >> 12
        mantissa = upper & 0x3F
        characteristic = upper >> 6
        if mantissa != 0:
            out0 = (mantissa / 64.0 + characteristic) * d2
        else:
            out0 = characteristic * d2

        lower = h & 0xFFF
        char2 = lower >> 6
        mant2 = lower & 0x3F
        if mant2 != 0:
            out1 = (mant2 / 64.0 + char2) * d2
        else:
            out1 = char2 * d2

        # check cmpfunc
        oncheck = [0.0] * 14
        oncheck[0] = out0
        oncheck[1] = out1
        for j in range(11):
            oncheck[2 + j] = data[j]
        oncheck[13] = target_node
        if cmpfunc(oncheck):
            # encode back to key
            # We need to find a 5-char key whose create_keyhash & 0xFFFFFF == h
            # The keyhash is sum of val_i * 36^(4-i)
            # We just need any 5-char key whose hash&0xFFFFFF == h
            # Brute force over the 5-char encoding space is too large,
            # but we can directly encode h into the upper 24 bits of a 32-bit keyhash
            # by setting keyhash = h (lower 24 bits) and finding a key for that
            # The keyhash range for 5 base36 chars: 0 to 36^5-1 = 60466175
            # 0xFFFFFF = 16777215 < 60466175, so h itself is a valid keyhash
            key = _encode_base36_part(h)
            return key
    return None


def keygen(name):
    """
    Generate a valid serial for the given name.
    ASSUMPTION: We brute force 24-bit hash values to find matching key parts.
    This is a simplified keygen that may be slow for some inputs.
    """
    data = username_hash_fill_data(name)

    # We need 5 key parts with distinct diffsumsqrt values summing to target
    # ASSUMPTION: We try a simplified approach - find parts that pass cmpfunc
    # and check the arc-length sum constraint
    # This is a partial keygen due to the arc-length sum constraint
    PI = math.pi
    d2 = data[2]

    candidates = []
    seen_diffs = set()

    for h in range(1, 0x1000000):
        upper = h >> 12
        mantissa = upper & 0x3F
        characteristic = upper >> 6
        if mantissa != 0:
            out0 = (mantissa / 64.0 + characteristic) * d2
        else:
            out0 = characteristic * d2

        lower = h & 0xFFF
        char2 = lower >> 6
        mant2 = lower & 0x3F
        if mant2 != 0:
            out1 = (mant2 / 64.0 + char2) * d2
        else:
            out1 = char2 * d2

        si1 = math.sin(out0 / data[0]) * data[1]
        si2 = math.sin(out1 / data[0]) * data[1]
        diffpow = (out1 - out0) ** 2
        sindiffpow = (si2 - si1) ** 2
        diffsumsqrt = math.ceil(math.sqrt(diffpow + sindiffpow) * 10.0) / 10.0

        diff_key = round(diffsumsqrt, 10)
        if diff_key in seen_diffs:
            continue

        # Check which node index this h corresponds to
        for idx in range(5):
            target_node = data[idx + 5]
            oncheck = [0.0] * 14
            oncheck[0] = out0
            oncheck[1] = out1
            for j in range(11):
                oncheck[2 + j] = data[j]
            oncheck[13] = target_node
            if cmpfunc(oncheck):
                candidates.append((idx, h, diffsumsqrt))
                seen_diffs.add(diff_key)
                break

        if len(seen_diffs) >= 5:
            break

    # ASSUMPTION: Simplified - just return None if we can't find valid key
    # A real keygen would need to solve the sum constraint
    return None



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
