def _build_corptag(username: str, corp_tag: str) -> str:
    """
    Repeat corp_tag until its length >= len(username),
    then truncate/use only the first len(username) characters.
    """
    corptag = ""
    while len(corptag) < len(username):
        corptag += corp_tag
    return corptag


def _compute_password_bytes(username: str, corptag: str) -> bytes:
    """
    For each position i in username:
        result[i] = (ord(username[i]) + ord(corptag[i]) - 0x96) & 0xFF
    Returns raw bytes (may include non-printable bytes).
    """
    result = []
    for i in range(len(username)):
        val = (ord(username[i]) + ord(corptag[i]) - 0x96) & 0xFF
        result.append(val)
    return bytes(result)


def keygen(username: str, corp_tag: str = "AAAA") -> bytes:
    """
    Given a username and a corp_tag, produce the password bytes.
    The password is raw bytes; caller should handle encoding as needed.
    corp_tag defaults to 'AAAA' but any non-empty string is valid.
    """
    if not username:
        raise ValueError("Username must not be empty")
    if not corp_tag:
        raise ValueError("Corp tag must not be empty")
    corptag = _build_corptag(username, corp_tag)
    return _compute_password_bytes(username, corptag)


def verify(username: str, corp_tag: str, password_bytes: bytes) -> bool:
    """
    Verify that password_bytes matches the expected password for (username, corp_tag).
    password_bytes should be the raw byte sequence produced by keygen.
    """
    expected = keygen(username, corp_tag)
    return password_bytes == expected



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
