#!/usr/bin/env python3
"""
Stage 2: run Sonnet 4.6 over the assembled corpus to extract, per crackme:
  1) whether it has a unique flag/password/serial
  2) what that flag is (verbatim, if present)
  3) obfuscation / protector / anti-debugging techniques mentioned

Arch/platform are intentionally NOT asked for (they live in crackmes.json).

DEFAULT MODE IS DRY-RUN. It writes the Batches request file and prints a token
+ cost estimate. It does NOT contact the API. Pass --submit to actually send
the batch (requires ANTHROPIC_API_KEY and the `anthropic` package).

Usage:
  python3 extract_flags.py                 # dry run: build requests + estimate
  python3 extract_flags.py --submit        # create the batch job (costs money)
  python3 extract_flags.py --collect BATCH_ID   # fetch results when ended
"""
import os, sys, json, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "pipeline")
CORPUS = os.path.join(OUT, "corpus.jsonl")
REQFILE = os.path.join(OUT, "batch_requests.jsonl")
RESFILE = os.path.join(OUT, "results.jsonl")

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024

# Sonnet 4.6 list price per 1M tokens; Batches API = 50% off.
PRICE_IN, PRICE_OUT = 3.00, 15.00
BATCH_DISCOUNT = 0.5

SYSTEM = (
    "You are a reverse-engineering analyst. You are given the crackme's own "
    "description, its user COMMENTS, and any SOLUTION write-ups (author notes "
    "plus the text extracted from their solution archives). Binaries are NOT "
    "provided — judge only from this text.\n\n"
    "Determine three things:\n"
    "1. has_unique_flag: does this crackme have a single correct secret "
    "(password / serial / key / flag) that a solver must find? Some crackmes "
    "instead accept any valid key (keygen-me) or have no single answer — mark "
    "those false.\n"
    "2. flag: if a specific correct secret is stated in the comments/solutions, "
    "return it VERBATIM. If it is a keygen (no single value) or not revealed in "
    "the text, return null. Do not guess or invent one.\n"
    "3. obfuscation: list protector / packer / obfuscation / anti-debug / "
    "anti-VM techniques that the text says are used (e.g. UPX, VMProtect, "
    "IsDebuggerPresent, string encryption, control-flow flattening). Empty list "
    "if none mentioned.\n"
    "4. no_flag_reason: if has_unique_flag is FALSE, classify WHY there is no "
    "single secret:\n"
    "   - 'keygen_algorithmic': the key/serial is derived from input (name, id, "
    "computer name) so infinitely many valid pairs exist / a keygen is required;\n"
    "   - 'patch_or_enable_me': the goal is to patch or enable the binary "
    "(bypass a check, enable a button), not to find a secret;\n"
    "   - 'any_input_matches_pattern': any input satisfying a format/constraint "
    "is accepted (e.g. any 10-char string with '@' at index 4);\n"
    "   - 'multiple_valid_answers': a small fixed set of different valid answers;\n"
    "   - 'not_a_secret_challenge': analysis/reversing exercise with no password;\n"
    "   - 'other'.\n"
    "   If has_unique_flag is TRUE, set no_flag_reason to 'n_a' (this includes "
    "the case where a unique flag exists but is not revealed in the text).\n\n"
    "Only report what the provided text supports. Set confidence accordingly."
)

SCHEMA = {
    "type": "object",
    "properties": {
        "has_unique_flag": {"type": "boolean"},
        "flag": {"type": ["string", "null"]},
        "flag_source": {
            "type": "string",
            "enum": ["comment", "solution", "description", "none"],
        },
        "obfuscation": {"type": "array", "items": {"type": "string"}},
        "no_flag_reason": {
            "type": "string",
            "enum": ["keygen_algorithmic", "patch_or_enable_me",
                     "any_input_matches_pattern", "multiple_valid_answers",
                     "not_a_secret_challenge", "other", "n_a"],
        },
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "evidence": {"type": "string"},
    },
    "required": ["has_unique_flag", "flag", "flag_source", "obfuscation",
                 "no_flag_reason", "confidence", "evidence"],
    "additionalProperties": False,
}


# Per-solution writeup character cap applied at request-build time (tune to fit
# budget). Author notes are kept in full; only the bulk writeup dump is trimmed.
WRITEUP_CAP = int(os.environ.get("WRITEUP_CAP", "8000"))


def render_user(rec: dict) -> str:
    parts = [f"CRACKME: {rec.get('name')}  (author: {rec.get('author')}, lang: {rec.get('lang')})"]
    if rec.get("info"):
        parts.append("DESCRIPTION:\n" + rec["info"])
    if rec.get("comments"):
        parts.append("COMMENTS:\n" + "\n".join(
            f"- [{c.get('author')}] {c.get('text')}" for c in rec["comments"]))
    for i, s in enumerate(rec.get("solutions", []), 1):
        body = []
        if s.get("info"):
            body.append("author note: " + s["info"])
        if s.get("writeup"):
            w = s["writeup"]
            if WRITEUP_CAP and len(w) > WRITEUP_CAP:
                w = w[:WRITEUP_CAP] + "\n...[writeup truncated]"
            body.append(w)
        if body:
            parts.append(f"SOLUTION {i} (by {s.get('author')}):\n" + "\n".join(body))
    if rec.get("has_pdf_writeup"):
        parts.append("(NOTE: a PDF write-up also exists but was not text-extracted.)")
    return "\n\n".join(parts)


def has_signal(rec: dict) -> bool:
    if rec.get("comments"):
        return True
    for s in rec.get("solutions", []):
        if s.get("info") or s.get("writeup"):
            return True
    return False


def signal_weight(rec: dict) -> int:
    w = sum(len(c["text"]) for c in rec.get("comments", []))
    for s in rec.get("solutions", []):
        w += len(s.get("writeup", "")) + len(s.get("info", "")) * 2
    return w


def build_requests(limit=0, sample=False):
    records = [json.loads(l) for l in open(CORPUS)]
    skipped = [r["id"] for r in records if not has_signal(r)]
    records = [r for r in records if has_signal(r)]
    if sample:
        records.sort(key=signal_weight, reverse=True)
    if limit:
        records = records[:limit]
    reqs, est_in, est_out = [], 0, 0
    for rec in records:
            user = render_user(rec)
            est_in += len(SYSTEM) // 4 + len(user) // 4 + 120  # +schema/overhead
            est_out += 120
            reqs.append({
                "custom_id": rec["id"],
                "params": {
                    "model": MODEL,
                    "max_tokens": MAX_TOKENS,
                    "system": SYSTEM,
                    "messages": [{"role": "user", "content": user}],
                    "output_config": {
                        "format": {"type": "json_schema", "schema": SCHEMA}
                    },
                },
            })
    return reqs, skipped, est_in, est_out


def load_key():
    # Prefer key.txt (explicitly provided) over any stale env var that would
    # otherwise silently shadow it.
    p = os.path.join(ROOT, "key.txt")
    if os.path.exists(p):
        k = open(p).read().strip()
        if k:
            return k
    k = os.environ.get("ANTHROPIC_API_KEY")
    if k:
        return k
    sys.exit("No API key: provide key.txt or set ANTHROPIC_API_KEY")


def dry_run(limit=0, sample=False):
    reqs, skipped, est_in, est_out = build_requests(limit, sample)
    with open(REQFILE, "w") as f:
        for r in reqs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    json.dump(skipped, open(os.path.join(OUT, "no_signal_ids.json"), "w"))
    cost = (est_in / 1e6 * PRICE_IN + est_out / 1e6 * PRICE_OUT) * BATCH_DISCOUNT
    cost_full = est_in / 1e6 * PRICE_IN + est_out / 1e6 * PRICE_OUT
    print(f"requests to send : {len(reqs)}")
    print(f"skipped (no signal, default to unknown): {len(skipped)}")
    print(f"est input tokens : {est_in:,}")
    print(f"est output tokens: {est_out:,}")
    print(f"model            : {MODEL}")
    print(f"est cost (Batches, 50% off): ${cost:,.2f}")
    print(f"est cost (real-time)       : ${cost_full:,.2f}")
    print(f"\nrequest file written: {REQFILE}")
    print("DRY RUN ONLY — nothing submitted. Re-run with --submit to send.")


def submit(limit=0, sample=False):
    import anthropic
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    reqs, skipped, _, _ = build_requests(limit, sample)
    client = anthropic.Anthropic(api_key=load_key())
    batch = client.messages.batches.create(requests=[
        Request(custom_id=r["custom_id"],
                params=MessageCreateParamsNonStreaming(**r["params"]))
        for r in reqs
    ])
    json.dump({"batch_id": batch.id, "count": len(reqs)},
              open(os.path.join(OUT, "batch_job.json"), "w"), indent=2)
    print(f"submitted batch {batch.id} with {len(reqs)} requests")
    print("poll status with: python3 extract_flags.py --collect", batch.id)


def collect(batch_id: str, out_path=RESFILE):
    import anthropic
    client = anthropic.Anthropic(api_key=load_key())
    b = client.messages.batches.retrieve(batch_id)
    print("status:", b.processing_status, "counts:", b.request_counts)
    if b.processing_status != "ended":
        print("not finished yet; re-run later.")
        return
    n = 0
    with open(out_path, "w") as out:
        for r in client.messages.batches.results(batch_id):
            row = {"id": r.custom_id}
            if r.result.type == "succeeded":
                txt = next((b.text for b in r.result.message.content if b.type == "text"), "{}")
                try:
                    row.update(json.loads(txt))
                except Exception:
                    row["parse_error"] = txt[:500]
            else:
                row["error"] = r.result.type
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {n} results to {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--collect", metavar="BATCH_ID")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sample", action="store_true",
                    help="order by richest signal, and route output to results_sample.jsonl")
    args = ap.parse_args()
    out_path = os.path.join(OUT, "results_sample.jsonl") if args.sample else RESFILE
    if args.collect:
        collect(args.collect, out_path)
    elif args.submit:
        submit(args.limit, args.sample)
    else:
        dry_run(args.limit, args.sample)
