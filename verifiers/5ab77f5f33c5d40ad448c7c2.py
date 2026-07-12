import ctypes
import struct
import subprocess
import sys

# The serial validation algorithm from killswitch's GNARMOCK KeygenMe
# 
# Algorithm (from the assembly writeup):
# 1. Run CPUID with EAX=0 -> save result EAX to DWORD_403814h (called 'max_leaf')
# 2. Run CPUID with EAX=1 -> save result EAX to DWORD_403818h (processor info)
# 3. From processor info (EAX of CPUID leaf 1):
#    stepping  = eax & 0xF
#    model     = (eax >> 4) & 0xF
#    family    = (eax >> 8) & 0xF
# 4. EDI = max_leaf (from CPUID EAX=0)
#    EAX = stepping XOR model
#    EAX = EAX << family   (SHL EAX, CL where CL=family)
#    ESI = 0
#    Loop EDI times: ESI = EAX + ESI*2
#    result = ESI  -> DWORD_403018h
# 5. GetSystemTime -> get wMinute
#    final = wMinute * result  (IMUL, truncated to 32-bit signed)
#    DWORD_403018h = final
# 6. Serial accepted if atoi(user_input) == DWORD_403018h
#    (The comparison is done as 32-bit signed, but atoi returns signed int)
#
# NOTE: The serial is TIME-DEPENDENT (changes each minute) and
#       CPU-DEPENDENT (depends on CPUID results of the machine running the crackme).
#       The keygen must be run on the SAME machine as the crackme, at the SAME minute.

def _get_cpuid_info():
    """Try to get CPUID EAX=0 and EAX=1 results using Python cpuid if available."""
    # ASSUMPTION: We use the cpuid module or ctypes inline asm fallback.
    # On most systems without a direct cpuid binding we use the 'cpuid' PyPI package.
    try:
        import cpuid  # pip install cpuid
        # CPUID EAX=0
        regs0 = cpuid.cpuid(0)
        max_leaf = regs0[0]  # EAX
        # CPUID EAX=1
        regs1 = cpuid.cpuid(1)
        proc_info = regs1[0]  # EAX
        return max_leaf, proc_info
    except ImportError:
        # ASSUMPTION: Fallback - try to read from /proc/cpuinfo or use known typical values
        # This is a best-effort fallback; for real use the cpuid module is needed.
        # We'll attempt to get the Family/Model/Stepping another way.
        import platform
        # Use a ctypes approach on x86/x86_64
        return _cpuid_ctypes(0), _cpuid_ctypes(1)

def _cpuid_ctypes(leaf):
    """Run CPUID via ctypes inline code (x86/x86_64 only)."""
    # ASSUMPTION: This approach works on Linux/Windows x86-64 with execute permissions.
    # Returns only EAX.
    import ctypes, ctypes.util, os, tempfile, struct
    # Build a tiny shellcode: cpuid, then return EAX in EAX
    # 32-bit: push ebx; xchg eax,ecx; cpuid; xchg eax,[esp]; pop eax; ret
    # We'll use a simpler approach: write a C extension inline if possible
    # For pure Python fallback, raise NotImplementedError
    raise NotImplementedError("cpuid module required: pip install cpuid")

def compute_serial_value(max_leaf, proc_info, minute):
    """
    Compute the expected serial value given CPUID results and current minute.
    All arithmetic is 32-bit (unsigned intermediate, but stored as signed 32-bit at end).
    """
    # Extract fields from proc_info (CPUID EAX=1)
    stepping = proc_info & 0xF          # EAX & 0xF  (EAX in asm)
    model    = (proc_info >> 4) & 0xF   # EDX in asm (SHR EDX,4; AND EDX,0Fh)
    family   = (proc_info >> 8) & 0xF   # ECX in asm (SHR ECX,8; AND ECX,0Fh)

    edi = max_leaf & 0xFFFFFFFF  # EDI = DWORD_403814h
    eax_init = stepping          # AND EAX,0Fh
    edx_val  = model             # EDX after AND
    ecx_val  = family            # ECX (shift count)

    if edi == 0:  # TEST EDI,EDI; JBE skip
        esi = 0
    else:
        # XOR EAX,EDX
        eax = (eax_init ^ edx_val) & 0xFFFFFFFF
        # SHL EAX,CL
        shift = ecx_val & 0xFF  # shift amount
        eax = (eax << shift) & 0xFFFFFFFF
        # Loop: for EDI times: ESI = EAX + ESI*2
        esi = 0
        count = edi
        for _ in range(count):
            esi = (eax + esi * 2) & 0xFFFFFFFF

    # IMUL ECX, DWORD_403018h  -- ECX = minute, multiply by esi
    ecx = minute & 0xFFFF  # MOVZX ECX, WORD (wMinute)
    result = (ecx * esi) & 0xFFFFFFFF

    # Convert to signed 32-bit (as atoi and CMP work with signed)
    result_signed = ctypes.c_int32(result).value
    return result_signed

def keygen(name):
    """
    Generate valid serial for the CURRENT minute on the CURRENT machine.
    name is not used in the algorithm (only serial matters).
    Returns the serial string.
    NOTE: The serial is machine- and time-dependent.
    """
    import datetime
    try:
        max_leaf, proc_info = _get_cpuid_info()
    except NotImplementedError as e:
        raise RuntimeError(f"Cannot generate serial: {e}")

    now = datetime.datetime.utcnow()
    minute = now.minute
    val = compute_serial_value(max_leaf, proc_info, minute)
    return str(val)

def verify(name, serial):
    """
    Verify serial against the algorithm.
    Returns True if serial matches the computed value for the current minute.
    NOTE: Serial is time- and machine-dependent.
    """
    import datetime
    try:
        max_leaf, proc_info = _get_cpuid_info()
    except NotImplementedError:
        # ASSUMPTION: Without CPUID we cannot verify
        return False

    now = datetime.datetime.utcnow()
    minute = now.minute

    try:
        serial_int = int(serial)
    except ValueError:
        return False

    expected = compute_serial_value(max_leaf, proc_info, minute)
    return serial_int == expected


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
