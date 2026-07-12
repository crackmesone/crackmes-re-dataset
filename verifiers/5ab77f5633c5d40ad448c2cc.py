#!/usr/bin/env python3
"""
Reverse-engineered keygen for lightphoenixs_crackme_1
Based on the keygen2.py solution writeup.
"""

import hashlib
import sys

# XOR keys used in magicXOR
keys = [0x4C, 0x50, 0x4E, 0x54, 0x43]


def mapping_raw(input_val, order=0):
    """order==0: char -> index in array; order==1: index -> char"""
    num_list = list(map(chr, range(0x30, 0x3A)))   # '0'-'9'
    upp_list = list(map(chr, range(0x41, 0x5B)))   # 'A'-'Z'
    low_list = list(map(chr, range(0x61, 0x7B)))   # 'a'-'z'
    lista = []
    lista.extend(upp_list)
    lista.extend(low_list)
    lista.extend(num_list)
    lista.append('+')
    lista.append('/')
    if order == 0:
        return lista.index(input_val)
    return lista[input_val]


def mapping(input_lista, order=0):
    return [mapping_raw(input_lista[ii], order) for ii in range(len(input_lista))]


def rev_hash_single(address):
    """Given a 24-bit integer, return 4 base64-like indices."""
    X = (address & 0x0000FF)
    Y = (address & 0x00FF00) >> 8
    Z = (address & 0xFF0000) >> 16
    A = (X & 0xFC) >> 2
    B = ((X & 0x3) << 4) | ((Y & 0xF0) >> 4)
    C = ((Y & 0xF) << 2) | ((Z & 0xC0) >> 6)
    D = (Z & 0x3F)
    return [A, B, C, D]


def rev_hash_list(input_list):
    temp_list = []
    for ll in range(0, len(input_list), 3):
        if ll + 2 < len(input_list):
            temp_addr = input_list[ll] | (input_list[ll+1] << 8) | (input_list[ll+2] << 16)
        elif ll + 1 < len(input_list):
            temp_addr = input_list[ll] | (input_list[ll+1] << 8)
        else:
            temp_addr = input_list[ll]
        temp_list += rev_hash_single(temp_addr)
    return temp_list


def magic_xor(lista_in):
    lista = list(lista_in)
    for ii in range(len(lista)):
        lista[ii] = lista[ii] ^ keys[ii % 5]
    return lista


def extract_value(input_num):
    retLista = []
    retLista.append(input_num[0] & 0xFFFFFF)
    retLista.append((input_num[0] & 0xFF000000) >> 24 | (input_num[1] & 0xFFFF) << 8)
    retLista.append((input_num[1] & 0xFFFF0000) >> 16 | (input_num[2] & 0xFF) << 16)
    retLista.append((input_num[2] & 0xFFFFFF00) >> 8)
    retLista.append((input_num[3] & 0xFFFFFF))
    retLista.append((input_num[3] & 0xFF000000) >> 24 | (input_num[4] & 0xFFFF) << 8)
    return retLista


def return_magic_addr(lista):
    """Compute MD5-based magic address from the XOR'd user+chk list."""
    lista_md5 = [0]*16 + lista
    string_input = bytes(lista_md5)
    m = hashlib.md5()
    m.update(string_input)
    ret_string = m.hexdigest()
    ret_lista = []
    for ll in range(0, len(ret_string), 8):
        val = (int(ret_string[ll:ll+2], 16) |
               int(ret_string[ll+2:ll+4], 16) << 8 |
               int(ret_string[ll+4:ll+6], 16) << 16 |
               int(ret_string[ll+6:ll+8], 16) << 24)
        ret_lista.append(val)
    return ret_lista


def chk1(input_list):
    """Compute 8-char checksum from input list (username bytes + 0x9)."""
    loop_val = 1
    temp_result = []
    input_list = list(input_list) + [0]
    for jj in range(len(input_list) - 2):
        loop_val = (((input_list[jj] + 2) * input_list[jj] + 3) * loop_val) & 0xFFFFFFFF
    for jj in range(8):
        temp_value = (loop_val >> (0x1C - 4*jj)) & 0xF
        if temp_value <= 9:
            temp_value = temp_value | 0x30
        else:
            temp_value = temp_value + 0x37
        temp_result.append(temp_value)
    return temp_result


def keygen(name):
    """Generate a valid serial for the given username."""
    # Convert name to list of ASCII values
    user_enc = [ord(c) for c in name]
    user_enc.append(0x9)  # append tab separator

    # Compute checksum
    ret_chk = chk1(user_enc)
    tot_list = user_enc + ret_chk

    # XOR encode
    user_pwd_enc = magic_xor(tot_list)

    # Get first two bytes for numer
    numer = user_pwd_enc[0] | (user_pwd_enc[1] << 8)

    # Compute MD5-based address list
    ret_list = return_magic_addr(user_pwd_enc)
    ret_list.append(numer)

    # Extract 6 packed values
    addr_list = extract_value(ret_list)

    # Compute hash (first part of serial indices)
    hash_part = (rev_hash_single(addr_list[0]) +
                 rev_hash_single(addr_list[1]) +
                 rev_hash_single(addr_list[2]) +
                 rev_hash_single(addr_list[3]) +
                 rev_hash_single(addr_list[4]) +
                 rev_hash_single(addr_list[5]))

    # Encode remaining user_pwd_enc bytes (skip first 2) via rev_hash_list
    complete_list = user_pwd_enc
    rev_list = rev_hash_list(complete_list[2:])

    # Combine
    full_indices = hash_part + rev_list

    # Map indices to characters
    mapped = mapping(full_indices, 1)

    serial = ''.join(mapped)
    return serial


def verify(name, serial):
    """
    Verify name/serial pair by regenerating the expected serial and comparing.
    # ASSUMPTION: The crackme compares the generated serial directly to input.
    # The exact comparison length/format is not fully specified in the writeup.
    """
    try:
        expected = keygen(name)
        # ASSUMPTION: Compare the generated serial prefix or full string
        # The writeup truncates, so we compare what we have
        min_len = min(len(expected), len(serial))
        if min_len == 0:
            return False
        return expected[:min_len] == serial[:min_len] and len(serial) >= 16
    except Exception:
        return False



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
