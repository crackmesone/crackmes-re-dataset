import re
import struct

# ASSUMPTION: .NET's String.GetHashCode() for a given string must be replicated.
# The .NET GetHashCode() algorithm differs between 32-bit and 64-bit CLR versions
# and is not guaranteed to be stable across runs in newer .NET versions.
# The classic .NET 2.0/4.0 32-bit algorithm is used here as the most common case
# for crackmes of this era (2008).

def dotnet_get_hash_code(s: str) -> int:
    """
    Replicates the classic .NET 2.0 String.GetHashCode() for 32-bit CLR.
    This is the algorithm typically used in .NET 2.0/4.0 on 32-bit processes.
    Returns a signed 32-bit integer (like C# int).
    """
    # ASSUMPTION: Using the well-known .NET 2.0 32-bit GetHashCode algorithm.
    # hash1 = 5381, hash2 = 5381
    # for each pair of chars: hash1 = ((hash1 << 5) + hash1 + hash2) ^ char1
    #                          hash2 = ((hash2 << 5) + hash2 + hash1) ^ char2
    # return hash1 + hash2 * 1566083941
    hash1 = 5381
    hash2 = hash1
    i = 0
    chars = [ord(c) for c in s]
    length = len(chars)
    while i < length:
        c1 = chars[i]
        hash1 = (((hash1 << 5) + hash1) ^ c1) & 0xFFFFFFFF
        if i + 1 < length:
            c2 = chars[i + 1]
            hash2 = (((hash2 << 5) + hash2) ^ c2) & 0xFFFFFFFF
        i += 2
    result = (hash1 + (hash2 * 1566083941)) & 0xFFFFFFFF
    # Convert to signed 32-bit
    if result >= 0x80000000:
        result -= 0x100000000
    return result


def to_signed32(n: int) -> int:
    """Ensure integer is treated as signed 32-bit (mimic C# int arithmetic)."""
    n = n & 0xFFFFFFFF
    if n >= 0x80000000:
        n -= 0x100000000
    return n


def generate_signature(name: str, machine_name: str, user_name: str) -> str:
    """
    Generates the signature file content.
    Format: r<num4>*d<num5>*t<num6>*
    where:
      num4 = name.GetHashCode() * 45
      num5 = machine_name.GetHashCode() * 25
      num6 = (user_name.GetHashCode() * 32) / 10  (integer division)
    """
    num = to_signed32(dotnet_get_hash_code(name) * 45)
    num2 = to_signed32(dotnet_get_hash_code(machine_name) * 25)
    num3 = to_signed32((dotnet_get_hash_code(user_name) * 32) // 10)

    signature = f"r{num}*d{num2}*t{num3}*"
    return signature


def verify(name: str, serial: str) -> bool:
    """
    Verifies a signature string against name, machine name, and user name.
    'serial' here is the full content of the signature file.
    Machine name and username are taken from the environment (as the crackme does).
    """
    import os
    # ASSUMPTION: machine_name and user_name come from the running environment,
    # mirroring Environment.MachineName and Environment.UserName in C#.
    machine_name = os.environ.get('COMPUTERNAME', os.uname().nodename if hasattr(os, 'uname') else '')
    user_name = os.environ.get('USERNAME', os.environ.get('USER', ''))

    # Parse the signature file content using the same regexes as the crackme
    regex_r = re.compile(r'r([-0-9]*)\*')
    regex_d = re.compile(r'd([-0-9]*)\*')
    regex_t = re.compile(r't([-0-9]*)\*')

    try:
        num4 = int(regex_r.search(serial).group(1))
        num5 = int(regex_d.search(serial).group(1))
        num6 = int(regex_t.search(serial).group(1))
    except (AttributeError, ValueError):
        return False

    num = to_signed32(dotnet_get_hash_code(name) * 45)
    num2 = to_signed32(dotnet_get_hash_code(machine_name) * 25)
    num3 = to_signed32((dotnet_get_hash_code(user_name) * 32) // 10)

    return (num == num4) and (num2 == num5) and (num3 == num6)


def keygen(name: str, machine_name: str = None, user_name: str = None) -> str:
    """
    Generates a valid signature string for the given name.
    If machine_name or user_name are not provided, reads from environment.
    """
    import os
    if machine_name is None:
        machine_name = os.environ.get('COMPUTERNAME', '')
        if not machine_name:
            try:
                machine_name = os.uname().nodename
            except AttributeError:
                machine_name = ''
    if user_name is None:
        user_name = os.environ.get('USERNAME', os.environ.get('USER', ''))

    return generate_signature(name, machine_name, user_name)



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
