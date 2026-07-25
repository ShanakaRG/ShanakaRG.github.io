#!/usr/bin/env python3
"""
Build the website.

    python build.py            build once into docs/
    python build.py --serve    build, then serve at http://localhost:8000
    python build.py --watch    rebuild automatically whenever content changes

You should never need to edit an HTML file. Everything the site displays comes
from the files in content/. This script turns them into finished pages.

    content/*.yaml           the data (education, projects, awards, ...)
    content/publications.bib your papers, in standard BibTeX
    content/about.md         your bio, in plain text
    templates/*.html         page layouts (rarely need touching)
    static/                  css, js, images, PDFs, slides
    docs/                    <- generated. Never edit by hand; it gets wiped.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
import time
from pathlib import Path

try:
    import yaml
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    sys.exit(
        "Missing dependencies. Run:\n\n    pip install -r requirements.txt\n"
    )

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUTPUT = ROOT / "docs"


# --------------------------------------------------------------------------
# Loading content
# --------------------------------------------------------------------------

def load_yaml(name: str):
    """Read content/<name>.yaml. Returns {} or [] if the file is absent."""
    path = CONTENT / f"{name}.yaml"
    if not path.exists():
        print(f"  ! content/{name}.yaml not found — skipping")
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


# --------------------------------------------------------------------------
# A very small Markdown subset, so content files can stay readable
#   blank line          -> new paragraph
#   - item              -> bullet list
#   [text](url)         -> link
#   **bold**  *italic*  -> emphasis
# --------------------------------------------------------------------------

def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def inline(text) -> str:
    """Render one line of the Markdown subset, without a wrapping paragraph."""
    return _inline(str(text)) if text else ""


def md(text) -> str:
    """Render the Markdown subset to HTML."""
    if not text:
        return ""
    blocks = re.split(r"\n\s*\n", str(text).strip())
    out = []
    for block in blocks:
        lines = [ln for ln in block.strip().split("\n") if ln.strip()]
        if lines and all(ln.strip().startswith(("- ", "* ")) for ln in lines):
            items = "".join(
                f"<li>{_inline(ln.strip()[2:].strip())}</li>" for ln in lines
            )
            out.append(f"<ul>{items}</ul>")
        else:
            out.append("<p>" + _inline(" ".join(ln.strip() for ln in lines)) + "</p>")
    return "\n".join(out)


# --------------------------------------------------------------------------
# BibTeX
# --------------------------------------------------------------------------

def _parse_fields(body: str) -> dict:
    fields, i, n = {}, 0, len(body)
    key_re = re.compile(r"\s*([A-Za-z_][\w-]*)\s*=\s*")
    while i < n:
        m = key_re.match(body, i)
        if not m:
            nxt = body.find(",", i)
            if nxt == -1:
                break
            i = nxt + 1
            continue
        name, i = m.group(1).lower(), m.end()
        if i < n and body[i] == "{":
            depth, j = 1, i + 1
            while j < n and depth:
                depth += (body[j] == "{") - (body[j] == "}")
                j += 1
            value, i = body[i + 1:j - 1], j
        elif i < n and body[i] == '"':
            j = i + 1
            while j < n and body[j] != '"':
                j += 1
            value, i = body[i + 1:j], j + 1
        else:
            j = i
            while j < n and body[j] != ",":
                j += 1
            value, i = body[i:j], j
        while i < n and body[i] in " \t\n,":
            i += 1
        value = re.sub(r"\s+", " ", value).replace("{", "").replace("}", "").strip()
        if value:
            fields[name] = value
    return fields


def parse_bib(path: Path) -> list[dict]:
    """Parse a .bib file into a list of dictionaries."""
    if not path.exists():
        print(f"  ! {path.name} not found — no publications will be listed")
        return []
    text = re.sub(r"(?m)^\s*%.*$", "", path.read_text(encoding="utf-8"))
    entries, i = [], 0
    head_re = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,")
    while True:
        m = head_re.search(text, i)
        if not m:
            break
        depth, j = 1, m.end()
        while j < len(text) and depth:
            depth += (text[j] == "{") - (text[j] == "}")
            j += 1
        entry = {"entrytype": m.group(1).lower(), "key": m.group(2)}
        entry.update(_parse_fields(text[m.end():j - 1]))
        entries.append(entry)
        i = j
    return entries


def _format_author(raw: str) -> tuple[str, str]:
    """'Gunasekara, Shanaka Ramesh' -> ('S. R. Gunasekara', 'Gunasekara')"""
    raw = raw.strip()
    if "," in raw:
        surname, given = (p.strip() for p in raw.split(",", 1))
    else:
        parts = raw.split()
        surname, given = parts[-1], " ".join(parts[:-1])
    initials = " ".join(
        f"{p[0].upper()}." for p in re.split(r"[\s.\-]+", given) if p
    )
    return (f"{initials} {surname}".strip(), surname)


def authors_html(raw: str, me: str) -> str:
    names = []
    for author in re.split(r"\s+and\s+", raw or ""):
        if not author.strip():
            continue
        formatted, surname = _format_author(author)
        if me and surname.lower() == me.lower():
            formatted = f'<span class="me">{html.escape(formatted)}</span>'
        else:
            formatted = html.escape(formatted)
        names.append(formatted)
    return ", ".join(names)


def venue_html(e: dict) -> str:
    """Assemble the italic venue line from whichever BibTeX fields exist."""
    bits = []
    main = e.get("journal") or e.get("booktitle") or e.get("howpublished") or ""
    if main:
        bits.append(main)
    if e.get("volume"):
        bits.append(f"vol. {e['volume']}")
    if e.get("number"):
        bits.append(f"no. {e['number']}")
    if e.get("pages"):
        bits.append("pp. " + e["pages"].replace("--", "\u2013"))
    if e.get("address"):
        bits.append(e["address"])
    if e.get("note"):
        bits.append(e["note"])
    if e.get("issn"):
        bits.append(f"ISSN {e['issn']}")
    if e.get("isbn"):
        bits.append(f"ISBN {e['isbn']}")
    return html.escape(", ".join(bits))


LINK_FIELDS = [
    ("doi", "DOI", "https://doi.org/{}"),
    ("url", "Abstract", "{}"),
    ("pdf", "PDF", "static/{}"),
    ("slides", "Slides", "static/{}"),
    ("video", "Video", "{}"),
    ("code", "Code", "{}"),
    ("poster", "Poster", "static/{}"),
]


def publication_links(e: dict) -> list[dict]:
    links = []
    for field, label, pattern in LINK_FIELDS:
        if e.get(field):
            links.append({"label": label, "href": pattern.format(e[field])})
    return links


JOURNAL_TYPES = {"article"}
CONFERENCE_TYPES = {"inproceedings", "conference", "proceedings", "misc",
                    "incollection", "unpublished"}


def build_publications(cfg: dict) -> dict:
    me = cfg.get("author_surname", "")
    entries = parse_bib(CONTENT / "publications.bib")
    prepared = []
    for e in entries:
        prepared.append({
            "title": html.escape(e.get("title", "Untitled")),
            "authors": authors_html(e.get("author", ""), me),
            "venue": venue_html(e),
            "year": e.get("year", ""),
            "tag": e.get("tag") or ("Journal" if e["entrytype"] in JOURNAL_TYPES
                                    else "Conference"),
            "links": publication_links(e),
            "entrytype": e["entrytype"],
            # optional per-paper thumbnail, e.g. image = {img/pubs/foo.png}
            "image": ("static/" + e["image"]) if e.get("image") else "",
        })
    prepared.sort(key=lambda p: (p["year"], p["title"]), reverse=True)
    journals = [p for p in prepared if p["entrytype"] in JOURNAL_TYPES]
    conferences = [p for p in prepared if p["entrytype"] not in JOURNAL_TYPES]

    # grouped by year, newest first — for the visual layout
    by_year = []
    seen = {}
    for p in prepared:
        seen.setdefault(p["year"], []).append(p)
    for year in sorted(seen, reverse=True):
        by_year.append({"year": year, "items": seen[year]})

    return {"journals": journals, "conferences": conferences,
            "by_year": by_year, "total": len(prepared)}


# --------------------------------------------------------------------------
# Projects
# --------------------------------------------------------------------------

def build_projects(raw) -> list[dict]:
    projects = []
    for p in raw or []:
        p = dict(p)
        p["slug"] = p.get("slug") or re.sub(r"[^a-z0-9]+", "-",
                                            p.get("title", "").lower()).strip("-")
        for key in ("objective", "approach", "outcome", "funding"):
            if p.get(key):
                p[key + "_html"] = md(p[key])
        p["images"] = p.get("images") or []
        p["files"] = p.get("files") or []
        p["links"] = p.get("links") or []
        p["collaborators"] = p.get("collaborators") or []
        projects.append(p)
    return projects


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def collect() -> dict:
    site = load_yaml("site")
    about_path = CONTENT / "about.md"
    about = about_path.read_text(encoding="utf-8") if about_path.exists() else ""

    projects = build_projects(load_yaml("projects"))
    publications = build_publications(site)
    awards = load_yaml("awards") or {}

    # Travel entries: each may have a markdown 'body'
    travel = load_yaml("travel") or []
    for t in travel:
        if t.get("body"):
            t["body_html"] = md(t["body"])
        t["images"] = t.get("images") or []

    # Blog posts: each may have a markdown 'excerpt'
    blog = load_yaml("blog") or []
    for post in blog:
        if post.get("excerpt"):
            post["excerpt_html"] = md(post["excerpt"])

    return {
        "site": site,
        "about_html": md(about),
        "education": load_yaml("education") or [],
        "experience": load_yaml("experience") or [],
        "presentations": load_yaml("presentations") or [],
        "service": load_yaml("service") or [],
        "projects": projects,
        "publications": publications,
        "travel": travel,
        "blog": blog,
        "awards": awards.get("awards", []),
        "training": awards.get("training", []),
        "interests": site.get("interests", []),
        "highlights": site.get("highlights", []),
    }


def build() -> None:
    if not TEMPLATES.exists():
        sys.exit("templates/ folder is missing")

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["md"] = md
    env.filters["inline"] = inline

    data = collect()

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    shutil.copytree(STATIC, OUTPUT / "static")
    (OUTPUT / ".nojekyll").touch()

    bib = CONTENT / "publications.bib"
    if bib.exists():
        (OUTPUT / "static" / "files").mkdir(parents=True, exist_ok=True)
        shutil.copy(bib, OUTPUT / "static" / "files" / "publications.bib")

    pages = [
        ("index.html", "index.html"),
        ("background.html", "background.html"),
        ("research.html", "research.html"),
        ("publications.html", "publications.html"),
        ("awards.html", "awards.html"),
        ("travel.html", "travel.html"),
        ("blog.html", "blog.html"),
    ]

    for template_name, out_name in pages:
        template = env.get_template(template_name)
        page_data = dict(data, current_page=out_name)
        (OUTPUT / out_name).write_text(template.render(**page_data),
                                       encoding="utf-8")
        print(f"  built docs/{out_name}")

    print(f"\nDone. {data['publications']['total']} publications, "
          f"{len(data['projects'])} projects, {len(data['awards'])} awards.")
    print("Open docs/index.html, or run:  python build.py --serve")


# --------------------------------------------------------------------------
# Convenience: local preview and auto-rebuild
# --------------------------------------------------------------------------

def serve(port: int = 8000) -> None:
    import http.server
    import socketserver
    import functools

    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(OUTPUT))
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"\nServing http://localhost:{port}  (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


def watch() -> None:
    watched = [CONTENT, TEMPLATES, STATIC]

    def snapshot():
        stamps = {}
        for folder in watched:
            for path in folder.rglob("*"):
                if path.is_file():
                    stamps[path] = path.stat().st_mtime
        return stamps

    print("Watching content/, templates/ and static/ for changes. Ctrl+C to stop.")
    last = snapshot()
    try:
        while True:
            time.sleep(1)
            now = snapshot()
            if now != last:
                print("\nChange detected, rebuilding...")
                try:
                    build()
                except Exception as exc:  # keep watching after a mistake
                    print(f"  Build failed: {exc}")
                last = now
    except KeyboardInterrupt:
        print("\nStopped watching.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the website.")
    parser.add_argument("--serve", action="store_true",
                        help="serve the built site on localhost")
    parser.add_argument("--watch", action="store_true",
                        help="rebuild whenever a content file changes")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    print("Building site...")
    build()

    if args.watch:
        watch()
    elif args.serve:
        serve(args.port)
