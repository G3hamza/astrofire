"""Bronze manifest: SHA-256, size, source URL, license and download time for every raw file.

Re-running detects changes: if a file's hash differs from the previous manifest, it is reported
(Bronze is immutable; a change means a new download that must be reviewed).
"""
import csv, os
from datetime import datetime, timezone
from pipelines.common import BRONZE, MANIFESTS, PSI, NTRS, rel, sha256, write_csv, psi_url, RUN_TS


def build():
    prev = {}
    mf = MANIFESTS / "bronze_manifest.csv"
    if mf.exists():
        prev = {r["path"]: r["sha256"] for r in csv.DictReader(open(mf, encoding="utf-8"))}
    ntrs = {}
    cat = NTRS / "catalog.csv"
    if cat.exists():
        for r in csv.DictReader(open(cat, encoding="utf-8")):
            ntrs[(r.get("txt") or "").replace("\\", "/")] = r
            ntrs[(r.get("pdf") or "").replace("\\", "/")] = r
    rows, changed = [], []
    from pipelines.common import ROOT
    for p in sorted(list(BRONZE.rglob("*")) + list((ROOT / "data" / "curated").glob("*.csv"))):
        if not p.is_file(): continue
        r = rel(p)
        sub = p.relative_to(BRONZE).parts if BRONZE in p.parents else ("curated", p.name)
        source, acc, url, lic = sub[0], "", "", ""
        if source == "psi" and len(sub) > 2:
            acc = sub[1].split("_")[0]; url = psi_url(acc); lic = "CC0 1.0 (NASA PSI)"
        elif source == "ntrs":
            m = ntrs.get("/".join(sub[1:]))
            if m: acc = f"NTRS-{m['id']}"; url = m["url"]
            lic = "NASA NTRS (US Gov work unless noted; check each paper)"
        elif source == "standards":
            lic = "NASA technical standard (public)"
        elif source == "curated":
            url = "https://ntrs.nasa.gov/citations/20130010991"; lic = "transcribed from NASA NTRS paper"
        elif source == "taskbook":
            url = "https://taskbook.nasaprs.com"; lic = "NASA Task Book (public)"
        h = sha256(p)
        if r in prev and prev[r] != h: changed.append(r)
        rows.append(dict(path=r, layer="bronze", source_system=source, source_id=acc, source_url=url,
                         original_filename=p.name, bytes=p.stat().st_size, sha256=h, license=lic,
                         downloaded_at=datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                         manifest_built_at=RUN_TS))
    write_csv(mf, rows)
    return rows, changed


if __name__ == "__main__":
    rows, changed = build()
    print(f"bronze_manifest.csv: {len(rows)} files; changed since last run: {len(changed)}")
