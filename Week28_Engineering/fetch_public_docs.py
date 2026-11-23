"""Snapshot PSF-licensed CPython documentation at a release tag for the public pilot."""
import hashlib
import json
from urllib.request import urlopen

from retrieval import ROOT


def fetch():
    target = ROOT / "data" / "public_docs"
    (target / "manuals").mkdir(parents=True, exist_ok=True)
    manifest, provenance = [], []
    for name, upstream in (("tutorial_venv", "Doc/tutorial/venv.rst"),
                           ("venv", "Doc/library/venv.rst"),
                           ("ensurepip", "Doc/library/ensurepip.rst")):
        url = f"https://raw.githubusercontent.com/python/cpython/v3.12.8/{upstream}"
        with urlopen(url, timeout=30) as response:
            raw = response.read()
        (target / "manuals" / f"{name}.txt").write_bytes(raw)
        manifest.append(dict(id=name, path=f"manuals/{name}.txt", title=f"CPython {upstream}",
                             version="3.12.8", trusted=True))
        provenance.append(dict(source_id=name, url=url, retrieved_on="2026-11-23",
                               sha256=hashlib.sha256(raw).hexdigest(), license="Python Software Foundation License"))
    with urlopen("https://raw.githubusercontent.com/python/cpython/v3.12.8/LICENSE", timeout=30) as response:
        (target / "LICENSE.txt").write_bytes(response.read())
    (target / "sources.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (target / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print("Saved three CPython documentation sources and their license/provenance.")


if __name__ == "__main__":
    fetch()
