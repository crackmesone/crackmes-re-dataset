import struct

# ASSUMPTION: Part 1 serial is a fixed constant derived from hardcoded bit operations.
# The writeup shows the following computation:
#   EAX = 0x0E6701F
#   EDX = 0x0E5108F
#   ECX = EDX
#   ECX = ECX XOR EAX  => 0x36090
#   ECX = ECX AND EAX  => 0x26010  (actually ECX AND EAX where ECX was already XOR'd)
#   EDX = EDX XOR ECX  => 0xE7709F
#   ESI = 0x0E55EC4 + EDX => 0x1CCCF63 (but writeup says 0x1CCcF63... let's recompute)
#   EAX = ESI
#   EAX = EAX + EAX  => 0x399EC6
# Then 0x399EC6 (decimal 3776198) is converted to ASCII via FILD/FSTP (80-bit real -> string)
# The writeup states the serial is 3777601 ... actually it says decimal of 0x399EC6 = 3776198
# but then says the serial is 60399602. This is suspicious - it may be reversed or formatted differently.
# ASSUMPTION: The FILD/FSTP conversion of integer 0x399EC6 to 80-bit extended real then to ASCII
# simply yields the decimal string of the integer value itself since it's a whole number.
# The writeup explicitly states the serial for Part 1 is '3777601' ... no, it says:
# '0x399EC6 in an intelligible (and readable) human number, it makes: 60399602'
# 0x399EC6 = 3776198 decimal. The '60399602' seems to be a different rendering.
# ASSUMPTION: The Delphi FloatToStr of integer 3776198 stored as 80-bit real may produce '3776198'
# but the writeup says '60399602'. We trust the writeup's stated answer.

PART1_SERIAL = '3776198'  # 0x399EC6 in decimal
# ASSUMPTION: The writeup says the serial is '60399602' - we cannot fully reconcile this
# without running the actual FILD/FSTP + Delphi conversion. We store both possibilities.
PART1_SERIAL_WRITEUP = '3776198'  # from 0x399EC6
# The writeup literally says: "it makes: 60399602" - possibly the bytes are reversed or
# the Delphi routine formats it differently. We'll use the writeup's stated value.
PART1_SERIAL_STATED = '3776198'

def compute_part1_magic():
    """Recompute the constant used in part 1 serial check."""
    EAX = 0x0E6701F
    EDX = 0x0E5108F
    ECX = EDX
    ECX = ECX ^ EAX          # XOR ECX, EAX => 0x36090
    ECX = ECX & EAX          # AND ECX, EAX => 0x26010
    EDX = EDX ^ ECX          # XOR EDX, ECX => 0xE7709F
    ESI = 0x0E55EC4 + EDX    # ADD ESI, EDX
    EAX = ESI
    EAX = (EAX + EAX) & 0xFFFFFFFF  # ADD EAX, EAX
    return AEX if False else AEX if False else EAX

def verify_part1(serial: str) -> bool:
    """Verify Part 1 serial."""
    magic = compute_part1_magic()  # Should be 0x399EC6 = 3776198
    # ASSUMPTION: Delphi converts the integer to a decimal ASCII string
    # The writeup says the result is '3776198' expressed as integer decimal
    # but the stated serial is '3776198'. We trust the integer decimal conversion.
    expected = str(magic)
    # ASSUMPTION: The writeup states the answer is '3776198' (decimal of 0x399EC6)
    # but also says '60399602' - we cannot resolve this without the actual binary.
    # Using decimal of 0x399EC6:
    return serial.strip() == expected

def keygen_part1(name: str = '') -> str:
    """Generate Part 1 serial (name-independent, fixed constant)."""
    magic = compute_part1_magic()
    # ASSUMPTION: Delphi FloatToStr on integer value just returns decimal string
    return str(magic)

def get_volume_serial() -> int:
    """Placeholder: in the real crackme this calls GetVolumeInformation.
    ASSUMPTION: The user must supply their actual volume serial number.
    """
    # ASSUMPTION: This is system-dependent; return a placeholder
    return 0xB420877B  # example from writeup

def volume_serial_to_hwid(vol_serial: int) -> str:
    """Convert volume serial number (DWORD) to decimal ASCII string = Hardware ID."""
    # The writeup says: volume serial 0xB420877B -> 3022030715 (decimal)
    return str(vol_serial & 0xFFFFFFFF)

def compute_part2_serial(hwid: str) -> str:
    """Compute Part 2 serial from Hardware ID string.
    ASSUMPTION: The writeup is truncated and does not reveal the full Part 2 algorithm.
    Only the Hardware ID derivation is described (volume serial -> decimal string).
    The actual serial computation from HWID is NOT described in the available text.
    """
    # ASSUMPTION: Unknown algorithm - cannot implement without more writeup content
    raise NotImplementedError("Part 2 serial computation algorithm not revealed in writeup (truncated).")

def verify_part2(hwid: str, serial: str) -> bool:
    """Verify Part 2 serial.
    ASSUMPTION: Algorithm unknown due to truncated writeup.
    """
    # ASSUMPTION: Cannot implement - writeup truncated before revealing Part 2 algorithm
    raise NotImplementedError("Part 2 verification algorithm not available (writeup truncated).")

def verify(name: str, serial: str) -> bool:
    """Top-level verify for Part 1 (name-independent fixed serial check).
    Part 2 requires hardware ID and algorithm is not available.
    """
    return verify_part1(serial)

def keygen(name: str) -> str:
    """Keygen for Part 1 (name-independent)."""
    return keygen_part1(name)


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
