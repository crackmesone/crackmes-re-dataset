# Keygen for SirWardrake's KeygenMe(Second)_SWD
# Algorithm: simple character substitution via sbox
# Each character in the username (ASCII 0x21..0x7e) maps to a fixed string.
# The generated password is the concatenation of those strings.
# The password must be exactly 16 characters long (enforced by memcmp in the binary),
# so the username must be chosen such that the total length of substituted strings == 16.

# ASSUMPTION: sbox was recovered empirically by cnathansmith using the crackme itself;
# it covers printable ASCII from 0x21 ('!') to 0x7e ('~'), index = ord(c) - 0x21

sbox = [
    'd66','t96','K2','b32','r66','I64','Y98','p0',
    'G34','W64','n66','E96','U2','l32','C66','S96',
    'j98','A0','Q34','h64','x98','O96','f2','v32','M66',
    'd96','t98','K0','b34','r64','I98','Y0','p2','G32',
    'W66','n96','E2','U0','l34','C64','S98','j0','A2',
    'Q32','h66','x96','O2','f32','v34','M64','d98','t0',
    'K34','b32','r66','I96','Y2','p32','G34','W64',
    'n98','E0','U34','l64','C66','S96','j2','A32','Q66',
    'h64','x98','O0','f34','v64','M66','d96','t2','K32',
    'b66','r96','I98','Y0','p34','G64','W98','n96','E2',
    'U32','l66','C96','S98','j0','A34','Q64'
]


def _char_to_sub(c: str) -> str:
    """Return the substitution string for a single character, or raise ValueError."""
    idx = ord(c)
    if idx < 0x21 or idx > 0x7e:
        raise ValueError(f'Invalid character: {c!r} (must be printable ASCII 0x21-0x7e)')
    return sbox[idx - 0x21]


def verify(name: str, serial: str) -> bool:
    """
    Validate a (username, password) pair.
    The password must equal the concatenation of substitutions for each character
    in the username, AND the total length must be exactly 16.
    """
    try:
        expected = ''.join(_char_to_sub(c) for c in name)
    except ValueError:
        return False
    return len(expected) == 16 and serial == expected


def keygen(name: str) -> str:
    """
    Generate the correct password for the given username.
    Raises ValueError if any character is invalid.
    Also warns if the generated password is not exactly 16 characters
    (the crackme enforces this via memcmp with size check).
    """
    parts = [_char_to_sub(c) for c in name]
    password = ''.join(parts)
    if len(password) != 16:
        raise ValueError(
            f'Generated password has length {len(password)}, but the crackme requires exactly 16. '
            f'Choose a different username.'
        )
    return password


def find_valid_usernames(max_len: int = 10):
    """
    Generator that yields (username, password) pairs where the password
    is exactly 16 characters. Tries all single-character repeated usernames first,
    then brute-forces short combinations.
    """
    # Pre-compute lengths of each substitution
    chars = [chr(i) for i in range(0x21, 0x7f)]
    sub_lens = {c: len(_char_to_sub(c)) for c in chars}

    # Simple greedy: find characters whose substitutions divide 16
    # and build usernames of repeated characters
    for c in chars:
        l = sub_lens[c]
        if 16 % l == 0:
            n = 16 // l
            username = c * n
            password = ''.join(_char_to_sub(ch) for ch in username)
            yield username, password



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
