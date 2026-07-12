# Reconstructed keygen for Fun KeygenMe #0 - Boolean Madness
# Based on the C keygen source from the writeup
# Uses a modified MD5 (modified magic constants) - we use standard MD5 here
# ASSUMPTION: The modified MD5 uses non-standard magic constants; we use standard hashlib MD5
# as the exact modifications are not shown in the truncated writeup.
# ASSUMPTION: Parts 3 and 4 generation logic is truncated; only partial logic is reconstructed.

import hashlib
from ctypes import c_uint32

Table1 = "FAZBYCXDWEVFUGTHSIRJQKPLOMNÀABCDEFGHIJKLMNOPQRSTUVWXYZÀABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklmNOPQRSTUVWXYZ"
Table2 = "ÀABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklmNOPQRSTUVWXYZ"
Table3 = "ÀABCDEFGHIJKLMNOPQRSTUVWXYZÀABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklmNOPQRSTUVWXYZ"
Table4 = ".0123456789ABCDEFAZBYCXDWEVFUGTHSIRJQKPLOMNÀABCDEFGHIJKLMNOPQRSTUVWXYZÀABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklmNOPQRSTUVWXYZ"


def generate_first_hash(name):
    upper_name = name.upper()
    length = len(upper_name)
    hash1 = []
    for j in range(length):
        ch = ord(upper_name[j])
        s = (ch * 0x1337) % 0x69
        even = s % 0x1A
        if even > 0:
            if even <= 0x1A:
                hash1.append(Table1[even])
                continue
            else:
                while even > 0x1A:
                    even -= 6
        else:
            while even < 1:
                even += 6
        hash1.append(Table1[even])
    return ''.join(hash1)


def generate_second_hash(hash1):
    length = len(hash1)
    Count = 5
    hash2 = []
    for i in range(length):
        index = (ord(hash1[i]) + Count) ^ 0x69
        index = (index * index) % 0x34
        if index > 0:
            if index <= 0x34:
                hash2.append(Table2[index % len(Table2)])
                continue
            else:
                while index > 0x34:
                    index -= 3
        else:
            while index < 1:
                index += 3
        hash2.append(Table2[index % len(Table2)])
    h2 = ''.join(hash2)
    rev_h2 = h2[::-1]
    return h2 + rev_h2


def generate_first_md5_hash(hash_input):
    # Reverse the hash, compute MD5, output uppercase hex reversed
    # ASSUMPTION: Standard MD5 used; original uses modified magic constants
    reversed_input = hash_input[::-1]
    digest = hashlib.md5(reversed_input.encode('latin-1')).hexdigest().upper()
    # wsprintf builds uppercase hex
    md5_1 = digest
    md5_1_rev = md5_1[::-1]
    return md5_1_rev


def generate_second_md5_hash(md5_hash):
    # ASSUMPTION: Standard MD5
    digest = hashlib.md5(md5_hash.encode('latin-1')).hexdigest().upper()
    return digest[::-1]


def generate_third_hash(hash_input):
    # hash_input is 32 chars (MD5 hex)
    l = len(hash_input)  # should be 32
    lc = ord(hash_input[l - 1])
    fc = ord(hash_input[0])
    s = lc + fc
    ff = ord(hash_input[15])
    result = []
    for di in range(16):
        ch = ord(hash_input[di])
        ff = ff + ch
        even = ff % s if s != 0 else ff
        even = even % 0x1A
        if even > 0:
            if even <= 0x1A:
                result.append(Table3[even % len(Table3)])
                continue
            else:
                while even > 0x1A:
                    even -= 3
        else:
            while even < 1:
                even += 3
        result.append(Table3[even % len(Table3)])
    # ASSUMPTION: second half of third hash uses similar loop over chars 16-31
    ff2 = ord(hash_input[31])
    for di in range(16, 32):
        ch = ord(hash_input[di])
        ff2 = ff2 + ch
        even = ff2 % s if s != 0 else ff2
        even = even % 0x1A
        if even > 0:
            if even <= 0x1A:
                result.append(Table3[even % len(Table3)])
                continue
            else:
                while even > 0x1A:
                    even -= 3
        else:
            while even < 1:
                even += 3
        result.append(Table3[even % len(Table3)])
    return ''.join(result)


def generate_first_part_of_key(hash_input):
    # ASSUMPTION: Uses Table4 with some index derivation from hash bytes
    # The writeup is truncated here; we reconstruct a plausible version
    result = []
    for i in range(min(9, len(hash_input))):
        idx = ord(hash_input[i]) % len(Table4)
        result.append(Table4[idx])
    return ''.join(result)


def generate_second_part_of_key(hash_input):
    # ASSUMPTION: similar to first part but different table or offset
    result = []
    for i in range(min(9, len(hash_input))):
        idx = (ord(hash_input[i]) ^ 0x42) % len(Table2)
        result.append(Table2[idx])
    return ''.join(result)


def generate_third_part_of_key(hash_input):
    # ASSUMPTION: uses Table3
    result = []
    for i in range(min(9, len(hash_input))):
        idx = (ord(hash_input[i]) + i) % len(Table3)
        result.append(Table3[idx])
    return ''.join(result)


def generate_fourth_part_of_key(hash_input):
    # ASSUMPTION: uses Table4
    result = []
    for i in range(min(9, len(hash_input))):
        idx = (ord(hash_input[i]) * 3) % len(Table4)
        result.append(Table4[idx])
    return ''.join(result)


def keygen(name):
    hash1 = generate_first_hash(name)
    hash2 = generate_second_hash(hash1)
    md5_1 = generate_first_md5_hash(hash2)
    md5_2 = generate_second_md5_hash(md5_1)
    hash3 = generate_third_hash(md5_2)

    part1 = generate_first_part_of_key(md5_2)
    part2 = generate_second_part_of_key(md5_2)
    part3 = generate_third_part_of_key(hash3)
    part4 = generate_fourth_part_of_key(md5_2)

    serial = "{}-{}-{}-{}".format(part1, part2, part3, part4)
    return serial


def verify(name, serial):
    # ASSUMPTION: We regenerate and compare; actual crackme comparison logic unknown
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
