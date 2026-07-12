# Tag taxonomy

Obfuscation labels are **multi-label** (a crackme can carry several) and organized
in two levels:

```
raw_obfuscation_tags   free-text tags the model wrote      (4,654 distinct strings)
      │  normalize_tags.py  (regex → controlled vocabulary)
      ▼
obfuscation_classes    21 high-level classes               (below)
      │  subclassify.py     (regex → specific techniques)
      ▼
antidebug_methods / packers / controlflow_methods   specific sub-labels
```

The exact mapping rules are regexes in `pipeline/normalize_tags.py` (classes) and
`pipeline/subclassify.py` (sub-labels) — edit and re-run to adjust the scheme, no
API cost. Counts below = crackmes carrying that tag (of 4,598).

## Obfuscation classes (21)

| Class | Crackmes | What it covers |
|---|---:|---|
| Anti-debugging | 731 | detects/thwarts a debugger (IsDebuggerPresent, ptrace, PEB checks, INT3 scans, timing, HW breakpoints, tool-window detection) |
| Packer | 532 | runtime executable packer (UPX, FSG, ASPack, PECompact, MPRESS, …) |
| String / data encryption | 514 | encrypted/obfuscated strings or data (XOR, RC4, string encryption) |
| Self-modifying / runtime decrypt | 312 | code rewrites/decrypts itself at runtime (SMC, section decryption, polymorphic, VirtualProtect) |
| Code virtualization / VM | 256 | custom bytecode interpreter / virtualized code |
| Crypto / hash algorithm | 205 | standard crypto/hash in the key check (MD5, SHA, CRC32, AES, TEA) |
| Anti-tamper / integrity | 137 | checksum/CRC self-checks, anti-patch |
| Control-flow obfuscation | 133 | flattening, junk branches, indirect jumps, state machines, exception-driven flow |
| Anti-disassembly | 126 | junk bytes, opaque predicates, misaligned code that breaks disassemblers |
| Timing checks | 123 | rdtsc/GetTickCount timing to detect single-stepping/analysis |
| Exception-based | 85 | SEH/VEH/INT2D used for obfuscation or control flow |
| Import / API obfuscation | 78 | runtime import resolution, API hashing, IAT obfuscation |
| Custom / generic obfuscation | 73 | bespoke/unspecified "obfuscated" without a named mechanism |
| Encoding (base64/hex) | 72 | reversible encodings (base64, hex, rot13) |
| Commercial protector | 39 | named protectors (Themida, VMProtect, .NET Reactor, ConfuserEx, ASProtect…) |
| Stripped / no symbols | 38 | symbols removed |
| Anti-attach / thread tricks | 34 | anti-attach, thread suspension, TLS-callback tricks |
| Binary hardening (ASLR/PIE/canary) | 29 | compiler mitigations (ASLR, PIE, stack canary, NX) |
| Anti-VM / sandbox | 22 | VM/sandbox detection |
| Nag / trial | 12 | nag screens, trial/time limits |
| Anti-static analysis | 5 | explicitly thwarts static analysis |

## Sub-labels

**`antidebug_methods` (17)** — IsDebuggerPresent (211), Debugger/tool window detection (158),
Timing rdtsc/GetTickCount (118), PEB BeingDebugged/NtGlobalFlag (81), INT3/0xCC scan (74),
ptrace (57), Exception-based SEH/VEH/INT2D (54), Hardware breakpoints DRx (45),
NtQueryInformationProcess (26), OutputDebugString (25), CheckRemoteDebuggerPresent (24),
Self-debug/block-debugger (21), TLS callback (19), Anti-dump (16), Parent-process check (11),
DbgBreakPoint/DbgUiRemoteBreakin patch (8), CloseHandle invalid-handle (5)

**`packers` (12)** — UPX (219), FSG (62), ASPack (45), MPRESS (31), tElock (12), Petite (9),
Yoda (8), PECompact (5), exepack (3), other named (2), PKLite (1), MEW (1)

**`controlflow_methods` (6)** — Spaghetti/junk-branch (40), Exception/interrupt-based (29),
Indirect/computed jumps & calls (23), State machine/dispatcher (21), Control-flow flattening CFF (16),
Return-address/stack-based (14)

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
