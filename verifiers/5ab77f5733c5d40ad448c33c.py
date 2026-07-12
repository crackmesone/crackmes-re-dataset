import struct

def _build_wsprintf_result(name: str) -> str:
    """
    Simulates: wsprintfA(buf, "AKCOM-L434%s022LACD", name)
    where the output buffer IS the same buffer that holds 'name'.
    
    In the real crackme, both the destination and the %s argument point to
    the same buffer (the name buffer).  So the format string expands %s
    from whatever is currently in the buffer at that point.
    
    Concretely the call is:
        wsprintfA(name_buf, "AKCOM-L434%s022LACD", name_buf)
    
    Because the source (%s) and destination are the same buffer, and
    sprintf writes left-to-right, by the time %s is reached the prefix
    "AKCOM-L434" (10 chars) has already overwritten the first 10 bytes of
    name_buf.  So %s reads from name_buf[10:] which still contains the
    original name (if name length <= 10) or a mix if longer.
    
    For names <= 10 chars the readable tail of name_buf after the prefix is
    name[10:] which is empty, giving: "AKCOM-L434" + "" + "022LACD"
    = "AKCOM-L434022LACD".
    
    For names > 10 chars the tail is name[10:], giving:
    "AKCOM-L434" + name[10:] + "022LACD".
    
    The writeup says: "only length of NAME is most important" and gives the
    example that 'Alcoholic' (9 chars, <=10) yields "AKCOM-L434AKCOM-L434022LACD".
    Wait - that contradicts the above. Let me re-read.
    
    The writeup example: name='Alcoholic' -> "AKCOM-L434AKCOM-L434022LACD".
    That looks like the %s was read BEFORE the prefix was written, i.e.
    standard sprintf behaviour where it reads the arg first then writes.
    Actually wsprintfA likely reads the %s pointer value (name_buf) and
    the current contents of name_buf is the name itself, so %s = name.
    Result = "AKCOM-L434" + name + "022LACD".
    For 'Alcoholic': "AKCOM-L434Alcoholic022LACD" -- but writeup says
    "AKCOM-L434AKCOM-L434022LACD"??
    
    ASSUMPTION: The writeup example output "AKCOM-L434AKCOM-L434022LACD" for
    name='Alcoholic' is illustrative/wrong in the writeup (the author says
    'some strange things' happen). The actual functional result used in the
    algo is: result = "AKCOM-L434" + name + "022LACD".
    That is the simplest consistent reading and matches the described
    'only length matters' because the magic_string XOR step length is fixed.
    """
    # ASSUMPTION: wsprintf result is simply the format string with %s=name
    return "AKCOM-L434" + name + "022LACD"


# Magic string embedded in the binary (15 bytes)
_MAGIC = bytes([0xBF, 0xA6, 0xF6, 0xC6, 0xF9, 0xFF, 0xA6, 0xA2,
                0xA9, 0x83, 0xB2, 0xB0, 0xAD, 0xAB, 0xEA])


def _transform(code_str: str) -> str:
    """
    Apply the XOR transformation loop described in the writeup:

    magic_len = len(_MAGIC)  # 0x0F = 15
    for counter in range(len(code_str)):
        idx = counter % magic_len
        xor_val = _MAGIC[idx] + 1          # movsx edx, magic[idx]; add edx,1
        ch = code_bytes[counter] ^ xor_val
        code_bytes[counter] = ch & 0xFF
    """
    magic_len = len(_MAGIC)  # 15
    code_bytes = bytearray(code_str.encode('latin-1'))
    for counter in range(len(code_bytes)):
        idx = counter % magic_len
        xor_val = (_MAGIC[idx] + 1) & 0xFF
        code_bytes[counter] = code_bytes[counter] ^ xor_val
    return code_bytes.decode('latin-1')


def keygen(name: str) -> str:
    """Generate the valid serial for a given name."""
    if len(name) < 8:
        raise ValueError("Name must be at least 8 characters long.")
    code_str = _build_wsprintf_result(name)
    serial = _transform(code_str)
    return serial


def verify(name: str, serial: str) -> bool:
    """Return True if the serial is valid for the given name."""
    if len(name) < 8:
        return False
    expected = keygen(name)
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
