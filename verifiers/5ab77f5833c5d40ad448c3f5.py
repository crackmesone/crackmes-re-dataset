import os
import getpass


def keygen(username: str) -> str:
    """
    Generate the key file content for the given username.
    
    Algorithm (from cm1_keygen.cpp / assembly analysis):
    For each character c in username:
      - d = c - n  (where n starts at 0, then n = prev_c // 10)
      - x = d // 25       -> number of '*****+-' groups (each group adds 25: 5*5 + 1 - 1? no...)
      
    Wait - let's re-read the C keygen carefully:
      d = c - n
      x = d / 25       -> for each: append '*****+-'   (net effect: +5*5 +1 -1 = +25... but that cancels)
    
    Actually from the C keygen:
      x = d/25:   for j in range(x): key += '*****+-'   (* is +5, so ***** = +25, then + = +1 -> 26, then - = -1 -> 25 net = +25 per group? No...)
    
    Wait, re-read: the accumulator (esi) changes are:
      '*' => esi += 5
      '+' => esi += 1  
      '-' => esi -= 1
      '/' => esi -= 5
    And ',' means: read next byte from key, check it equals esi, check it equals username[i], then esi //= 10
    
    From the C keygen:
      d = c - n
      x = d // 25;  y = (d % 25) // 5;  z = (d % 25) % 5
      for j in range(x): key += '*****+-'   -> net: +25 per group (5*5=+25, then +1, then -1 -> back to +25)
      for j in range(y): key += '*'          -> net: +5 per star
      for j in range(z): key += '+'          -> net: +1 per plus
      key += ','   -> comma triggers the check: read c from file, verify esi==c==username[i], then esi//=10
      key += c     -> the character itself is appended as the byte after ','
      n = c // 10
    
    So the key for each char c (with carry n from previous):
      d = c - n
      x = d // 25, y = (d%25)//5, z = (d%25)%5
      emit x copies of '*****+-', y copies of '*', z copies of '+', then ',', then chr(c)
      carry = c // 10
    """
    key = ''
    n = 0
    for ch in username:
        c = ord(ch)
        d = c - n
        x = d // 25
        y = (d % 25) // 5
        z = (d % 25) % 5
        for _ in range(x):
            key += '*****+-'
        for _ in range(y):
            key += '*'
        for _ in range(z):
            key += '+'
        key += ','
        key += ch
        n = c // 10
    return key


def verify(username: str, serial: str) -> bool:
    """
    Simulate the crackme's validation loop.
    
    State:
      esi = 0  (accumulator)
      x102c = 0  (index into username)
      x102d = ' '  (last operator seen, initialized to space)
      ebx = 1  (consecutive-same-operator counter? actually tracks operator repeat count)
    
    For each byte read from serial:
      if byte not in ('*','+',',','-','/') -> fail
      switch (byte - '*'):
        case 0 ('*'): esi += 5
        case 1 ('+'): esi += 1
        case 3 ('-'): esi -= 1
        case 5 ('/'): esi -= 5  (note: '/' - '*' = 5)
          after: if byte != x102d -> ebx = 1; else ebx stays, check ebx<=5
                 if byte == x102d and ebx > 5 -> fail (max 5 consecutive same op)
                 x102d = byte
        case 2 (','): 
          read next byte (c) from serial
          if c != esi -> fail
          if username[x102c] != esi -> fail  (i.e., c must equal username[x102c])
          x102c += 1
          if x102c < len(username): esi //= 10
          else:
            # username fully consumed; next read must return 0 bytes (end of serial)
            # check no more bytes in serial -> success
            # esi //= 10 still happens at 0x804861a
            esi //= 10
    
    After loop ends (serial exhausted):
      check username[x102c] == '\0' i.e. x102c == len(username) -> success
    
    NOTE: The assembly is complex; using the C keygen as ground truth for the algorithm.
    This verify() re-simulates using the file-content approach.
    """
    # We'll simulate by parsing the serial string as a stream
    data = serial
    pos = 0
    esi = 0
    x102c = 0  # index into username
    x102d = ' '  # last operator
    ebx = 1  # consecutive operator count? Actually from asm: ebx counts up to 5
    
    OPERATORS = {'*', '+', '-', '/'}
    
    while pos < len(data):
        byte = data[pos]
        pos += 1
        
        if byte == ',':
            # Read next byte from serial - this should equal esi and username[x102c]
            if pos >= len(data):
                return False
            c = data[pos]
            pos += 1
            
            c_val = ord(c)
            
            # Check c == esi
            if c_val != esi:
                return False
            
            # Check username[x102c] == esi
            if x102c >= len(username):
                return False
            if ord(username[x102c]) != esi:
                return False
            
            x102c += 1
            
            # Check if username is fully consumed
            if x102c < len(username):
                # More chars to process
                esi = esi // 10
            else:
                # Username done; check no more data in serial
                esi = esi // 10
                # After this, loop reads next byte; if serial ends -> check username[x102c]==0 -> success
                # If serial has more data -> continue loop -> eventually check will fail or succeed
                # The crackme checks: after the read loop ends, username[x102c] must be '\0'
                # So we just let the loop continue; if pos==len(data) the while ends
                continue
        
        elif byte in OPERATORS:
            if byte == '*':
                esi += 5
            elif byte == '+':
                esi += 1
            elif byte == '-':
                esi -= 1
            elif byte == '/':
                esi -= 5
            
            # ASSUMPTION: The ebx/x102d logic in the original asm tracks consecutive same operators
            # The C keygen doesn't produce more than 5 consecutive same operators by construction
            # We skip the strict ebx check here as the keygen never violates it
            if byte != x102d:
                ebx = 1
            else:
                ebx += 1
                if ebx > 5:
                    return False  # too many consecutive same operators
            x102d = byte
        
        else:
            return False
    
    # After serial exhausted, check that username is fully consumed
    return x102c == len(username)



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
