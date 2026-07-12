# Reconstructed algorithms for 'steps' crackme by xorolc
# Steps 1-4 are name/serial combos; Step 5 is keyfile-based.
# All implementations are based directly on the Delphi keygen source in the writeups.

def verify_step1(name: str, serial: str) -> bool:
    if len(name) < 4:
        return False
    total = sum(ord(c) for c in name)
    return serial == str(total)

def keygen_step1(name: str) -> str:
    if len(name) < 4:
        raise ValueError('Name must be at least 4 chars')
    return str(sum(ord(c) for c in name))


def verify_step2(name: str, serial: str) -> bool:
    if len(name) < 4:
        return False
    name_upper = name.upper()
    # Pad/wrap name to at least 8 chars using cycling index j
    result = ''
    j = 0
    for i in range(8):
        if i < len(name_upper):
            ch = ord(name_upper[i])
        else:
            # ASSUMPTION: when nome[i] is #0 (past end), use nome[j] cycling
            ch = ord(name_upper[j])
            j += 1
        result += format(ch ^ (0x50 + i), '02X')
    return serial.upper() == result.upper()

def keygen_step2(name: str) -> str:
    if len(name) < 4:
        raise ValueError('Name must be at least 4 chars')
    name_upper = name.upper()
    result = ''
    j = 0
    for i in range(8):
        if i < len(name_upper):
            ch = ord(name_upper[i])
        else:
            ch = ord(name_upper[j])
            j += 1
        result += format(ch ^ (0x50 + i), '02X')
    return result


def verify_step3(name: str, serial: str) -> bool:
    if len(name) < 4:
        return False
    val = [9, 19, 29, 25, 132, 140, 150, 154]
    temp = [0] * 8
    j = 0
    for i in range(8):
        if i < len(name):
            temp[i] = val[i] ^ ord(name[i])
        else:
            # ASSUMPTION: cycling through name from start when past end
            temp[i] = val[i] ^ ord(name[j])
            j += 1
    for i in range(4):
        temp[i] = temp[i] ^ temp[7 - i]
    result = ''
    for i in range(4):
        result += format((temp[i] ^ temp[i + 4]) & 0xFF, '02X')
    return serial.upper() == result.upper()

def keygen_step3(name: str) -> str:
    if len(name) < 4:
        raise ValueError('Name must be at least 4 chars')
    val = [9, 19, 29, 25, 132, 140, 150, 154]
    temp = [0] * 8
    j = 0
    for i in range(8):
        if i < len(name):
            temp[i] = val[i] ^ ord(name[i])
        else:
            temp[i] = val[i] ^ ord(name[j])
            j += 1
    for i in range(4):
        temp[i] = temp[i] ^ temp[7 - i]
    result = ''
    for i in range(4):
        result += format((temp[i] ^ temp[i + 4]) & 0xFF, '02X')
    return result


def _step4_calc(name: str) -> int:
    import ctypes
    # Use 32-bit integer arithmetic matching Delphi Integer (signed 32-bit)
    def u32(x):
        return x & 0xFFFFFFFF
    def s32(x):
        x = x & 0xFFFFFFFF
        if x >= 0x80000000:
            x -= 0x100000000
        return x
    temp = 0
    if len(name) > 6:
        for i in range(25):
            temp = s32((s32(temp) + 48) * 1911)
    else:
        for c in name:
            temp = s32((s32(temp) + ord(c)) * 1911)
    # ASSUMPTION: XOR/OR operations on 32-bit signed integers, matching Delphi
    temp = s32(s32(temp) ^ s32(2205442832))
    temp = s32(s32(temp) ^ s32(1420678174))
    temp = s32(s32(temp) ^ s32(2882395881))
    temp = s32(s32(temp) | s32(305279506))
    return temp

def verify_step4(name: str, serial: str) -> bool:
    if len(name) < 1:
        return False
    return serial == str(_step4_calc(name))

def keygen_step4(name: str) -> str:
    if len(name) < 1:
        raise ValueError('Name must not be empty')
    return str(_step4_calc(name))


def keygen_step5_keyfile() -> bytes:
    # Step 5 is keyfile-based (step5key.key), NOT name/serial.
    # The keyfile bytes at offset i (1-indexed) XOR'd with (0x77 + i - 1) must equal
    # the corresponding byte of "Step 5 was fun!"
    # offset 1 xor 0x77, offset 2 xor 0x78, ...
    target = b'Step 5 was fun!'
    keyfile = bytearray()
    for i, ch in enumerate(target):
        keyfile.append(ch ^ (0x77 + i))
    return bytes(keyfile)

def verify_step5_keyfile(data: bytes) -> bool:
    target = b'Step 5 was fun!'
    if len(data) < len(target):
        return False
    for i, ch in enumerate(target):
        if data[i] ^ (0x77 + i) != ch:
            return False
    return True


# Generic dispatcher
def verify(name: str, serial: str, step: int = 1) -> bool:
    if step == 1:
        return verify_step1(name, serial)
    elif step == 2:
        return verify_step2(name, serial)
    elif step == 3:
        return verify_step3(name, serial)
    elif step == 4:
        return verify_step4(name, serial)
    else:
        raise ValueError('Step 5 is keyfile-based, not name/serial')

def keygen(name: str, step: int = 1) -> str:
    if step == 1:
        return keygen_step1(name)
    elif step == 2:
        return keygen_step2(name)
    elif step == 3:
        return keygen_step3(name)
    elif step == 4:
        return keygen_step4(name)
    else:
        raise ValueError('Step 5 is keyfile-based; use keygen_step5_keyfile()')



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
