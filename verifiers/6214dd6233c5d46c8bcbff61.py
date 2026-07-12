# "Danofred's KeygenMe - 01 (update)" Solution
# Reconstructed from nimaid's writeup
#
# Algorithm:
#   secret = "tryHarderToMakeAGoodKeyGen"  (length = 26)
#   For each index i in [0, len(username)):
#     username_index = (ord(username[i]) ^ 26) % len(username)
#     password[i]    = username[username_index]
#
# Verified against known pairs from comments:
#   cookies4you -> c44kessoc4o  (see note below)
#   Yurri       -> ruiiY

SECRET = "tryHarderToMakeAGoodKeyGen"
SECRET_LENGTH = len(SECRET)  # 26


def keygen(username: str) -> str:
    username = str(username)
    username_length = len(username)
    if username_length == 0:
        return ""
    output_password = ""
    for i in range(username_length):
        username_index = (ord(username[i]) ^ SECRET_LENGTH) % username_length
        output_password += username[username_index]
    return output_password


def verify(name: str, serial: str) -> bool:
    return keygen(name) == serial



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
