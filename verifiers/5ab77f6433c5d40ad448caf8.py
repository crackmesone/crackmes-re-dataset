from itertools import permutations


def get_permutations(s):
    """Generate all permutations of string s in lexicographic order of indices."""
    perms = [''.join(p) for p in permutations(s)]
    return perms


def compute_serial(country_first5, name_sum):
    """
    Implements Dark.StrM logic.
    country_first5: first 5 chars of selected country string
    name_sum: sum of char values of letters in name
    """
    permut = get_permutations(country_first5)
    s2 = permut[3]
    s3 = permut[10]
    s4 = permut[17]

    ch1 = s2[3]
    ch2 = s3[3]
    ch3 = s4[3]

    n1 = ord(ch1)
    n2 = ord(ch2)
    n3 = ord(ch3)

    c1 = name_sum << 2
    c2 = c1 & 0xff
    c3 = c1 ^ c2
    c4 = c1 | c3

    d = c2 * 2 + c3 * 3 + c4 * 4 + n1 * 10 + n2 * 11 + n3 * 12

    s5 = str(d)
    s6 = s5
    s5 = s5[:2]
    y = int(s5)
    y1 = int(s6)

    a = [
        [2, 2, y],
        [4, 6, 2],
        [3, 4, 4]
    ]
    b = [
        [2, 2, 3],
        [8, 9, 5],
        [6, 2, 2]
    ]
    c = [[0]*3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            c[i][j] = 0
            for k in range(3):
                c[i][j] += a[i][k] * b[k][j]

    y2 = c[2][2]
    y2 = y2 * y1
    return str(y2)


# Valid country options as presented in the dropdown
COUNTRY_OPTIONS = ["Australia", "Brazil", "Egypt", "Germany", "India", "Mexico", "Other"]


def name_sum(name):
    """Sum of ASCII values of letters in name."""
    total = 0
    for ch in name:
        if ch.isalpha():
            total += ord(ch)
    return total


def verify(name, serial, country="India"):
    """
    Verify name+serial combo.
    country must be one of the dropdown options: Australia, Brazil, Egypt, Germany, India, Mexico, Other
    The crackme uses the country selection as the 'cmp' parameter but the actual check is:
      Dark.StrM(country, serial, sum_of_name_letters) returns the expected serial string
    """
    if country not in COUNTRY_OPTIONS:
        raise ValueError(f"Country must be one of {COUNTRY_OPTIONS}")
    # Need at least 5 characters in country name
    country5 = country[:5]
    if len(country5) < 5:
        # ASSUMPTION: country names in the list all have >= 5 chars; 'Other' has 5 chars, so this is fine
        pass
    s_sum = name_sum(name)
    expected = compute_serial(country5, s_sum)
    return serial == expected


def keygen(name, country="India"):
    """
    Generate the correct serial for the given name and country.
    country must be one of: Australia, Brazil, Egypt, Germany, India, Mexico, Other
    """
    if country not in COUNTRY_OPTIONS:
        raise ValueError(f"Country must be one of {COUNTRY_OPTIONS}")
    country5 = country[:5]
    s_sum = name_sum(name)
    return compute_serial(country5, s_sum)



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
