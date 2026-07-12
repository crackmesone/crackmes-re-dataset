import hashlib

# ASSUMPTION: The 'letter' function extracts only alphabetic characters from a string
# ASSUMPTION: The 'number' function extracts only digit characters from a string
# ASSUMPTION: The hardware ID is read from the system (we cannot reproduce exactly without knowing the machine)
# ASSUMPTION: Strings.Mid in VB is 1-based; we translate accordingly
# ASSUMPTION: sha1 returns hex digest (lowercase), then UCase is applied at the end

def sha1(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()

def letter(s):
    """Extract only alphabetic characters from s."""
    return ''.join(c for c in s if c.isalpha())

def number(s):
    """Extract only digit characters from s."""
    return ''.join(c for c in s if c.isdigit())

def generate_serial(name, hardware_id):
    """
    Generates a serial for the given name and hardware_id.
    
    Algorithm (from disassembly):
    1. sString = sha1(name + hardware_id)
    2. sString = number(sString) + letter(sString)   # separate digits and letters, concat
    3. sString = sha1(sString)                        # hash again
    4. str2 = sString[0:4]                            # first 4 chars
    5. str  = letter(sString)                         # letters only from sString
       str  = str[len(str)-4 : len(str)-4+4]         # last 4 chars of letters
       # ASSUMPTION: VB Mid(str, str.Length-4, 4) => 0-based: str[len-4:len] (last 4 chars of letter-only string)
    6. str5 = number(sString)[0:4]                    # first 4 digits of sString
    7. str3 = sString[len(sString)-4 : len(sString)] # last 4 chars of sString
    8. serial = UCase(str2 + '-' + str + '-' + str5 + '-' + str3)
    """
    # Step 1
    s_string = sha1(name + hardware_id)
    
    # Step 2: separate numbers and letters, numbers first then letters
    s_string = number(s_string) + letter(s_string)
    
    # Step 3: hash again
    s_string = sha1(s_string)
    
    # Step 4: first 4 chars
    # VB Mid(sString, 1, 4) => 0-based [0:4]
    str2 = s_string[0:4]
    
    # Step 5: letters only, then last 4 chars
    letters_only = letter(s_string)
    # VB: Strings.Mid(str, (str.Length - 4), 4)
    # VB Mid is 1-based, so Mid(str, str.Length-4, 4) => 0-based: [str.Length-4-1 : str.Length-4-1+4] = [len-5:len-1]
    # ASSUMPTION: VB Mid(s, start, length) where start is 1-based.
    # Mid(str, str.Length-4, 4): start=str.Length-4 (1-based), length=4
    # 0-based: start_0 = (str.Length-4) - 1 = str.Length-5
    # So: letters_only[len-5 : len-1]
    # However, writeup solution 2 says 'take last 4 chars' so likely they mean the last 4
    # ASSUMPTION: treating as last 4 chars (str[-4:])
    if len(letters_only) >= 4:
        str_var = letters_only[-4:]
    else:
        str_var = letters_only.ljust(4, '0')
    
    # Step 6: first 4 digits
    nums_only = number(s_string)
    str5 = nums_only[0:4] if len(nums_only) >= 4 else nums_only.ljust(4, '0')
    
    # Step 7: last 4 chars of sString
    # VB: Strings.Mid(sString, sString.Length - 4, 4)
    # 1-based start = sString.Length-4, length=4 => 0-based [len-5:len-1]
    # Again writeup says 'last 4 chars'
    # ASSUMPTION: treating as last 4 chars
    str3 = s_string[-4:]
    
    # Step 8: assemble and uppercase
    serial = (str2 + '-' + str_var + '-' + str5 + '-' + str3).upper()
    return serial

def verify(name, serial):
    """
    Verify a serial for a given name.
    NOTE: This crackme uses hardware ID (from TotalPhysicalMemory + ComputerName).
    Since we cannot know the hardware ID, we cannot verify without it.
    This function attempts to verify by trying to reconstruct the serial.
    ASSUMPTION: hardware_id must be provided externally; here we cannot auto-detect.
    """
    # ASSUMPTION: Without knowing the hardware_id, we cannot fully verify.
    # This is a hardware-locked crackme.
    if serial is None or len(serial) != 19:
        return False
    # We cannot verify without hardware_id
    raise NotImplementedError("Hardware ID required for verification. Use keygen(name, hardware_id) instead.")

def keygen(name, hardware_id=""):
    """
    Generate a valid serial for name + hardware_id.
    hardware_id: the hardware ID string shown in the crackme UI (from TotalPhysicalMemory + ComputerName sha1)
    ASSUMPTION: hardware_id is what is shown in the ID textbox of the crackme.
    """
    return generate_serial(name, hardware_id)


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
