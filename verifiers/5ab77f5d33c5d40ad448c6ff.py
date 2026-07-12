import random
import time

abc = "1AULWJZI92BCDEFG86K4NPQRST3V5XY7"

magic_bits = ["16", "AJ", "AT", "UL", "LA", "L7", "WX", "6J", "6T", "KL", "4A", "47", "NX"]

index_table = [0x11, 0x25, 0x39, 0x43, 0x61, 0x7F, 0x9D]

local_10 = [0x0D, 0x02, 0x18, 0x10, 0x0A, 0x13, 0x05]

vienetai = [
    [0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18],
    [0x04, 0x03, 0x06, 0x05, 0x07, 0x08, 0x0A, 0x09, 0x12, 0x11, 0x14, 0x13, 0x16, 0x15, 0x18, 0x17],
    [0x0D, 0x00, 0x17, 0x01, 0x16, 0x02, 0x15, 0x03, 0x14, 0x04, 0x13, 0x05, 0x12, 0x06, 0x11, 0x07],
    [0x0A, 0x15, 0x00, 0x07, 0x0E, 0x12, 0x03, 0x04, 0x05, 0x0F, 0x13, 0x16, 0x11, 0x01, 0x18, 0x06],
    [0x04, 0x17, 0x09, 0x10, 0x02, 0x08, 0x14, 0x0D, 0x05, 0x16, 0x06, 0x18, 0x07, 0x12, 0x01, 0x15],
    [0x01, 0x10, 0x0D, 0x18, 0x03, 0x0A, 0x16, 0x05, 0x17, 0x14, 0x07, 0x11, 0x02, 0x12, 0x08, 0x04],
    [0x09, 0x04, 0x0A, 0x14, 0x10, 0x00, 0x0E, 0x01, 0x16, 0x13, 0x11, 0x15, 0x0F, 0x03, 0x07, 0x06],
]

local_4 = [
    [0x00, 0x01],
    [0x01, 0x00],
    [0x08, 0x09],
    [0x09, 0x08],
    [0x0E, 0x0F],
    [0x0F, 0x0E],
    [0x18, 0x17],
]

local_9 = [
    [0x0A, 0x0E, 0x0F, 0x10],
    [0x0D, 0x0E, 0x0F, 0x10],
    [0x0A, 0x0E, 0x0F, 0x10],
    [0x02, 0x0D, 0x14, 0x17],
    [0x00, 0x03, 0x11, 0x13],
    [0x00, 0x06, 0x09, 0x15],
    [0x02, 0x08, 0x0D, 0x12],
]


def get_code_from_table(ch):
    for i in range(31):
        if abc[i] == ch:
            return i
    return -1


def L00403DD0(arg1, arg2, arg3):
    """Signed integer division helper (ripped from original)."""
    a = False
    if arg2 < 0:
        a = True
        arg2 = ~arg2
        arg1 = ~arg1
    arg2 = arg2 // arg3
    arg1 = arg1 // arg3
    if a:
        arg2 = ~arg2
        arg1 = ~arg1
    return arg1, arg2


def get_hash(s):
    """Hash function from the keygen (ripped from original C code)."""
    var1 = 160
    var2 = 0
    var3 = 0
    buff2 = []
    for ch in s:
        b = (ord(ch) & 255) ^ ((var1 & 0xFFFF) >> 8)
        buff2.append(b)
        var2 = var2 + b
        var1 = (((ord(ch) & 255) + (var1 & 0xFFFF)) * 66 + 6) & 0xFFFF
    while var3 == 0:
        if var2 <= 100:
            break
        var2, var3 = L00403DD0(var2, var3, 10)
    return var2


def keygen(name, company, magic_index=None):
    """
    Generate a valid serial for (name, company).
    name and company must be at least 5 characters.
    magic_index: 0-12 to pick a specific magic_bits pair, or None for random.
    """
    if len(name) < 5 or len(company) < 5:
        raise ValueError("Name and company must be at least 5 characters long.")

    serial = ['\x00'] * 26
    serial[25] = '\x00'

    if magic_index is None:
        magic_index = random.randint(0, 12)

    serial[0x0B] = magic_bits[magic_index][0]
    serial[0x0C] = magic_bits[magic_index][1]

    a = get_code_from_table(serial[0x0B])
    idx = get_code_from_table(serial[0x0C])
    idx = idx + (a << 5)
    idx = idx & 0xFF

    index = -1
    for i in range(7):
        if index_table[i] == idx:
            index = i
            break

    if index == -1:
        raise ValueError(f"magic_index {magic_index} did not map to a valid index_table entry (idx=0x{idx:02X}).")

    # Place the fixed character at local_10[index]
    serial[local_10[index]] = abc[16]  # abc[16] = 'G'

    chksum = 0
    pairs = []
    for i in range(8):
        a_rand = random.randint(0, 31)
        b_rand = random.randint(0, 31)
        serial[vienetai[index][i * 2]] = abc[a_rand]
        serial[vienetai[index][i * 2 + 1]] = abc[b_rand]
        combined = b_rand + (a_rand << 5)
        chksum += (combined & 0xFF)

    chksum = chksum % 0xFF
    a_val = (chksum // 0x10) // 2
    serial[local_4[index][0]] = abc[a_val]
    a_val2 = chksum - (a_val * 0x20)
    serial[local_4[index][1]] = abc[a_val2]

    name_h = get_hash(name)
    company_h = get_hash(company)

    chksum2 = (name_h * 0xB3) + (company_h * 0x1F) + 0xFE57
    h1 = (chksum2 >> 8) & 0xFF
    h2 = chksum2 & 0xFF

    a_h1 = (h1 // 0x10) // 2
    serial[local_9[index][0]] = abc[a_h1]
    a_h1b = h1 - a_h1 * 0x20
    serial[local_9[index][1]] = abc[a_h1b]
    a_h2 = (h2 // 0x10) // 2
    serial[local_9[index][2]] = abc[a_h2]
    a_h2b = h2 - a_h2 * 0x20
    serial[local_9[index][3]] = abc[a_h2b]

    # serial[25] is null terminator, not part of displayed serial
    return ''.join(serial[:25])


def verify(name, serial, company):
    """
    Verify a serial for (name, company).
    Regenerates what the serial should encode and checks consistency.
    ASSUMPTION: The crackme validates by re-deriving and comparing the
    name/company hash portion and the internal checksum portion.
    We verify by re-running the check logic.
    """
    if len(name) < 5 or len(company) < 5:
        return False
    if len(serial) < 25:
        return False

    # Step 1: Determine magic index from serial[0x0B] and serial[0x0C]
    a = get_code_from_table(serial[0x0B])
    idx = get_code_from_table(serial[0x0C])
    if a == -1 or idx == -1:
        return False
    idx = idx + (a << 5)
    idx = idx & 0xFF

    index = -1
    for i in range(7):
        if index_table[i] == idx:
            index = i
            break
    if index == -1:
        return False

    # Step 2: Check fixed character at local_10[index]
    if serial[local_10[index]] != abc[16]:  # must be 'G'
        return False

    # Step 3: Verify internal checksum
    chksum = 0
    for i in range(8):
        pos_a = vienetai[index][i * 2]
        pos_b = vienetai[index][i * 2 + 1]
        ca = get_code_from_table(serial[pos_a])
        cb = get_code_from_table(serial[pos_b])
        if ca == -1 or cb == -1:
            return False
        combined = cb + (ca << 5)
        chksum += (combined & 0xFF)

    chksum = chksum % 0xFF
    a_val = (chksum // 0x10) // 2
    a_val2 = chksum - (a_val * 0x20)

    if a_val < 0 or a_val >= len(abc):
        return False
    if a_val2 < 0 or a_val2 >= len(abc):
        return False

    if serial[local_4[index][0]] != abc[a_val]:
        return False
    if serial[local_4[index][1]] != abc[a_val2]:
        return False

    # Step 4: Verify name/company hash portion
    name_h = get_hash(name)
    company_h = get_hash(company)
    chksum2 = (name_h * 0xB3) + (company_h * 0x1F) + 0xFE57
    h1 = (chksum2 >> 8) & 0xFF
    h2 = chksum2 & 0xFF

    a_h1 = (h1 // 0x10) // 2
    a_h1b = h1 - a_h1 * 0x20
    a_h2 = (h2 // 0x10) // 2
    a_h2b = h2 - a_h2 * 0x20

    for val, pos_i in [(a_h1, 0), (a_h1b, 1), (a_h2, 2), (a_h2b, 3)]:
        if val < 0 or val >= len(abc):
            return False
        if serial[local_9[index][pos_i]] != abc[val]:
            return False

    return True



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
