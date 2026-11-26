#!/usr/bin/env python3
"""Genera il sito statico delle linee guida nella cartella _site/.

Uso:  python build.py
Fonti: site.json (dati del sito), chapters.json (ordine e titoli), content/*.html (testo dei capitoli).
Non servono librerie esterne.
"""
import json, re, shutil, html, zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
site = json.loads((ROOT / "site.json").read_text(encoding="utf8"))
chapters = json.loads((ROOT / "chapters.json").read_text(encoding="utf8"))
esc = html.escape
export = json.loads((ROOT / "esportazioni.json").read_text(encoding="utf8"))


# ---- Esportazione in Markdown (HTML dei capitoli -> .md) ----
SEP = '<span class="separator" aria-hidden="true">/</span>'
VOID = {"br", "hr", "img", "meta", "link", "input"}


class Node:
    def __init__(self, tag, attrs=None):
        self.tag, self.attrs, self.kids = tag, dict(attrs or []), []


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs)
        self.stack[-1].kids.append(n)
        if tag not in VOID:
            self.stack.append(n)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].kids.append(data)


def inline(node, table=False):
    out = ""
    for k in node.kids:
        if isinstance(k, str):
            out += re.sub(r"\s+", " ", k)
            continue
        t, inner = k.tag, inline(k, table)
        if t in ("strong", "b"):
            out += f"**{inner.strip()}**" if inner.strip() else ""
        elif t in ("em", "i"):
            out += f"*{inner.strip()}*" if inner.strip() else ""
        elif t == "code":
            out += f"`{inner}`"
        elif t == "a":
            out += f"[{inner.strip()}]({k.attrs.get('href', '')})"
        elif t == "span" and "btn" in k.attrs.get("class", ""):
            out += f"[{inner.strip()}]"
        elif t == "br":
            out += " " if table else "  \n"
        elif t in ("ul", "ol", "p"):
            out += " " + inner + " "
        else:
            out += inner
    return out.replace("|", "\\|") if table else out


def list_md(node, depth=0):
    lines, n = [], 0
    for li in [k for k in node.kids if not isinstance(k, str) and k.tag == "li"]:
        n += 1
        mark = f"{n}." if node.tag == "ol" else "-"
        pad = "  " * depth
        text, subs = "", []
        for k in li.kids:
            if not isinstance(k, str) and k.tag in ("ul", "ol"):
                subs.append(k)
            elif not isinstance(k, str) and k.tag == "p":
                text += inline(k).strip() + " "
            else:
                text += re.sub(r"\s+", " ", k) if isinstance(k, str) else inline(Wrap(k))
        lines.append(f"{pad}{mark} {text.strip()}")
        for sub in subs:
            lines.extend(list_md(sub, depth + 1))
    return lines


class Wrap(Node):
    def __init__(self, child):
        super().__init__("x")
        self.kids = [child]


def table_md(node):
    rows = []
    def collect(n):
        for k in n.kids:
            if isinstance(k, str):
                continue
            if k.tag == "tr":
                rows.append([inline(c, True).strip() for c in k.kids if not isinstance(c, str) and c.tag in ("th", "td")])
            else:
                collect(k)
    collect(node)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join("---" for _ in range(width)) + " |"]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def blocks(node):
    out = []
    for k in node.kids:
        if isinstance(k, str):
            if k.strip():
                out.append(re.sub(r"\s+", " ", k).strip())
            continue
        t = k.tag
        if t == "p":
            out.append(inline(k).strip())
        elif t in ("h2", "h3", "h4"):
            out.append("#" * int(t[1]) + " " + inline(k).strip())
        elif t in ("ul", "ol"):
            out.append("\n".join(list_md(k)))
        elif t == "table":
            out.append(table_md(k))
        elif t == "pre":
            txt = "".join(x if isinstance(x, str) else inline(x) for x in k.kids)
            out.append("```\n" + txt.strip("\n") + "\n```")
        elif t == "blockquote":
            inner = "\n\n".join(b for b in blocks(k) if b)
            out.append("\n".join(("> " + l).rstrip() for l in inner.split("\n")))
        else:
            out.extend(blocks(k))
    return [b for b in out if b]


def to_md(fragment):
    tree = Tree()
    tree.feed(fragment)
    return "\n\n".join(blocks(tree.root)) + "\n"


def chapter_md(c, body):
    m = re.match(r"(Capitolo|Appendice) (\w+)", c["kicker"])
    head = f"{m.group(2)}. {c['title']}" if m and m.group(1) == "Capitolo" else (
        f"Appendice {m.group(2)}. {c['title']}" if m else c["title"])
    return f"# {head}\n\n" + to_md(body)


def kb(n):
    return f"{max(1, round(n / 1024))} kB"


def icon(name, cls=""):
    c = f"icon {cls}".strip()
    return f'<svg class="{c}" aria-hidden="true"><use href="assets/bootstrap-italia/svg/sprites.svg#it-{name}"></use></svg>'


def nav_groups(current, tag="ul", cls="link-list", link_cls="list-item"):
    """Elenco dei capitoli raggruppati, con il capitolo corrente segnato da aria-current."""
    out, group = [], None
    for c in chapters:
        if c["group"] != group:
            if group is not None:
                out.append("</ul>")
            group = c["group"]
            out.append(f'<ul class="{cls}"><li><h3>{esc(group)}</h3></li>')
        cur = c["slug"] == current
        attrs = ' aria-current="page"' if cur else ""
        active = " active" if cur else ""
        out.append(f'<li><a class="{link_cls} medium{active}" href="{c["slug"]}.html"{attrs}><span>{esc(c["title"])}</span></a></li>')
    out.append("</ul>")
    return "\n".join(out)


def nav_html(current):
    return nav_groups(current)


def toc_html(body):
    items = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)
    if len(items) < 2:
        return ""
    lis = "".join(f'<li><a class="list-item" href="#{i}"><span>{t}</span></a></li>' for i, t in items)
    return (
        '<nav class="page-toc" aria-labelledby="page-toc-title"><p class="h6 text-uppercase" id="page-toc-title">In questa pagina</p>'
        f'<div class="link-list-wrapper"><ul class="link-list">{lis}</ul></div></nav>'
    )


def edit_links(c):
    repo = site.get("repo", "").rstrip("/")
    if not repo:
        return ""
    b = site.get("branch", "main")
    return (
        '<p class="page-actions">'
        f'<a class="d-inline-flex align-items-center" href="{repo}/edit/{b}/content/{c["file"]}">{icon("pencil", "icon-sm icon-primary me-1")}Modifica questo capitolo su GitHub</a>'
        f'<a class="d-inline-flex align-items-center" href="{repo}/issues/new?template=proposta-di-modifica.yml&amp;title={esc(c["title"])}">{icon("comment", "icon-sm icon-primary me-1")}Proponi una modifica</a>'
        "</p>"
    )


def bootstrapize(body):
    """Aggiunge le classi di Bootstrap Italia al testo dei capitoli (il testo in content/ resta HTML semplice)."""
    body = re.sub(r"<th>", '<th scope="col">', body)
    body = re.sub(r'<table class="(\w+)">', r'<table class="table \1">', body)
    body = body.replace('<div class="tbl">', '<div class="tbl table-responsive">')
    # Pulsanti d'esempio (non cliccabili): "btn primary" nel testo = pulsante primario, "btn" = secondario
    body = body.replace('<span class="btn primary">', '<span class="btn btn-primary btn-sm">')
    body = body.replace('<span class="btn">', '<span class="btn btn-outline-primary btn-sm">')
    return body


def page(title, body, current, crumbs, extra_head=""):
    body = bootstrapize(body)
    ente, nome = esc(site["ente"]), esc(site["titolo"])
    sub = f'Versione {esc(site["versione"])}'
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
<title>{esc(title)} · {esc(site["titolo"])}</title>
<meta name="description" content="{esc(site["descrizione"])}">
<link rel="stylesheet" href="assets/bootstrap-italia/css/bootstrap-italia.min.css">
<link rel="stylesheet" href="assets/style.css">
{extra_head}
</head>
<body>
<div class="skiplinks">
  <a class="visually-hidden-focusable" href="#contenuto">Vai al contenuto principale</a>
  <a class="visually-hidden-focusable" href="#footer">Vai al piede di pagina</a>
</div>
<header class="it-header-wrapper">
  <div class="it-header-slim-wrapper">
    <div class="container"><div class="row"><div class="col-12"><div class="it-header-slim-wrapper-content">
      <span class="navbar-brand">{ente}</span>
    </div></div></div></div>
  </div>
  <div class="it-nav-wrapper">
    <div class="it-header-center-wrapper">
      <div class="container"><div class="row"><div class="col-12"><div class="it-header-center-content-wrapper">
        <div class="it-brand-wrapper">
          <a href="index.html">
            <img class="brand-logo" src="assets/logo-pa-digitale-2026.svg" alt="" width="49" height="48">
            <div class="it-brand-text">
              <div class="it-brand-title">{nome}</div>
              <div class="it-brand-tagline d-none d-md-block">{sub}</div>
            </div>
          </a>
        </div>
        <div class="it-right-zone">
          <div class="it-search-wrapper">
            <span class="d-none d-md-block">Cerca</span>
            <a class="search-link rounded-icon" href="#search-modal" role="button" aria-label="Cerca nelle linee guida" aria-haspopup="dialog" data-bs-toggle="modal" data-bs-target="#search-modal">{icon("search", "")}</a>
          </div>
        </div>
      </div></div></div></div>
    </div>
    <div class="it-header-navbar-wrapper d-lg-none">
      <div class="container"><div class="row"><div class="col-12">
        <nav class="navbar navbar-expand-lg" aria-label="Capitoli">
          <button class="custom-navbar-toggler" type="button" aria-controls="menu-capitoli" aria-expanded="false" aria-label="Mostra o nascondi l’elenco dei capitoli" data-bs-target="#menu-capitoli" data-bs-toggle="navbarcollapsible">{icon("burger", "")}</button>
          <div class="navbar-collapsable" id="menu-capitoli">
            <div class="overlay" style="display:none"></div>
            <div class="close-div"><button class="btn close-menu" type="button"><span class="visually-hidden">Nascondi l’elenco dei capitoli</span>{icon("close-big", "")}</button></div>
            <div class="menu-wrapper">
              <div class="link-list-wrapper menu-link-list">
{nav_groups(current)}
              </div>
            </div>
          </div>
        </nav>
      </div></div></div>
    </div>
  </div>
</header>

<div class="modal fade" id="search-modal" tabindex="-1" aria-labelledby="search-modal-title" aria-hidden="true">
  <div class="modal-dialog modal-dialog-scrollable modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h2 class="modal-title h5" id="search-modal-title">Cerca nelle linee guida</h2>
        <button class="btn-close" type="button" data-bs-dismiss="modal" aria-label="Chiudi la ricerca">{icon("close", "icon-sm")}</button>
      </div>
      <div class="modal-body">
        <form role="search" id="search-form" action="#" onsubmit="return false">
          <div class="form-group">
            <label for="q">Cerca per parola, per esempio Pec, grassetto o CUP</label>
            <input id="q" type="search" class="form-control" autocomplete="off" aria-controls="results" aria-describedby="q-status">
          </div>
        </form>
        <p id="q-status" class="visually-hidden" role="status" aria-live="polite"></p>
        <div id="results" class="results link-list-wrapper" hidden></div>
      </div>
    </div>
  </div>
</div>

<div class="container" id="main-container">
  <div class="row"><div class="col-12">
    <nav class="breadcrumb-container" aria-label="Percorso di navigazione"><ol class="breadcrumb">{crumbs}</ol></nav>
  </div></div>
  <div class="row pb-5">
    <aside class="col-lg-3 d-none d-lg-block" id="sidebar" aria-label="Capitoli">
      <div class="sidebar-wrapper it-line-right-side sidebar-sticky">
        <div class="sidebar-linklist-wrapper">
          <div class="link-list-wrapper">
{nav_groups(current)}
          </div>
        </div>
      </div>
    </aside>
    <main id="contenuto" class="col-12 col-lg-9" tabindex="-1">
{body}
    </main>
  </div>
</div>

<footer class="it-footer" id="footer">
  <div class="it-footer-main">
    <div class="container">
      <section>
        <div class="row clearfix"><div class="col-sm-12"><div class="it-brand-wrapper">
          <a href="index.html">
            <img class="brand-logo" src="assets/logo-pa-digitale-2026.svg" alt="" width="49" height="48">
            <div class="it-brand-text">
              <div class="it-brand-title">{nome}</div>
              <div class="it-brand-tagline d-none d-md-block">{ente} · {sub}</div>
            </div>
          </a>
        </div></div></div>
      </section>
    </div>
  </div>
</footer>

<a href="#" aria-label="Torna su" data-bs-toggle="backtotop" class="back-to-top back-to-top-small">{icon("arrow-up", "icon-light")}</a>

<script>window.__PUBLIC_PATH__ = "assets/bootstrap-italia/fonts";</script>
<script src="assets/bootstrap-italia/js/bootstrap-italia.bundle.min.js"></script>
<script src="assets/site.js"></script>
</body>
</html>
"""


def write_exports(bodies):
    """Scrive i file .md e lo zip in _site/download/ e restituisce la tabella dei download."""
    dl = OUT / "download"
    dl.mkdir()
    by_slug = {c["slug"]: c for c in chapters}
    md = {slug: chapter_md(by_slug[slug], bodies[slug]) for slug in bodies if slug != "intelligenza-artificiale"}
    files = {}
    for f in export["file"]:
        text = ""
        if f.get("intro"):
            text += "# Linee guida di content design di PA digitale 2026\n\n" + f["intro"] + "\n\n"
        text += "\n".join(md[s] for s in f["capitoli"])
        files[f["file"]] = text
    comp = export["completo"]
    files[comp["file"]] = (
        f"# {comp['titolo']} (versione {site['versione']})\n\n"
        + "\n".join(md[c["slug"]] for c in chapters if c["slug"] in md and c["slug"] != "fonti")
    )
    for name, text in files.items():
        (dl / name).write_text(text, encoding="utf8")
    with zipfile.ZipFile(dl / export["zip"], "w", zipfile.ZIP_DEFLATED) as z:
        for name in files:
            z.write(dl / name, name)

    def row(name, desc):
        size = kb((dl / name).stat().st_size)
        return (
            f'<tr><td><code>{esc(name)}</code></td><td>{esc(desc)}</td>'
            f'<td><a class="btn btn-outline-primary btn-sm text-nowrap" href="download/{esc(name)}" download>{icon("download", "icon-sm icon-primary me-1")}Scarica<span class="visually-hidden"> {esc(name)}</span> (MD, {size})</a></td></tr>'
        )

    rows = "".join(row(f["file"], f["descrizione"]) for f in export["file"])
    rows += row(comp["file"], comp["descrizione"])
    zrow = (
        f'<p><a class="btn btn-primary" href="download/{esc(export["zip"])}" download>{icon("download", "icon-sm icon-white me-1")}Scarica tutti i file '
        f'(ZIP, {kb((dl / export["zip"]).stat().st_size)})</a></p>'
    )
    return (
        zrow + '<div class="tbl"><table class="plain"><thead><tr><th>File</th><th>Contenuto</th><th>Download</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></div>"
    )


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)
    (OUT / ".nojekyll").write_text("")

    bodies = {c["slug"]: (ROOT / "content" / c["file"]).read_text(encoding="utf8").strip() for c in chapters}
    download_html = write_exports(bodies)

    index = []
    for n, c in enumerate(chapters):
        body = bodies[c["slug"]].replace("{{DOWNLOAD}}", download_html)
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()
        index.append({"slug": c["slug"], "title": c["title"], "num": c["num"], "text": text})
        prev = chapters[n - 1] if n else None
        nxt = chapters[n + 1] if n + 1 < len(chapters) else None
        pn = ""
        if prev:
            pn += f'<a class="pn prev" href="{prev["slug"]}.html">{icon("arrow-left", "icon-sm icon-primary")}<span class="pn-text"><span class="pn-label">Precedente</span>{esc(prev["title"])}</span></a>'
        if nxt:
            pn += f'<a class="pn next" href="{nxt["slug"]}.html"><span class="pn-text"><span class="pn-label">Successivo</span>{esc(nxt["title"])}</span>{icon("arrow-right", "icon-sm icon-primary")}</a>'
        article = (
            f'<article class="page">\n<header class="phead"><p class="kicker">{esc(c["kicker"])}</p><h1>{esc(c["title"])}</h1></header>\n'
            f'{toc_html(body)}\n<div class="prose">\n{body}\n</div>\n{edit_links(c)}\n<nav class="pnav" aria-label="Capitoli precedente e successivo">{pn}</nav>\n</article>'
        )
        crumbs = (
            f'<li class="breadcrumb-item"><a href="index.html">Home</a>{SEP}</li>'
            f'<li class="breadcrumb-item">{esc(c["group"])}{SEP}</li>'
            f'<li class="breadcrumb-item active" aria-current="page">{esc(c["title"])}</li>'
        )
        (OUT / f'{c["slug"]}.html').write_text(page(c["title"], article, c["slug"], crumbs), encoding="utf8")

    cards, group, buf = [], None, []
    def flush():
        if group is not None:
            cards.append(f'<div class="col-md-6 col-xl-4"><div class="card-wrapper card-space"><section class="card card-bg no-after"><div class="card-body"><h2 class="card-title h5">{esc(group)}</h2><div class="link-list-wrapper"><ul class="link-list">{"".join(buf)}</ul></div></div></section></div></div>')
    for c in chapters:
        if c["group"] != group:
            flush(); group, buf = c["group"], []
        buf.append(f'<li><a class="list-item" href="{c["slug"]}.html"><span>{esc(c["title"])}</span></a></li>')
    flush()
    home = (
        f'<article class="page home"><header class="phead"><p class="kicker">{esc(site["ente"])}</p>'
        f'<h1>{esc(site["titolo"])}</h1></header>\n'
        f'<p class="lead">{esc(site["descrizione"])}</p>\n<div class="row cards">{"".join(cards)}</div></article>'
    )
    (OUT / "index.html").write_text(
        page("Home", home, "", '<li class="breadcrumb-item active" aria-current="page">Home</li>'), encoding="utf8"
    )
    (OUT / "assets" / "search-index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf8")
    print(f"Sito generato in {OUT} ({len(chapters)} capitoli)")


if __name__ == "__main__":
    build()
