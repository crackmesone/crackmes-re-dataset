#!/usr/bin/env python3
"""
Stage 1 (local, no API): assemble one text record per crackme from
  - crackme.info  (the challenge description)
  - all comments  (comment.info)
  - all solutions: solution.info  +  flattened WRITEUP TEXT from the solution
    archive (nested, password-protected). Binaries and images are skipped;
    only human-readable text/source/markup is extracted.

Output: pipeline/corpus.jsonl  (one JSON object per crackme)
        pipeline/corpus_stats.json

Nothing here calls any API. Safe to run repeatedly.
"""
import os, io, re, json, glob, zipfile, html.parser, collections

try:
    import pypdf
    _HAVE_PYPDF = True
except Exception:
    _HAVE_PYPDF = False

MAX_PDF_PAGES = 40   # cap pages parsed per PDF

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = os.path.join(ROOT, "database")
SOLDIR = os.path.join(ROOT, "solution")
OUT  = os.path.join(ROOT, "pipeline")

# ---- tuning knobs (bound token cost) ----
MAX_CHARS_PER_FILE   = 20000    # truncate any single writeup file
MAX_WRITEUP_PER_CM   = 80000    # total writeup text kept per crackme
MAX_COMMENT_CHARS    = 20000    # total comment text kept per crackme

ARCHIVE_PASSWORDS = [b"crackmes.one", b"crackmes.de", b"crackmes", None]

# Extensions we treat as binary/non-text and never extract.
SKIP_EXT = {
    ".exe",".dll",".sys",".bin",".o",".obj",".lib",".a",".so",".dylib",
    ".ico",".res",".resx",".png",".jpg",".jpeg",".gif",".bmp",".webp",".tif",".tiff",
    ".zip",".rar",".7z",".gz",".tar",".cab",".apk",".jar",".class",".dex",
    ".mp4",".avi",".mov",".mp3",".wav",".pdf",  # pdf handled separately (flagged, not text-extracted here)
    ".db",".sqlite",".dat",".pdb",".idb",".i64",".ncb",".suo",".pyc",
}
# PDF writeups: extracted locally with pypdf when possible; if a PDF yields no
# usable text (scanned/image-only), we flag has_pdf so the API stage can decide
# whether to attach it natively.
PDF_EXT = {".pdf"}


def pdf_to_text(data: bytes) -> str:
    if not _HAVE_PYPDF:
        return ""
    try:
        reader = pypdf.PdfReader(io.BytesIO(data))
        out = []
        for i, page in enumerate(reader.pages):
            if i >= MAX_PDF_PAGES:
                break
            try:
                out.append(page.extract_text() or "")
            except Exception:
                continue
        return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
    except Exception:
        return ""


class _Stripper(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.buf = []
        self._skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
    def handle_data(self, data):
        if not self._skip:
            self.buf.append(data)
    def text(self):
        return re.sub(r"\n{3,}", "\n\n", "".join(self.buf))


def html_to_text(raw: str) -> str:
    p = _Stripper()
    try:
        p.feed(raw)
        return p.text()
    except Exception:
        return re.sub(r"<[^>]+>", " ", raw)


def decode(data: bytes) -> str:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("latin-1", "ignore")


def looks_binary(data: bytes) -> bool:
    if b"\x00" in data[:4096]:
        return True
    chunk = data[:4096]
    if not chunk:
        return True
    nonprint = sum(1 for b in chunk if b < 9 or (13 < b < 32))
    return nonprint / len(chunk) > 0.10


def _open_first(zf: zipfile.ZipFile):
    """Return a working password for zf, or False if none work / empty."""
    names = [n for n in zf.namelist() if not n.endswith("/")]
    if not names:
        return None
    for pw in ARCHIVE_PASSWORDS:
        try:
            zf.read(names[0], pwd=pw)
            return pw
        except Exception:
            continue
    return False


def extract_texts(zbytes: bytes, depth=0, budget=None):
    """Recursively pull text files out of a (possibly nested, encrypted) zip.
    Returns (list_of_text_chunks, has_pdf_bool)."""
    if budget is None:
        budget = [MAX_WRITEUP_PER_CM]
    chunks, has_pdf = [], False
    if depth > 3 or budget[0] <= 0:
        return chunks, has_pdf
    try:
        zf = zipfile.ZipFile(io.BytesIO(zbytes))
    except Exception:
        return chunks, has_pdf
    pw = _open_first(zf)
    if pw is False or pw is None:
        return chunks, has_pdf
    for n in zf.namelist():
        if n.endswith("/") or budget[0] <= 0:
            continue
        ext = os.path.splitext(n)[1].lower()
        try:
            data = zf.read(n, pwd=pw)
        except Exception:
            continue
        if ext == ".zip" or (ext == "" and data[:2] == b"PK"):
            sub, pdf = extract_texts(data, depth + 1, budget)
            chunks += sub
            has_pdf = has_pdf or pdf
            continue
        if ext in PDF_EXT:
            ptext = pdf_to_text(data)
            if len(ptext) >= 40:            # got a usable text layer
                ptext = ptext[:MAX_CHARS_PER_FILE]
                piece = f"\n----- writeup file (pdf): {n} -----\n" + ptext
                piece = piece[:budget[0]]
                budget[0] -= len(piece)
                chunks.append(piece)
            else:                            # scanned / image-only PDF
                has_pdf = True
            continue
        if ext in SKIP_EXT:
            continue
        if looks_binary(data):
            continue
        text = decode(data)
        if ext in (".htm", ".html"):
            text = html_to_text(text)
        text = text.strip()
        if not text:
            continue
        text = text[:MAX_CHARS_PER_FILE]
        header = f"\n----- writeup file: {n} -----\n"
        piece = header + text
        piece = piece[:budget[0]]
        budget[0] -= len(piece)
        chunks.append(piece)
    return chunks, has_pdf


def main():
    crackmes = json.load(open(os.path.join(DB, "crackmes.json")))
    comments = json.load(open(os.path.join(DB, "comments.json")))
    solutions = json.load(open(os.path.join(DB, "solutions.json")))

    c_by = collections.defaultdict(list)
    for c in comments:
        if c.get("deleted"): continue
        c_by[c.get("crackmehexid")].append(c)
    s_by = collections.defaultdict(list)
    for s in solutions:
        s_by[s.get("crackmehexid") or s.get("crackmeid")].append(s)

    stats = collections.Counter()
    tok_est = 0
    with open(os.path.join(OUT, "corpus.jsonl"), "w") as fout:
        for cm in crackmes:
            hid = cm.get("hexid")
            rec = {
                "id": hid,
                "name": cm.get("name"),
                "author": cm.get("author"),
                "lang": cm.get("lang"),
                "info": (cm.get("info") or "").strip(),
                "comments": [],
                "solutions": [],
                "has_pdf_writeup": False,
            }
            # comments
            cbudget = MAX_COMMENT_CHARS
            for c in c_by.get(hid, []):
                t = (c.get("info") or "").strip()
                if not t: continue
                t = t[:cbudget]; cbudget -= len(t)
                rec["comments"].append({"author": c.get("author"), "text": t})
                if cbudget <= 0: break
            # solutions
            budget = [MAX_WRITEUP_PER_CM]
            for s in s_by.get(hid, []):
                sinfo = (s.get("info") or "").strip()
                # boilerplate import notice carries no signal on its own
                if "imported from crackmes" in sinfo.lower() and len(sinfo) < 200:
                    sinfo = ""
                writeup = ""
                zpath = os.path.join(SOLDIR, (s.get("hexid") or s.get("_id") or "") + ".zip")
                if os.path.exists(zpath) and budget[0] > 0:
                    try:
                        chunks, pdf = extract_texts(open(zpath, "rb").read(), 0, budget)
                        writeup = "\n".join(chunks)
                        rec["has_pdf_writeup"] = rec["has_pdf_writeup"] or pdf
                    except Exception:
                        stats["solzip_err"] += 1
                if sinfo or writeup:
                    rec["solutions"].append({
                        "author": s.get("author"),
                        "info": sinfo,
                        "writeup": writeup,
                    })
            # bookkeeping
            if rec["comments"]: stats["with_comments"] += 1
            if any(s["writeup"] for s in rec["solutions"]): stats["with_writeup_text"] += 1
            if rec["has_pdf_writeup"]: stats["with_unextractable_pdf"] += 1
            if not rec["comments"] and not rec["solutions"]:
                stats["empty_signal"] += 1
            blob = rec["info"] + " ".join(c["text"] for c in rec["comments"]) + \
                   " ".join(s["info"] + s["writeup"] for s in rec["solutions"])
            tok_est += len(blob) // 4
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            stats["total"] += 1

    stats_out = dict(stats)
    stats_out["approx_input_tokens_total"] = tok_est
    json.dump(stats_out, open(os.path.join(OUT, "corpus_stats.json"), "w"), indent=2)
    print(json.dumps(stats_out, indent=2))


if __name__ == "__main__":
    main()
