import os
import re
import shutil
import subprocess
from typing import Dict, Any
from fastapi import FastAPI

app = FastAPI()

def _first_nonempty_line(text: str) -> str:
    for line in (text or "").splitlines():
        s = line.strip()
        if s:
            return s
    return ""

def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    combined = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, combined

def _extract_version(line: str) -> str:
    # Accept lines like "pdfinfo version 22.02.0" or "pdftoppm version 22.02.0"
    m = re.search(r'(pdfinfo|pdftoppm)\s+version\s+([0-9][\w\.\-+]*)', line, re.IGNORECASE)
    return m.group(0) if m else ""

def _poppler_version() -> Dict[str, Any]:
    # 1) Debian/Ubuntu: query the installed package first (most reliable)
    rc, out = _run(["dpkg-query", "-W", "-f=${Version}\\n", "poppler-utils"])
    if rc == 0:
        ver = _first_nonempty_line(out)
        if ver:
            # also surface the binary path if present
            pdfinfo_path = shutil.which("pdfinfo") or shutil.which("pdftoppm")
            return {"status": "ok", "path": pdfinfo_path or "", "version": f"poppler-utils {ver}"}

    # 2) Try pdftoppm -v (often prints to stderr, but returns 0)
    pdftoppm_path = shutil.which("pdftoppm")
    if pdftoppm_path:
        rc, out = _run([pdftoppm_path, "-v"])
        line = _first_nonempty_line(out)
        ver = _extract_version(line)
        if ver:
            return {"status": "ok (via pdftoppm)", "path": pdftoppm_path, "version": ver}
        if rc == 0 and line:  # accept generic line if exit code OK
            return {"status": "ok (via pdftoppm)", "path": pdftoppm_path, "version": line}

    # 3) Try pdfinfo -v (don’t use --version; some builds treat it as a filename)
    pdfinfo_path = shutil.which("pdfinfo")
    if pdfinfo_path:
        rc, out = _run([pdfinfo_path, "-v"])
        line = _first_nonempty_line(out)
        ver = _extract_version(line)
        if ver:
            return {"status": "ok", "path": pdfinfo_path, "version": ver}
        if rc == 0 and line and "I/O Error" not in line:
            return {"status": "ok", "path": pdfinfo_path, "version": line}

    return {"status": "missing"}

def check_binaries() -> Dict[str, Dict[str, Any]]:
    results: Dict[str, Dict[str, Any]] = {}

    # ---- Tesseract ----
    tesseract_path = shutil.which("tesseract")
    if tesseract_path:
        rc, out = _run([tesseract_path, "--version"])
        line = _first_nonempty_line(out)
        results["tesseract"] = {
            "status": "ok" if rc == 0 else "error",
            "path": tesseract_path,
            "version": line or "unknown",
        }
    else:
        results["tesseract"] = {"status": "missing"}

    # ---- Poppler ----
    results["poppler"] = _poppler_version()

    return results

def overall_ok(deps: Dict[str, Dict[str, Any]]) -> bool:
    def good(x: Dict[str, Any]) -> bool:
        return x.get("status", "").startswith("ok")
    return good(deps.get("tesseract", {})) and good(deps.get("poppler", {}))

@app.get("/")
async def index():
    deps = check_binaries()
    return {"details": "Hello World", "ok": overall_ok(deps), "dependencies": deps}
