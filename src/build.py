#!/usr/bin/env python3
"""Сборщик полного сайта «Инком-Аудит» (SEO-версия).

Читает модули страниц из src/pages/*.py (каждый экспортирует словарь PAGE, формат описан
в src/CONTRACT.md) и пишет готовый статический сайт.

Темы: «pechat» (синие чернила, по умолчанию, вывод в ../site/full/) и «sverka» (петроль + оранжевый,
отдельный сайт). Примеры запуска из папки incom-audit/:

    python3 -I src/build.py                              # тема pechat, как раньше
    python3 -I src/build.py --theme sverka --out docs \
        --site-url https://greenorangeptftm.github.io/incom-audit --noindex
"""
import argparse
import datetime
import importlib
import importlib.util
import re
import shutil
import struct
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent            # incom-audit/src
ROOT = SRC.parent                                # incom-audit/
DEFAULT_PHOTOS = (ROOT.parent / "incom-redesign" / "site" / "assets" / "photos")

KINDS = {"home", "hub", "service", "page", "article", "blog", "contacts", "order"}
SECTION_TYPES = {"prose", "facts", "steps", "cards", "table", "checklist", "checker",
                 "calculator", "photo", "quote", "articles", "cta", "why"}


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


def load_photos(photos_dir):
    photos = {}
    for p in sorted(photos_dir.glob("*.jpg")):
        if p.stem.endswith("-900"):
            continue
        small = photos_dir / (p.stem + "-900.jpg")
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
                "checklist": ["items"], "photo": ["photo"], "quote": ["text"], "cta": ["button"], "why": ["items"]}.get(s["type"], [])
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
    return p


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
    return re.sub(r'((?:href|src|action|poster|imagesrcset)=")/(?!/)', lambda m: m.group(1) + root, html)


def expand_photos(html, ctx, templates):
    cls = getattr(templates, "PROSE_PHOTO_CLS", "duo prose-photo")

    def repl(m):
        attrs = m.group(1)
        key = re.search(r'data-photo="([^"]+)"', attrs).group(1)
        alt_m = re.search(r'alt="([^"]*)"', attrs)
        alt = alt_m.group(1) if alt_m else ""
        cap_m = re.search(r'data-caption="([^"]*)"', attrs)
        cap = cap_m.group(1) if cap_m else ""
        return templates.figure(ctx, key, alt, cls=cls, sizes="(max-width: 900px) 100vw, 800px", caption=cap)
    return re.sub(r'<img\b([^>]*\bdata-photo="[^"]+"[^>]*)>', repl, html)


# ---------- правила клиента: без «ё», без лишних точек ----------
INLINE = {"a", "span", "small", "strong", "em", "b", "i", "abbr", "time", "cite", "code", "sup", "sub", "u", "s", "mark", "q",
          "svg", "path", "use", "g", "circle", "rect", "img", "input", "select", "option", "textarea"}
SKIP_TAGS = ("script", "style", "pre", "textarea")
ABBR = {"г", "гг", "руб", "млн", "млрд", "тыс", "ул", "д", "корп", "стр", "ст", "п", "пп", "ч", "т", "кв", "им", "коп", "см", "пр", "др", "тел", "e", "ex", "no", "vs"}
TOKEN_RE = re.compile(r"(<!--.*?-->|<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<pre\b[^>]*>.*?</pre>|<textarea\b[^>]*>.*?</textarea>|<[^>]+>)", re.S)
ATTR_RE = re.compile(r'\b(alt|title|placeholder|aria-label|content)="([^"]*)"')
WORD_RE = re.compile(r"[\wа-яёА-ЯЁ№]+$")
OPENER = "«„(\"'*¹²³"


def _yo(t):
    return t.replace("ё", "е").replace("Ё", "Е")


def _keeps_sentence(nxt):
    """Дальше идёт новое предложение: заглавная буква, цифра или открывающая кавычка."""
    c = nxt.lstrip()[:1]
    return bool(c) and (c.isupper() or c.isdigit() or c in OPENER)


def _strip_trailing_period(text):
    t = text.rstrip()
    if not t.endswith(".") or t.endswith("..") or t.endswith("…"):
        return text
    m = WORD_RE.search(t[:-1])
    if m and m.group(0).lower() in ABBR:
        return text
    return t[:-1] + text[len(t):]


def _tag_name(tok):
    m = re.match(r"</?\s*([a-zA-Z][a-zA-Z0-9]*)", tok)
    return m.group(1).lower() if m else ""


def finalize_text(html):
    """Тема «Сверка»: заменяет «ё» на «е» и убирает точки в конце текстовых блоков.
    Точка остаётся, если за ней (сквозь строчные теги) идёт новое предложение с заглавной буквы, цифры или кавычки,
    а также после сокращений (г., руб., ул., д., ст., т. д.) и внутри чисел/многоточий."""
    toks = TOKEN_RE.split(html)
    n = len(toks)

    def next_text(k):
        # что идёт после токена k: ('text', фрагмент) | ('block', None) | ('end', None)
        for j in range(k + 1, n):
            tk = toks[j]
            if not tk:
                continue
            if tk.startswith("<"):
                if tk.startswith("<!--"):
                    continue
                name = _tag_name(tk)
                if name in INLINE:
                    continue
                return "block", None
            if tk.strip():
                return "text", tk
        return "end", None

    out = []
    for k, tk in enumerate(toks):
        if not tk:
            continue
        if tk.startswith("<"):
            if tk.startswith("<!--"):
                out.append(_yo(tk))
            elif tk.lower().startswith(("<script", "<style", "<pre", "<textarea")):
                out.append(_yo(tk) if 'application/ld+json' in tk[:120] else tk)
            else:
                out.append(ATTR_RE.sub(lambda m: '%s="%s"' % (m.group(1), _strip_trailing_period(_yo(m.group(2)))), tk))
            continue
        t = _yo(tk)
        if "." in t:
            res, i = [], 0
            while i < len(t):
                c = t[i]
                if c != ".":
                    res.append(c); i += 1; continue
                # многоточие — целиком
                if t[i:i + 3] == "...":
                    res.append("..."); i += 3; continue
                after = t[i + 1:]
                prev = "".join(res)
                word = WORD_RE.search(prev)
                keep = False
                if after and not after[0].isspace():
                    keep = True                       # 31.12, т.д, 2.5 — точка внутри слова/числа
                elif word and word.group(0).lower() in ABBR:
                    keep = True
                elif after.strip():
                    keep = _keeps_sentence(after)
                else:
                    kind, nxt = next_text(k)
                    keep = kind == "text" and _keeps_sentence(nxt)
                if keep:
                    res.append(".")
                i += 1
            t = "".join(res)
        out.append(t)
    return "".join(out)


def clean_dir(out):
    if out.exists():
        for child in out.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    out.mkdir(parents=True, exist_ok=True)


def build(theme, out, site_url, photos_dir, noindex):
    sys.path.insert(0, str(SRC))
    templates = importlib.import_module("templates" if theme == "pechat" else "templates_" + theme)
    assets_src = SRC / ("assets" if theme == "pechat" else "assets-" + theme)
    standalone = theme != "pechat"   # отдельный сайт: фото и логотипы лежат внутри out/assets/

    photos = load_photos(photos_dir)
    pages, errors = load_pages()
    today = datetime.date.today().isoformat()
    by_path = {p["path"]: p for p in pages}
    articles = sorted([p for p in pages if p["kind"] == "article"], key=lambda p: p.get("date", ""), reverse=True)

    clean_dir(out)
    (out / "assets").mkdir(parents=True, exist_ok=True)
    for f in assets_src.iterdir():
        if f.is_file() and not f.name.startswith("_"):
            shutil.copy2(f, out / "assets" / f.name)

    defs_path = assets_src / "_defs.svg"
    defs_svg = defs_path.read_text(encoding="utf-8") if defs_path.exists() else ""
    if standalone:
        assets_url = site_url + "/assets/"
        photo_rel = "assets/photos/"
    else:
        assets_url = site_url.rsplit("/", 1)[0] + "/assets/"
        photo_rel = "../assets/photos/"

    warns, used_photos = [], set()
    for page in pages:
        root = rel_root(page["path"])
        ctx = dict(site_url=site_url, assets_url=assets_url, noindex=noindex, root=root, theme=theme,
                   photo_prefix=root + photo_rel, photos=photos, pages=pages, by_path=by_path,
                   articles=articles, today=today, defs=defs_svg)
        for key in (page.get("photo"),) + tuple(s.get("photo") for s in page.get("sections") or [] if isinstance(s, dict)):
            if key and key not in photos:
                warns.append("%s: нет фотографии %r" % (page["_file"], key))
        html = templates.render(page, ctx)
        html = expand_photos(html, ctx, templates)
        html = rewrite_links(html, root)
        if theme == "sverka":
            html = finalize_text(html)
        used_photos.update(re.findall(r'photos/([A-Za-z0-9_-]+?)(?:-900)?\.jpg', html))
        target = out / page["path"] / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        for w in warnings_for(page):
            warns.append("%s: %s" % (page["_file"], w))

    # старые адреса: заглушка с переадресацией на новый путь (ключ redirect_from у страницы)
    for page in pages:
        for old in page.get("redirect_from") or []:
            new_abs = "%s/%s" % (site_url, page["path"])
            rel = rel_root(old) + page["path"]
            stub = ('<!doctype html>\n<html lang="ru"><head><meta charset="utf-8"><title>Страница переехала</title>'
                    '<meta name="robots" content="noindex"><link rel="canonical" href="%s">'
                    '<meta http-equiv="refresh" content="0; url=%s"><script>location.replace("%s")</script></head>'
                    '<body><p>Страница переехала: <a href="%s">%s</a></p></body></html>\n' % (new_abs, rel, rel, rel, new_abs))
            target = out / old / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(stub, encoding="utf-8")

    for path, label in templates.EXPECTED_PAGES:
        if path not in by_path:
            warns.append("ожидаемая страница ещё не написана: /%s (%s) — ссылки на неё уже стоят" % (path, label))

    # 404 (если тема умеет)
    if hasattr(templates, "render_404"):
        ctx = dict(site_url=site_url, assets_url=assets_url, noindex=True, root="", theme=theme,
                   photo_prefix=photo_rel, photos=photos, pages=pages, by_path=by_path, articles=articles, today=today, defs=defs_svg)
        html = rewrite_links(templates.render_404(ctx), "")
        if theme == "sverka":
            html = finalize_text(html)
        used_photos.update(re.findall(r'photos/([A-Za-z0-9_-]+?)(?:-900)?\.jpg', html))
        (out / "404.html").write_text(html, encoding="utf-8")

    # фотографии и логотипы отдельного сайта
    if standalone:
        pdir = out / "assets" / "photos"
        pdir.mkdir(parents=True, exist_ok=True)
        for name in sorted(used_photos):
            for fn in (name + ".jpg", name + "-900.jpg"):
                src = photos_dir / fn
                if src.exists():
                    shutil.copy2(src, pdir / fn)
                elif fn.endswith(".jpg") and not fn.endswith("-900.jpg"):
                    warns.append("нет файла фотографии %s" % fn)
        logo_src = photos_dir.parent / "logo"
        if logo_src.exists():
            ldir = out / "assets" / "logo"
            ldir.mkdir(parents=True, exist_ok=True)
            for f in logo_src.glob("*.svg"):
                shutil.copy2(f, ldir / f.name)

    # sitemap.xml
    items = []
    for page in sorted(pages, key=lambda p: p["path"]):
        last = (page.get("updated") or page.get("date") or today) if page["kind"] == "article" else today
        prio = {"home": "1.0", "service": "0.8", "hub": "0.8", "article": "0.6"}.get(page["kind"], "0.5")
        items.append("  <url><loc>%s/%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>" % (site_url, page["path"], last, prio))
    (out / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % "\n".join(items), encoding="utf-8")

    # robots.txt
    if noindex:
        robots = ("# Макет закрыт от индексации. На боевом сайте заменить «Disallow: /» на «Allow: /»\n"
                  "# и собрать сайт с флагом --index (убирает <meta name=\"robots\" content=\"noindex\">).\n"
                  "User-agent: *\nDisallow: /\n\nSitemap: %s/sitemap.xml\n" % site_url)
    else:
        robots = "User-agent: *\nAllow: /\nDisallow: /assets/\n\nSitemap: %s/sitemap.xml\n" % site_url
    (out / "robots.txt").write_text(robots, encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")

    print("Собрано страниц: %d (тема %s) → %s" % (len(pages), theme, out))
    for p in pages:
        print("  /%s" % p["path"])
    for w in warns:
        print("ПРЕДУПРЕЖДЕНИЕ: " + w)
    for e in errors:
        print("ОШИБКА: " + e)
    return 1 if errors else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Сборка сайта «Инком-Аудит»")
    ap.add_argument("--theme", choices=("pechat", "sverka"), default="pechat")
    ap.add_argument("--out", help="папка вывода (по умолчанию: ../site/full для pechat, docs для sverka)")
    ap.add_argument("--site-url", help="адрес сайта без завершающего «/» (для canonical, sitemap, JSON-LD)")
    ap.add_argument("--photos", help="папка с фотографиями (по умолчанию ../../incom-redesign/site/assets/photos)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--noindex", dest="noindex", action="store_true", help="закрыть от индексации (по умолчанию)")
    g.add_argument("--index", dest="noindex", action="store_false", help="открыть для индексации (боевой сайт)")
    ap.set_defaults(noindex=True)
    a = ap.parse_args(argv)

    if a.theme == "pechat":
        out = Path(a.out) if a.out else ROOT.parent / "incom-redesign" / "site" / "full"
        site_url = a.site_url or "https://greenorangeptftm.github.io/incom-redesign/full"
    else:
        out = Path(a.out) if a.out else ROOT / "docs"
        site_url = a.site_url or "https://greenorangeptftm.github.io/incom-audit"
    photos_dir = Path(a.photos) if a.photos else DEFAULT_PHOTOS
    if not photos_dir.exists():
        print("ОШИБКА: папка с фотографиями не найдена: %s" % photos_dir)
        return 1
    return build(a.theme, out.resolve(), site_url.rstrip("/"), photos_dir.resolve(), a.noindex)


if __name__ == "__main__":
    sys.exit(main())
