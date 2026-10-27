# -*- coding: utf-8 -*-
"""Шаблоны полного сайта «Инком-Аудит» («Печать»). Чистые функции: словарь страницы + контекст → HTML."""
import html as _html
import json
import re

PHONE = "+7 (499) 130-80-18"
PHONE_HREF = "tel:+74991308018"
MAIL = "help@incom-consult.ru"
ORG = "ООО «Инком-Аудит»"

NAV = [("Аудит", "/audit/"), ("МСФО", "/msfo/"), ("Бухучет", "/buhgalterskie-uslugi/"), ("Консалтинг", "/konsalting/"),
       ("Блог", "/blog/"), ("О нас", "/o-kompanii/"), ("Контакты", "/kontakty/")]

# Страницы, на которые ведут меню и подвал. Пишутся другими модулями; сборщик предупредит, если файла ещё нет.
EXPECTED_PAGES = [
    ("audit/", "Аудиторские услуги"),
    ("audit/obyazatelnyj/", "Обязательный аудит"),
    ("audit/stoimost/", "Стоимость аудита"),
    ("audit/otchetnosti/", "Аудит отчётности"),
    ("audit/zastroyshchikov/", "Аудит застройщиков"),
    ("audit/nalogovyj/", "Налоговый аудит"),
    ("audit/iniciativnyj/", "Инициативный аудит"),
    ("audit/due-diligence/", "Дью дилидженс"),
    ("msfo/", "МСФО"),
    ("buhgalterskie-uslugi/", "Бухгалтерские услуги"),
    ("konsalting/", "Консалтинг"),
    ("o-kompanii/", "О нас"),
    ("kontakty/", "Контакты"),
    ("zakazat-audit/", "Заказать аудит"),
    ("blog/", "Блог"),
]

FOOTER_SERVICES = [
    ("Аудиторские услуги", "/audit/"),
    ("Обязательный аудит", "/audit/obyazatelnyj/"),
    ("Стоимость аудита", "/audit/stoimost/"),
    ("Аудит отчётности", "/audit/otchetnosti/"),
    ("Аудит застройщиков", "/audit/zastroyshchikov/"),
    ("Налоговый аудит", "/audit/nalogovyj/"),
    ("Инициативный аудит", "/audit/iniciativnyj/"),
    ("Дью дилидженс", "/audit/due-diligence/"),
    ("Подготовка отчетности по МСФО", "/msfo/"),
    ("Бухгалтерские услуги", "/buhgalterskie-uslugi/"),
    ("Консалтинг", "/konsalting/"),
]
FOOTER_COMPANY = [
    ("О нас", "/o-kompanii/"),
    ("Блог", "/blog/"),
    ("Заказать аудит", "/zakazat-audit/"),
    ("Критерии обязательного аудита", "/#check"),
    ("Контакты", "/kontakty/"),
]

INDUSTRIES = [
    ("Торговля", "ind-trade", "Стеллажи с коробками на складе", ["инвентаризация запасов и сверка с учётом", "вычеты НДС по поставщикам и продажи через маркетплейсы"]),
    ("Строительство", "ind-construction-2", "Строящиеся башни и краны", ["обязательный аудит застройщиков по 214-ФЗ", "эскроу-счета и раздельный учёт затрат по объектам"]),
    ("Производство", "ind-production", "Производственный цех", ["себестоимость и запасы по ФСБУ 5/2019", "основные средства по ФСБУ 6/2020"]),
    ("Лизинг", "ind-leasing", "Экскаватор на строительной площадке", ["учёт аренды и лизинга по ФСБУ 25/2018", "предметы лизинга и графики платежей"]),
    ("IT", "ind-it", "Коридор серверного зала", ["нематериальные активы по ФСБУ 14/2022", "условия льгот для аккредитованных IT-компаний"]),
]

MARK_SVG = ('<svg viewBox="0 0 120 120" aria-hidden="true"><defs><linearGradient id="{id}B" x1="0" x2="1"><stop offset="0" stop-color="#0A4384"/>'
            '<stop offset="1" stop-color="#155A9F"/></linearGradient><linearGradient id="{id}G" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7C96A6"/>'
            '<stop offset="1" stop-color="#B9C9C9"/></linearGradient></defs>{circle}<path fill="url(#{id}B)" d="M37 6.75A58 58 0 0 0 37 113.25Z"/>'
            '<path fill="url(#{id}G)" d="M68 117.45V77A37 37 0 0 0 90.75 10.82A58 58 0 0 1 68 117.45Z"/>{text}</svg>')
LOCKUP_TEXT = ('<g fill="#17295A" font-family="Arial, Helvetica, sans-serif" font-weight="700"><text x="41.5" y="31" font-size="14.5" textLength="58" '
               'lengthAdjust="spacingAndGlyphs">Income</text><text x="41.5" y="54" font-size="14.5" textLength="42" lengthAdjust="spacingAndGlyphs">Audit</text></g>')
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120'%3E%3Ccircle cx='60' cy='60' r='58' fill='%23fff'/%3E"
           "%3Cpath fill='%230C4B8B' d='M37 6.75A58 58 0 0 0 37 113.25Z'/%3E%3Cpath fill='%239AB0BC' d='M68 117.45V77A37 37 0 0 0 90.75 10.82A58 58 0 0 1 68 117.45Z'/%3E%3C/svg%3E")
FONTS = "https://fonts.googleapis.com/css2?family=Martian+Mono:wght@400;500&family=Onest:wght@400;500;600;700&family=Unbounded:wght@500;600;700;800&display=swap"
SEAL_MINI = '<svg class="{cls}" viewBox="0 0 120 120" aria-hidden="true"><use href="#seal-mini" filter="url(#ink-s)"/></svg>'


def esc(s):
    return _html.escape(str(s), quote=True)


def slug(s, i):
    t = re.sub(r"[^a-z0-9а-я]+", "-", str(s).lower().replace("ё", "е")).strip("-")
    return t[:40] or "sec-%d" % i


def mark(idp, circle=False, lockup=False):
    return MARK_SVG.format(id=idp, circle='<circle cx="60" cy="60" r="59" fill="#fff"/>' if circle else "", text=LOCKUP_TEXT if lockup else "")


def figure(ctx, key, alt, cls="duo", sizes="100vw", caption="", lazy=True, extra=""):
    """Фото в дуотоне с srcset. Ключ должен быть в ctx['photos'], иначе возвращает пустую строку."""
    ph = ctx["photos"].get(key)
    if not ph:
        return ""
    p = ctx["photo_prefix"]
    srcset = "%s%s.jpg %dw" % (p, key, ph["w"])
    src = "%s%s.jpg" % (p, key)
    if ph["small"]:
        srcset = "%s%s-900.jpg %dw, " % (p, key, ph["sw"]) + srcset
    load = 'loading="lazy" decoding="async"' if lazy else 'fetchpriority="high" decoding="async"'
    cap = "<figcaption>%s</figcaption>" % esc(caption) if caption else ""
    return ('<figure class="%s"%s><img src="%s" srcset="%s" sizes="%s" width="%d" height="%d" alt="%s" %s>%s</figure>'
            % (cls, extra, src, srcset, sizes, ph["w"], ph["h"], esc(alt), load, cap))


def photo_url(ctx, key):
    return ctx["assets_url"] + "photos/%s.jpg" % key


def btn(label, href, kind="seal", arrow=True):
    arr = ' <span class="arr" aria-hidden="true">→</span>' if arrow and kind == "seal" else ""
    return '<a class="btn btn--%s" href="%s">%s%s</a>' % (kind, esc(href), esc(label), arr)


# ---------- каркас ----------
def header(ctx, page):
    path = "/" + page["path"]
    links, sheet = [], []
    for label, href in NAV:
        cur = path == href or (href != "/" and path.startswith(href))
        aria = ' aria-current="page"' if cur else ""
        links.append('<a href="%s"%s>%s</a>' % (href, aria, label))
        sheet.append('<a href="%s"%s>%s <span aria-hidden="true">→</span></a>' % (href, aria, label))
    cta = "#zayavka"
    return (
        '<header class="lg" data-tone="light" id="lg">\n  <div class="lg__bar">\n'
        '    <a class="lg__brand" href="/" aria-label="Инком-Аудит, на главную">%s<span><b>ИНКОМ-АУДИТ</b><small>Аудиторская компания</small></span></a>\n'
        '    <nav class="lg__links" aria-label="Разделы"><span class="lg__lens" aria-hidden="true"></span>%s</nav>\n'
        '    <a class="lg__phone" href="%s">%s</a>\n'
        '    <a class="lg__cta" href="%s">Рассчитать стоимость</a>\n'
        '    <button class="lg__burger" type="button" aria-expanded="false" aria-controls="lg-sheet" aria-label="Открыть меню"><i></i><i></i><i></i></button>\n'
        '  </div>\n  <nav class="lg__sheet" id="lg-sheet" hidden aria-label="Меню">\n    %s\n'
        '    <a href="/#check">Нужен ли нам аудит? <span aria-hidden="true">→</span></a>\n'
        '    <a class="lg__sheet-tel" href="%s">%s</a>\n    <a class="lg__sheet-cta" href="%s">Рассчитать стоимость</a>\n  </nav>\n</header>\n'
        % (mark("hdr", circle=True), "".join(links), PHONE_HREF, PHONE, cta, "\n    ".join(sheet), PHONE_HREF, PHONE, cta))


def footer(ctx, page):
    svc = "".join('<li><a href="%s">%s</a></li>' % (h, esc(l)) for l, h in FOOTER_SERVICES)
    comp = "".join('<li><a href="%s">%s</a></li>' % (h, esc(l)) for l, h in FOOTER_COMPANY)
    return (
        '<footer class="ftr" data-tone="dark" aria-label="Подвал сайта">\n  <div class="wrap">\n    <div class="ftr__grid">\n'
        '      <div class="ftr__brand">\n        <a class="ftr__logo" href="/" aria-label="Инком-Аудит, на главную"><span class="ftr__badge">%s</span>'
        '<span><b>ИНКОМ-АУДИТ</b><small>Развитие и поддержка вашего бизнеса</small></span></a>\n'
        '        <p class="ftr__legal">%s. Член СРО ААС «Содружество», ОРНЗ 12006082980. Аудиторские, бухгалтерские, юридические и консалтинговые услуги по всей России. Офис в Москве.</p>\n'
        '      </div>\n      <div><p class="ftr__h">Услуги</p><ul>%s</ul></div>\n      <div><p class="ftr__h">Компания</p><ul>%s</ul></div>\n'
        '      <div><p class="ftr__h">Контакты</p><ul><li><a href="%s">%s</a></li><li><a href="mailto:%s">%s</a></li><li>Офис в Москве · работаем по всей России</li></ul></div>\n'
        '    </div>\n    <div class="ftr__bottom"><span>© 2010–2026 %s</span><span>Фотографии: Unsplash (свободная лицензия). Макет сайта.</span></div>\n  </div>\n</footer>\n'
        % (mark("ft", lockup=True), ORG, svc, comp, PHONE_HREF, PHONE, MAIL, MAIL, ORG))


def vswitch(ctx):
    r = ctx["root"]
    return ('<nav class="vswitch" id="vswitch" aria-label="Варианты дизайна"><a href="%s../">Обзор</a><a href="%s../sverka/">Сверка</a>'
            '<a href="%s../pechat/">Печать</a><a href="%s../logo/">Логотип</a><a href="%s" aria-current="page">Сайт</a></nav>\n' % (r, r, r, r, r or "./"))


def jsonld(obj):
    return '<script type="application/ld+json">%s</script>\n' % json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def org_obj(ctx):
    return {"@type": "Organization", "name": ORG, "alternateName": "Инком-Аудит", "url": ctx["site_url"] + "/",
            "logo": ctx["assets_url"] + "logo/incom-mark.svg", "telephone": PHONE, "email": MAIL,
            "address": {"@type": "PostalAddress", "streetAddress": "ул. Твардовского, д. 2, корп. 5", "postalCode": "123458", "addressLocality": "Москва", "addressCountry": "RU"}}


def head_jsonld(ctx, page):
    url = ctx["site_url"] + "/" + page["path"]
    out = []
    if page["kind"] == "home":
        o = org_obj(ctx)
        o.update({"@context": "https://schema.org", "foundingDate": "2010", "areaServed": "RU",
                  "memberOf": {"@type": "Organization", "name": "СРО ААС «Содружество»"},
                  "identifier": {"@type": "PropertyValue", "propertyID": "ОРНЗ", "value": "12006082980"},
                  "contactPoint": {"@type": "ContactPoint", "telephone": PHONE, "email": MAIL, "contactType": "sales", "availableLanguage": "ru"}})
        out.append(jsonld(o))
    crumbs = page.get("breadcrumbs")
    if crumbs:
        items = []
        for i, (name, href) in enumerate(crumbs, 1):
            it = {"@type": "ListItem", "position": i, "name": name}
            it["item"] = (ctx["site_url"] + "/" + href.lstrip("/")) if href else url
            items.append(it)
        out.append(jsonld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}))
    sch = page.get("schema") or {}
    if page["kind"] == "service" and sch.get("service"):
        s = {"@context": "https://schema.org", "@type": "Service", "name": sch["service"], "serviceType": sch.get("type", sch["service"]),
             "description": page["description"], "url": url, "areaServed": "RU", "provider": org_obj(ctx)}
        if sch.get("min_price"):
            s["offers"] = {"@type": "Offer", "priceCurrency": "RUB", "url": url,
                           "priceSpecification": {"@type": "PriceSpecification", "priceCurrency": "RUB", "minPrice": sch["min_price"]}}
        out.append(jsonld(s))
    if page.get("faq"):
        out.append(jsonld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in page["faq"]]}))
    if page["kind"] == "article":
        a = {"@context": "https://schema.org", "@type": "Article", "headline": page["h1"], "description": page["description"],
             "datePublished": page["date"], "dateModified": page.get("updated") or page["date"], "inLanguage": "ru",
             "author": {"@type": "Organization", "name": page.get("author") or ORG}, "publisher": org_obj(ctx),
             "mainEntityOfPage": {"@type": "WebPage", "@id": url}}
        if page.get("photo"):
            a["image"] = photo_url(ctx, page["photo"])
        out.append(jsonld(a))
    return "".join(out)


def base(ctx, page, body):
    url = ctx["site_url"] + "/" + page["path"]
    og_img = photo_url(ctx, page.get("photo") or "moscow-city-aerial")
    robots = '<meta name="robots" content="noindex, nofollow">\n' if ctx["noindex"] else ""
    return (
        '<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n%s'
        '<title>%s</title>\n<meta name="description" content="%s">\n<link rel="canonical" href="%s">\n'
        '<meta property="og:type" content="%s">\n<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n'
        '<meta property="og:url" content="%s">\n<meta property="og:image" content="%s">\n<meta property="og:locale" content="ru_RU">\n<meta property="og:site_name" content="Инком-Аудит">\n'
        '<meta name="theme-color" content="#F3F5FA">\n<link rel="icon" href="%s">\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" href="%s">\n<link rel="stylesheet" href="/assets/full.css">\n%s'
        '</head>\n<body>\n<a class="skip" href="#main">Перейти к содержимому</a>\n%s\n%s<main id="main">\n%s</main>\n%s%s'
        '<script src="/assets/full.js" defer></script>\n</body>\n</html>\n'
        % (robots, esc(page["title"]), esc(page["description"]), url, "article" if page["kind"] == "article" else "website",
           esc(page.get("og_title") or page["h1"]), esc(page["description"]), url, og_img, FAVICON, FONTS, head_jsonld(ctx, page),
           ctx["defs"], header(ctx, page), body, footer(ctx, page), vswitch(ctx)))


# ---------- общие блоки ----------
def crumbs(page):
    c = page.get("breadcrumbs")
    if not c:
        return ""
    li = []
    for name, href in c:
        li.append('<li><a href="%s">%s</a></li>' % (href, esc(name)) if href else '<li aria-current="page">%s</li>' % esc(name))
    return '<ol class="crumbs" aria-label="Вы здесь">%s</ol>' % "".join(li)


def facts(items, cls="req req--n"):
    if not items:
        return ""
    cells = "".join('<div><dt>%s</dt><dd%s>%s</dd></div>' % (esc(k), ' class="is-seal"' if "₽" in str(v) else "", esc(v)) for k, v in items)
    return '<dl class="%s" style="--n:%d">%s</dl>' % (cls, len(items), cells)


def zayavka(ctx, page):
    opts = ["Обязательный аудит", "Стоимость аудита", "Аудит застройщика по 214-ФЗ", "Налоговый аудит или требование ФНС",
            "Инициативный или экспресс-аудит", "Due diligence перед сделкой", "Отчётность по МСФО", "Бухгалтерское сопровождение", "Консалтинг и споры", "Другое"]
    pre = page.get("form_task") or ""
    options = "".join('<option%s>%s</option>' % (' selected' if o == pre else "", o) for o in opts)
    bg = figure(ctx, "moscow-city-sunset", "", cls="contact-band__bg", sizes="100vw")
    return (
        '<section class="band contact-band on-seal" id="zayavka" data-tone="dark" aria-labelledby="zayavka-h">\n%s'
        '  <div class="wrap contact">\n    <div class="contact__info">\n      <h2 class="h2" id="zayavka-h">Расскажите о задаче. Назовём стоимость.</h2>\n'
        '      <p class="lead">Позвоните или оставьте заявку. Всё, что вы расскажете о компании, остаётся между нами.</p>\n'
        '      <p class="contact__phone" id="phoneTxt">%s</p>\n      <div class="contact__row"><a class="btn btn--white" href="%s">Позвонить</a>'
        '<button class="btn btn--line-inv" type="button" data-copy="%s" data-target="phoneTxt">Скопировать номер</button></div>\n'
        '      <p class="contact__mail"><span id="mailTxt">%s</span><button class="copy" type="button" data-copy="%s" data-target="mailTxt">Скопировать</button></p>\n'
        '      <p class="contact__geo">Офис в Москве · работаем по всей России</p>\n    </div>\n'
        '    <form class="lead-form" id="leadForm" novalidate aria-labelledby="lead-h">\n'
        '      <div class="lead-form__head"><span>Заявка</span><span>Перезвоним и уточним задачу</span></div>\n      <h3 id="lead-h">Рассчитаем стоимость</h3>\n'
        '      <div class="fld"><label for="f-name">Как вас зовут</label><input id="f-name" name="name" autocomplete="name" required></div>\n'
        '      <div class="fld"><label for="f-phone">Телефон</label><input id="f-phone" name="phone" type="tel" autocomplete="tel" inputmode="tel" placeholder="+7 ___ ___-__-__" required></div>\n'
        '      <div class="fld"><label for="f-company">Компания или ИНН <span class="opt">необязательно</span></label><input id="f-company" name="company" autocomplete="organization"></div>\n'
        '      <div class="fld"><label for="f-task">Задача</label><select id="f-task" name="task">%s</select></div>\n'
        '      <button class="btn btn--seal" type="submit">Отправить заявку <span class="arr" aria-hidden="true">→</span></button>\n'
        '      <p class="lead-form__legal">Нажимая кнопку, вы соглашаетесь на обработку персональных данных.</p>\n'
        '      <p class="lead-form__msg" id="leadMsg" role="status" hidden></p>\n    </form>\n  </div>\n</section>\n'
        % (('  <div class="contact-band__bg" aria-hidden="true">%s</div>\n' % bg) if bg else "", PHONE, PHONE_HREF, PHONE, MAIL, MAIL, options))


def checker(sec=None):
    sec = sec or {}
    h2 = esc(sec.get("h2") or "Нужен ли вам обязательный аудит?")
    intro = esc(sec.get("intro") or "Заполните бланк. Он сверит ваши данные с критериями статьи 5 закона № 307-ФЗ «Об аудиторской деятельности».")
    return (
        '<div class="check" id="check">\n  <div class="check__intro">\n    <h2 class="h2 check__h" id="check-h">%s</h2>\n    <p class="lead">%s</p>\n'
        '    <ul class="check__crit"><li>Доходы за прошлый год<b>&gt; 800 млн ₽</b></li><li>Активы на 31 декабря прошлого года<b>&gt; 400 млн ₽</b></li>'
        '<li>Акционерное общество<b>скорее всего, да</b></li><li>Застройщик по 214-ФЗ<b>ежегодно</b></li><li>Ценные бумаги на торгах, консолидированная отчётность<b>да</b></li></ul>\n'
        '    <p class="check__note">Достаточно одного критерия. Это предварительная оценка, уточним на консультации.</p>\n  </div>\n'
        '  <form class="blank" id="blank" novalidate aria-labelledby="check-h">\n'
        '    <div class="blank__head"><span>Бланк предварительной проверки</span><span class="blank__ex" id="blankEx">Пример заполнения</span></div>\n'
        '    <div class="blank__grid">\n      <div class="fld"><label for="b-inc">Доходы за 2025 год</label><div class="blank__input"><input id="b-inc" name="inc" inputmode="decimal" autocomplete="off" value="920" aria-describedby="b-help"><span>млн ₽</span></div></div>\n'
        '      <div class="fld"><label for="b-ast">Активы на 31.12.2025</label><div class="blank__input"><input id="b-ast" name="ast" inputmode="decimal" autocomplete="off" value="310" aria-describedby="b-help"><span>млн ₽</span></div></div>\n    </div>\n'
        '    <p class="fld__help" id="b-help">Аудит отчётности за 2026 год: смотрим доходы за 2025 год и активы на 31.12.2025. Можно указать примерно.</p>\n'
        '    <fieldset><legend>Отметьте, если относится к вам</legend>\n'
        '      <label class="cb" for="b-ao"><input type="checkbox" id="b-ao" name="ao"><span class="cb__box" aria-hidden="true"></span><span>Акционерное общество (АО или ПАО)</span></label>\n'
        '      <label class="cb" for="b-dev"><input type="checkbox" id="b-dev" name="dev"><span class="cb__box" aria-hidden="true"></span><span>Застройщик по 214-ФЗ</span></label>\n'
        '      <label class="cb" for="b-sec"><input type="checkbox" id="b-sec" name="sec"><span class="cb__box" aria-hidden="true"></span><span>Ценные бумаги на торгах или консолидированная отчётность группы</span></label>\n    </fieldset>\n'
        '    <div class="blank__act"><button class="btn btn--seal" type="submit">Проверить</button><p class="blank__err" id="blankErr" role="alert"></p></div>\n'
        '    <div class="blank__result" id="blankResult">\n      <div class="blank__mp"><span>М.П.</span><div class="rstamp is-must" id="rstamp" aria-hidden="true"><span class="rstamp__top">Обязательный аудит</span><span class="rstamp__main" id="rstampMain">Обязателен</span><span class="rstamp__sub">предварительно</span></div></div>\n'
        '      <div class="blank__out" aria-live="polite"><ul class="blank__reasons" id="blankReasons"><li class="yes">Доходы 920 млн ₽ больше 800 млн ₽</li><li class="no">Активы 310 млн ₽ не больше 400 млн ₽</li></ul>\n'
        '        <p class="blank__verdict" id="blankVerdict">Аудит обязателен: для этого достаточно одного критерия.</p>\n        <p class="blank__note">Предварительная оценка, уточним на консультации.</p>\n'
        '        <a class="link" href="/audit/obyazatelnyj/">Подробнее об обязательном аудите</a>\n      </div>\n    </div>\n  </form>\n</div>\n' % (h2, intro))


def calculator(sec=None):
    sec = sec or {}
    h2 = esc(sec.get("h2") or "Из чего складывается стоимость аудита")
    intro = esc(sec.get("intro") or "Укажите основные параметры компании. Калькулятор покажет базовую ставку и то, что увеличит объём работы. Точную цену назовём после оценки объёма.")
    return (
        '<div class="calcwrap" id="calc">\n  <div class="calc__intro"><h2 class="h2 check__h" id="calc-h">%s</h2><p class="lead">%s</p></div>\n'
        '  <form class="blank calc" id="calcForm" novalidate aria-labelledby="calc-h">\n'
        '    <div class="blank__head"><span>Оценка объёма работ</span><span>без обязательств</span></div>\n'
        '    <div class="calc__grid">\n'
        '      <div class="fld"><label for="c-rev">Выручка за год</label><div class="blank__input blank__input--s"><input id="c-rev" name="rev" inputmode="decimal" autocomplete="off" value="300"><span>млн ₽</span></div></div>\n'
        '      <div class="fld"><label for="c-ast">Активы на 31 декабря</label><div class="blank__input blank__input--s"><input id="c-ast" name="ast" inputmode="decimal" autocomplete="off" value="150"><span>млн ₽</span></div></div>\n'
        '      <div class="fld"><label for="c-ent">Юридических лиц</label><select id="c-ent" name="ent"><option value="1">одно</option><option value="2">два</option><option value="3">три</option><option value="5">четыре и больше</option></select></div>\n'
        '      <div class="fld"><label for="c-type">Вид аудита</label><select id="c-type" name="type"><option value="must">обязательный аудит</option><option value="init">инициативный аудит</option><option value="express">экспресс-аудит</option>'
        '<option value="dev">аудит застройщика (214-ФЗ)</option><option value="tax">налоговый аудит</option><option value="ifrs">аудит отчётности по МСФО</option><option value="dd">due diligence</option></select></div>\n'
        '      <div class="fld"><label for="c-ind">Отрасль</label><select id="c-ind" name="ind"><option value="trade">торговля</option><option value="build">строительство</option><option value="prod">производство</option><option value="lease">лизинг</option><option value="it">IT</option><option value="other">другая</option></select></div>\n'
        '      <div class="fld"><label for="c-term">Сроки</label><select id="c-term" name="term"><option value="normal">обычные</option><option value="fast">сжатые</option></select></div>\n'
        '    </div>\n'
        '    <div class="blank__act"><button class="btn btn--seal" type="submit">Оценить</button></div>\n'
        '    <div class="calc__out" id="calcOut" aria-live="polite">\n      <p class="calc__lbl">Базовая ставка</p><p class="calc__price" id="calcPrice">от 40&nbsp;000&nbsp;₽</p>\n'
        '      <ul class="calc__factors" id="calcFactors"><li class="na">Нажмите «Оценить», чтобы увидеть, что влияет на цену в вашем случае</li></ul>\n'
        '      <p class="blank__note">Это ориентир. Точную стоимость и сроки зафиксируем в коммерческом предложении после короткого звонка.</p>\n'
        '      <a class="btn btn--line" href="#zayavka">Получить точный расчёт</a>\n    </div>\n  </form>\n</div>\n' % (h2, intro))


def article_cards(ctx, limit=3, exclude=None):
    cards = []
    for a in ctx["articles"]:
        if exclude and a["path"] == exclude:
            continue
        if len(cards) >= limit:
            break
        tags = "".join('<span class="tag">%s</span>' % esc(t) for t in (a.get("tags") or [])[:3])
        cards.append('<a class="post" href="/%s"><p class="post__date">%s · %s</p><h3>%s</h3><p>%s</p><div class="post__tags">%s</div><span class="link">Читать</span></a>'
                     % (a["path"], ru_date(a.get("date", "")), esc(a.get("reading") or "статья"), esc(a["h1"]), esc(a.get("excerpt", "")), tags))
    return cards


def ru_date(iso):
    m = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    try:
        y, mo, d = iso.split("-")
        return "%d %s %s" % (int(d), m[int(mo) - 1], y)
    except Exception:  # noqa: BLE001
        return esc(iso)


# ---------- секции ----------
def sec_open(s, i, cls=""):
    sid = s.get("id") or slug(s.get("h2") or "", i)
    h2 = '<h2 class="h2s">%s</h2>' % esc(s["h2"]) if s.get("h2") else ""
    intro = '<p class="sec__intro">%s</p>' % esc(s["intro"]) if s.get("intro") else ""
    return '<section class="sec%s" id="%s">%s%s' % ((" " + cls) if cls else "", sid, h2, intro), sid


def render_section(ctx, s, i):
    t = s["type"]
    if t == "checker":
        return '<section class="sec sec--wide" id="%s">%s</section>' % (s.get("id") or "check-sec", checker(s)), s.get("id") or "check-sec", s.get("h2") or "Нужен ли аудит?"
    if t == "calculator":
        return '<section class="sec sec--wide" id="%s">%s</section>' % (s.get("id") or "calc-sec", calculator(s)), s.get("id") or "calc-sec", s.get("h2") or "Стоимость"
    if t == "cta":
        body = ('<div class="cta-box"><h2>%s</h2><p>%s</p>%s</div>'
                % (esc(s.get("h2") or "Обсудим вашу задачу"), esc(s.get("text", "")), btn(s["button"][0], s["button"][1], "white")))
        sid = s.get("id") or "cta-%d" % i
        return '<section class="sec" id="%s">%s</section>' % (sid, body), sid, None
    if t == "photo":
        body = figure(ctx, s["photo"], s.get("alt") or s.get("caption") or "", cls="duo sec-photo", sizes="(max-width: 900px) 100vw, 800px", caption=s.get("caption", ""))
        sid = s.get("id") or "photo-%d" % i
        return '<section class="sec" id="%s">%s</section>' % (sid, body), sid, None
    head, sid = sec_open(s, i)
    if t == "prose":
        body = '<div class="prose">%s</div>' % s["html"]
    elif t == "facts":
        body = facts(s["items"], cls="req req--n req--doc")
    elif t == "steps":
        li = "".join('<li><span class="steps__n" aria-hidden="true">%02d</span><h3>%s</h3><p>%s</p></li>' % (n, esc(a), b) for n, (a, b) in enumerate(s["items"], 1))
        body = '<ol class="steps">%s</ol>' % li
    elif t == "cards":
        n = min(3, max(2, len(s["items"]))) if len(s["items"]) != 4 else 2
        cs = "".join('<a class="card" href="%s"><h3>%s</h3><p>%s</p><span class="link">Подробнее</span></a>' % (esc(h), esc(a), esc(b)) for a, b, h in s["items"])
        body = '<div class="cards" style="--n:%d">%s</div>' % (n, cs)
    elif t == "table":
        th = "".join("<th>%s</th>" % esc(x) for x in s["head"])
        rows = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in s["rows"])
        note = '<p class="sec__note">%s</p>' % esc(s["note"]) if s.get("note") else ""
        body = '<div class="tbl"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>%s' % (th, rows, note)
    elif t == "checklist":
        body = '<ul class="ticks">%s</ul>' % "".join("<li>%s</li>" % x for x in s["items"])
    elif t == "quote":
        body = '<blockquote class="law"><p>%s</p>%s</blockquote>' % (s["text"], ('<cite>%s</cite>' % esc(s["source"])) if s.get("source") else "")
    elif t == "articles":
        body = '<div class="posts posts--doc">%s</div>' % "".join(article_cards(ctx, s.get("limit", 3)))
    else:
        body = ""
    return head + body + "</section>", sid, s.get("h2")


def faq_html(page):
    f = page.get("faq")
    if not f:
        return ""
    items = "".join('<details><summary>%s</summary><div><p>%s</p></div></details>' % (esc(q), a) for q, a in f)
    return '<section class="sec" id="faq"><h2 class="h2s">Вопросы и ответы</h2><div class="faq">%s</div></section>' % items


def related_html(page):
    r = page.get("related")
    if not r:
        return ""
    cs = "".join('<a class="card" href="%s"><h3>%s</h3><p>%s</p><span class="link">Перейти</span></a>' % (esc(h), esc(a), esc(b)) for h, a, b in r)
    n = 3 if len(r) >= 3 else 2
    return ('<section class="band band--paper related" aria-labelledby="rel-h"><div class="wrap"><div class="shead"><h2 class="h2" id="rel-h">Смотрите также</h2></div>'
            '<div class="cards" style="--n:%d">%s</div></div></section>\n' % (n, cs))


def toc_html(entries):
    entries = [(sid, h) for sid, h in entries if h]
    if len(entries) < 2:
        return ""
    li = "".join('<li><a href="#%s">%s</a></li>' % (sid, esc(h)) for sid, h in entries)
    return '<aside class="toc" aria-label="На этой странице"><div class="toc__in"><p class="toc__h">На этой странице</p><ol>%s</ol></div></aside>' % li


def doc_sections(ctx, page):
    parts, toc = [], []
    for i, s in enumerate(page.get("sections") or [], 1):
        html, sid, h = render_section(ctx, s, i)
        parts.append(html)
        toc.append((sid, h))
    fq = faq_html(page)
    if fq:
        parts.append(fq)
        toc.append(("faq", "Вопросы и ответы"))
    return "\n".join(parts), toc


# ---------- страницы ----------
def page_hero(ctx, page, tone="light"):
    kick = '<p class="kicker">%s</p>' % esc(page["kicker"]) if page.get("kicker") else ""
    lead = '<p class="lead">%s</p>' % page["lead"] if page.get("lead") else ""
    ctas = []
    if page.get("cta"):
        ctas.append(btn(page["cta"][0], page["cta"][1]))
    if page.get("cta2"):
        ctas.append(btn(page["cta2"][0], page["cta2"][1], "line"))
    cta = '<div class="phero__cta">%s</div>' % "".join(ctas) if ctas else ""
    ph = figure(ctx, page["photo"], page.get("photo_alt") or page["h1"], cls="duo phero__ph", sizes="(max-width: 900px) 100vw, 480px", lazy=False) if page.get("photo") else ""
    fx = ('<div class="wrap phero__facts">%s</div>' % facts(page["facts"])) if page.get("facts") else ""
    return ('<section class="phero%s" data-tone="%s">\n  <div class="wrap phero__in%s">\n    <div class="phero__text">%s%s<h1>%s</h1>%s%s</div>\n    %s\n  </div>\n  %s</section>\n'
            % (" phero--nophoto" if not ph else "", tone, " phero__in--one" if not ph else "", crumbs(page), kick, esc(page["h1"]), lead, cta, ph, fx))


def render_doc(ctx, page):
    body, toc = doc_sections(ctx, page)
    doc = ('<div class="wrap doc-page">%s<article class="doc-body">%s</article></div>\n' % (toc_html(toc), body)) if body else ""
    return page_hero(ctx, page) + doc + related_html(page) + zayavka(ctx, page)


def render_contacts(ctx, page):
    body, toc = doc_sections(ctx, page)
    info = (
        '<section class="band band--paper" aria-label="Контакты компании"><div class="wrap cpage">\n'
        '  <div class="cpage__main"><p class="cpage__lbl">Телефон</p><p class="contact__phone contact__phone--ink" id="phoneTxt">%s</p>'
        '<div class="contact__row"><a class="btn btn--seal" href="%s">Позвонить</a><button class="btn btn--line" type="button" data-copy="%s" data-target="phoneTxt">Скопировать номер</button></div>\n'
        '  <p class="cpage__lbl">Почта</p><p class="contact__mail contact__mail--ink"><span id="mailTxt">%s</span><button class="copy copy--ink" type="button" data-copy="%s" data-target="mailTxt">Скопировать</button></p>\n'
        '  <p class="cpage__lbl">География</p><p class="cpage__txt">Офис в Москве · работаем по всей России: на месте и удалённо</p></div>\n'
        '  <dl class="req req--n req--doc" style="--n:1"><div><dt>Организация</dt><dd>%s</dd></div><div><dt>Членство</dt><dd>СРО ААС «Содружество»</dd></div><div><dt>ОРНЗ</dt><dd>12006082980</dd></div><div><dt>Работаем</dt><dd>с 2010 года</dd></div></dl>\n'
        '</div></section>\n' % (PHONE, PHONE_HREF, PHONE, MAIL, MAIL, ORG))
    doc = ('<div class="wrap doc-page doc-page--notoc"><article class="doc-body">%s</article></div>\n' % body) if body else ""
    return page_hero(ctx, page) + info + doc + related_html(page) + zayavka(ctx, page)


def render_article(ctx, page):
    body, toc = doc_sections(ctx, page)
    dl = ['<time datetime="%s">%s</time>' % (page["date"], ru_date(page["date"]))]
    if page.get("updated") and page["updated"] != page["date"]:
        dl.append("обновлено " + ru_date(page["updated"]))
    if page.get("reading"):
        dl.append(esc(page["reading"]))
    dl.append(esc(page.get("author") or "Аудиторы «Инком-Аудит»"))
    tags = "".join('<span class="tag">%s</span>' % esc(t) for t in (page.get("tags") or []))
    ph = figure(ctx, page["photo"], page.get("photo_alt") or page["h1"], cls="duo art-ph", sizes="(max-width: 900px) 100vw, 800px", lazy=False) if page.get("photo") else ""
    head = ('<section class="art-head" data-tone="light"><div class="wrap"><div class="art-head__in">%s<p class="dateline">%s</p><h1>%s</h1>%s%s</div></div></section>\n'
            % (crumbs(page), " · ".join(dl), esc(page["h1"]), ('<p class="lead">%s</p>' % page["lead"]) if page.get("lead") else "", ph))
    doc = '<div class="wrap doc-page">%s<article class="doc-body">%s%s</article></div>\n' % (
        toc_html(toc), body, ('<div class="art-tags"><span class="toc__h">Теги</span>%s</div>' % tags) if tags else "")
    more = article_cards(ctx, 3, exclude=page["path"])
    rel = related_html(page)
    if more:
        rel += ('<section class="band band--paper" aria-labelledby="more-h"><div class="wrap"><div class="shead"><h2 class="h2" id="more-h">Другие статьи</h2>'
                '<p class="lead"><a class="link" href="/blog/">Все статьи блога</a></p></div><div class="posts">%s</div></div></section>\n' % "".join(more))
    return head + doc + rel + zayavka(ctx, page)


def render_blog(ctx, page):
    cards = article_cards(ctx, 100)
    empty = '<p class="lead">Статьи появятся здесь. Пока посмотрите разделы услуг.</p>' if not cards else ""
    body, _ = doc_sections(ctx, page)
    grid = ('<section class="band" aria-label="Статьи"><div class="wrap"><div class="posts">%s</div>%s</div></section>\n' % ("".join(cards), empty))
    doc = ('<div class="wrap doc-page doc-page--notoc"><article class="doc-body">%s</article></div>\n' % body) if body else ""
    return page_hero(ctx, page) + grid + doc + zayavka(ctx, page)


def render_home(ctx, page):
    h = page.get("hero") or {}
    cred = "".join("<li>%s</li>" % esc(c) for c in h.get("cred") or ["300+ проектов", "СРО ААС «Содружество»", "ОРНЗ 12006082980"])
    hero_photo = figure(ctx, h.get("photo") or "moscow-city-aerial", "Башни Москва-Сити с высоты", cls="duo hero__photo", sizes="(max-width: 960px) 100vw, 46vw", caption="Работаем по всей России", lazy=False)
    hero = (
        '<section class="hero" id="top" data-tone="light" aria-labelledby="hero-h">\n  <div class="stamps" id="stamps" aria-hidden="true"></div>\n'
        '  <div class="wrap hero__inner">\n    <div class="hero__text">\n      <p class="kicker">%s</p>\n      <h1 id="hero-h"%s>%s</h1>\n      <p class="hero__sub">%s</p>\n'
        '      <div class="hero__cta">%s%s</div>\n      <ul class="hero__cred" aria-label="Коротко о компании">%s</ul>\n    </div>\n'
        '    <div class="hero__visual">\n      %s\n'
        '      <figure class="doc" aria-label="Фрагмент аудиторского заключения">\n        <div class="doc__sheet">\n'
        '          <div class="doc__head"><span>Аудиторское заключение независимого аудитора</span><span>стр. 1</span></div>\n'
        '          <p class="doc__addr">Участникам и руководству ООО «<span class="redact"></span><span class="sr-only">название скрыто</span>»</p>\n'
        '          <p class="doc__h">Мнение</p>\n          <p class="doc__blur" aria-hidden="true">Мы провели аудит прилагаемой годовой бухгалтерской отчётности организации, состоящей из бухгалтерского баланса по состоянию на 31 декабря 2025 года.</p>\n'
        '          <p class="doc__p">По нашему мнению, прилагаемая годовая бухгалтерская отчётность отражает достоверно во всех существенных отношениях финансовое положение организации по состоянию на 31 декабря 2025 года.</p>\n'
        '          <div class="doc__sign"><span class="doc__lbl">Руководитель задания</span><span class="doc__rule"><svg class="sig" viewBox="0 0 300 110" aria-hidden="true">'
        '<path pathLength="1" d="M14 74C22 52 34 26 46 22c10-3 10 12 2 28-7 14-18 28-22 32 10-18 28-36 38-34 8 2 0 22 8 22 10 0 16-20 26-20 8 0 2 18 12 18 12 0 18-24 30-26 10-1 6 22 16 22 12 0 20-28 34-34 10-4 14 8 6 20-8 12-24 22-14 24 14 3 32-16 44-18 10-1 6 12 16 12 12 0 20-10 28-14"/>'
        '<path pathLength="1" d="M36 92c54-8 134-12 252-22"/></svg></span></div>\n'
        '          <div class="doc__mp"><b>ООО «Инком-Аудит» · ОРНЗ 12006082980</b><span>М.П.</span></div>\n        </div>\n'
        '        <div class="seal-wrap" aria-hidden="true" title="Поставить печать ещё раз"><span class="seal-shadow"></span><span class="seal-fx"></span>\n'
        '          <svg class="seal" viewBox="0 0 240 240" focusable="false"><defs><path id="ring-main" d="M120,120 m-88,0 a88,88 0 1,1 176,0 a88,88 0 1,1 -176,0"/></defs>'
        '<g filter="url(#ink)"><circle cx="120" cy="120" r="113" fill="none" stroke="currentColor" stroke-width="5"/><circle cx="120" cy="120" r="105" fill="none" stroke="currentColor" stroke-width="1.4"/>'
        '<g class="seal__ring"><text font-family="Unbounded, \'Arial Black\', sans-serif" font-weight="600" font-size="12" fill="currentColor"><textPath href="#ring-main" textLength="546" lengthAdjust="spacing">ООО «ИНКОМ-АУДИТ» • С 2010 • ОРНЗ 12006082980 •</textPath></text></g>'
        '<circle cx="120" cy="120" r="72" fill="none" stroke="currentColor" stroke-width="2.4"/><circle cx="120" cy="120" r="66.5" fill="none" stroke="currentColor" stroke-width=".9"/><use href="#mark-mono" x="73" y="73" width="94" height="94"/></g></svg>\n'
        '        </div>\n        <figcaption class="doc__cap">Фрагмент типового заключения. Данные клиента скрыты.</figcaption>\n      </figure>\n    </div>\n  </div>\n'
        '  <p class="hero__hint" aria-hidden="true">Кликните по свободному месту, чтобы поставить печать</p>\n</section>\n'
        % (esc(h.get("kicker") or "Аудиторская компания · с 2010 года"), ' class="is-long"' if len(page["h1"]) > 55 else "", h.get("h1_html") or esc(page["h1"]), h.get("sub") or page.get("lead", ""),
           btn(*(h.get("cta") or ("Рассчитать стоимость", "#zayavka"))), btn(*(h.get("cta2") or ("Нужен ли нам аудит?", "#check")), "line"), cred, hero_photo))

    req = ('<section class="req-band" data-tone="light" aria-label="Реквизиты компании"><div class="wrap">%s</div></section>\n'
           % facts(page["facts"], cls="req" if len(page["facts"]) == 6 else "req req--n")) if page.get("facts") else ""

    d = page.get("directory") or []
    rows = "".join('<a href="%s"><span class="n">%02d</span><b>%s</b><span class="pr">%s</span><span class="d">%s</span></a>'
                   % (esc(href), i, esc(t), esc(pr), esc(desc)) for i, (t, desc, pr, href) in enumerate(d, 1))
    directory = ('<section class="band" id="services" data-tone="light" aria-labelledby="svc-h"><div class="wrap"><div class="shead"><h2 class="h2" id="svc-h">%s</h2><p class="lead">%s</p></div>'
                 '<div class="dir">%s</div></div></section>\n' % (esc(page.get("directory_h2") or "Услуги"), page.get("directory_lead") or "", rows)) if d else ""

    sits = page.get("situations") or []
    sc = "".join('<a class="sitc" href="%s"><span class="sit__q">%s</span><span class="sit__tag">%s</span><span class="sit__arr" aria-hidden="true"></span></a>' % (esc(href), esc(q), esc(tag)) for q, tag, href in sits)
    situations = ('<section class="band band--paper" id="situations" data-tone="light" aria-labelledby="sit-h"><div class="wrap"><div class="shead"><h2 class="h2" id="sit-h">С чем к нам приходят</h2>'
                  '<p class="lead">Выберите ситуацию, похожую на вашу. Покажем, какая услуга нужна и сколько она стоит.</p></div><div class="sits">%s</div></div></section>\n' % sc) if sits else ""

    check = '<section class="band check-band" id="check-band" data-tone="light" aria-labelledby="check-h"><div class="wrap">%s</div></section>\n' % checker()

    inds = []
    for n, (name, key, alt, pts) in enumerate(page.get("industries") or INDUSTRIES):
        inds.append('<article class="ind" data-reveal style="--d:%.2fs">%s%s<div class="ind__body"><h3 class="ind__t">%s</h3><ul class="ind__pts">%s</ul></div></article>'
                    % (n * 0.08, figure(ctx, key, alt, cls="duo ind__ph", sizes="(max-width: 1100px) 66vw, 230px"), SEAL_MINI.format(cls="ind__stamp"), esc(name), "".join("<li>%s</li>" % esc(p) for p in pts)))
    industries = ('<section class="band" id="industries" data-tone="light" aria-labelledby="ind-h"><div class="wrap"><div class="shead"><h2 class="h2" id="ind-h">Отрасли, которые мы знаем изнутри</h2>'
                  '<p class="lead">Наши клиенты работают в торговле, строительстве, производстве, лизинге и IT. В каждой отрасли свои участки риска, на них смотрим в первую очередь.</p></div>'
                  '<div class="inds">%s</div><p class="swipe-hint" aria-hidden="true">Листайте отрасли</p></div></section>\n' % "".join(inds))

    steps = page.get("process") or []
    st = "".join('<li class="proc__step"><span class="proc__n" aria-hidden="true">%02d</span><h3>%s</h3><p>%s</p></li>' % (i, esc(a), esc(b)) for i, (a, b) in enumerate(steps, 1))
    process = ('<section class="band band--paper" id="process" data-tone="light" aria-labelledby="proc-h"><div class="wrap"><div class="shead"><h2 class="h2" id="proc-h">%s</h2><p class="lead">%s</p></div>'
               '<ol class="proc">%s</ol><p class="proc__more"><a class="link" href="/zakazat-audit/">Как заказать аудит: подробно о каждом шаге</a></p></div></section>\n'
               % (esc(page.get("process_h2") or "Шесть шагов от заявки до заключения"), esc(page.get("process_lead") or "Сроки и стоимость фиксируем в договоре до начала проверки."), st)) if steps else ""

    posts = article_cards(ctx, 3)
    articles = ('<section class="band" id="articles" data-tone="light" aria-labelledby="art-h"><div class="wrap"><div class="shead"><h2 class="h2" id="art-h">Блог для бухгалтера и собственника</h2>'
                '<p class="lead">Разбираем критерии, сроки и документы простым языком. <a class="link" href="/blog/">Все статьи</a></p></div><div class="posts">%s</div></div></section>\n' % "".join(posts)) if posts else ""

    ab = page.get("about") or {}
    about = ""
    if ab:
        paras = "".join("<p>%s</p>" % p for p in ab.get("paragraphs") or [])
        why = "".join('<li data-reveal><p class="why__st">%s</p><p class="why__cap">%s</p></li>' % (a, esc(b)) for a, b in ab.get("why") or [])
        about = ('<section class="band about-band" id="about" data-tone="light" aria-labelledby="about-h"><div class="wrap about">%s<div class="about__main"><h2 class="h2" id="about-h">%s</h2>%s'
                 '<p class="about__motto">%s%s</p><ul class="why__list">%s</ul><p><a class="btn btn--line" href="/o-kompanii/">О компании подробнее</a></p></div></div></section>\n'
                 % (figure(ctx, ab.get("photo") or "moscow-stalin-highrise", "Московская улица и высотка на Котельнической набережной", cls="duo about__ph", sizes="(max-width: 960px) 92vw, 460px", caption="Офис в Москве"),
                    esc(ab.get("h2") or "Работаем с 2010 года"), paras, SEAL_MINI.format(cls=""), esc(ab.get("motto") or "Актуальные решения — наше искусство"), why))

    extra, _ = doc_sections(ctx, page)
    extra = ('<div class="wrap doc-page doc-page--notoc"><article class="doc-body">%s</article></div>\n' % extra) if extra else ""
    return hero + req + directory + situations + check + industries + process + articles + about + extra + zayavka(ctx, page)


def render(page, ctx):
    k = page["kind"]
    if k == "home":
        body = render_home(ctx, page)
    elif k == "article":
        body = render_article(ctx, page)
    elif k == "blog":
        body = render_blog(ctx, page)
    elif k == "contacts":
        body = render_contacts(ctx, page)
    else:
        body = render_doc(ctx, page)
    return base(ctx, page, body)
