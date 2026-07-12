import hashlib
import struct

# We need CRC and MD5 implementations.
# MD5 is standard. CRC (GetStringCRC) is unknown - using CRC32 as assumption.
# ASSUMPTION: GetStringCRC uses a standard CRC32 variant (e.g., zlib.crc32)
import zlib

def ror32(value, count):
    count = count & 31
    value = value & 0xFFFFFFFF
    return ((value >> count) | (value << (32 - count))) & 0xFFFFFFFF

def rol32(value, count):
    count = count & 31
    value = value & 0xFFFFFFFF
    return ((value << count) | (value >> (32 - count))) & 0xFFFFFFFF

def mini_rol(x, n):
    # 4-bit rotate left
    n = n & 3
    return ((x << n) | (x >> (4 - n))) & 0xF

def mini_ror(x, n):
    # 4-bit rotate right
    n = n & 3
    return ((x >> n) | (x << (4 - n))) & 0xF

def get_string_crc(s):
    # ASSUMPTION: GetStringCRC is zlib crc32 of the bytes of the string
    data = s.encode('latin-1')
    return zlib.crc32(data) & 0xFFFFFFFF

def md5_string(s):
    # Returns lowercase hex MD5
    return hashlib.md5(s.encode('latin-1')).hexdigest().lower()

def do_work(nmd, count):
    # Delphi 1-indexed: nmd[count], nmd[count+1], nmd[count+2], nmd[count+3]
    # count is 1-based in the loop, so we access nmd[count-1..count+2] in 0-based
    # Original: ord(nmd[count+3]) shl 24 | ord(nmd[count+2]) shl 16 | ord(nmd[count+1]) shl 8 | ord(nmd[count])
    # Delphi strings are 1-indexed, so nmd[count] in Pascal = nmd[count-1] in Python
    def safe_ord(s, idx_1based):
        idx = idx_1based - 1
        if 0 <= idx < len(s):
            return ord(s[idx])
        return 0
    c0 = safe_ord(nmd, count)
    c1 = safe_ord(nmd, count + 1)
    c2 = safe_ord(nmd, count + 2)
    c3 = safe_ord(nmd, count + 3)
    return ((c3 << 24) | (c2 << 16) | (c1 << 8) | c0) & 0xFFFFFFFF

def keygen(name):
    nam = name
    len_n = len(nam)
    if len_n < 5:
        return 'Name must contain at least 5 chars!'

    # --- First part ---
    i = 1
    ib_1 = 0
    while i <= 0x64:  # until i > 100
        ia_1 = (len_n + i) & 0xFFFFFFFF
        char_idx = ((i - 1) % len_n)  # 0-based
        char_val = ord(nam[char_idx])
        ib_1 = rol32(((ia_1 * ib_1) + char_val * i) & 0xFFFFFFFF, 1)
        i += 1

    st1 = list(str(ib_1))
    for j in range(len(st1)):
        ak = j  # ak = j-1 where j is 1-based, so ak = 0-based index
        if (ak % 3) == 0:
            digit_val = ord(st1[j]) - 0x30
            new_val = ((~digit_val) & 0xF) + 0x41
            st1[j] = chr(new_val)
    st1 = ''.join(st1)

    # --- Second part ---
    ib_2 = 1
    stc = list(str(get_string_crc(nam)))
    len_s = len(stc)
    for i in range(len_s):
        ak = i  # ak = i-1 where i is 1-based
        if (ak % 3) == 0:
            if (len_n & 1) == 0:
                ia_2 = 1
            else:
                ia_2 = 2
            ib_2 = (ib_2 + ror32(ord(stc[i]), ia_2)) & 0xFFFFFFFF
        else:
            if (len_n & 1) == 0:
                ia_2 = 2
            else:
                ia_2 = 1
            ib_2 = (ib_2 * rol32(ord(stc[i]), ia_2)) & 0xFFFFFFFF

    st2 = list(str(ib_2))
    len_s = len(st2)
    for j in range(len_s):
        ak = j  # 0-based
        if (ak % 3) == 0:
            if (len_n & 1) == 0:
                pq = 1
            else:
                pq = 2
            digit_val = ord(st2[j]) - 0x30
            st2[j] = chr(mini_rol(digit_val, pq) + 0x41)
        else:
            if (len_n & 1) == 0:
                digit_val = ord(st2[j]) - 0x30
                st2[j] = chr(mini_ror(digit_val, 1) + 0x41)
            # if len_n is odd and (ak%3)!=0, no change
    st2 = ''.join(st2)

    # --- Third part ---
    ib_3 = 0
    nmd = md5_string(nam)
    len_s = len(nmd)  # always 32 for MD5 hex
    for i in range(1, len_s + 1):  # 1-based like Delphi
        ia_3 = do_work(nmd, i)
        if (len_n & 1) == 0:
            ib_3 = (ib_3 + ((ia_3 ^ 0x12345678) + ia_3)) & 0xFFFFFFFF
        else:
            ib_3 = (ib_3 + ((ia_3 ^ 0x87654321) + ia_3)) & 0xFFFFFFFF

    st3 = list(str(ib_3))
    len_s = len(st3)
    for j in range(len_s):
        # j is 0-based; Delphi j is 1-based, condition: ((j-1) and 1) = 0 means j is odd (1,3,5,...)
        # In 0-based: j=0,2,4,... -> (j & 1) == 0
        if (j & 1) == 0:
            if (len_n & 1) == 0:
                pq = 5
                qp = 3
            else:
                pq = 2
                qp = 2
            digit_val = ord(st3[j]) - 0x30
            st3[j] = chr(mini_ror(digit_val, qp) + 0x41 + pq)
    st3 = ''.join(st3)

    return st1 + '-' + st2 + '-' + st3 + '-4BE708B1'

def verify(name, serial):
    expected = keygen(name)
    if isinstance(expected, str) and expected.startswith('Name'):
        return False
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
