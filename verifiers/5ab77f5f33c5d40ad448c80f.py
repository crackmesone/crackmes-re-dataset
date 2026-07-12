import struct

# ============================================================
# Reconstruction of thecolonials_keygenme01_x64 algorithm
# Based on the keygen source by ToMKoL (truncated writeup)
#
# Protection: Custom CRC-64 with HWID (HDD) based CRC table
# The CRC table is generated from HDD volume label/serial,
# which makes full offline verification impossible without
# knowing the target machine's HWID.
#
# What we CAN reconstruct from the source:
#   - hash_str(str) -> single byte hash
#   - crc64(str) -> 64-bit CRC using crctab[256]
#   - volume_hash(disklabel, disksn, diskflags) -> 64-bit value
#   - generate(uname, mail, serial) -> serial string
#   - gen_crc_tab() builds crctab[] from volume info
# ============================================================

# ASSUMPTION: Standard CRC-64 polynomial (ECMA-182) used as base,
# but the table is seeded/modified by HWID data.
# The exact polynomial and table-generation from HWID is not shown
# in the truncated writeup, so we use a placeholder.

CRC64_POLY = 0xad93d23594c935a9  # ASSUMPTION: common CRC-64 polynomial

def gen_crc_tab_standard():
    """Generate a standard CRC-64 table (without HWID modification).
    ASSUMPTION: The real crackme XORs/modifies entries with HWID-derived values.
    """
    table = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ CRC64_POLY
            else:
                crc >>= 1
        table.append(crc & 0xFFFFFFFFFFFFFFFF)
    return table

# ASSUMPTION: In the real crackme, crctab is built by gen_crc_tab()
# which reads HDD volume info. We use the standard table here.
crctab = gen_crc_tab_standard()

def hash_str(s: bytes) -> int:
    """Single-byte hash of a string.
    ASSUMPTION: Simple sum/xor of bytes mod 256 - exact algorithm not shown.
    """
    # ASSUMPTION: rotating XOR hash
    h = 0
    for b in s:
        h = ((h << 1) | (h >> 7)) & 0xFF
        h ^= b
    return h & 0xFF

def crc64(s: bytes) -> int:
    """CRC-64 using the (HWID-seeded) crctab.
    ASSUMPTION: Standard CRC-64 table-lookup algorithm.
    """
    crc = 0xFFFFFFFFFFFFFFFF
    for b in s:
        idx = (crc ^ b) & 0xFF
        crc = crctab[idx] ^ (crc >> 8)
    return crc & 0xFFFFFFFFFFFFFFFF

def volume_hash(disklabel: bytes, disksn: int, diskflags: int) -> int:
    """Hash combining disk label, serial number, and flags.
    ASSUMPTION: Exact combination not shown; using CRC64 of label XOR'd with sn/flags.
    """
    # ASSUMPTION: volume_hash incorporates disksn and diskflags into a 64-bit result
    base = crc64(disklabel)
    result = base ^ (disksn & 0xFFFFFFFF) ^ ((diskflags & 0xFFFFFFFF) << 32)
    return result & 0xFFFFFFFFFFFFFFFF

def generate(uname: bytes, mail: bytes, hwid_crc: int = 0) -> str:
    """Generate serial from name and email.
    ASSUMPTION: hwid_crc would normally come from gen_crc_tab() / volume_hash().
    Serial format is not fully shown; reconstructed from typical CRC keygen patterns.
    """
    # ASSUMPTION: serial is formatted as hex groups derived from
    # crc64 of name, crc64 of mail, hash_str of name, hash_str of mail
    # combined with HWID CRC.

    name_crc = crc64(uname)
    mail_crc = crc64(mail)
    name_hash = hash_str(uname)
    mail_hash = hash_str(mail)

    # ASSUMPTION: combine values to form serial
    # Typical pattern for such crackmes:
    part1 = (name_crc ^ hwid_crc) & 0xFFFFFFFF
    part2 = (mail_crc ^ hwid_crc) & 0xFFFFFFFF
    part3 = (name_hash ^ mail_hash) & 0xFF

    # ASSUMPTION: serial format is something like XXXXXXXX-XXXXXXXX-XX
    serial = "{:08X}-{:08X}-{:02X}".format(part1, part2, part3)
    return serial

def verify(name: str, serial: str, hwid_crc: int = 0) -> bool:
    """Verify serial for given name.
    ASSUMPTION: We regenerate the serial and compare.
    Email is not available in verify(); real crackme uses both name+email.
    This verify() is incomplete because email is required.
    """
    # ASSUMPTION: without email we cannot fully verify
    # This is a structural limitation from the truncated writeup
    raise NotImplementedError(
        "verify() requires both name AND email (see generate). "
        "Use keygen() to generate a serial for a name+email pair."
    )

def keygen(name: str, email: str, hwid_crc: int = 0) -> str:
    """Generate a valid serial for the given name and email.
    hwid_crc: ASSUMPTION: in the real crackme this comes from HDD volume info.
    Pass 0 for offline use (will not match the crackme without real HWID).
    """
    uname = name.encode('ascii', errors='replace')
    mail = email.encode('ascii', errors='replace')

    if len(uname) < 4:
        raise ValueError("Name must be at least 4 chars!")
    if len(mail) < 8:
        raise ValueError("Mail must be at least 8 chars!")

    return generate(uname, mail, hwid_crc)


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
