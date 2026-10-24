#!/usr/bin/env python3
"""Сборщик полного сайта «Инком-Аудит» (дизайн «Печать», SEO-версия).

Читает модули страниц из full-src/pages/*.py (каждый экспортирует словарь PAGE,
формат описан в full-src/CONTRACT.md) и пишет готовый статический сайт в site/full/.

Запуск из корня репозитория:  python3 -I full-src/build.py
"""
import datetime
import importlib.util
import re
import shutil
import struct
import sys
from pathlib import Path

SITE_URL = "https://greenorangeptftm.github.io/incom-redesign/full"
NOINDEX = True  # макет закрыт от индексации; на боевом сайте поставить False и открыть robots.txt

ROOT = Path(__file__).resolve().parent.parent  # incom-redesign/
SRC = ROOT / "full-src"
OUT = ROOT / "site" / "full"
PHOTOS_DIR = ROOT / "site" / "assets" / "photos"
ASSETS_URL = SITE_URL.rsplit("/", 1)[0] + "/assets/"

sys.path.insert(0, str(SRC))
import templates  # noqa: E402

KINDS = {"home", "hub", "service", "page", "article", "blog", "contacts", "order"}
SECTION_TYPES = {"prose", "facts", "steps", "cards", "table", "checklist", "checker",
                 "calculator", "photo", "quote", "articles", "cta"}


# ---------- фотографии ----------
def jpeg_size(path):
    data = path.read_bytes()
    i = 2
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + length
    raise ValueError("не удалось прочитать размер %s" % path)


def load_photos():
    photos = {}
    for p in sorted(PHOTOS_DIR.glob("*.jpg")):
        if p.stem.endswith("-900"):
            continue
        small = PHOTOS_DIR / (p.stem + "-900.jpg")
        w, h = jpeg_size(p)
        sw, sh = jpeg_size(small) if small.exists() else (w, h)
        photos[p.stem] = dict(w=w, h=h, sw=sw, sh=sh, small=small.exists())
    return photos


# ---------- страницы ----------
def load_pages():
    pages, errors = [], []
    for f in sorted((SRC / "pages").glob("*.py")):
        if f.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location("page_" + f.stem, f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            page = getattr(mod, "PAGE", None)
        except Exception as e:  # noqa: BLE001
            errors.append("%s: не загружается (%s: %s)" % (f.name, type(e).__name__, e))
            continue
        if not isinstance(page, dict):
            errors.append("%s: нет словаря PAGE" % f.name)
            continue
        page = dict(page)
        page["_file"] = f.name
        problems = validate(page)
        if problems:
            errors.extend("%s: %s" % (f.name, p) for p in problems)
            continue
        pages.append(page)
    return pages, errors


def validate(page):
    p = []
    kind = page.get("kind")
    if kind not in KINDS:
        p.append("неизвестный kind %r (допустимо: %s)" % (kind, ", ".join(sorted(KINDS))))
    for key in ("path", "title", "description", "h1"):
        if not isinstance(page.get(key), str):
            p.append("нет строки %r" % key)
    path = page.get("path", "")
    if isinstance(path, str) and path and not path.endswith("/"):
        p.append("path должен заканчиваться на «/»: %r" % path)
    if isinstance(path, str) and path.startswith("/"):
        p.append("path пишется без ведущего «/»: %r" % path)
    for i, s in enumerate(page.get("sections") or []):
        if not isinstance(s, dict) or "type" not in s:
            p.append("секция %d: нужен словарь с ключом type" % (i + 1))
            continue
        if s["type"] not in SECTION_TYPES:
            p.append("секция %d: неизвестный type %r (допустимо: %s)" % (i + 1, s["type"], ", ".join(sorted(SECTION_TYPES))))
        need = {"prose": ["html"], "facts": ["items"], "steps": ["items"], "cards": ["items"], "table": ["head", "rows"],
                "checklist": ["items"], "photo": ["photo"], "quote": ["text"], "cta": ["text", "button"]}.get(s["type"], [])
        for k in need:
            if k not in s:
                p.append("секция %d (%s): нет поля %r" % (i + 1, s["type"], k))
    for key in ("faq", "related", "facts"):
        v = page.get(key)
        if v is not None and not isinstance(v, (list, tuple)):
            p.append("%r должен быть списком" % key)
    if kind == "article":
        for key in ("date", "excerpt"):
            if not isinstance(page.get(key), str):
                p.append("для статьи нужна строка %r" % key)
    if kind == "service" and not (isinstance(page.get("schema"), dict) and page["schema"].get("service")):
        p.append("предупреждение: для kind=service желателен schema=dict(service=…)")
    return [x for x in p if not x.startswith("предупреждение")] + []


def warnings_for(page):
    w = []
    if len(page.get("title", "")) > 70:
        w.append("title длиннее 70 знаков (%d)" % len(page["title"]))
    d = len(page.get("description", ""))
    if d and not 90 <= d <= 170:
        w.append("description вне 90–170 знаков (%d)" % d)
    if page.get("kind") == "service" and not (isinstance(page.get("schema"), dict) and page["schema"].get("service")):
        w.append("нет schema.service — Service JSON-LD не будет")
    return w


# ---------- вывод ----------
def rel_root(path):
    depth = len([s for s in path.split("/") if s])
    return "../" * depth


def rewrite_links(html, root):
    # href="/audit/" → href="../audit/" по глубине страницы; протокольные "//" не трогаем
    return re.sub(r'((?:href|src|action|poster)=")/(?!/)', lambda m: m.group(1) + root, html)


def expand_photos(html, ctx):
    def repl(m):
        attrs = m.group(1)
        key = re.search(r'data-photo="([^"]+)"', attrs).group(1)
        alt_m = re.search(r'alt="([^"]*)"', attrs)
        alt = alt_m.group(1) if alt_m else ""
        cap_m = re.search(r'data-caption="([^"]*)"', attrs)
        cap = cap_m.group(1) if cap_m else ""
        return templates.figure(ctx, key, alt, cls="duo prose-photo", sizes="(max-width: 900px) 100vw, 800px", caption=cap)
    return re.sub(r'<img\b([^>]*\bdata-photo="[^"]+"[^>]*)>', repl, html)


def build():
    photos = load_photos()
    pages, errors = load_pages()
    today = datetime.date.today().isoformat()
    by_path = {p["path"]: p for p in pages}
    articles = sorted([p for p in pages if p["kind"] == "article"], key=lambda p: p.get("date", ""), reverse=True)

    if OUT.exists():
        for child in OUT.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    for f in (SRC / "assets").iterdir():
        if f.is_file() and not f.name.startswith("_"):
            shutil.copy2(f, OUT / "assets" / f.name)

    defs_svg = (SRC / "assets" / "_defs.svg").read_text(encoding="utf-8")
    warns = []
    for page in pages:
        root = rel_root(page["path"])
        ctx = dict(site_url=SITE_URL, assets_url=ASSETS_URL, noindex=NOINDEX, root=root,
                   photo_prefix=root + "../assets/photos/", photos=photos, pages=pages, by_path=by_path,
                   articles=articles, today=today, defs=defs_svg)
        for key in (page.get("photo"),) + tuple(s.get("photo") for s in page.get("sections") or [] if isinstance(s, dict)):
            if key and key not in photos:
                warns.append("%s: нет фотографии %r" % (page["_file"], key))
        html = templates.render(page, ctx)
        html = expand_photos(html, ctx)
        html = rewrite_links(html, root)
        out = OUT / page["path"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        for w in warnings_for(page):
            warns.append("%s: %s" % (page["_file"], w))

    for path, label in templates.EXPECTED_PAGES:
        if path not in by_path:
            warns.append("ожидаемая страница ещё не написана: /%s (%s) — ссылки на неё уже стоят" % (path, label))

    # sitemap.xml
    items = []
    for page in sorted(pages, key=lambda p: p["path"]):
        if page["kind"] == "article":
            last = page.get("updated") or page.get("date") or today
        else:
            last = today
        prio = {"home": "1.0", "service": "0.8", "hub": "0.8", "article": "0.6"}.get(page["kind"], "0.5")
        items.append("  <url><loc>%s/%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>" % (SITE_URL, page["path"], last, prio))
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % "\n".join(items), encoding="utf-8")

    # robots.txt
    (OUT / "robots.txt").write_text(
        "# Макет закрыт от индексации. На боевом сайте заменить «Disallow: /» на «Allow: /» (и убрать NOINDEX в build.py).\n"
        "User-agent: *\nDisallow: /\n\nSitemap: %s/sitemap.xml\n" % SITE_URL, encoding="utf-8")

    print("Собрано страниц: %d → %s" % (len(pages), OUT))
    for p in pages:
        print("  /%s" % p["path"])
    for w in warns:
        print("ПРЕДУПРЕЖДЕНИЕ: " + w)
    for e in errors:
        print("ОШИБКА: " + e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(build())
