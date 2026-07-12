import math
from datetime import datetime


def get_modifier() -> int:
    """
    C# equivalent:
        int dayOfWeek = (int)DateTime.Now.DayOfWeek;  // Sunday=0, Monday=1, ..., Saturday=6
        int day = DateTime.Now.Day;
        return ((int)Math.Pow(day, dayOfWeek) ^ (day * dayOfWeek)) % 26;
    """
    now = datetime.now()
    day = now.day
    # C# DayOfWeek: Sunday=0, Monday=1, ..., Saturday=6
    # Python weekday(): Monday=0, ..., Sunday=6  ->  convert:
    python_weekday = now.weekday()
    csharp_day_of_week = (python_weekday + 1) % 7

    pow_part = int(math.pow(day, csharp_day_of_week))
    mul_part = day * csharp_day_of_week
    return (pow_part ^ mul_part) % 26


def get_math(username: str) -> str:
    """
    C# equivalent (from Form1.cs):
        string text = "";
        for (int i = 0; i < username.Length; i++)
            text += username[i] ^ GetModifier();
        if (text.Length % 2 != 0)
            text += "1";
        do {
            int result;
            int.TryParse(text.Substring(0, 2), out result);
            text2 = (result <= 26) ? (text2 + (char)(result + 64)) : (text2 + result);
            text = text.Substring(2);
        } while (text != "");
        return text2;
    NOTE: username[i] ^ GetModifier() in C# on a char produces an int, which is then
    concatenated to a string via implicit int-to-string conversion.
    """
    modifier = get_modifier()

    # Step 1: XOR each character with modifier, concatenate numeric string representations
    text = ""
    for ch in username:
        xor_value = ord(ch) ^ modifier
        text += str(xor_value)

    # Step 2: Pad with '1' if odd length
    if len(text) % 2 != 0:
        text += "1"

    # Step 3: Process two digits at a time
    text2 = ""
    while text != "":
        chunk = text[:2]
        try:
            result = int(chunk)
        except ValueError:
            result = 0
        if result <= 26:
            # chr(result + 64): 1->A, 2->B, ..., 26->Z, 0->@ (edge case)
            text2 += chr(result + 64)
        else:
            text2 += str(result)
        text = text[2:]

    return text2


def keygen(name: str) -> str:
    """Generate the serial/password for the given username (valid for today only)."""
    if not name:
        return ""
    return get_math(name)


def verify(name: str, serial: str) -> bool:
    """Return True if serial matches the expected key for name (today)."""
    if not name:
        return False
    return get_math(name) == serial



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
