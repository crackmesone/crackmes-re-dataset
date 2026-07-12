def keygen(user):
    """
    Generate a valid serial (as raw bytes) for the given username.
    The serial is userLen*3 bytes long, split into three sections.

    Section 1 (indices 0 .. userLen-1):
      arg3 starts at 0
      serial[i] = ((arg3 + 15) ^ ord(user[i])) & 0xff
      After the last byte of section 1: arg3 = serial[userLen-1] - 10

    Section 2 (indices userLen .. 2*userLen-1):
      serial[i] = ((18 - arg3) ^ ord(user[i % userLen])) & 0xff
      After the last byte of section 2: arg3 = serial[2*userLen-1] + 113

    Section 3 (indices 2*userLen .. 3*userLen-1):
      serial[i] = (((arg3 - 76) * 2) ^ ord(user[i % userLen])) & 0xff
      arg3 = serial[i] for the next iteration
    """
    user_bytes = [ord(c) for c in user]
    userLen = len(user_bytes)
    serial = []
    arg3 = 0

    # Section 1
    for i in range(userLen):
        val = ((arg3 + 15) ^ user_bytes[i]) & 0xff
        serial.append(val)
        if i < userLen - 1:
            arg3 = val
        else:
            arg3 = (val - 10) & 0xff

    # Section 2
    for i in range(userLen):
        val = ((18 - arg3) ^ user_bytes[i % userLen]) & 0xff
        serial.append(val)
        if i < userLen - 1:
            arg3 = val
        else:
            arg3 = (val + 113) & 0xff

    # Section 3
    for i in range(userLen):
        val = (((arg3 - 76) * 2) ^ user_bytes[i % userLen]) & 0xff
        serial.append(val)
        arg3 = val

    return bytes(serial)


def verify(user, serial):
    """
    Verify that serial (bytes or list of ints) matches the expected password
    for the given username, using the breakme_magic algorithm.
    """
    user_bytes = [ord(c) for c in user]
    userLen = len(user_bytes)
    if len(serial) != userLen * 3:
        return False
    if isinstance(serial, (bytes, bytearray)):
        pwd = list(serial)
    else:
        pwd = list(serial)

    arg3 = 0

    # Section 1
    for i in range(userLen):
        expected = ((arg3 + 15) ^ user_bytes[i]) & 0xff
        if pwd[i] != expected:
            return False
        if i < userLen - 1:
            arg3 = expected
        else:
            arg3 = (expected - 10) & 0xff

    # Section 2
    for i in range(userLen):
        expected = ((18 - arg3) ^ user_bytes[i % userLen]) & 0xff
        if pwd[userLen + i] != expected:
            return False
        if i < userLen - 1:
            arg3 = expected
        else:
            arg3 = (expected + 113) & 0xff

    # Section 3
    for i in range(userLen):
        expected = (((arg3 - 76) * 2) ^ user_bytes[i % userLen]) & 0xff
        if pwd[2 * userLen + i] != expected:
            return False
        arg3 = expected

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
