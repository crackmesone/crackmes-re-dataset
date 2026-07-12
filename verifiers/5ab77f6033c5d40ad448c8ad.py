import hashlib
import socket


def md5_hex(s: str) -> str:
    """Return uppercase MD5 hex digest of a UTF-8 / Latin-1 string."""
    return hashlib.md5(s.encode('latin-1')).hexdigest().upper()


def keygen(name: str, computer_name: str = None) -> str:
    """
    Generate a valid serial for the given username and computer name.
    If computer_name is None, the local machine name is used.
    """
    if len(name) < 3:
        return 'At least 3 charakters!'

    if computer_name is None:
        computer_name = socket.gethostname()

    # Step 1: MD5 of username
    username_md5 = md5_hex(name)  # already uppercase

    # Step 2: XOR each byte of username with len(username), format as 2-digit hex, concatenate
    xor_len = len(name)
    hex_bytes = ''
    for ch in name:
        xored = ord(ch) ^ xor_len
        hex_bytes += '{:02X}'.format(xored)

    # Step 3: MD5 of the hex-byte string
    hex_bytes_md5 = md5_hex(hex_bytes)

    # Step 4: computer name (uppercase)
    computer_name_upper = computer_name.upper()

    # Step 5: concatenate hex_bytes_md5 + username_md5 + computer_name (all uppercase)
    solution_string = hex_bytes_md5 + username_md5 + computer_name_upper

    # Step 6: MD5 of that combined string
    solution_md5 = md5_hex(solution_string)

    # Step 7: format as 8 groups of 4 hex chars separated by '-'
    # The MD5 is 32 chars; split into 8 x 4
    groups = [solution_md5[i*4:(i+1)*4] for i in range(8)]
    serial = '-'.join(groups)

    return serial  # already uppercase from md5_hex


def verify(name: str, serial: str, computer_name: str = None) -> bool:
    """
    Verify that the serial is valid for the given name and computer name.
    """
    if len(name) < 3:
        return False
    expected = keygen(name, computer_name)
    return serial.upper() == expected.upper()



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
