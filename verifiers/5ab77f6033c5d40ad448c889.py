# Reverse-engineered keygen / verifier for lord_phoenix CrackMe #6
# Based on the solution writeup by deroko/ARTeam
#
# The crackme uses a VM (bytecode interpreter) executed via SEH (int3 handler).
# The full bytecode stream and all VM instructions were NOT fully disclosed in the
# writeup - only partial analysis of opcode 3 (compare-and-branch) was shown,
# plus the fact that the wanted serial length is 0x1E (30 chars).
#
# ASSUMPTION: The core check is that the serial must be exactly 30 characters long
#             and satisfy VM-driven comparisons that were NOT fully described.
# ASSUMPTION: Without the full bytecode dump or complete writeup, the exact
#             arithmetic/character checks cannot be reconstructed.
# ASSUMPTION: The EIP adjustment formula shown is:
#             new_eip = current_int3_eip + (0xDEAD1219 ^ 0xDEAD1337)
#             which equals current_int3_eip + 0x12E  (not 0x12E, let's compute)
#             0xDEAD1219 ^ 0xDEAD1337 = 0x12E
#             This is a relative jump offset in the bytecode stream.
#
# What IS known from the writeup:
#   - Serial is read via GetDlgItemTextA with max length 0x1F (31 bytes)
#   - The VM checks that len(serial) >= 0x1E (30 characters) [opcode 3, cmp_jnb]
#   - VM opcode 3 example: compare EAX (length of serial) >= 0x1E
#     If NOT taken (EAX < 0x1E), EIP += 0x12 (skip to bad branch)
#     If taken (EAX >= 0x1E), EIP = int3_eip + 0x12E (continue good branch)
#   - The VM has at least opcodes 1-5 with reg/reg, reg/imm, reg/mem modes
#   - Comparison types: 1=jz, 2=jnz, 3=jb, 4=jnb

def _xor_key():
    # 0xDEAD1219 ^ 0xDEAD1337
    return 0xDEAD1219 ^ 0xDEAD1337  # = 0x12E

SERIAL_LEN = 0x1E  # 30 characters, from writeup: dd 1Eh is DATA_TO_INSTRUCTION

def verify(name: str, serial: str) -> bool:
    """
    Partially reconstructed verifier.
    The only confirmed check from the writeup is that serial length >= 30 (0x1E).
    Full VM bytecode was not disclosed; further character-level checks are UNKNOWN.
    """
    # ASSUMPTION: Length check is the first (and possibly gating) VM check shown.
    if len(serial) < SERIAL_LEN:
        return False
    # Trim to exactly 30 chars if longer (max read was 0x1F=31 bytes incl. null)
    serial = serial[:SERIAL_LEN]

    # ASSUMPTION: Additional character-by-character checks exist in the VM
    # but their bytecode was not shown in the writeup. We cannot implement them.
    # Returning True here only means the length check passes.
    # PLACEHOLDER for unknown VM checks:
    # return _vm_check(name, serial)  # not implementable from available info
    raise NotImplementedError(
        "Full VM algorithm not disclosed in writeup. "
        "Only the serial length check (>= 30 chars) is known."
    )

def keygen(name: str) -> str:
    """
    Cannot generate a valid serial without knowing the full VM bytecode.
    ASSUMPTION: A 30-character serial of all zeros might satisfy length check
    but will almost certainly fail further VM checks.
    """
    # ASSUMPTION: placeholder - real checks unknown
    raise NotImplementedError(
        "Keygen cannot be implemented: full VM validation algorithm "
        "was not disclosed in the available writeup text."
    )


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
