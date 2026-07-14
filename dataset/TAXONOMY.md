# Tag taxonomy

Obfuscation labels are **multi-label** (a crackme can carry several) and organized
in two levels:

```
raw_obfuscation_tags   free-text tags the model wrote      (4,654 distinct strings)
      │  normalize_tags.py  (regex → controlled vocabulary)
      ▼
obfuscation_classes    13 high-level classes               (below)
      │  subclassify.py     (regex → specific techniques)
      ▼
antidebug_methods / packers / controlflow_methods / antidisasm_methods /
crypto_methods / encryption_methods                 specific sub-labels
```

The exact mapping rules are regexes in `pipeline/normalize_tags.py` (classes) and
`pipeline/subclassify.py` (sub-labels) — edit and re-run to adjust the scheme, no
API cost. Counts below = crackmes carrying that tag (of 4,598).

> **Design choices baked into the vocabulary:** *Timing checks*, *Anti-attach /
> thread tricks*, and the debugger-detection use of *exceptions* are all
> anti-debugging techniques, so they are folded into **Anti-debugging** (with
> `Timing (rdtsc/GetTickCount)`, `Anti-attach / thread suspension`, and
> `Exception-based (SEH/VEH/INT2D)` as sub-labels). *Commercial protectors*
> (Themida, VMProtect, .NET Reactor, …) are folded into **Packer**, with the
> protector name kept as a packer sub-label. Exceptions are dual-use, so each
> crackme's exception tags are routed to **Anti-debugging** and/or **Control-flow
> obfuscation** based on wording.

## Obfuscation classes (13)

| Class | Crackmes | What it covers |
|---|---:|---|
| Anti-debugging | 756 | detects/thwarts a debugger — incl. timing (rdtsc/GetTickCount), anti-attach/thread tricks, and SEH/INT2D debugger detection |
| String / data encryption | 589 | encrypted/obfuscated strings or data (XOR, RC4, string encryption) |
| Packer | 563 | runtime packers (UPX, FSG, ASPack, MPRESS, …) **and** commercial protectors (Themida, VMProtect, .NET Reactor, ConfuserEx, ASProtect, …) |
| Self-modifying / runtime decrypt | 312 | code rewrites/decrypts itself at runtime (SMC, section decryption, polymorphic, VirtualProtect) |
| Crypto / hash algorithm | 283 | standard crypto/hash in the key check (MD5, SHA, CRC32, AES, TEA) |
| Code virtualization / VM | 256 | custom bytecode interpreter / virtualized code |
| Control-flow obfuscation | 187 | flattening, junk branches, indirect jumps, state machines, exception-driven flow |
| Anti-disassembly | 183 | junk bytes, opaque predicates, misaligned code that breaks disassemblers |
| Anti-tamper / integrity | 137 | checksum/CRC self-checks, anti-patch |
| Import / API obfuscation | 78 | runtime import resolution, API hashing, IAT obfuscation |
| Custom / generic obfuscation | 73 | bespoke/unspecified "obfuscated" with no named mechanism |
| Anti-VM / sandbox | 22 | VM/sandbox detection |
| Nag / trial | 12 | nag screens, trial/time limits |

## Sub-labels

**`antidebug_methods` (18)** — IsDebuggerPresent (211), Debugger/tool window detection (158),
Timing rdtsc/GetTickCount (118), PEB BeingDebugged/NtGlobalFlag (81), INT3/0xCC scan (74),
ptrace (57), Exception-based SEH/VEH/INT2D (54), Hardware breakpoints DRx (45),
NtQueryInformationProcess (26), OutputDebugString (25), CheckRemoteDebuggerPresent (24),
Self-debug/block-debugger (21), TLS callback (19), Anti-dump (16), Parent-process check (11),
Anti-attach/thread suspension (9), DbgBreakPoint/DbgUiRemoteBreakin patch (8),
CloseHandle invalid-handle (5)

**`packers` (24)** — runtime packers: UPX (219), FSG (62), ASPack (45), MPRESS (31),
tElock (12), Petite (9), Yoda (8), PECompact (5), exepack (3), PKLite (1), MEW (1),
other named (2); commercial protectors: VMProtect (9), ASProtect (7), .NET Reactor (7),
ConfuserEx (6), Enigma (3), Themida (3), ExeCryptor (3), WinLicense (2), SmartAssembly (2),
PELock (1), CodeVirtualizer (1), Dotfuscator (1)

**`controlflow_methods` (6)** — Spaghetti/junk-branch (40), Exception/interrupt-based (29),
Indirect/computed jumps & calls (23), State machine/dispatcher (21), Control-flow flattening CFF (16),
Return-address/stack-based (14)

**`antidisasm_methods` (5)** — Junk/garbage bytes (87), Opaque predicates (18),
Malformed PE / bad bytes UD2 (12), Overlapping/misaligned instructions (8),
Jump-based desync (7); 20 crackmes have a generic anti-disassembly tag with no
specific mechanism.

**`crypto_methods` (12)** — MD5 (69), CRC32 (49), RSA (37), AES (32), SHA-256 (30),
SHA-1 (23), TEA/XTEA (23), Base64 (22), RC4 (18), other/custom hash (12), Blowfish (11),
DES/3DES (7); 9 crackmes have no named algorithm.

**`encryption_methods` (6)** — XOR (353), Base64 (25), RC4 (24), Substitution/table (14),
TEA/XTEA (12), AES (11); 120 crackmes have a generic string/data-encryption tag with
no named cipher.

---

## Worked example

`kleygenme_2_n0se by n0ise` — https://crackmes.one/crackme/5ab77f5533c5d40ad448c1ee

```json
{
  "hexid": "5ab77f5533c5d40ad448c1ee",
  "name": "kleygenme_2_n0se by n0ise",
  "platform": "Windows", "arch": "x86", "language": "Borland Delphi", "difficulty": 4.0,

  "has_unique_flag": false,
  "flag": null,
  "no_flag_reason": "keygen_algorithmic",

  "verifier": {
    "recovered": "full",
    "contract": "python3 <id>.py {keygen | verify <args>}",
    "interface": {"kind": "name+serial", "verify_args": 2},
    "safety": "safe",
    "self_test": {"pass": true, "keygen_ok": true, "accepts_valid": true, "rejects_invalid": true},
    "code": "..."
  },

  "obfuscation_classes":  ["Anti-debugging", "Packer"],
  "antidebug_methods":    ["Debugger/tool window detection", "IsDebuggerPresent", "PEB BeingDebugged / NtGlobalFlag"],
  "packers":              ["UPX"],
  "raw_obfuscation_tags": ["UPX", "IsDebuggerPresent", "window name search (Olly detection)", "FS:[30] PEB debugger check"],

  "label_confidence": "high",
  "provenance": {"model": "claude-sonnet-4-6", "binary_verified": false}
}
```

**What it means, field by field:**

- **It's a keygen, not a fixed-secret crackme.** `has_unique_flag: false` with
  `no_flag_reason: keygen_algorithmic` — the valid serial is *computed from the
  username*, so there's no single flag; the deliverable is a script.
- **The verifier was fully reconstructed and works.** `recovered: "full"` and
  `self_test.pass: true` (it generated a valid pair, `verify` accepted it, and
  rejected a corrupted one). `interface.kind: "name+serial"` → the CLI takes two
  args. Running it:
  ```
  $ python3 verifiers/5ab77f5533c5d40ad448c1ee.py keygen
  alice   RK302482857327Q-ZX42A-PM2215119OU
  Kevin   RK302482857327Q-ZX62A-PM2547533OU
  bob     Name too small          # the algorithm requires name length >= 4
  $ python3 verifiers/5ab77f5533c5d40ad448c1ee.py verify alice RK302482857327Q-ZX42A-PM2215119OU
  1
  ```
- **The tags show the two-level scheme in action.** The 4 free-text
  `raw_obfuscation_tags` normalize into 2 `obfuscation_classes`:
  - `UPX` → **Packer** (and `packers: ["UPX"]` at the sub-label level)
  - `IsDebuggerPresent`, `window name search (Olly detection)`, `FS:[30] PEB debugger check`
    → all **Anti-debugging** (sub-labels: `IsDebuggerPresent`, `Debugger/tool window
    detection`, `PEB BeingDebugged / NtGlobalFlag`)
- **Provenance travels with it.** `binary_verified: false` — the label came from
  the (human-moderated) writeup via the model, not yet confirmed by running the
  binary. `label_confidence: high` is the model's own confidence.

So one record tells you: the challenge *type* (keygen), a *working solver* you can
run, and *what defenses* the binary uses — at both a coarse (classes) and fine
(specific techniques) grain.
