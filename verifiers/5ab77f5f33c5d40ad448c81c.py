import os
import ctypes

def get_windows_username():
    """Try to get the Windows logon username, fallback to os.getlogin()."""
    try:
        # On Windows, GetUserNameA or environment variable
        username = os.environ.get('USERNAME', '')
        if username:
            return username
        return os.getlogin()
    except Exception:
        return os.getlogin()

# ASSUMPTION: The 'windows username' used in the algorithm is the OS logon name.
# The algorithm described:
# Step 1: For each character in the typed Name (username field),
#         add the length of the Windows logon username to its ASCII value,
#         then add 2.
# Step 2: For each character produced by step 1,
#         subtract the length of the typed Name (username field) from it.
# The result is the expected serial/key string.
#
# Rules:
#   - Key (serial) must be at least 5 characters long
#     (since it's derived char-by-char from the name, name must be >= 5 chars)
#   - The name must NOT have length 7 (would cause abort)

def generate_key(name, windows_username=None):
    """Generate the expected key for a given name."""
    if windows_username is None:
        windows_username = get_windows_username()
    
    win_user_len = len(windows_username)
    name_len = len(name)
    
    key_chars = []
    for ch in name:
        # Step 1: add length of windows username, then add 2
        val = ord(ch) + win_user_len + 2
        # Step 2: subtract length of typed name
        val = val - name_len
        key_chars.append(chr(val & 0xFF))
    
    return ''.join(key_chars)

def verify(name, serial, windows_username=None):
    """Verify that the serial matches what is expected for the given name."""
    if windows_username is None:
        windows_username = get_windows_username()
    
    # Rule: key must be at least 5 characters
    if len(serial) < 5:
        return False
    
    # Rule: name must not have length 7
    if len(name) == 7:
        return False
    
    # ASSUMPTION: name must also be at least 5 chars (same rule applies)
    if len(name) < 5:
        return False
    
    expected = generate_key(name, windows_username)
    return serial == expected

def keygen(name, windows_username=None):
    """Generate a valid serial for the given name."""
    if windows_username is None:
        windows_username = get_windows_username()
    
    if len(name) < 5:
        raise ValueError('Name must be at least 5 characters long')
    if len(name) == 7:
        raise ValueError('Name must not be exactly 7 characters long')
    
    return generate_key(name, windows_username)


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
