# keygen / verify for theq's P.D.C. crackme
# Reconstructed from ZaiRoN's KEYGEN.ASM writeup.
#
# The writeup is a full MASM keygenerator that builds a polymorphic
# protection routine at runtime and executes it to validate / generate
# the serial.  The ASM source was truncated before the final serial-
# generation step, so we cannot reconstruct the exact numeric result.
#
# What IS clear from the source:
#   1. Name must be at least 4 characters.
#   2. A "sequence" is computed from the name via simula_401A10().
#   3. A second sequence (seq_clos) is computed from the first via
#      simula_401AB0(), using a 79-byte (0x4F) constant string
#      (the 'clos' string).
#   4. Two more sequences (seq_conc, seq_imag) are computed via
#      simula_401A10() from constant strings.
#   5. A polymorphic code block is built in a heap allocation, using
#      seq_clos to drive instruction selection from six instruction
#      templates (tipo_istr0-5) and four poly-operand tables
#      (poly0-poly3).  'valore' (starting 0x0B,0xAD,0xBA,0xBE) is
#      modified by the build loop whenever a template of size 0x1E is
#      selected.
#   6. That polymorphic routine is executed and produces the serial.
#
# Because simula_401A10 / simula_401AB0 bodies are NOT shown, and the
# polymorphic execution result is not shown, we can only provide
# structural stubs.

# ASSUMPTION: simula_401A10 is a simple byte-mixing / checksum function
#             over the input buffer.  Body unknown.
# ASSUMPTION: simula_401AB0 is a second transformation that mixes the
#             'sequence' with the 'clos' constant string.
# ASSUMPTION: The final serial is a hex or decimal string derived from
#             the 32-bit result of the polymorphic routine.

CLOS  = b"Close your eyes and begin to relax. Take a deep breath, and let it out slowly."
CONC  = b"Concentrate on your breathing.With each breath you become more relaxed."
IMAG  = b"Imagine a brilliant white light above you, "
VALOR = bytearray([0x0B, 0xAD, 0xBA, 0xBE, 0x00])

# instruction-type selector table lengths (from tipo_istr* first bytes)
TIPO_LENS = [0x0A, 0x18, 0x1E, 0x18, 0x26, 0x18]

def simula_401A10(buf: bytes, length: int, out_len: int = 0xFF) -> bytearray:
    """ASSUMPTION: unknown – placeholder using a simple additive mix."""
    result = bytearray(out_len)
    acc = 0
    for i in range(length):
        acc = (acc ^ buf[i] + i) & 0xFFFF
        result[i % out_len] = (result[i % out_len] + acc) & 0xFF
    return result

def simula_401AB0(sequence: bytearray, clos_len: int, clos_buf: bytes) -> bytearray:
    """ASSUMPTION: unknown – placeholder mixing sequence with clos."""
    result = bytearray(0xFF)
    for i in range(clos_len):
        result[i] = (sequence[i % len(sequence)] ^ clos_buf[i]) & 0xFF
    return result

def build_serial_from_seq(name: str, seq_clos: bytearray) -> str:
    """ASSUMPTION: The polymorphic loop over seq_clos produces a 32-bit
       value used as the serial.  We approximate by XOR-folding the
       sequence bytes, modulated by VALOR."""
    val = bytearray([0x0B, 0xAD, 0xBA, 0xBE, 0x00])
    acc = 0
    for b in seq_clos:
        lo = b & 0x0F
        hi = (b >> 4) & 0x0F
        tipo_idx = lo % 6
        poly_idx = hi % 6
        # ASSUMPTION: each iteration updates acc based on template index
        if TIPO_LENS[tipo_idx] == 0x1E:
            val[4] = (val[4] + 1) & 0xFF
        acc = (acc ^ (b << tipo_idx) ^ poly_idx) & 0xFFFF
    # Mix with valore bytes
    result = acc ^ (val[0] | (val[1] << 8)) ^ (val[2] | (val[3] << 8))
    return "%04X" % (result & 0xFFFF)

def compute_sequences(name: str):
    nb = name.encode('ascii', errors='replace')
    n = len(nb)
    seq   = simula_401A10(nb, n)
    seq_clos = simula_401AB0(seq, 0x4F, CLOS)
    seq_conc = simula_401A10(CONC, 0x48)
    seq_imag = simula_401A10(IMAG, 0x2C)
    return seq, seq_clos, seq_conc, seq_imag

def keygen(name: str) -> str:
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters")
    _, seq_clos, _, _ = compute_sequences(name)
    return build_serial_from_seq(name, seq_clos)

def verify(name: str, serial: str) -> bool:
    if len(name) < 4:
        return False
    expected = keygen(name)
    return serial.strip().upper() == expected.upper()


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
