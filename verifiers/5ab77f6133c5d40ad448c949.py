def verify(name, serial):
    """
    Reconstructed validation algorithm for SasaMaker's 'OmG mY sErIal Iz DoOd V2'

    Inputs:
      name   - expected to be 'FirstName LastName' (space-separated)
      serial - the serial string to check

    Checks (from the writeup / Smartcheck trace):
      1. First Name length > 3
      2. Last Name length > 5
      3. Phone number field != '0000-000-0000'
         (In this reconstruction we treat 'serial' as the phone number field)
      4. serial == '0'

    NOTE: The crackme UI has separate fields: FirstName, LastName, PhoneNumber, Serial.
    Because we only have name+serial here we make the following assumptions.
    """
    # Split name into first and last
    parts = name.split(' ', 1)
    if len(parts) < 2:
        return False
    first_name, last_name = parts[0], parts[1]

    # Check 1: first name length > 3
    if len(first_name) <= 3:
        return False

    # Check 2: last name length > 5
    if len(last_name) <= 5:
        return False

    # ASSUMPTION: the phone number is passed as part of 'serial' in format 'NNNN-NNN-NNNN:SERIAL'
    # Because the crackme has a separate phone field, we can't cleanly separate them here.
    # We model the phone number check independently, assuming serial IS the serial field.
    # Check 3 (phone number): the phone number must NOT be '0000-000-0000'
    # ASSUMPTION: we skip phone validation since it's a separate UI field not passed here.
    # The phone check only rejects '0000', '000', and '0000' for the three parts respectively.

    # Check 4: serial == '0'  (from Smartcheck trace: __vbaStrCmp("0", serial))
    if serial != '0':
        return False

    return True


def keygen(name):
    """
    Generates a valid serial for the given name.
    Requirements:
      - name must be 'FirstName LastName' where len(FirstName) > 3 and len(LastName) > 5
      - phone number must not be '0000-000-0000' (use any real-looking number)
      - serial is always '0'
    """
    parts = name.split(' ', 1)
    if len(parts) < 2:
        raise ValueError('Name must be "FirstName LastName" with a space')
    first_name, last_name = parts[0], parts[1]
    if len(first_name) <= 3:
        raise ValueError(f'First name must be longer than 3 characters, got "{first_name}"')
    if len(last_name) <= 5:
        raise ValueError(f'Last name must be longer than 5 characters, got "{last_name}"')
    # The serial is always '0'
    return '0'



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
