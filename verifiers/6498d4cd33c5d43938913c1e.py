# KeygenMePls by Wiktuur (.NET)
# Reverse-engineered from dnSpy decompilation (see writeups by cnathansmith and bang1338)
#
# KEY INSIGHT: The Check() function is:
#   return s1 == Key3(name) & s3 == Key2(name) & s2 == Key1(name)
# where s1/s2/s3 correspond to the three key boxes in display order.
#
# CRITICAL BUG: Key1(), Key2(), Key3() all use base.Name (the form name = "Form1")
# instead of the user-supplied name argument. So the key is FIXED regardless of username.
#
# The form name is always "Form1":
#   name[0]='F', name[1]='o', name[2]='r', name[3]='m', name[4]='1'
#
# Key1(name) = name[-1] + "118" + name[-3] + "4"
# Key2(name) = "132" + name[3] + "5" + name[3]
# Key3(name) = "12254" + name[2]
#
# The UI boxes map as:
#   keyBox1 (s1) must equal Key3()
#   keyBox2 (s2) must equal Key1()
#   keyBox3 (s3) must equal Key2()

FORM_NAME = "Form1"  # base.Name of the WinForms form -- hardcoded, not user input


def _compute_keys():
    """Compute the three fixed key parts using form name 'Form1'."""
    name = FORM_NAME
    key1 = f"{name[-1]}118{name[-3]}4"   # '1' + '118' + 'r' + '4' = '1118r4'
    key2 = f"132{name[3]}5{name[3]}"     # '132' + 'm' + '5' + 'm' = '132m5m'
    key3 = f"12254{name[2]}"             # '12254' + 'r' = '12254r'
    return key1, key2, key3


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial for a given username.
    Serial format: "<part1>-<part2>-<part3>" (hyphen-separated, spaces stripped)
    where part1=keyBox1, part2=keyBox2, part3=keyBox3.

    Note: 'name' is IGNORED by the real algorithm (bug in original code).
    The keys are derived from the hardcoded form name 'Form1'.
    """
    key1, key2, key3 = _compute_keys()

    # Parse serial -- expect format like "12254r - 1118r4 - 132m5m"
    parts = [p.strip() for p in serial.split('-')]
    if len(parts) != 3:
        return False

    s1, s2, s3 = parts[0], parts[1], parts[2]

    # From Check(): s1==Key3() & s3==Key2() & s2==Key1()
    return s1 == key3 and s2 == key1 and s3 == key2


def keygen(name: str) -> str:
    """
    Generate a valid serial for any username.
    Since the algorithm ignores the username (uses hardcoded form name),
    the same serial works for everyone.
    Returns serial as 'keyBox1 - keyBox2 - keyBox3'.
    """
    key1, key2, key3 = _compute_keys()
    # keyBox1=key3, keyBox2=key1, keyBox3=key2
    return f"{key3} - {key1} - {key2}"



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
