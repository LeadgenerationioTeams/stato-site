#!/usr/bin/env python3
"""Validate canonical links and Organization/WebSite JSON-LD on every src HTML page."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
APEX = "https://stato.tech"

CANONICAL_RE = re.compile(
    r'<link\s+[^>]*\brel=["\']canonical["\'][^>]*>',
    re.IGNORECASE,
)
CANONICAL_HREF_RE = re.compile(
    r'<link\s+[^>]*\brel=["\']canonical["\'][^>]*\bhref=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
CANONICAL_HREF_RE_ALT = re.compile(
    r'<link\s+[^>]*\bhref=["\']([^"\']+)["\'][^>]*\brel=["\']canonical["\']',
    re.IGNORECASE,
)
LD_JSON_RE = re.compile(
    r'<script\s+[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)

ORG_ID = f"{APEX}/#organization"
EXPECTED_ORG = {
    "@type": "Organization",
    "@id": ORG_ID,
    "name": "Stato Technologies Limited",
    "url": f"{APEX}/",
}
EXPECTED_WEBSITE = {
    "@type": "WebSite",
    "name": "Stato",
    "url": f"{APEX}/",
    "publisher": {"@id": ORG_ID},
}


def canonical_for_file(path: Path) -> str:
    rel = path.relative_to(SRC).as_posix()
    if rel == "index.html":
        return f"{APEX}/"
    return f"{APEX}/{rel}"


def extract_canonical_hrefs(html: str) -> list[str]:
    hrefs: list[str] = []
    for tag in CANONICAL_RE.findall(html):
        m = CANONICAL_HREF_RE.search(tag) or CANONICAL_HREF_RE_ALT.search(tag)
        if m:
            hrefs.append(m.group(1))
    return hrefs


def find_graph_nodes(data: dict) -> list[dict]:
    if "@graph" in data and isinstance(data["@graph"], list):
        return [n for n in data["@graph"] if isinstance(n, dict)]
    if "@type" in data:
        return [data]
    return []


def node_by_type(nodes: list[dict], schema_type: str) -> dict | None:
    for n in nodes:
        t = n.get("@type")
        if t == schema_type or (isinstance(t, list) and schema_type in t):
            return n
    return None


def validate_json_ld(block: str, errors: list[str]) -> None:
    try:
        data = json.loads(block.strip())
    except json.JSONDecodeError as e:
        errors.append(f"JSON-LD parse error: {e}")
        return

    nodes = find_graph_nodes(data)
    org = node_by_type(nodes, "Organization")
    site = node_by_type(nodes, "WebSite")

    if org is None:
        errors.append("missing Organization @type in JSON-LD")
    else:
        for key, val in EXPECTED_ORG.items():
            if org.get(key) != val:
                errors.append(f"Organization {key}: expected {val!r}, got {org.get(key)!r}")
        addr = org.get("address")
        if not isinstance(addr, dict) or addr.get("@type") != "PostalAddress":
            errors.append("Organization address: expected PostalAddress object")
        else:
            if addr.get("addressCountry") != "GB":
                errors.append(f"addressCountry: expected 'GB', got {addr.get('addressCountry')!r}")
            street = addr.get("streetAddress", "")
            if "Regent House" not in street or "Heaton Lane" not in street:
                errors.append("address streetAddress missing Regent House / Heaton Lane")
            if addr.get("postalCode") != "SK4 1BS":
                errors.append(f"postalCode: expected 'SK4 1BS', got {addr.get('postalCode')!r}")
        ident = org.get("identifier")
        if not isinstance(ident, dict) or ident.get("@type") != "PropertyValue":
            errors.append("identifier: expected PropertyValue")
        elif ident.get("propertyID") != "Companies House" or ident.get("value") != "17541466":
            errors.append("identifier Companies House / 17541466 mismatch")
        for forbidden in ("logo", "sameAs", "telephone", "email"):
            if forbidden in org:
                errors.append(f"Organization must not include {forbidden}")

    if site is None:
        errors.append("missing WebSite @type in JSON-LD")
    else:
        for key, val in EXPECTED_WEBSITE.items():
            if site.get(key) != val:
                errors.append(f"WebSite {key}: expected {val!r}, got {site.get(key)!r}")


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    html = path.read_text(encoding="utf-8")
    expected = canonical_for_file(path)

    canonical_tags = CANONICAL_RE.findall(html)
    if len(canonical_tags) != 1:
        errors.append(f"expected exactly 1 canonical link, found {len(canonical_tags)}")
    else:
        hrefs = extract_canonical_hrefs(html)
        if len(hrefs) != 1:
            errors.append("canonical tag present but href not parsed")
        elif hrefs[0] != expected:
            errors.append(f"canonical href: expected {expected!r}, got {hrefs[0]!r}")

    ld_blocks = LD_JSON_RE.findall(html)
    if len(ld_blocks) != 1:
        errors.append(f"expected exactly 1 JSON-LD block, found {len(ld_blocks)}")
    else:
        validate_json_ld(ld_blocks[0], errors)

    return errors


def main() -> int:
    files = sorted(SRC.rglob("*.html"))
    if len(files) == 0:
        print("No HTML files under src/", file=sys.stderr)
        return 1

    failed = 0
    print(f"Checking {len(files)} HTML file(s) under {SRC.relative_to(ROOT)}/\n")
    for path in files:
        rel = path.relative_to(ROOT)
        errs = check_file(path)
        if errs:
            failed += 1
            print(f"FAIL {rel}")
            for e in errs:
                print(f"  - {e}")
        else:
            print(f"OK   {rel}  canonical={canonical_for_file(path)!r}")

    print()
    if failed:
        print(f"{failed} file(s) failed, {len(files) - failed} passed.")
        return 1
    print(f"All {len(files)} file(s) passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
