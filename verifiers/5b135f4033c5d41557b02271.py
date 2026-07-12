import ctypes
import struct

def _rol32(val, n):
    val = val & 0xFFFFFFFF
    n = n & 31
    return ((val << n) | (val >> (32 - n))) & 0xFFFFFFFF

def algo_on_kd0(kd, div):
    rem = kd[0] % div
    rolled = _rol32(kd[0], 0x10)
    rolled ^= rem
    kd[0] = (rolled * 0x1000193) & 0xFFFFFFFF
    return rem

def stage_1(username, kd):
    ul = len(username)
    kd[0] = 0x811c9dc5
    for i in range(ul):
        kd[0] ^= username[i]
        kd[0] = (kd[0] * 0x1000193) & 0xFFFFFFFF
    for i in range(4):
        rem = algo_on_kd0(kd, 0x01000193)
        rem = (rem + 0x1000193) & 0xFFFFFFFF
        kd[i + 1] = rem
        rem = algo_on_kd0(kd, 0x7fffffff)
        rem = (rem + 0x7FFFFFFF) & 0xFFFFFFFF
        kd[i + 5] = rem

def stage_2(username, kd):
    ul = len(username)
    abc = b'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for i in range(ul):
        c = username[i]
        anded = [0] * 8
        anded[0] = c
        anded[1] = c & 0x1
        anded[2] = c & 0x2
        anded[3] = c & 0x4
        anded[4] = c & 0x8
        anded[5] = c & 0x10
        anded[6] = c & 0x20
        anded[7] = c & 0x40
        if anded[1] or anded[2] or anded[3] or anded[4]:
            rem = algo_on_kd0(kd, 0xff)
            anded[0] ^= rem
            anded[0] &= 0xFF
        for j in range(4):
            if anded[1]:
                rem = algo_on_kd0(kd, 0xff)
                xrd = rem ^ anded[0]
                kd[j + 5] = (kd[j + 5] + xrd) & 0xFFFFFFFF
            if anded[2]:
                dc = anded[0]
                rem = algo_on_kd0(kd, 0xff)
                dc ^= rem
                kd[j + 5] = (kd[j + 5] - dc) & 0xFFFFFFFF
            if anded[3]:
                rem = algo_on_kd0(kd, 0xff)
                kd[j + 5] = kd[j + 5] ^ (rem ^ anded[0])
                kd[j + 5] &= 0xFFFFFFFF
            if anded[4]:
                rem = algo_on_kd0(kd, 0xff)
                kd[j + 5] = kd[j + 5] | (rem ^ anded[0])
                kd[j + 5] &= 0xFFFFFFFF
            if anded[5]:
                kd[j + 5] = (kd[j + 5] + anded[0]) & 0xFFFFFFFF
            if anded[6]:
                kd[j + 5] = (kd[j + 5] - anded[0]) & 0xFFFFFFFF
            if anded[7]:
                kd[j + 5] = kd[j + 5] ^ anded[0]
                kd[j + 5] &= 0xFFFFFFFF
        for j in range(4):
            kd[j + 5] = (kd[j + 5] * kd[j + 1]) & 0xFFFFFFFF
    # Build the output strings stored in kd[9..16] (pairs of uint32)
    # kd[j*2+9] is the start of an 8-byte field for j in 0..3
    # We store them as byte arrays in a side structure
    result_strings = []
    for j in range(4):
        b = kd[j + 5]
        chars = []
        for x in range(7):
            r = b % 0x24
            b = b // 0x24
            chars.append(abc[r:r+1].decode('ascii'))
        result_strings.append(''.join(chars))
    return result_strings

def stage_3(result_strings):
    # Each segment is 7 chars + '-', last segment ends with null (we use empty)
    parts = []
    for i in range(4):
        s = result_strings[i].ljust(7, '0')[:7]
        parts.append(s)
    # Join with '-', last segment no trailing dash
    return '-'.join(parts)

def keygen(name):
    if isinstance(name, str):
        username_bytes = name.encode('utf-8')
    else:
        username_bytes = name
    kd = [0] * 17
    stage_1(username_bytes, kd)
    result_strings = stage_2(username_bytes, kd)
    serial = stage_3(result_strings)
    return serial

def verify(name, serial):
    expected = keygen(name)
    return serial == expected


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
