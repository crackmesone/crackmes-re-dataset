import ctypes
import socket
import os

# ASSUMPTION: We cannot call GetComputerNameA / GetUserNameA from Python exactly,
# so we approximate using socket.gethostname() and os.getlogin().
# The algorithm is reconstructed from the assembly writeup.

def _compute_hash1(name: str) -> tuple:
    """
    Returns (buff1_final, buff2_final, name_len)
    buff1 starts at 0x01791117, buff2 starts at 0.
    For each char in name:
        edx = char_value + buff1
        buff2 += edx
        buff1 += 1  (INC DWORD PTR SS:[EBP-8])
    After loop:
        ESI = name_len * buff2 + buff1
    buff1_final = 0x01791117 + name_len
    buff2_final = sum over loop
    ESI (hash2) = name_len * buff2_final + buff1_final
    """
    buff1 = 0x01791117
    buff2 = 0
    name_len = len(name)
    for ch in name:
        edx = (ord(ch) + buff1) & 0xFFFFFFFF
        buff2 = (buff2 + edx) & 0xFFFFFFFF
        buff1 = (buff1 + 1) & 0xFFFFFFFF
    # buff1 is now 0x01791117 + name_len
    esi = (name_len * buff2 + buff1) & 0xFFFFFFFF
    return buff1, buff2, name_len, esi


def _get_computer_and_user() -> str:
    """
    Concatenates ComputerName + UserName (as Windows would),
    then reverses, then uppercases.
    ASSUMPTION: Using Python equivalents of GetComputerNameA and GetUserNameA.
    """
    try:
        computer_name = socket.gethostname()
    except Exception:
        computer_name = ""
    try:
        user_name = os.getlogin()
    except Exception:
        user_name = ""
    # wsprintfA formats computer_name as "%s", then lstrcatA appends user_name
    concatenated = computer_name + user_name
    # Reverse the concatenated string
    reversed_str = concatenated[::-1]
    # CharUpperA -> uppercase
    reversed_str = reversed_str.upper()
    return reversed_str


def _compute_hash1_from_pcinfo(reversed_str: str, name_len: int) -> int:
    """
    The loop starting at 004012F1:
      EAX starts at 0x20 (32)
      For each index i from 0x20 to 0x20+len(reversed_str)-1:
          ecx = reversed_str[i - 0x20]  (signed byte)
          ecx ^= i  (XOR with EAX which starts at 0x20 and increments)
          ecx *= name_len  (IMUL with username length = input name length)
          hash_buff += ecx
    ASSUMPTION: 'name_len' here is the length of the *input user name*
    (the writeup says 'multiply with usernamelength').
    """
    hash_buff = 0
    eax = 0x20
    for ch in reversed_str:
        # MOVSX ECX, BYTE -> signed byte
        ecx = ord(ch)
        if ecx > 127:
            ecx -= 256
        # XOR ECX, EAX
        ecx ^= eax
        # IMUL ECX, name_len (signed 32-bit)
        ecx = ctypes.c_int32(ecx * name_len).value
        # ADD hash_buff, ECX
        hash_buff = ctypes.c_int32(hash_buff + ecx).value
        eax += 1
    # Return as unsigned 32-bit
    return ctypes.c_uint32(hash_buff).value


def verify(name: str, serial: str) -> bool:
    """
    Reconstructed verification:
    1. name must be >= 4 chars
    2. Compute hash2 (ESI) from input name
    3. Get reversed+uppercased (ComputerName+UserName)
    4. Compute hash1 from pc info
    5. serial (decimal string) converted via atol -> integer
    6. Check: (hash1 ^ serial_int) == (hash1 + hash2) & 0xFFFFFFFF
       Rearranged: serial_xor_hash1 == hash1 + hash2
       i.e. serial_int ^ hash1 == hash1 + hash2  (mod 2^32, signed comparison)
    """
    if len(name) < 4:
        return False

    buff1, buff2, name_len, esi = _compute_hash1(name)
    hash2 = esi  # ESI = name_len * buff2 + buff1

    reversed_str = _get_computer_and_user()
    hash1 = _compute_hash1_from_pcinfo(reversed_str, name_len)

    # atol converts serial string (decimal) to integer
    try:
        serial_int = int(serial)
    except ValueError:
        return False
    serial_int = ctypes.c_uint32(serial_int).value

    # CMP EAX, ECX where EAX = hash1 + ESI, ECX = serial ^ hash1
    eax = ctypes.c_uint32(hash1 + hash2).value
    ecx = ctypes.c_uint32(serial_int ^ hash1).value
    return eax == ecx


def keygen(name: str) -> str:
    """
    Generate valid serial for given name.
    serial_int = (hash1 + hash2) ^ hash1  (then convert to decimal string)
    Because: serial_int ^ hash1 must equal hash1 + hash2
    => serial_int = hash1 ^ (hash1 + hash2)
    """
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters.")

    buff1, buff2, name_len, esi = _compute_hash1(name)
    hash2 = esi

    reversed_str = _get_computer_and_user()
    hash1 = _compute_hash1_from_pcinfo(reversed_str, name_len)

    serial_int = ctypes.c_uint32(hash1 ^ ctypes.c_uint32(hash1 + hash2).value).value
    return str(serial_int)



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
