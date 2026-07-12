def _substr(s, start, count):
    """C++ std::string::substr(start, count) - extracts up to 'count' chars from position 'start'"""
    return s[start:start+count]


def verify(name, serial):
    """
    The crackme ignores 'name'; the serial IS the password.
    Algorithm based on the writeups:
    1. Password must be exactly 10 characters long.
    2. Password must NOT be a palindrome (password != strrev(password)).
    3. Reverse the password in place to get rev_password.
    4. Build substrings from rev_password:
         substr1 = rev_password[1:6]   (start=1, count=5)
         substr2 = rev_password[6:10]  (start=6, count=9, but only 4 chars remain)
         substr3 = rev_password[7:11]  (start=7, count=4, but only 3 chars remain)
    5. Concatenate them: combined = substr3 + substr2 + substr1
       (from sample: password='abxbxahzz!' -> rev='!zzhaхbxba' wait, let's re-derive)
    
    Re-derivation from sample:
      password = 'abxbxahzz!'  (10 chars)
      rev_password = strrev('abxbxahzz!') = '!zzhaхbxba'  -- let's compute properly
      'abxbxahzz!'[::-1] = '!zzhaхbxba'  ... let's do it step by step:
      a b x b x a h z z !   (indices 0-9)
      reversed: ! z z h a x b x b a  (indices 0-9)
      rev_password = '!zzhaхbxba'  -> '!zzhaxbxba'
      
      substr1 = rev_password[1:6]  = 'zzhax'
      substr2 = rev_password[6:10] = 'bxba'
      substr3 = rev_password[7:10] = 'xba'  (only 3 chars from pos 7)
      
      combined = substr3 + substr2 + substr1 = 'xba' + 'bxba' + 'zzhax' = 'xbabxbazzhax'
    
    Checks on combined string 'xbabxbazzhax':
      7. starts with 'x'  -> combined[0] == 'x'
      7b. last 3 chars == 'hax'  -> combined[9:12] == 'hax'  (length is 12)
      8.  char at index 3 == 'b'  -> combined[3] == 'b'
      9.  chars at index 7,8 == 'zz' -> combined[7:9] == 'zz'
    """
    password = serial  # The check is purely on the serial/password
    
    # Check 1: length must be 10
    if len(password) != 10:
        return False
    
    # Check 2: must not be a palindrome
    rev_password = password[::-1]
    if password == rev_password:
        return False
    
    # Steps 3-5: build substrings from rev_password
    substr1 = _substr(rev_password, 1, 5)   # rev_password[1:6]
    substr2 = _substr(rev_password, 6, 9)   # rev_password[6:15] clamped to [6:10]
    substr3 = _substr(rev_password, 7, 4)   # rev_password[7:11] clamped to [7:10]
    
    combined = substr3 + substr2 + substr1
    # combined should be 12 chars: 3 + 4 + 5
    
    # Check 7a: combined starts with 'x'
    if not combined.startswith('x'):
        return False
    
    # Check 7b: last 3 chars of combined == 'hax'
    if combined[-3:] != 'hax':
        return False
    
    # Check 8: combined[3] == 'b'
    if len(combined) < 4 or combined[3] != 'b':
        return False
    
    # Check 9: combined[7:9] == 'zz'
    if len(combined) < 9 or combined[7:9] != 'zz':
        return False
    
    return True


def keygen(name):
    """
    Generate a valid password.
    
    We need to find a 10-char password such that when reversed, the combined
    string satisfies all checks.
    
    Let rev_password = r[0]r[1]r[2]r[3]r[4]r[5]r[6]r[7]r[8]r[9]
    
    substr1 = r[1:6]   (5 chars)
    substr2 = r[6:10]  (4 chars)
    substr3 = r[7:10]  (3 chars)
    
    combined = substr3 + substr2 + substr1
              = r[7]r[8]r[9] + r[6]r[7]r[8]r[9] + r[1]r[2]r[3]r[4]r[5]
              = r7 r8 r9 r6 r7 r8 r9 r1 r2 r3  ... wait, let me index properly
    
    combined[0]  = r[7]   must be 'x'
    combined[1]  = r[8]
    combined[2]  = r[9]
    combined[3]  = r[6]   must be 'b'
    combined[4]  = r[7]   = 'x' (same as combined[0])
    combined[5]  = r[8]   = combined[1]
    combined[6]  = r[9]   = combined[2]
    combined[7]  = r[1]   must be 'z' (zz check: combined[7:9]='zz')
    combined[8]  = r[2]   must be 'z'
    combined[9]  = r[3]   combined[-3:] = combined[9:12] = r[3]r[4]r[5] must be 'hax'
    combined[10] = r[4]
    combined[11] = r[5]
    
    So from constraints:
      r[7] = 'x'
      r[6] = 'b'
      r[1] = 'z'
      r[2] = 'z'
      r[3] = 'h'
      r[4] = 'a'
      r[5] = 'x'
    
    r[0] and r[8], r[9] are free (any character).
    But password != rev_password, so we need r[0]r[1]...r[9] != r[9]r[8]...r[0] as password.
    (Actually: rev_password is the reverse of password, and
     password[::-1] = rev_password, so password itself must not be a palindrome,
     which means rev_password (=password[::-1]) must != password.)
    
    Let's choose free chars: r[0]='a', r[8]='z', r[9]='!'
    rev_password = 'a' 'z' 'z' 'h' 'a' 'x' 'b' 'x' 'z' '!'
                 = 'azzhaхbxz!'
    password = rev_password[::-1] = '!zxbxhaзza'  -> let's compute properly
    rev_password = 'azzhaxbxz!'
    password = '!zxbxhazza'
    
    Verify not palindrome: 'azzhaxbxz!' != '!zxbxhazza'  -> True
    
    Use the known sample: password = 'abxbxahzz!' which verifies as True.
    """
    # Construct from known constraints on rev_password:
    # r[1]='z', r[2]='z', r[3]='h', r[4]='a', r[5]='x', r[6]='b', r[7]='x'
    # r[0], r[8], r[9] are free - choose something that avoids palindrome
    r = ['a', 'z', 'z', 'h', 'a', 'x', 'b', 'x', 'z', '!']
    rev_password = ''.join(r)
    password = rev_password[::-1]
    # Safety check
    assert verify(name, password), "keygen produced invalid password!"
    return password



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
