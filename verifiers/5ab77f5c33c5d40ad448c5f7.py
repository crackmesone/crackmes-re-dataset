# DaXXoR KeygenMe - Algorithm Reconstruction
# Based on writeup by Moonbaby
#
# Algorithm:
# 1. Name length must be between 6 and 13 (inclusive): 5 < len < 14
# 2. Default alphabet string: "AbCdEfGhIjKlMnOpQrStUvWxYzaBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890"
# 3. For each position i in 0..61, check if reaDefStr[i] appears in the name.
#    If yes, append the token for position i to reaTemp.
# 4. The token for position i is: str(i+1) + "%"  (but position 3 (char 'd') maps to nothing in the source
#    - ASSUMPTION: every index maps to str(index+1)+"%", the source code just lists them explicitly)
# 5. After building reaTemp (which is the serial for one pass), reverse it by prepending:
#    MovStr prepends reaTemp before reaTempSerial each iteration.
#    Actually: the serial is built by prepending each new token, giving a reversed order.
# 6. The final serial is TempSerial repeated ceil(LenUser/4) times (loop increments i by 4 each time,
#    starting from 0, while i < LenUser).
#
# From the example: Moonbaby -> chars present: M,o,n,b,a,y
# DefStr index: A=0,b=1,C=2,d=3,E=4,f=5,G=6,h=7,I=8,j=9,K=10,l=11,M=12,n=13,O=14,...
# b is at index 1 -> "2%"
# M is at index 12 -> "13%"
# n is at index 13 -> "14%"
# a is at index 26 -> token = "27%"... but writeup says "01%"
# ASSUMPTION: The second half of the alphabet (aBcDe...z) uses 01%, 02%, 03%... format
# From the raw table bytes: after z (index 25) comes a->"01%", B->"02%", etc.
# So indices 0-25 use "N%" and indices 26-51 use "0N%" (with leading zero concept)
# Actually from table: index 26 = 'a' -> "01%", index 27 = 'B' -> "02%", ...
# index 51 = 'Z' -> "026%", then digits 1->"0x", 2->"1x"... (different format)
# ASSUMPTION for digits: looking at table end: 1->"0x", 2->"1x", 3->"9x", 4->"5x",
# 5->"4x", 6->"6x", 7->"3x", 8->"8x", 9->"7x", 0->"2x"

DEF_STR = "AbCdEfGhIjKlMnOpQrStUvWxYzaBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890"

# Token table built from the writeup's raw hex dump
# Indices 0-25: letters A,b,C,d,E,f,G,h,I,j,K,l,M,n,O,p,Q,r,S,t,U,v,W,x,Y,z
# Tokens: 1%,2%,3%,4%,5%,6%,7%,8%,9%,10%,11%,12%,13%,14%,15%,16%,17%,18%,19%,20,21%,22%,23%,24%,25%,26%
# Note: index 19 (t) -> "20" (no % in table for 't'?), ASSUMPTION: it's "20%" like others
# Indices 26-51: a,B,c,D,e,F,g,H,i,J,k,L,m,N,o,P,q,R,s,T,u,V,w,X,y,Z
# Tokens: 01%,02%,03%,04%,05%,06%,07%,08%,09%,010%,011%,012%,013%,014%,015%,016%,017%,018%,019%,020%,021%,022%,023%,024%,025%,026%
# Indices 52-61: 1,2,3,4,5,6,7,8,9,0
# Tokens: 0x,1x,9x,5x,4x,6x,3x,8x,7x,2x

TOKEN_TABLE = [
    # 0-25 (uppercase-ish first half)
    "1%", "2%", "3%", "4%", "5%", "6%", "7%", "8%", "9%", "10%",
    "11%", "12%", "13%", "14%", "15%", "16%", "17%", "18%", "19%", "20%",
    "21%", "22%", "23%", "24%", "25%", "26%",
    # 26-51 (second half)
    "01%", "02%", "03%", "04%", "05%", "06%", "07%", "08%", "09%", "010%",
    "011%", "012%", "013%", "014%", "015%", "016%", "017%", "018%", "019%", "020%",
    "021%", "022%", "023%", "024%", "025%", "026%",
    # 52-61 (digits 1,2,3,4,5,6,7,8,9,0)
    "0x", "1x", "9x", "5x", "4x", "6x", "3x", "8x", "7x", "2x",
]


def build_temp_serial(name):
    """Build the base TempSerial from the name."""
    rea_temp = ""
    for i in range(62):
        char_at_i = DEF_STR[i]
        if char_at_i in name:
            token = TOKEN_TABLE[i]
            # MovStr prepends: new token goes BEFORE existing serial
            rea_temp = token + rea_temp
    return rea_temp


def compute_loop_count(length):
    """Number of loop iterations: start i=0, i+=4, while i < length."""
    count = 0
    i = 0
    while i < length:
        count += 1
        i += 4
    return count


def keygen(name):
    length = len(name)
    if length <= 5 or length >= 14:
        raise ValueError(f"Name length must be 6-13, got {length}")
    temp_serial = build_temp_serial(name)
    loops = compute_loop_count(length)
    serial = temp_serial * loops
    return serial


def verify(name, serial):
    length = len(name)
    if length <= 5 or length >= 14:
        return False
    try:
        expected = keygen(name)
    except ValueError:
        return False
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
