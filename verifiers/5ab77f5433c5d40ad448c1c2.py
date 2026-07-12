#!/usr/bin/env python3
"""
smokefx_v2 by waynemodz - Key Validation Algorithm

Based on the writeup by GIV:
- Name must be >= 4 characters
- Name is converted to lowercase
- Spaces and dots are stripped (not allowed)
- For each character in the lowercased, stripped name:
  Part 1: If ASCII value is in range 0x30..0x39 (digits '0'-'9'):
    The digit is converted to int, then passed through sub_0045AA60 (unknown),
    then IntToStr is called and the result is appended.
    # ASSUMPTION: sub_0045AA60 is unknown; we skip digit handling or assume identity.
  Part 2 (letters a-m, ASCII 0x61..0x6D, i.e. <= 109 = 0x6D 'm'):
    result_char = chr(ord(char) + position)  # position is 1-based
    result_num  = position + 3
    append result_char + str(result_num)
  Part 3 (letters n-z, ASCII > 0x6D, i.e. > 109):
    result_char = chr(ord(char) - position)  # position is 1-based
    result_num  = position + 1
    append result_char + str(result_num)

Example from writeup:
  'aaaa' -> 'b4c5d6e7'  (a=0x61 <= 0x6D, pos1: chr(97+1)='b', 1+3=4 -> 'b4'; pos2: 'c5'; etc.)
  'nnnn' -> 'm2l3k4j5'  (n=0x6E > 0x6D, pos1: chr(110-1)='m', 1+1=2 -> 'm2'; pos2: 'l3'; etc.)
"""

def _process_name(name: str) -> str:
    """Lowercase and strip spaces/dots."""
    name = name.lower()
    name = name.replace(' ', '').replace('.', '')
    return name


def _compute_serial(cleaned_name: str) -> str:
    serial = ''
    for i, ch in enumerate(cleaned_name):
        pos = i + 1  # 1-based position
        ascii_val = ord(ch)

        if '0' <= ch <= '9':
            # Digit branch: passes through sub_0045AA60 then IntToStr
            # ASSUMPTION: sub_0045AA60 behavior is unknown; we treat it as identity
            # and just append the digit converted to int then back to string.
            digit_int = int(ch)
            # ASSUMPTION: sub_0045AA60 might do some transformation; skipping it.
            serial += str(digit_int)
        elif ascii_val <= 0x6D:  # 'a' to 'm' (ASCII 97..109)
            # Part 1: char += position, num = position + 3
            result_char = chr(ascii_val + pos)
            result_num = pos + 3
            serial += result_char + str(result_num)
        else:  # 'n' to 'z' (ASCII 110..122)
            # Part 2: char -= position, num = position + 1
            result_char = chr(ascii_val - pos)
            result_num = pos + 1
            serial += result_char + str(result_num)

    return serial


def verify(name: str, serial: str) -> bool:
    cleaned = _process_name(name)
    if len(cleaned) < 4:
        return False
    expected = _compute_serial(cleaned)
    return serial == expected


def keygen(name: str) -> str:
    cleaned = _process_name(name)
    if len(cleaned) < 4:
        raise ValueError(f"Name (cleaned) must be at least 4 characters, got: '{cleaned}'")
    return _compute_serial(cleaned)



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
