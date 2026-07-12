# Self-contained implementation of all 5 crackme algorithms from
# W02057's Ultimate Kit for Newbies

# NOTE: The crackme kit has 5 separate challenges.
# We implement verify/keygen for each, then provide a unified dispatcher.
# The 'name' parameter is used as the crackme number selector when calling
# the unified verify/keygen (e.g. name='1' or '2:Alice').
# For direct use, call verify_N / keygen_N directly.


# ---- Crackme #1: Fixed password ----
# Password (case-insensitive) must equal 'monkeypoop'
def verify_1(password: str) -> bool:
    return password.lower() == 'monkeypoop'

def keygen_1() -> str:
    return 'monkeypoop'


# ---- Crackme #2: serial = name + '1234' ----
def verify_2(name: str, serial: str) -> bool:
    if name == '':
        return False
    if serial == '':
        return False
    return serial == name + '1234'

def keygen_2(name: str) -> str:
    return name + '1234'


# ---- Crackme #3: serial = name + str(len(name) + 28) ----
def verify_3(name: str, serial: str) -> bool:
    if name == '':
        return False
    if serial == '':
        return False
    expected = name + str(len(name) + 28)
    return serial == expected

def keygen_3(name: str) -> str:
    return name + str(len(name) + 28)


# ---- Crackme #4: serial = first4chars(name) + '2254', name must be >= 8 chars ----
# Note: Strings.Mid(name, 1, 4) in VB is 1-indexed, returns first 4 chars
def verify_4(name: str, serial: str) -> bool:
    if len(name) < 8:
        return False
    if serial == '':
        return False
    first4 = name[:4]
    expected = first4 + '2254'
    return serial == expected

def keygen_4(name: str) -> str:
    if len(name) < 8:
        raise ValueError('Username must be at least 8 characters long.')
    return name[:4] + '2254'


# ---- Crackme #5: serial = character-substitution cipher applied to lowercase name (spaces removed) ----
# The substitution table from the decompiled code:
SUBSTITUTION = {
    'a': '@',
    'b': '1',
    'c': '*',
    'd': '4',
    'e': '!',
    'f': '#',
    'g': '-',
    'h': '%',
    'i': '\u00a3',  # £
    'j': '$',
    'k': '^',
    'l': "'",
    'm': '.',
    'n': '~',
    'o': '+',
    'p': '=',
    'q': '2',
    'r': '\\',
    's': '9',
    't': '/',
    'u': '6',
    'v': ':',
    'w': '8',
    'x': ']',
    'y': '7',
    'z': '[',
}

def _apply_substitution(name: str) -> str:
    """Apply crackme#5 substitution: lowercase, remove spaces, replace chars."""
    s = name.lower().replace(' ', '')
    # Apply each replacement in order (as the original code chains .Replace() calls)
    # Since the replacements are from original letters to symbols,
    # and the targets are non-alpha symbols, order does not cause conflicts.
    result = ''
    for ch in s:
        result += SUBSTITUTION.get(ch, ch)
    return result

def verify_5(name: str, serial: str) -> bool:
    if serial == '':
        return False
    expected = _apply_substitution(name)
    return serial == expected

def keygen_5(name: str) -> str:
    return _apply_substitution(name)


# ---- Unified dispatcher ----
# For compatibility with the verify(name, serial) -> bool signature,
# we treat 'name' as '<crackme_number>:<actual_name>' for crackmes 2-5,
# and '<crackme_number>' for crackme 1.
# For standalone use, call verify_N / keygen_N directly.

def verify(name: str, serial: str) -> bool:
    """
    Unified verify dispatcher.
    name format:
      '1'         -> crackme 1 (serial is the password)
      '2:Alice'   -> crackme 2, username=Alice
      '3:Alice'   -> crackme 3, username=Alice
      '4:AliceXYZ'-> crackme 4, username=AliceXYZ (>=8 chars)
      '5:James Perry' -> crackme 5, name=James Perry
    serial: the password/serial to check
    """
    parts = name.split(':', 1)
    crackme_num = parts[0].strip()
    actual_name = parts[1] if len(parts) > 1 else ''

    if crackme_num == '1':
        return verify_1(serial)
    elif crackme_num == '2':
        return verify_2(actual_name, serial)
    elif crackme_num == '3':
        return verify_3(actual_name, serial)
    elif crackme_num == '4':
        return verify_4(actual_name, serial)
    elif crackme_num == '5':
        return verify_5(actual_name, serial)
    else:
        raise ValueError(f'Unknown crackme number: {crackme_num}')


def keygen(name: str) -> str:
    """
    Unified keygen dispatcher.
    name format same as verify().
    """
    parts = name.split(':', 1)
    crackme_num = parts[0].strip()
    actual_name = parts[1] if len(parts) > 1 else ''

    if crackme_num == '1':
        return keygen_1()
    elif crackme_num == '2':
        return keygen_2(actual_name)
    elif crackme_num == '3':
        return keygen_3(actual_name)
    elif crackme_num == '4':
        return keygen_4(actual_name)
    elif crackme_num == '5':
        return keygen_5(actual_name)
    else:
        raise ValueError(f'Unknown crackme number: {crackme_num}')


# ---- Self-test ----

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
