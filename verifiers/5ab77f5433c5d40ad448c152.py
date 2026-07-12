import struct

def abss(i):
    """Equivalent to i * ((i > 0) ? 1 : -1) in C (long int)"""
    # Note: in C with signed long int, abss(0) = 0*(-1) = 0
    if i > 0:
        return i
    else:
        return -i

def keygen(name, email):
    """Generate serial for given name and email."""
    buffer = [0] * (0x100 * 2)  # two sections of 0x100 dwords
    # buffer[0..0xFF] = i, buffer[0x100..0x1FF] = name[i % len(name)]
    for i in range(0x100):
        buffer[i] = i
        buffer[0x100 + i] = ord(name[i % len(name)])

    # First key-scheduling loop (RC4-like KSA using name)
    c1 = 0
    c2 = 0
    for i in range(0x100):
        eax = c2
        eax += buffer[i]          # buffer[i*4] in C
        eax += buffer[0x100 + i]  # buffer[i*4 + 0x400] in C
        c2 = abss(eax) & 0xFF
        t01 = buffer[i]
        buffer[i] = buffer[c2]
        buffer[c2] = t01

    # Second loop (RC4-like PRGA, XOR with email)
    c1 = 0
    c2 = 0
    email_buf = []
    for i in range(0x20):
        email_buf.append(ord(email[i % len(email)]))

    result = []
    for i in range(0x20):
        c1 = abss(c1 + 1) & 0xFF
        c2 = abss(c2 + buffer[c1]) & 0xFF

        t01 = buffer[c1]
        buffer[c1] = buffer[c2]
        buffer[c2] = t01

        t01 = buffer[c1]
        t01 += buffer[c2]
        t01 = abss(t01) & 0xFF
        t02 = buffer[t01]

        r = email_buf[i] ^ t02
        result.append(r & 0xFF)

    # Serial format: first byte is printed as '0', rest as decimal integers concatenated
    # From the keygen: if i==0 print '0', else print (int)(r & 0xFF)
    serial = '0'
    for i in range(1, 0x20):
        serial += str(result[i])
    return serial

def verify(name, serial):
    """Verify name/email pair - but the crackme uses email not name for second loop.
    The serial is compared against generated serial via strcmp.
    We need both name and email; 'serial' here is the email to try.
    Actually: verify(name, email) -> computed serial, then compare with entered serial.
    
    To match the crackme interface: verify(name, email_and_serial) is ambiguous.
    We implement verify(name, email) -> bool by checking if keygen produces a valid serial.
    Since we don't have the entered serial to compare against here, we return the serial.
    
    For a real verify(name_email_tuple, serial) call:
    """
    # ASSUMPTION: The crackme takes name + email as inputs and checks entered serial
    # against computed serial. We treat 'serial' parameter as the entered serial string,
    # and 'name' as a tuple (name, email) or we treat email as a separate argument.
    # Implementing as: name = actual username, serial = 'email:entered_serial'
    if ':' in serial:
        parts = serial.split(':', 1)
        email = parts[0]
        entered_serial = parts[1]
        computed = keygen(name, email)
        return computed == entered_serial
    else:
        # ASSUMPTION: serial is the email, return computed serial for display
        return keygen(name, serial)


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
