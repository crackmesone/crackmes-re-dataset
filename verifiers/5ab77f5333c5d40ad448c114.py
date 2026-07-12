# Reconstructed from the keygen assembly (Immortal2_Keygen.asm)
# GenerateKey proc analysis:
#   1. Uppercase the name
#   2. Sum all ASCII values of name chars into DX (16-bit)
#   3. Add 0x324 to DX
#   4. Perform bit manipulations on DX:
#      - AX = DX << 10 (16-bit, i.e. (dx * 0x400) & 0xFFFF)
#      - DX = DX << 22 ... but DX is 16-bit, so shl dx,22 is effectively shl dx,(22 mod 16)=6
#        => DX = (dx << 6) & 0xFFFF
#      - DX = DX + AX  (both 16-bit, result 16-bit)
#   5. Add original DX (saved via push/pop) back: DX = DX + original_sum
#   6. Multiply DX by 0x19 (25), keep low 16 bits
#   7. Produce 4 code characters using CodeTable = "123456789ABCDEF"
#      char0: high nibble of DH  => (val >> 12) & 0xF  -> CodeTable index
#      char1: low  nibble of DH  => (val >>  8) & 0xF  -> CodeTable index
#      char2: bits [6:3] of DL   => (val >> 7) & 0xF   -> CodeTable index
#      char3: low  nibble of DL  => val & 0xF           -> CodeTable index
#
# Note on the bit-shift sequence:
#   push edx          ; save original dx in eax after pop
#   mov ax,dx
#   shl ax,0Ah        ; ax = (name_sum+0x324) << 10, 16-bit
#   shl dx,22h        ; 22h = 34 decimal; for 16-bit reg, shift count mod 16 = 34 mod 16 = 2
#                     ; ASSUMPTION: x86 shifts 16-bit regs mod 32 in 32-bit mode actually
#                     ;   but 'shl dx,22h' on a 16-bit operand: shift count masked to 5 bits = 0x22 & 0x1F = 2
#                     ; => dx = (name_sum+0x324) << 2, 16-bit
#   add dx,ax         ; dx = ((ns<<2) + (ns<<10)) & 0xFFFF
#   pop eax           ; eax = original edx = original dx (name_sum+0x324 in low 16)
#   add dx,ax         ; dx += (name_sum+0x324)
#   imul edx,19h      ; edx = dx * 25 (but dx is low 16 of edx here; result taken as full 32-bit then DX=high16, DL=low8 of low16)
#                     ; ASSUMPTION: after imul edx,19h we use edx as 32-bit; dh = byte(edx>>8), dl = byte(edx)

CODE_TABLE = "123456789ABCDEF"

def _to16(x):
    return x & 0xFFFF

def _to32(x):
    return x & 0xFFFFFFFF

def generate_key(name):
    name = name.upper()
    
    # Sum ASCII values (accumulate in 16-bit DX)
    dx = 0
    for ch in name:
        dx = _to16(dx + ord(ch))
    
    # Add 0x324
    dx = _to16(dx + 0x324)
    
    # Save original dx
    saved = dx  # this is what gets popped into eax later
    
    # ax = dx << 10 (16-bit)
    ax = _to16(dx << 0xA)
    
    # shl dx, 0x22 => shift count = 0x22 & 0x1F = 2 (5-bit mask for 32-bit mode)
    # ASSUMPTION: 16-bit operand shift in 32-bit mode masks count to 5 bits
    dx = _to16(dx << 2)
    
    # dx = dx + ax (16-bit)
    dx = _to16(dx + ax)
    
    # pop eax: eax = saved (the original dx before shifts)
    eax = saved
    
    # add dx, ax (ax here is low16 of eax = saved)
    dx = _to16(dx + (eax & 0xFFFF))
    
    # imul edx, 0x19 => treat dx as signed 16-bit, extend to 32-bit, multiply by 25
    # But imul edx,19h operates on edx (32-bit); edx currently has dx in low16
    edx = dx  # dx was 16-bit unsigned; treat as 32-bit for imul
    edx = _to32(edx * 0x19)
    
    # Extract bytes
    dl = edx & 0xFF
    dh = (edx >> 8) & 0xFF
    
    # char0: high nibble of dh
    idx0 = (dh & 0xF0) >> 4
    # char1: low nibble of dh
    idx1 = dh & 0x0F
    # char2: (dl >> 7) & 0xF -- i.e. shr al,7 then and al,0Fh => bits [7:4] shifted by 3? 
    # ASSUMPTION: 'shr al,7' gives bit7 of dl in bit0; then 'and al,0Fh' keeps low4 => effectively bit7 only (0 or 1)
    # But looking more carefully at assembly:
    #   mov al,dl
    #   shr al,7        ; al = dl >> 7  (unsigned), result is 0 or 1 since only 1 bit
    #   and al,0Fh      ; still 0 or 1
    #   xlatb           ; CodeTable[al]
    # ASSUMPTION: this may actually be 'shr al,4' misread, but we follow literal assembly
    idx2 = (dl >> 7) & 0x0F
    # char3: low nibble of dl
    idx3 = dl & 0x0F
    
    # Build code (indices into CodeTable; CodeTable is 15 chars indexed 0-14)
    def lookup(idx):
        if idx < len(CODE_TABLE):
            return CODE_TABLE[idx]
        # ASSUMPTION: out of range wraps or uses last char
        return CODE_TABLE[idx % len(CODE_TABLE)]
    
    code = lookup(idx0) + lookup(idx1) + lookup(idx2) + lookup(idx3)
    return code

def verify(name, serial):
    expected = generate_key(name)
    return serial.upper() == expected.upper()

def keygen(name):
    return generate_key(name)


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
