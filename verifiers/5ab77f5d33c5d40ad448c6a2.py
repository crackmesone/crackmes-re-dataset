# re_venge crackme by crudd / [RET]
# Reversed from the writeup by the_dux
#
# Summary of the algorithm:
#  1. The program reads a binary Registry value named [RET] under
#     HKCU\Software\RET\Re-Venge\  (exactly 0x30 = 48 bytes).
#  2. It subtracts 0x20 from every byte of the 48-byte blob.
#  3. The result is interpreted as 3 null-padded (or 0x10-byte-wide) strings
#     that must be valid KERNEL32 export names.
#  4. GetProcAddress is called for each of the 3 names; all three must resolve
#     (return non-NULL) for the program to consider itself registered.
#  5. Additionally, byte [0x403008] must be 0x01 (set by a successful
#     RegOpenKeyExA + RegQueryValueExA sequence).
#
# The writeup is truncated before revealing WHICH three KERNEL32 functions
# are required, so we cannot fully determine the correct registry value.
# We CAN implement:
#   - the encoding/decoding transform (subtract 0x20 per byte)
#   - the structural validator (3 x 16-byte slots, each a valid KERNEL32 name)
#
# ASSUMPTION: The three required KERNEL32 function names are unknown because
# the writeup was cut off. Common guesses from context (the program uses
# registry + file I/O) might be e.g. CreateFileA, ReadFile, CloseHandle,
# but these are NOT confirmed by the text.  We mark them as ASSUMPTIONs.

import ctypes
import ctypes.wintypes
import platform

# --------------------------------------------------------------------------
# Low-level helpers
# --------------------------------------------------------------------------

def encode_name(name: str, slot_size: int = 0x10) -> bytes:
    """
    Given a plain KERNEL32 function name string, produce the 'slot_size'-byte
    blob that must be stored in the registry.
    The program does: stored_byte - 0x20 = name_byte
    So: stored_byte = name_byte + 0x20
    """
    encoded = bytes((b + 0x20) for b in name.encode('ascii'))
    # Pad / truncate to slot_size
    if len(encoded) > slot_size:
        encoded = encoded[:slot_size]
    else:
        encoded = encoded + bytes(slot_size - len(encoded))
    return encoded


def decode_registry_blob(blob: bytes) -> list:
    """
    Decode the 48-byte registry blob into 3 function name strings.
    Transform: name_byte = stored_byte - 0x20  (as unsigned; result mod 256)
    Each name occupies a 16-byte slot; trailing null bytes are stripped.
    """
    if len(blob) != 0x30:
        raise ValueError(f"Registry blob must be exactly 0x30 (48) bytes, got {len(blob)}")
    names = []
    for i in range(3):
        slot = blob[i * 0x10 : (i + 1) * 0x10]
        decoded = bytes((b - 0x20) & 0xFF for b in slot)
        # Strip trailing nulls / garbage after null
        name = decoded.split(b'\x00')[0].decode('ascii', errors='replace')
        names.append(name)
    return names


def _kernel32_has_export(name: str) -> bool:
    """Check whether KERNEL32.DLL exports the given name."""
    if platform.system() != 'Windows':
        # ASSUMPTION: On non-Windows we cannot call GetProcAddress;
        # we fall back to a static known-exports list.
        # This is a best-effort check only.
        return name in _KNOWN_KERNEL32_EXPORTS
    try:
        k32 = ctypes.windll.kernel32
        k32.GetModuleHandleA.restype = ctypes.wintypes.HMODULE
        hmod = k32.GetModuleHandleA(b'KERNEL32.DLL')
        k32.GetProcAddress.restype = ctypes.c_void_p
        addr = k32.GetProcAddress(hmod, name.encode('ascii'))
        return addr is not None and addr != 0
    except Exception:
        return False


# A small subset of well-known KERNEL32 exports for offline checking
_KNOWN_KERNEL32_EXPORTS = {
    'CreateFileA', 'CreateFileW', 'ReadFile', 'WriteFile', 'CloseHandle',
    'GetModuleHandleA', 'GetModuleHandleW', 'GetProcAddress',
    'VirtualAlloc', 'VirtualFree', 'ExitProcess', 'LoadLibraryA',
    'CreateProcessA', 'OpenProcess', 'TerminateProcess',
    'RegOpenKeyExA', 'RegQueryValueExA', 'RegCloseKey',
    'HeapAlloc', 'HeapFree', 'GetLastError', 'SetLastError',
}


# --------------------------------------------------------------------------
# Core validation logic
# --------------------------------------------------------------------------

# ASSUMPTION: The three required function names are unknown (writeup truncated).
# We leave them as placeholders.  Replace with the real names once known.
REQUIRED_FUNCTIONS = [
    # ASSUMPTION: unknown – replace with actual required names
    None,
    None,
    None,
]


def verify_blob(blob: bytes) -> bool:
    """
    Verify a 48-byte registry blob.
    Returns True if all three decoded names are valid KERNEL32 exports.
    This mirrors what the crackme does at runtime.
    """
    if len(blob) != 0x30:
        return False
    try:
        names = decode_registry_blob(blob)
    except Exception:
        return False
    return all(_kernel32_has_export(n) for n in names)


def verify(name: str, serial: str) -> bool:
    """
    verify(name, serial) -> bool

    'serial' is interpreted as a hex string (96 hex chars = 48 bytes),
    representing the binary registry value [RET].

    The 'name' parameter is not used by this crackme's algorithm
    (registration is purely key-file / registry based, not name-based).

    ASSUMPTION: The three required KERNEL32 function names are not known
    from the (truncated) writeup, so this can only do a structural check
    (correct length + valid KERNEL32 exports) rather than match specific
    required names.
    """
    # Accept hex string OR raw bytes represented as a string of hex digits
    serial_clean = serial.replace(' ', '').replace('-', '')
    try:
        blob = bytes.fromhex(serial_clean)
    except ValueError:
        # Maybe the caller passed raw bytes encoded as latin-1 string
        try:
            blob = serial.encode('latin-1')
        except Exception:
            return False

    if len(blob) != 0x30:
        return False

    # If we know the required functions, do an exact match
    if all(f is not None for f in REQUIRED_FUNCTIONS):
        try:
            names = decode_registry_blob(blob)
        except Exception:
            return False
        return names == REQUIRED_FUNCTIONS

    # ASSUMPTION: fall back to structural check only
    return verify_blob(blob)


def keygen(name: str) -> str:
    """
    keygen(name) -> hex-encoded 48-byte registry blob

    Produces a valid registry value for [RET].

    ASSUMPTION: The three required function names are not known from the
    writeup (it was truncated).  We use placeholder names that ARE valid
    KERNEL32 exports; replace them once the real names are discovered.
    """
    # ASSUMPTION: replace these with the real required function names
    func_names = [
        'CreateFileA',    # ASSUMPTION
        'ReadFile',       # ASSUMPTION
        'CloseHandle',    # ASSUMPTION
    ]

    blob = b''
    for fn in func_names:
        blob += encode_name(fn, slot_size=0x10)

    assert len(blob) == 0x30
    return blob.hex()


# --------------------------------------------------------------------------
# String-modification routine (the RET.key -> key.ret rename)
# Included for completeness; not part of serial validation.
# --------------------------------------------------------------------------

def decode_keyfile_name(data: bytes) -> bytes:
    """
    Mirrors the assembly at 0x4012B4 that transforms 'RET.key' -> 'key.ret'.
    Operates on a 7-byte buffer starting at 0x403000.

    Byte 0: -= 7
    Byte 1: += 0x20
    Byte 2: ^= 0x2D
    (byte 3 skipped via add eax, 2)
    Byte 4: += 7
    Byte 5: -= 0x20
    Byte 6: ^= 0x2D
    """
    buf = bytearray(data)
    buf[0] = (buf[0] - 0x07) & 0xFF
    buf[1] = (buf[1] + 0x20) & 0xFF
    buf[2] = (buf[2] ^ 0x2D) & 0xFF
    # index 3 is skipped (add eax, 2 after xor at index 2)
    buf[4] = (buf[4] + 0x07) & 0xFF
    buf[5] = (buf[5] - 0x20) & 0xFF
    buf[6] = (buf[6] ^ 0x2D) & 0xFF
    return bytes(buf)


# --------------------------------------------------------------------------
# Demo / self-test
# --------------------------------------------------------------------------


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
