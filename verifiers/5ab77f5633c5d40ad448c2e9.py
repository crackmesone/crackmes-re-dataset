# Reconstruction of antisocial_crackme_i by anonimoser
# Based on the keygen source (Antisocial.Asm) provided in the solution writeup.
#
# The crackme accepts a Name, an ID, and validates a Serial.
# The keygen works as follows:
#   1. CalcSeed(name)  -> nameseed  (integer)
#   2. CalcSeed(id)    -> idseed    (integer)
#   3. nameidseed = sprintf("%lu%lu", nameseed, idseed)  (decimal string concat)
#   4. Build serial from nameidseed using a character-interleaving formula.
#
# CalcSeed(buf):
#   seed = len(buf) * 0x29A
#   for i in range(1, len+1):
#       seed += buf[i-1] * i
#   return seed
#
# Serial construction (1-based index i from 1..strlen):
#   serial[2*i-2] = nameidseed[i-1]          (copy char)
#   serial[2*i-1] = chr( (strlen*i % (i*i)) + 0x41 )   (computed char)
#
# NOTE: The writeup was truncated so the exact CalcSeed loop body is partially
# inferred from context ("result = strlen*0x29A" then accumulate per-char * index).
# ASSUMPTION: CalcSeed accumulates: seed = len*0x29A + sum(char[i]*i for i in 1..len)

def calc_seed(buf: str) -> int:
    """Calculate the seed for a given string."""
    length = len(buf)
    seed = length * 0x29A  # imul edi, eax, 29Ah
    for i in range(1, length + 1):
        # ASSUMPTION: each character contributes ord(char)*i to the seed
        seed += ord(buf[i - 1]) * i
    return seed


def build_serial(nameidseed: str) -> str:
    """Build the serial string from the combined name+id seed string."""
    strlen = len(nameidseed)
    serial_chars = ['\x00'] * (strlen * 2)

    for i in range(1, strlen + 1):  # i from 1 to strlen (like ebx in asm)
        # serial[2*i-2] = nameidseed[i-1]
        serial_chars[2 * i - 2] = nameidseed[i - 1]

        # serial[2*i-1] = (strlen * i % (i * i)) + 0x41
        numerator = strlen * i
        divisor = i * i
        # idiv: signed division, remainder in edx
        remainder = numerator % divisor  # ASSUMPTION: positive remainder (Python % is always non-negative)
        ch = (remainder + 0x41) & 0xFF
        serial_chars[2 * i - 1] = chr(ch)

    return ''.join(serial_chars)


def keygen(name: str, id_str: str) -> str:
    """
    Generate the serial for a given name and ID.
    Both name and id_str must be at least 4 characters.
    """
    if len(name) < 4 or len(id_str) < 4:
        raise ValueError("Name and ID must be >= 4 characters")

    nameseed = calc_seed(name)
    idseed = calc_seed(id_str)

    # wsprintf(nameidseed, "%lu%lu", nameseed, idseed)
    # %lu is unsigned long decimal in C; Python integers are always non-negative here
    # ASSUMPTION: nameseed and idseed fit in 32-bit unsigned
    nameseed_u = nameseed & 0xFFFFFFFF
    idseed_u = idseed & 0xFFFFFFFF
    nameidseed = "%d%d" % (nameseed_u, idseed_u)

    serial = build_serial(nameidseed)
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify a (name, id, serial) tuple.
    Since the crackme uses both name and id, we embed id in the serial check.
    ASSUMPTION: The crackme's verify just checks that serial == keygen(name, id).
    This function takes serial as a string but we need the id too.
    We redefine: verify(name_plus_id, serial) where name_plus_id = 'name|id'.
    """
    # ASSUMPTION: caller passes name and serial; we need the ID separately.
    # For a pure (name, serial) interface, we cannot verify without ID.
    # We just expose the keygen and note the limitation.
    raise NotImplementedError(
        "verify() requires both name and id. Use keygen(name, id_str) to produce a serial, "
        "then check serial == keygen(name, id_str)."
    )


def verify_with_id(name: str, id_str: str, serial: str) -> bool:
    """Verify a name+id+serial triple."""
    expected = keygen(name, id_str)
    return serial == expected



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
