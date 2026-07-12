import sys

def _extend_name(name: str) -> str:
    """Extend or truncate name to exactly 18 characters."""
    if len(name) >= 18:
        return name[:18]
    result = name
    while len(result) < 18:
        needed = 18 - len(result)
        if len(name) <= needed:
            result += name
        else:
            result += name[:needed]
    return result[:18]


def _generate_serial(name18: str, path_len: int) -> str:
    """Core algorithm: build array, XOR, convert to hex string."""
    # Step 1: fill array of 18 entries, each entry = (char_val, index1, index2)
    # index1 cycles 1..3 (outer loop j in 0..2)
    # index2 cycles 1..6 (inner loop i in 0..5, maps to nameIndex%6 + 1)
    entries = []
    name_index = 0
    for j in range(3):          # index1 = j+1  -> 1, 2, 3
        for i in range(6):      # index2 = (name_index % 6) + 1  -> 1..6
            char_val = ord(name18[name_index])
            idx1 = j + 1
            idx2 = (name_index % 6) + 1
            entries.append([char_val, idx1, idx2])
            name_index += 1

    # Step 2: XOR transform
    # arr[0] = 2 * (arr[0] ^ (arr[2] + 3 + pathLen))
    # arr[0] = 2 * (arr[0] ^ (arr[1] + 3 + pathLen))
    for entry in entries:
        char_val, idx1, idx2 = entry
        char_val = (2 * (char_val ^ (idx2 + 3 + path_len))) & 0xFFFFFFFF
        char_val = (2 * (char_val ^ (idx1 + 3 + path_len))) & 0xFFFFFFFF
        entry[0] = char_val

    # Step 3: convert each transformed value to hex string and concatenate
    password = ''
    for entry in entries:
        password += format(entry[0], 'x')

    return password


def verify(name: str, serial: str, path_len: int = None) -> bool:
    """Verify a name/serial pair.

    path_len must be provided because the serial depends on the command-line
    length, which is runtime information.  When calling from a shell:
      - double-click: len('C:\\path\\to\\crackme.exe')
      - from cmd:     len('crackme.exe')  = 11
    """
    if path_len is None:
        # ASSUMPTION: default to 'crackme.exe' length when running from cmd
        path_len = len('crackme.exe')
    name18 = _extend_name(name)
    expected = _generate_serial(name18, path_len)
    return serial == expected


def keygen(name: str, path_len: int = None) -> str:
    """Generate the valid serial for a given name.

    path_len: length of the command-line string used when running the crackme.
    Default assumes running as 'crackme.exe' from cmd (length = 11).
    """
    if path_len is None:
        # ASSUMPTION: default to 'crackme.exe' length (11)
        path_len = len('crackme.exe')
    name18 = _extend_name(name)
    return _generate_serial(name18, path_len)



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
