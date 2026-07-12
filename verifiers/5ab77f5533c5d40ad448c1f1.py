def calc_password_length(name: str) -> int:
    """
    Steps 3-6 from the algorithm:
    large = len(name)
    large = large * 2 + 10
    if large != 50: large -= 7
    if first char is uppercase: large += 2
    if last char is uppercase: large += 3
    """
    large = len(name)
    large = large * 2 + 10
    if large != 50:
        large -= 7
    if 'A' <= name[0] <= 'Z':
        large += 2
    if 'A' <= name[-1] <= 'Z':
        large += 3
    return large


def get_capitals(name: str) -> str:
    """Extract only uppercase letters A-P from name (step 8: uppercase A-P)."""
    # ASSUMPTION: The source says 'A~P' range for capitals extracted into C,
    # but then the main loop checks 64 < ord(ch) < 91 (i.e., A-Z).
    # The original Chinese comment says 'A~P', but code uses A-Z.
    # We follow the actual code logic (A-Z).
    return ''.join(ch for ch in name if 'A' <= ch <= 'Z')


def verify(name: str, serial: str) -> bool:
    """
    Validates name and serial according to the crackme algorithm.
    """
    # Name must be 1-20 chars, all uppercase A-Z
    if not (0 < len(name) < 21):
        return False
    for ch in name:
        if not ('A' <= ch <= 'Z'):
            return False

    # Serial must be 1-50 chars
    if not (0 < len(serial) < 51):
        return False

    # Serial length must be strictly greater than name length
    if len(serial) <= len(name):
        return False

    # Calculate expected password length
    large = calc_password_length(name)

    # Check serial length matches computed large
    if len(serial) != large:
        return False

    # Build capitals string C (all uppercase letters from name)
    C = get_capitals(name)
    nCapital = len(C)

    if nCapital == 0:
        return False

    # X = large / len(C)  (integer division)
    X = large // nCapital

    # Now walk through serial checking placement:
    # F indexes C (capitals), J indexes non-capital chars in name, M for xyz cycling
    # xyz cycle: szChoice = ['z', 'x', 'y'], index by (u % 3) starting u=1
    # so cycle starting at u=1: szChoice[1%3]=x, szChoice[2%3]=y, szChoice[0%3]=z, ...
    xyz_choice = ['z', 'x', 'y']

    F = 0  # index into C (capitals)
    J = 0  # index into name for non-capital chars
    M = 1  # xyz counter starting at 1

    for i in range(large):
        # Check if this position is a 'cut point' for a capital
        if F < nCapital and i == F * X:
            # serial[i] must equal C[F]
            if serial[i] != C[F]:
                return False
            F += 1
        else:
            # Find next non-capital in name starting at J
            while J < len(name):
                if 'A' <= name[J] <= 'Z':
                    J += 1
                else:
                    break

            if J >= len(name):
                # Fill with xyz cycling
                expected = xyz_choice[M % 3]
                if serial[i] != expected:
                    return False
                M += 1
            else:
                # Fill with name[J] (non-capital char)
                if serial[i] != name[J]:
                    return False
                J += 1

    return True


def keygen(name: str) -> str:
    """
    Generates a valid serial for a given name.
    Name must be 1-20 uppercase letters (A-Z) with at least one char.
    Since the crackme requires all uppercase, the name is all capitals.
    """
    # Validate name
    if not (0 < len(name) < 21):
        raise ValueError("Name must be 1-20 characters")
    for ch in name:
        if not ('A' <= ch <= 'Z'):
            raise ValueError("Name must contain only uppercase letters A-Z")

    large = calc_password_length(name)
    C = get_capitals(name)
    nCapital = len(C)

    if nCapital == 0:
        raise ValueError("Name must have at least one uppercase letter")

    X = large // nCapital

    xyz_choice = ['z', 'x', 'y']

    result = [''] * large
    F = 0
    J = 0
    M = 1

    for i in range(large):
        if F < nCapital and i == F * X:
            result[i] = C[F]
            F += 1
        else:
            while J < len(name):
                if 'A' <= name[J] <= 'Z':
                    J += 1
                else:
                    break

            if J >= len(name):
                result[i] = xyz_choice[M % 3]
                M += 1
            else:
                result[i] = name[J]
                J += 1

    serial = ''.join(result)
    return serial



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
