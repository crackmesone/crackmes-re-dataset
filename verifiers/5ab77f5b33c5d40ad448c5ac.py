import ctypes

# Based on the writeup by Cyclops for KeyGenMe_1 by Wizzard
# The DLL exports VerifyInfo(name, company, serial)
# Internally it calls function 10001020 which:
#   1. Checks name length <= 0x20 (32)
#   2. Checks company length <= 0x40 (64)
#   3. Checks serial length >= 0x10 (16)
#   4. Concatenates company+name via wsprintf("%s%s", company, name)
#      (note: from disasm push order: ESI=company pushed first then ECX=name pushed second
#       but format is "%s%s" so result = company+name)
#   5. Loops over the combined string applying some transformation to build the serial
#   6. The generated serial is compared via lstrcmpA against the entered serial
#
# The loop body (starting at 100010E0) was TRUNCATED in the writeup.
# We can see some constants set before the loop:
#   BL = 8       (used as some constant/mask)
#   [ESP+11] = 0
#   [ESP+12] = 0x20 (space, 32)
#   [ESP+13] = 0x27 (39, apostrophe)
#   EDI = 2      (index or counter starting value)
#   EBP = 4      (another counter)
#
# The loop reads bytes from the combined string (ESI = index into combined string)
# and uses EDI (wraps at string length) and EBP.
# The truncated portion prevents full recovery of the transformation.
#
# ASSUMPTION: Based on the structure (constants 8, 0x20, 0x27, index EDI starting at 2,
# EBP starting at 4), a common pattern is to XOR each character with a rotating key
# or apply arithmetic. We cannot determine the exact transformation from the truncated writeup.
#
# ASSUMPTION: The serial generation loop likely does something like:
#   for each char in (company+name): apply some operation involving BL(8), 0x20, 0x27
# and produces a hex or character string.

def _build_combined(name: str, company: str) -> str:
    # From disasm: wsprintf("%s%s", company, name) -> company then name
    # ASSUMPTION: order is company+name based on push ESI(company) then ECX(name)
    # but the format string "%s%s" means first arg=company, second=name
    return company + name

def _generate_serial_attempt(name: str, company: str) -> str:
    """
    ASSUMPTION: The exact serial generation algorithm is unknown due to truncated writeup.
    This is a best-effort reconstruction based on visible constants and loop structure.
    Constants seen: BL=8, 0x20, 0x27, EDI starts=2, EBP starts=4
    """
    combined = _build_combined(name, company)
    n = len(combined)
    if n == 0:
        return ""
    
    # ASSUMPTION: The loop uses EDI as a secondary index (wrapping at n, starting at 2)
    # and EBP as another rotating value (starting at 4)
    # BL=8 might be a shift or XOR mask
    # We attempt a plausible reconstruction:
    result_chars = []
    edi = 2  # secondary index
    ebp = 4  # rotating counter
    bl = 8
    
    for esi in range(n):
        if edi >= n:
            edi = 0
        dl = ord(combined[esi])  # MOV DL,BYTE PTR SS:[ESP+ESI+18]
        # ASSUMPTION: some operation combining dl, combined[edi], ebp, bl
        # A common pattern: serial_byte = (dl + ord(combined[edi]) * ebp) ^ bl
        # This is speculative - the writeup was truncated before showing the operation
        val = (dl + ord(combined[edi]) * ebp) ^ bl
        val = val & 0xFF
        result_chars.append(val)
        edi += 1
        # ASSUMPTION: ebp rotates between 4 and some other value
    
    # ASSUMPTION: result is formatted as hex string or direct bytes
    serial = ''.join(f'{v:02X}' for v in result_chars)
    return serial

def verify(name: str, serial: str) -> bool:
    """
    Validate serial against name and company.
    NOTE: The original function takes (name, company, serial).
    Since company is not standard for this interface, we use empty company.
    ASSUMPTION: company defaults to empty string if not provided.
    """
    # ASSUMPTION: company is empty when not provided
    company = ""
    return verify_with_company(name, company, serial)

def verify_with_company(name: str, company: str, serial: str) -> bool:
    """
    Full verify with name, company, and serial.
    Mirrors the DLL VerifyInfo(name, company, serial) logic.
    """
    # Validation checks from disasm
    if not name:
        return False
    if not company:
        # ASSUMPTION: company can be empty based on test
        pass
    if not serial:
        return False
    if len(name) > 0x20:
        return False
    if len(company) > 0x40:
        return False
    if len(serial) < 0x10:
        return False
    
    expected = _generate_serial_attempt(name, company)
    return expected == serial

def keygen(name: str, company: str = "") -> str:
    """
    Generate serial for given name and company.
    WARNING: The exact algorithm is partially recovered (loop body was truncated).
    """
    if len(name) > 0x20:
        raise ValueError("Name too long (max 32 chars)")
    if len(company) > 0x40:
        raise ValueError("Company too long (max 64 chars)")
    serial = _generate_serial_attempt(name, company)
    if len(serial) < 0x10:
        # ASSUMPTION: pad if too short
        serial = serial.ljust(0x10, '0')
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
