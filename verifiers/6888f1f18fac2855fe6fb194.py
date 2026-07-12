import ctypes
import struct
from datetime import datetime

# NATO alphabet lookup table (every other 16-byte slot is a name, odd slots are spaces)
# The NATO string has entries at indices 0,2,4,...,50 (26 letters * 2 slots each)
NATO_WORDS = [
    "ALPHA", "BRAVO", "CHARLIE", "DELTA", "ECHO", "FOXTROT",
    "GOLF", "HOTEL", "INDIA", "JULIET", "KILO", "LIMA",
    "MIKE", "NOVEMBER", "OSCAR", "PAPA", "QUEBEC", "ROMEO",
    "SIERRA", "TANGO", "UNIFORM", "VICTOR", "WHISKEY",
    "XRAY", "YANKEE", "ZULU"
]


def CalculateInitialCoordinates(name: str, hour: int) -> tuple:
    """
    ASSUMPTION: The initial coordinate is computed from the player name and current hour.
    The exact hash algorithm used inside the crackme is not fully shown in the writeup.
    Based on the structure, we know:
    - name is stored in a std::string-like structure (small string optimization: <16 chars inline)
    - isNightTime = 1 if hour >= 18 or hour < 6, else 0
    - The hash is stored in RiceField.InitialCoordinate
    We reconstruct a plausible name hash below; this is a PARTIAL recovery.
    """
    # ASSUMPTION: isNightTime is determined by the hour
    isNight = 1 if (hour >= 18 or hour < 6) else 0

    # ASSUMPTION: Initial coordinate is a simple accumulation hash over the name bytes
    # The exact algorithm is not shown in the writeup; this is a placeholder
    coord = 0
    for ch in name:
        coord = (coord * 31 + ord(ch)) & 0xFFFFFFFF
    # ASSUMPTION: hour is mixed in somehow
    coord = (coord ^ (hour & 0xFF)) & 0xFFFFFFFF
    return coord, isNight


def CalculateFinalCoordinates(initialCoordinates: int, isNight: int) -> int:
    """
    ASSUMPTION: The final coordinate incorporates the day/night flag.
    The exact transformation is not shown; we assume XOR with a night flag shift.
    """
    # ASSUMPTION: simple combination; real algorithm not shown in writeup
    result = initialCoordinates
    if isNight:
        result = (result ^ 0xDEADBEEF) & 0xFFFFFFFF
    else:
        result = (result ^ 0xCAFEBABE) & 0xFFFFFFFF
    return result


def CalculateNatoIndex(byte_val: int) -> int:
    """
    From the writeup: each byte of targetCoordinate has 0x9c subtracted (mod 256)
    to get an index into the NATO table.
    """
    return (byte_val - 0x9c) & 0xFF


def ExtractionSignalGenerator(targetCoordinate: int) -> str:
    """
    Reconstructed from the writeup source code.
    The 4 bytes of targetCoordinate each map (after subtracting 0x9c mod 256)
    to a NATO word index (mod 26).
    The serial is four NATO words separated by dashes (ASSUMPTION on separator).
    """
    p3 = (targetCoordinate >> 24) & 0xFF
    p2 = (targetCoordinate >> 16) & 0xFF
    p1 = (targetCoordinate >> 8) & 0xFF
    p0 = targetCoordinate & 0xFF

    p3Num = (p3 - 0x9c) & 0xFF
    p2Num = (p2 - 0x9c) & 0xFF
    p1Num = (p1 - 0x9c) & 0xFF
    p0Num = (p0 - 0x9c) & 0xFF

    # ASSUMPTION: index wraps mod 26 to select a NATO word
    w3 = NATO_WORDS[p3Num % 26]
    w2 = NATO_WORDS[p2Num % 26]
    w1 = NATO_WORDS[p1Num % 26]
    w0 = NATO_WORDS[p0Num % 26]

    # ASSUMPTION: separator is '-'; the writeup truncates before showing the join format
    serial = f"{w3}-{w2}-{w1}-{w0}"
    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial combination.
    ASSUMPTION: The serial is compared to the output of ExtractionSignalGenerator
    using the current hour at verification time (same as during keygen).
    The crackme reads hour at runtime, so we do the same.
    """
    hour = datetime.now().hour
    initial, isNight = CalculateInitialCoordinates(name, hour)
    final = CalculateFinalCoordinates(initial, isNight)
    expected = ExtractionSignalGenerator(final)
    return serial.strip().upper() == expected.upper()


def keygen(name: str) -> str:
    """
    Generate a serial for the given name using the current time.
    NOTE: Due to partial algorithm recovery, this keygen is approximate.
    The real crackme uses mt19937 seeded by std::_Random_device() for some steps,
    and the exact CalculateInitialCoordinates and CalculateFinalCoordinates
    implementations are not fully shown in the writeup.
    """
    hour = datetime.now().hour
    initial, isNight = CalculateInitialCoordinates(name, hour)
    final = CalculateFinalCoordinates(initial, isNight)
    serial = ExtractionSignalGenerator(final)
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
