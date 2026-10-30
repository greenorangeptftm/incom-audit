# -*- coding: utf-8 -*-
"""Шаблоны темы «Сверка» (петроль + оранжевый, живые фотографии, пометки аудитора).

Чистые функции: словарь страницы (CONTRACT.md) + контекст сборщика → HTML.
Общие данные (меню, подвал, JSON-LD, реквизиты) берём из templates.py, чтобы темы не расходились.
"""
import re

import templates as T
from templates import (esc, slug, ru_date, head_jsonld, PHONE, PHONE_HREF, MAIL, ORG, NAV, EXPECTED_PAGES,  # noqa: F401
                       FOOTER_SERVICES, FOOTER_COMPANY, FOOTER_INFO, INDUSTRIES, mark)

PROSE_PHOTO_CLS = "ph prose-photo"
# Шрифты лежат на сайте (assets/fonts): без обращения к Google Fonts, основной текст подгружается первым
FONT_HEAD = ('<link rel="preload" as="font" type="font/woff2" href="/assets/fonts/onest-cyrillic.woff2" crossorigin>\n'
             '<link rel="preload" as="font" type="font/woff2" href="/assets/fonts/onest-latin.woff2" crossorigin>\n'
             '<link rel="stylesheet" href="/assets/fonts/fonts.css">\n')

# Иконки кнопок: штрих в стиле пометок аудитора
ICO = {
    "phone": '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M5.5 3.5h3.2l1.6 4.2-2 1.4a11.5 11.5 0 0 0 6.6 6.6l1.4-2 4.2 1.6v3.2a1.6 1.6 0 0 1-1.7 1.5A15.6 15.6 0 0 1 4 5.2a1.6 1.6 0 0 1 1.5-1.7z"/></svg>',
    "mail": '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 6.5h17v11h-17zM3.5 7l8.5 6 8.5-6"/></svg>',
    "pin": '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.4"/></svg>',
    "copy": '<svg class="ico ico-copy" viewBox="0 0 24 24" aria-hidden="true"><rect x="8.5" y="8.5" width="11" height="11" rx="2"/><path d="M15.5 8.5v-2a2 2 0 0 0-2-2h-7a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h2"/></svg>',
    "check": '<svg class="ico ico-check" viewBox="0 0 24 24" aria-hidden="true"><path pathLength="1" d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
    "x": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>',
}


def copy_btn(value, target, label="Скопировать", kind="ink"):
    """Кнопка копирования: обе подписи лежат в одной ячейке, поэтому ширина не прыгает, иконка превращается в галочку."""
    return ('<button class="btn btn-%s btn-copy" type="button" data-copy="%s" data-target="%s"><span class="ico-sw">%s%s</span>'
            '<span class="sw"><span>%s</span><span aria-hidden="true">Скопировано</span></span></button>'
            % (kind, esc(value), target, ICO["copy"], ICO["check"], esc(label)))


def ibtn(label, href, icon, kind="pen"):
    return '<a class="btn btn-%s btn-ico" href="%s">%s<span>%s</span></a>' % (kind, esc(href), ICO[icon], esc(label))

# Пометки аудитора: галочка «сверено», сигма «пересчитано», перпендикуляр «сверено с выпиской», круг «требует внимания»
TICK = "M4.2 13.2c1.7 1.3 3.4 3.2 4.9 5.6 2.6-6 6.2-10.6 10.9-14.3"
SIGMA = "M17.6 5.1c-3.6-.3-7.4-.1-11 .3l6.2 6.8-6.4 7.2c4-.4 8.2-.4 12.2-.2"
PERP = "M12.2 4.2c-.3 4.8-.2 9.6 0 14.3M4.8 19c4.7-.5 9.6-.5 14.6-.1"
RING = "M13 4c4.6.1 7.6 3.6 7.2 8.2-.4 4.6-4 7.8-8.6 7.6-4.5-.2-7.6-3.6-7.4-8 .2-4.4 3.7-7.6 8.4-7.5 1 .1 1.8.3 2.4.6"

PHOTO_POS = {"ind-construction-2": "50% 40%", "ind-production": "50% 50%", "ind-leasing": "52% 50%", "moscow-stalin-highrise": "50% 40%",
             "signing-hands": "40% 50%", "moscow-city-sunset": "60% 42%"}


def mk(d=TICK, cls="mk", label=None, extra=""):
    role = ' role="img" aria-label="%s"' % esc(label) if label else ' aria-hidden="true"'
    return '<svg class="%s" viewBox="0 0 24 24"%s%s><path pathLength="1" d="%s"/></svg>' % (cls, role, extra, d)


def figure(ctx, key, alt, cls="ph", sizes="100vw", caption="", lazy=True, extra="", tick=False, pos=None):
    """Фото в натуральном цвете с srcset. Неизвестный ключ → пустая строка (сборщик предупредит)."""
    ph = ctx["photos"].get(key)
    if not ph:
        return ""
    p = ctx["photo_prefix"]
    src = "%s%s.jpg" % (p, key)
    srcset = "%s %dw" % (src, ph["w"])
    if ph["small"]:
        srcset = "%s%s-900.jpg %dw, " % (p, key, ph["sw"]) + srcset
    load = 'loading="lazy" decoding="async"' if lazy else 'fetchpriority="high" decoding="async"'
    pos = pos or PHOTO_POS.get(key)
    style = ' style="object-position:%s"' % pos if pos else ""
    cap = "<figcaption>%s</figcaption>" % esc(caption) if caption else ""
    tk = ('<svg class="mk ph-tick" viewBox="0 0 24 24" aria-hidden="true"><path pathLength="1" d="%s"/></svg>' % TICK) if tick else ""
    return ('<figure class="%s"%s><img src="%s" srcset="%s" sizes="%s" width="%d" height="%d" alt="%s" %s%s>%s%s</figure>'
            % (cls, extra, src, srcset, sizes, ph["w"], ph["h"], esc(alt), load, style, tk, cap))


def preload(ctx, key, sizes):
    ph = ctx["photos"].get(key)
    if not ph:
        return ""
    p = ctx["photo_prefix"]
    srcset = "%s%s.jpg %dw" % (p, key, ph["w"])
    if ph["small"]:
        srcset = "%s%s-900.jpg %dw, " % (p, key, ph["sw"]) + srcset
    return '<link rel="preload" as="image" href="%s%s.jpg" imagesrcset="%s" imagesizes="%s" fetchpriority="high">\n' % (p, key, srcset, sizes)


def btn(label, href, kind="pen", arrow=True):
    arr = ' <span class="arr" aria-hidden="true">→</span>' if arrow and kind == "pen" else ""
    return '<a class="btn btn-%s" href="%s">%s%s</a>' % (kind, esc(href), esc(label), arr)


# ---------- логотип «Сверено · Тает»: кольцо, которое пробивает галочка навылет ----------
# Цвета через currentColor: в светлой шапке знак петрольный, в темной шапке и подвале белый. Конец кольца у места
# выхода галочки полупрозрачный (stop-opacity), поэтому на светлом фоне он серо-голубой, на темном растворяется.
# Анимация «Одним росчерком» в sverka.css (.sv__r/.sv__t): кольцо рисуется от разрыва, затем галочка, потом штрих
# снимается в том же порядке, непрерывно. ids градиента и маски уникальны на экземпляр: k = h (шапка) | f (подвал).
def sv_mark(k):
    return ('<svg class="sv" viewBox="-12 -12 224 224" aria-hidden="true"><defs>'
            '<linearGradient id="svg-%s" gradientUnits="userSpaceOnUse" x1="30" y1="170" x2="170" y2="30"><stop offset="0" stop-color="currentColor"/><stop offset="1" stop-color="currentColor" stop-opacity=".2"/></linearGradient>'
            '<mask id="svm-%s"><rect x="-12" y="-12" width="224" height="224" fill="#fff"/><path d="M152.9 81.0L191.2 48.9" fill="none" stroke="#000" stroke-width="32" stroke-linecap="round"/></mask></defs>'
            '<g mask="url(#svm-%s)"><circle class="sv__r" cx="100" cy="100" r="80" fill="none" stroke="url(#svg-%s)" stroke-width="13" transform="rotate(-25.9 100 100)"/></g>'
            '<path class="sv__t" d="M36.6 87.0L80.0 142.0L202.7 39.3" fill="none" stroke="currentColor" stroke-width="14" stroke-linejoin="round" stroke-linecap="round"/></svg>' % (k, k, k, k))


# Фавиконки лежат файлами в assets-sverka/_root/ (favicon.svg/.ico, favicon-120.png, apple-touch-icon.png): темный знак
# на белой плашке, как у старого сайта, чтобы читались в поиске Яндекса. Сборка копирует _root/ в корень сайта.


# ---------- каркас ----------
def header(page, tone):
    path = "/" + page["path"]
    links, sheet = [], []
    for label, href in NAV:
        cur = path == href or (href != "/" and path.startswith(href))
        aria = ' aria-current="page"' if cur else ""
        links.append('<a href="%s"%s>%s</a>' % (href, aria, label))
        sheet.append('<a href="%s"%s>%s <span aria-hidden="true">→</span></a>' % (href, aria, label))
    return (
        '<header class="lg" data-tone="%s" id="lg">\n  <div class="lg__bar">\n'
        '    <a class="lg__brand" href="/" aria-label="Инком-Аудит, на главную">%s<span><b>ИНКОМ-АУДИТ</b><small>Аудиторская компания</small></span></a>\n'
        '    <nav class="lg__links" aria-label="Разделы"><span class="lg__lens" aria-hidden="true"></span>%s</nav>\n'
        '    <a class="lg__phone" href="%s">%s</a>\n    <a class="lg__cta" href="#zayavka">Связаться с нами</a>\n'
        '    <button class="lg__burger" type="button" aria-expanded="false" aria-controls="lg-sheet" aria-label="Открыть меню"><i></i><i></i><i></i></button>\n'
        '  </div>\n  <nav class="lg__sheet" id="lg-sheet" hidden aria-label="Меню">\n    %s\n'
        '    <a href="#zayavka">Связаться с нами <span aria-hidden="true">→</span></a>\n'
        '    <a class="lg__sheet-phone" href="%s">%s</a>\n  </nav>\n</header>\n'
        % (tone, sv_mark("h"), "".join(links), PHONE_HREF, PHONE, "\n    ".join(sheet), PHONE_HREF, PHONE))


def footer():
    col = lambda title, items: '<div><h4>%s</h4><ul>%s</ul></div>' % (title, "".join('<li><a href="%s">%s</a></li>' % (h, esc(l)) for l, h in items))
    return (
        '<footer class="ftr" data-tone="dark" aria-label="Подвал сайта">\n  <div class="wrap">\n    <div class="ftr-grid">\n'
        '      <div class="ftr-brand">\n        <a class="ftr-logo" href="/" aria-label="Инком-Аудит, на главную">%s<span><b>ИНКОМ-АУДИТ</b><small>Аудиторская компания</small></span></a>\n      </div>\n'
        '      %s\n      %s\n      %s\n    </div>\n'
        '    <div class="ftr-docs"><a href="/info/">Обязательное раскрытие информации аудиторскими организациями</a><a href="/policy/">Политика обработки персональных данных</a></div>\n'
        '    <div class="legal"><span>© 2010–2026 %s</span></div>\n  </div>\n</footer>\n'
        % (sv_mark("f"), col("Услуги", FOOTER_SERVICES), col("О компании", FOOTER_COMPANY), col("Информация", FOOTER_INFO), ORG))


def mbar():
    return ('<nav class="mbar" id="mbar" aria-label="Быстрые действия"><a href="%s">Позвонить</a><a class="mbar-cta" href="#zayavka">Заявка</a></nav>\n' % PHONE_HREF)


def base(ctx, page, body, tone="light", pre=""):
    url = ctx["site_url"] + "/" + page["path"]
    og_img = T.photo_url(ctx, page.get("photo") or "moscow-city-sunset")
    robots = ('<meta name="robots" content="noindex, nofollow">\n' if ctx["noindex"]
              else '<meta name="robots" content="noindex, follow">\n' if page.get("noindex") else "")
    return (
        '<!doctype html>\n<html lang="ru" data-tone="%s">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n%s'
        '<title>%s</title>\n<meta name="description" content="%s">\n<link rel="canonical" href="%s">\n'
        '<meta property="og:type" content="%s">\n<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n'
        '<meta property="og:url" content="%s">\n<meta property="og:image" content="%s">\n<meta property="og:locale" content="ru_RU">\n<meta property="og:site_name" content="Инком-Аудит">\n'
        '<meta name="theme-color" content="%s">\n'
        # иконки: ico для старых браузеров и Яндекса, svg для современных, png 120 для Яндекса, apple-touch для iOS
        '<link rel="icon" href="/favicon.ico" sizes="32x32">\n<link rel="icon" type="image/svg+xml" href="/favicon.svg">\n'
        '<link rel="icon" type="image/png" sizes="120x120" href="/favicon-120.png">\n<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n'
        '%s<link rel="stylesheet" href="/assets/sverka.css?v=%s">\n%s%s'
        '<!-- Яндекс.Вебмастер: <meta name="yandex-verification" content="…"> -->\n'
        '<!-- Яндекс.Метрика: вставить код счётчика перед </head> -->\n'
        '</head>\n<body>\n<a class="skip" href="#main">Перейти к содержимому</a>\n%s<main id="main">\n%s</main>\n%s%s%s'
        '<script src="/assets/sverka.js?v=%s" defer></script>\n</body>\n</html>\n'
        % (tone, robots, esc(page["title"]), esc(page["description"]), url, "article" if page["kind"] == "article" else "website",
           esc(page.get("og_title") or page["h1"]), esc(page["description"]), url, og_img, "#0D3C55" if tone == "dark" else "#EEF2F4", FONT_HEAD, ctx.get("asset_v", "1"), pre,
           head_jsonld(ctx, page), header(page, tone), body, footer(), mbar(), modal(page), ctx.get("asset_v", "1")))


# ---------- общие блоки ----------
def strip(items, cls="strip"):
    if not items:
        return ""
    cells = "".join('<div><dt>%s</dt><dd%s>%s</dd></div>' % (esc(k), ' class="pen"' if "₽" in str(v) else "", esc(v)) for k, v in items)
    return '<dl class="%s" style="--n:%d">%s</dl>' % (cls, len(items), cells)


FORM_TASKS = ["Обязательный аудит", "Инициативный аудит", "Налоговый аудит", "Дью дилидженс перед сделкой",
              "Подготовка отчетности по МСФО", "Бухгалтерские услуги", "Консалтинг и споры", "Другое"]


def lead_form(page, p="f", cls="form-sheet", heading=True):
    """Форма заявки. Один и тот же бланк внизу страницы и во всплывающем окне, id полей различаются префиксом."""
    pre = page.get("form_task") or ""
    options = "".join('<option%s>%s</option>' % (' selected' if o == pre else "", o) for o in FORM_TASKS)
    h = '      <h3 id="%s-h">Форма обратной связи</h3>\n' % p if heading else ""
    aria = ' aria-labelledby="%s-h"' % p if heading else ' aria-label="Форма обратной связи"'
    return (
        '    <form class="%s" id="%s-form" data-lead novalidate%s>\n%s'
        '      <div class="fld"><label for="%s-name">Ваше имя*</label><input id="%s-name" name="name" autocomplete="name" required></div>\n'
        '      <div class="fld"><label for="%s-phone">Телефон*</label><input id="%s-phone" name="phone" type="tel" autocomplete="tel" inputmode="tel" placeholder="+7 ___ ___-__-__" required></div>\n'
        '      <div class="fld"><label for="%s-email">E-mail*</label><input id="%s-email" name="email" type="email" autocomplete="email" inputmode="email" required></div>\n'
        '      <div class="fld"><label for="%s-company">Наименование компании*</label><input id="%s-company" name="company" autocomplete="organization" required></div>\n'
        '      <div class="fld"><label for="%s-msg">Сообщение*</label><textarea id="%s-msg" name="message" rows="4" maxlength="500" required></textarea><span class="counter" data-count aria-live="polite">0 / 500</span></div>\n'
        '      <div class="fld"><label for="%s-task">Услуга*</label><select id="%s-task" name="task" required>%s</select></div>\n'
        '      <button class="btn btn-pen" type="submit">Отправить заявку <span class="arr" aria-hidden="true">→</span></button>\n'
        '      <label class="consent" for="%s-consent"><input class="cbx" id="%s-consent" name="consent" type="checkbox" value="yes" required>'
        '<span>Направляя форму обратной связи и предоставляя персональные данные, я выражаю согласие на обработку моих персональных данных '
        'в соответствии с условиями <a href="/policy/">Политики обработки персональных данных</a></span></label>\n'
        '      <p class="form-msg" role="status" hidden>%s<span class="form-msg__t"></span></p>\n    </form>\n'
        % (cls, p, aria, h, p, p, p, p, p, p, p, p, p, p, p, p, options, p, p, mk()))


def zayavka(page):
    return (
        '<section class="contact" id="zayavka" data-tone="dark" aria-labelledby="zayavka-h">\n  <div class="wrap contact-grid">\n'
        '    <div class="contact-l" data-rise>\n      <h2 class="h2 h2-long" id="zayavka-h">Для определения объема и стоимости услуг заполните форму обратной связи или свяжитесь с нами любым удобным способом</h2>\n'
        '      <p class="phone-big" id="phoneTxt">%s</p>\n'
        '      <div class="c-row">%s%s</div>\n'
        '      <p class="email"><a href="mailto:%s" id="mailTxt">%s</a></p>\n    </div>\n%s  </div>\n</section>\n'
        % (PHONE, ibtn("Позвонить", PHONE_HREF, "phone", "white"), copy_btn(PHONE, "phoneTxt", "Скопировать номер", "line"), MAIL, MAIL, lead_form(page, "f")))


def modal(page):
    """Всплывающее окно заявки: открывается кнопками «Узнать стоимость» и «Оставить заявку» вместо прокрутки к форме."""
    return (
        '<dialog class="modal" id="modal" aria-labelledby="modal-h">\n  <div class="modal__panel">\n'
        '    <button class="modal__x" type="button" aria-label="Закрыть">%s</button>\n'
        '    <div class="modal__side">\n      <p class="kicker kicker--dark">Заявка</p>\n      <h2 class="modal__h" id="modal-h">Узнать стоимость</h2>\n'
        '      <p class="modal__p">Для определения объема и стоимости услуг заполните форму или свяжитесь с нами любым удобным способом</p>\n'
        '      <div class="modal__c"><a class="modal__phone" href="%s">%s</a><a class="modal__mail" href="mailto:%s">%s</a></div>\n'
        '    </div>\n%s  </div>\n</dialog>\n'
        % (ICO["x"], PHONE_HREF, PHONE, MAIL, MAIL, lead_form(page, "m", cls="form-sheet form-sheet--modal", heading=False)))


def st(key, state):
    return ('<span class="st" id="st-%s" data-state="%s">%s<span class="st-no">нет</span></span>'
            % (key, state, mk(cls="mk" + ("" if state == "yes" else " is-armed"))))


def checker(sec=None, h2_cls="h2", self_page=False):
    sec = sec or {}
    h2 = esc(sec.get("h2") or "Критерии обязательного аудита")
    intro = esc(sec.get("intro") or "Аудит отчетности за 2026 год обязателен, если доходы за 2025 год больше 800 млн ₽ или активы на 31.12.2025 больше 400 млн ₽. Достаточно одного критерия*")
    more = "" if self_page else '<a class="link" id="checkMore" href="/audit/obyazatelnyj/">Подробнее об обязательном аудите</a>'
    return (
        '<div class="check-grid">\n  <div class="check-intro" data-rise>\n    <h2 class="%s" id="check-h">%s</h2>\n    <p class="lead">%s</p>\n'
        '    <p class="law-ref">Статья 5 Федерального закона № 307-ФЗ «Об аудиторской деятельности»</p>\n'
        '    <p class="fine">*Оценка является предварительной, Федеральный закон №307-ФЗ содержит также ряд других критериев</p>\n  </div>\n'
        '  <form class="wp" id="checkForm" novalidate aria-labelledby="check-h">\n'
        '    <div class="wp-cols" aria-hidden="true"><span>Показатель</span><span>Значение</span><span>Критерий</span><span>Итог</span></div>\n'
        '    <div class="wp-row"><label for="inc">Доходы за 2025 год</label><div class="wp-field"><input id="inc" name="inc" type="text" inputmode="decimal" autocomplete="off" value="640"><span class="unit">млн ₽</span></div><span class="wp-crit">больше 800 млн ₽</span>%s</div>\n'
        '    <div class="wp-row"><label for="ast">Активы на 31.12.2025</label><div class="wp-field"><input id="ast" name="ast" type="text" inputmode="decimal" autocomplete="off" value="455"><span class="unit">млн ₽</span></div><span class="wp-crit">больше 400 млн ₽</span>%s</div>\n'
        '    <div class="wp-row cb"><label class="cbl" for="ao"><input class="cbx" type="checkbox" id="ao" name="ao"><span>Компания — акционерное общество</span></label><span class="wp-crit">как правило, да</span>%s</div>\n'
        '    <div class="wp-row cb"><label class="cbl" for="dev"><input class="cbx" type="checkbox" id="dev" name="dev"><span>Привлекаем средства дольщиков по 214-ФЗ</span></label><span class="wp-crit">да</span>%s</div>\n'
        '    <div class="wp-row cb"><label class="cbl" for="secu"><input class="cbx" type="checkbox" id="secu" name="secu"><span>Ценные бумаги на торгах или консолидированная отчетность</span></label><span class="wp-crit">да</span>%s</div>\n'
        '    <div class="wp-result" aria-live="polite"><p class="verdict" id="verdict" data-v="yes">Скорее всего, обязательный аудит нужен</p>'
        '<p class="verdict-why" id="verdictWhy">Основание: активы на 31.12.2025 больше 400 млн ₽</p><p class="prelim">Предварительная оценка · уточним на консультации</p>'
        '<div class="wp-acts" id="checkActs" data-v="yes"><a class="btn btn-pen" id="checkCta" href="#zayavka"><span id="checkCtaT">Отправить заявку</span> <span class="arr" aria-hidden="true">→</span></a>'
        '<a class="btn btn-pen alt" href="/audit/iniciativnyj/">Инициативный аудит</a><a class="btn btn-ink alt" href="/audit/nalogovyj/">Налоговый аудит</a>%s</div></div>\n  </form>\n</div>\n'
        % (h2_cls, h2, intro, st("inc", "no"), st("ast", "yes"), st("ao", "no"), st("dev", "no"), st("sec", "no"), more))


def calculator(sec=None):
    sec = sec or {}
    h2 = esc(sec.get("h2") or "Из чего складывается стоимость аудита")
    intro = esc(sec.get("intro") or "Укажите основные параметры компании. Калькулятор покажет, что увеличит объём работы. Точную цену назовём после оценки объёма.")
    return (
        '<div class="calcwrap">\n  <div class="check-intro"><h2 class="h2s" id="calc-h">%s</h2><p class="lead">%s</p></div>\n'
        '  <form class="wp calc" id="calcForm" novalidate aria-labelledby="calc-h">\n'
        '    <div class="wp-hd"><p>Оценка объёма работ · без обязательств</p><span class="chip">Пример — поставьте свои значения</span></div>\n'
        '    <div class="calc-grid">\n'
        '      <div class="fld"><label for="c-rev">Выручка за год</label><div class="wp-field"><input id="c-rev" name="rev" inputmode="decimal" autocomplete="off" value="300"><span class="unit">млн ₽</span></div></div>\n'
        '      <div class="fld"><label for="c-ast">Активы на 31 декабря</label><div class="wp-field"><input id="c-ast" name="ast" inputmode="decimal" autocomplete="off" value="150"><span class="unit">млн ₽</span></div></div>\n'
        '      <div class="fld"><label for="c-ent">Юридических лиц</label><select id="c-ent" name="ent"><option value="1">одно</option><option value="2">два</option><option value="3">три</option><option value="5">четыре и больше</option></select></div>\n'
        '      <div class="fld"><label for="c-type">Вид аудита</label><select id="c-type" name="type"><option value="must">обязательный аудит</option><option value="init">инициативный аудит</option><option value="express">экспресс-аудит</option>'
        '<option value="dev">аудит застройщика (214-ФЗ)</option><option value="tax">налоговый аудит</option><option value="ifrs">аудит отчётности по МСФО</option></select></div>\n'
        '      <div class="fld"><label for="c-ind">Отрасль</label><select id="c-ind" name="ind"><option value="trade">торговля</option><option value="build">строительство</option><option value="prod">производство</option><option value="lease">лизинг</option><option value="it">IT</option><option value="other">другая</option></select></div>\n'
        '      <div class="fld"><label for="c-term">Сроки</label><select id="c-term" name="term"><option value="normal">обычные</option><option value="fast">сжатые</option></select></div>\n'
        '    </div>\n    <div class="calc-act"><button class="btn btn-ink" type="submit">Оценить</button></div>\n'
        '    <div class="calc-out" id="calcOut" aria-live="polite"><p class="lbl">Объём работ</p><p class="calc-price" id="calcPrice">стандартный</p>\n'
        '      <ul class="calc-factors" id="calcFactors"><li class="na">Нажмите «Оценить», чтобы увидеть, что влияет на цену в вашем случае</li></ul>\n'
        '      <p class="prelim">Это ориентир · точную стоимость и сроки зафиксируем в коммерческом предложении</p>\n'
        '      <a class="btn btn-pen" href="#zayavka">Получить точный расчёт <span class="arr" aria-hidden="true">→</span></a></div>\n  </form>\n</div>\n' % (h2, intro))


def article_cards(ctx, limit=3, exclude=None):
    cards = []
    for a in ctx["articles"]:
        if exclude and a["path"] == exclude:
            continue
        if len(cards) >= limit:
            break
        tags = "".join('<span class="tag">%s</span>' % esc(t) for t in (a.get("tags") or [])[:3])
        cards.append('<a class="post" href="/%s"><p class="post-date">%s</p><h3>%s</h3><p>%s</p><div class="post-tags">%s</div><span class="link">Читать <span class="arr" aria-hidden="true">→</span></span></a>'
                     % (a["path"], ru_date(a.get("date", "")), esc(a["h1"]), esc(a.get("excerpt", "")), tags))
    return cards


# ---------- секции документа ----------
def sec_open(s, i, cls=""):
    sid = s.get("id") or slug(s.get("h2") or "", i)
    h2 = '<h2 class="h2s">%s</h2>' % esc(s["h2"]) if s.get("h2") else ""
    intro = '<p class="sec-intro">%s</p>' % esc(s["intro"]) if s.get("intro") else ""
    return '<section class="sec%s" id="%s">%s%s' % ((" " + cls) if cls else "", sid, h2, intro), sid


def table_html(head, rows, note=""):
    th = "".join("<th>%s</th>" % esc(x) for x in head)
    body = []
    for r in rows:
        cells = "".join('<td data-th="%s">%s</td>' % (esc(head[j]) if j < len(head) else "", c) for j, c in enumerate(r))
        body.append("<tr>%s</tr>" % cells)
    note = '<p class="sec-note">%s</p>' % esc(note) if note else ""
    return '<div class="tbl"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>%s' % (th, "".join(body), note)


def render_section(ctx, s, i):
    t = s["type"]
    if t == "checker":
        sid = s.get("id") or "check"
        return '<section class="sec sec-wide" id="%s">%s</section>' % (sid, checker(s, h2_cls="h2s", self_page=(ctx.get("page") or {}).get("path") == "audit/obyazatelnyj/")), sid, s.get("h2") or "Критерии обязательного аудита"
    if t == "calculator":
        sid = s.get("id") or "calc"
        return '<section class="sec sec-wide" id="%s">%s</section>' % (sid, calculator(s)), sid, s.get("h2") or "Стоимость"
    if t == "cta":
        sid = s.get("id") or "cta-%d" % i
        body = '<div class="cta-box"><h2>%s</h2>%s%s</div>' % (esc(s.get("h2") or "Обсудим вашу задачу"), ('<p>%s</p>' % esc(s["text"])) if s.get("text") else "", btn(s["button"][0], s["button"][1]))
        return '<section class="sec" id="%s">%s</section>' % (sid, body), sid, None
    if t == "photo":
        sid = s.get("id") or "photo-%d" % i
        body = figure(ctx, s["photo"], s.get("alt") or s.get("caption") or "", cls="ph sec-photo", sizes="(max-width: 900px) 100vw, 800px", caption=s.get("caption", ""))
        return '<section class="sec" id="%s">%s</section>' % (sid, body), sid, None
    head, sid = sec_open(s, i)
    if t == "prose":
        body = '<div class="prose">%s</div>' % s["html"]
    elif t == "facts":
        body = strip(s["items"], cls="strip strip-doc")
    elif t == "steps":
        li = "".join('<li><span class="steps__n" aria-hidden="true">%d</span><h3>%s</h3><p>%s</p></li>' % (n, esc(a), b) for n, (a, b) in enumerate(s["items"], 1))
        body = '<ol class="steps" data-steps><span class="steps__line" aria-hidden="true"><span class="steps__fill"></span></span>%s</ol>' % li
    elif t == "cards":
        n = 2 if len(s["items"]) in (2, 4) else 3
        cs = "".join('<a class="card" href="%s"><h3>%s</h3><p>%s</p><span class="link">Подробнее <span class="arr" aria-hidden="true">→</span></span></a>' % (esc(h), esc(a), esc(b)) for a, b, h in s["items"])
        body = '<div class="cards" style="--n:%d">%s</div>' % (n, cs)
    elif t == "table":
        body = table_html(s["head"], s["rows"], s.get("note", ""))
    elif t == "checklist":
        body = '<ul class="ticks" data-dv>%s</ul>' % "".join("<li>%s<span>%s</span></li>" % (mk(), x) for x in s["items"])
    elif t == "quote":
        body = '<blockquote class="law"><p>%s</p>%s</blockquote>' % (s["text"], ('<cite>%s</cite>' % esc(s["source"])) if s.get("source") else "")
    elif t == "articles":
        body = '<div class="posts posts-doc">%s</div>' % "".join(article_cards(ctx, s.get("limit", 3)))
    elif t == "why":
        cs = "".join('<div class="whyc">%s<h3>%s</h3><p>%s</p></div>' % (ICONS.get(ic, ICONS["check"]), esc(a), esc(b)) for ic, a, b in s["items"])
        body = '<div class="why-cards">%s</div>' % cs
    else:
        body = ""
    return head + body + "</section>", sid, s.get("h2")


def faq_html(page):
    f = page.get("faq")
    if not f:
        return ""
    items = "".join('<details><summary>%s</summary><div><p>%s</p></div></details>' % (esc(q), a) for q, a in f)
    return '<section class="sec" id="faq"><h2 class="h2s">Часто задаваемые вопросы</h2><div class="faq">%s</div></section>' % items


def related_html(page):
    r = page.get("related")
    if not r:
        return ""
    cs = "".join('<a class="card" href="%s"><h3>%s</h3><p>%s</p><span class="link">Перейти <span class="arr" aria-hidden="true">→</span></span></a>' % (esc(h), esc(a), esc(b)) for h, a, b in r)
    n = 3 if len(r) >= 3 else 2
    return ('<section class="sec-band related" data-tone="light" aria-labelledby="rel-h"><div class="wrap"><div class="sec-head"><h2 class="h2" id="rel-h">Смотрите также</h2></div>'
            '<div class="cards" style="--n:%d">%s</div></div></section>\n' % (n, cs))


def toc_html(entries):
    entries = [(sid, h) for sid, h in entries if h]
    if len(entries) < 2:
        return "", ""
    li = "".join('<li><a href="#%s">%s</a></li>' % (sid, esc(h)) for sid, h in entries)
    aside = '<aside class="toc" aria-label="Содержание"><div class="toc__in"><ol>%s</ol></div></aside>' % li
    mobile = '<details class="toc-m"><summary>Содержание</summary><ol>%s</ol></details>' % li
    return aside, mobile


def doc_sections(ctx, page):
    parts, toc = [], []
    for i, s in enumerate(page.get("sections") or [], 1):
        html, sid, h = render_section(ctx, s, i)
        parts.append(html)
        toc.append((sid, h))
    fq = faq_html(page)
    if fq:
        parts.append(fq)
        toc.append(("faq", "Часто задаваемые вопросы"))
    return "\n".join(parts), toc


def doc_block(ctx, page, body, toc, with_toc=True):
    if not body:
        return ""
    aside, mobile = toc_html(toc) if with_toc else ("", "")
    return '<div class="wrap doc-page%s">%s<article class="doc-body">%s%s</article></div>\n' % ("" if aside else " doc-page--notoc", aside, mobile, body)


# ---------- страницы ----------
def page_hero(ctx, page, tone="light", photo=True):
    kick = '<p class="kicker">%s</p>' % esc(page["kicker"]) if page.get("kicker") else ""
    lead = '<p class="%s">%s</p>' % (page.get("lead_cls") or "lead", page["lead"]) if page.get("lead") else ""
    ctas = []
    if page.get("cta"):
        ctas.append(btn(page["cta"][0], page["cta"][1]))
    if page.get("cta2"):
        ctas.append(btn(page["cta2"][0], page["cta2"][1], "ink", arrow=False))
    cta = '<div class="phero-cta">%s</div>' % "".join(ctas) if ctas else ""
    if photo and page.get("collage"):
        ph = collage(ctx, "collage phero-ph", lazy=False)
    else:
        ph = figure(ctx, page["photo"], page.get("photo_alt") or page["h1"], cls="ph phero-ph", sizes="(max-width: 900px) 100vw, 520px", lazy=False, tick=True) if (photo and page.get("photo")) else ""
    fx = ('<div class="wrap phero-facts">%s</div>' % strip(page["facts"])) if page.get("facts") else ""
    return ('<section class="phero%s" data-tone="%s">\n  <div class="wrap phero-in">\n    <div class="phero-text">%s%s<h1>%s</h1>%s%s</div>\n    %s\n  </div>\n  %s</section>\n'
            % (" phero--nophoto" if not ph else "", tone, T.crumbs(page), kick, esc(page["h1"]), lead, cta, ph, fx))


def hero_preload(ctx, page):
    if page.get("collage"):
        return ""
    return preload(ctx, page["photo"], "(max-width: 900px) 100vw, 520px") if page.get("photo") else ""


def render_doc(ctx, page):
    body, toc = doc_sections(ctx, page)
    if page.get("keep_periods"):   # сборка не убирает точки внутри этих меток (политика ПД)
        body = "<!--keep-->" + body + "<!--/keep-->"
    form = "" if page.get("no_form") else zayavka(page)
    return base(ctx, page, page_hero(ctx, page) + doc_block(ctx, page, body, toc) + related_html(page) + form, pre=hero_preload(ctx, page))


ADDRESS = "123458, Москва, ул. Твардовского, д. 2, корп. 5"
MAP_URL = "https://yandex.ru/maps/?text=" + "Москва, улица Твардовского, 2к5".replace(" ", "%20")


def render_contacts(ctx, page):
    body, toc = doc_sections(ctx, page)
    row = lambda lbl, val, vid, cls, acts: ('<div class="crow"><p class="crow__l">%s</p><p class="crow__v%s" id="%s">%s</p><div class="crow__a">%s</div></div>'
                                           % (lbl, cls, vid, val, acts))
    rows = (row("Телефон", PHONE, "cPhone", " crow__v--tel", ibtn("Позвонить", PHONE_HREF, "phone") + copy_btn(PHONE, "cPhone"))
            + row("E-mail", MAIL, "cMail", "", ibtn("Написать", "mailto:" + MAIL, "mail") + copy_btn(MAIL, "cMail"))
            + row("Офис", ADDRESS, "cAddr", " crow__v--sm", ibtn("На карте", MAP_URL, "pin") + copy_btn(ADDRESS, "cAddr")))
    info = ('<section class="sec-band csec" data-tone="light" aria-label="Контакты компании"><div class="wrap">'
            '<div class="csheet" data-rise>%s</div></div></section>\n' % rows)
    return base(ctx, page, page_hero(ctx, page, photo=False) + info + doc_block(ctx, page, body, toc, with_toc=False) + related_html(page) + zayavka(page))


def render_article(ctx, page):
    body, toc = doc_sections(ctx, page)
    dl = ['<time datetime="%s">%s</time>' % (page["date"], ru_date(page["date"]))]
    if page.get("updated") and page["updated"] != page["date"]:
        dl.append("обновлено " + ru_date(page["updated"]))
    dl.append(esc(page.get("author") or "Аудиторы «Инком-Аудит»"))
    tags = "".join('<span class="tag">%s</span>' % esc(t) for t in (page.get("tags") or []))
    ph = figure(ctx, page["photo"], page.get("photo_alt") or page["h1"], cls="ph art-ph", sizes="(max-width: 900px) 100vw, 800px", lazy=False, tick=True) if page.get("photo") else ""
    head = ('<section class="art-head" data-tone="light"><div class="wrap"><div class="art-in">%s<p class="dateline">%s</p><h1>%s</h1>%s%s</div></div></section>\n'
            % (T.crumbs(page), " · ".join(dl), esc(page["h1"]), ('<p class="lead">%s</p>' % page["lead"]) if page.get("lead") else "", ph))
    tag_block = ('<div class="art-tags"><span class="lbl">Теги</span>%s</div>' % tags) if tags else ""
    doc = doc_block(ctx, page, body + tag_block, toc)
    more = article_cards(ctx, 3, exclude=page["path"])
    rel = related_html(page)
    if more:
        rel += ('<section class="sec-band sec-band--sheet" data-tone="light" aria-labelledby="more-h"><div class="wrap"><div class="sec-head"><h2 class="h2" id="more-h">Другие статьи</h2>'
                '<p class="lead"><a class="link" href="/blog/">Все статьи блога <span class="arr" aria-hidden="true">→</span></a></p></div><div class="posts">%s</div></div></section>\n' % "".join(more))
    return base(ctx, page, head + doc + rel + zayavka(page), pre=preload(ctx, page["photo"], "(max-width: 900px) 100vw, 800px") if page.get("photo") else "")


def render_blog(ctx, page):
    cards = article_cards(ctx, 100)
    empty = '<p class="lead">Статьи появятся здесь. Пока посмотрите разделы услуг.</p>' if not cards else ""
    body, toc = doc_sections(ctx, page)
    grid = '<section class="sec-band" data-tone="light" aria-label="Статьи"><div class="wrap"><div class="posts">%s</div>%s</div></section>\n' % ("".join(cards), empty)
    return base(ctx, page, page_hero(ctx, page, photo=False) + grid + doc_block(ctx, page, body, toc, with_toc=False) + zayavka(page))


LEDGER_ROWS = [
    ("01", "Основные средства", "48 920 400,00", "Дт", TICK, "сверено с первичкой", ""),
    ("10", "Материалы", "6 314 780,50", "Дт", SIGMA, "суммы пересчитаны", ""),
    ("19", "НДС по&nbsp;приобретённым ценностям", "2 418 600,00", "Дт", TICK, "исправлено, сверено", "flag"),
    ("41", "Товары", "31 702 115,20", "Дт", SIGMA, "суммы пересчитаны", "m-hide"),
    ("51", "Расчётные счета", "12 845 330,75", "Дт", PERP, "сверено с банковской выпиской", ""),
    ("60", "Расчёты с&nbsp;поставщиками", "9 236 004,10", "Кт", TICK, "сверено с первичкой", ""),
    ("62", "Расчёты с&nbsp;покупателями", "17 590 260,00", "Дт", TICK, "сверено с первичкой", "m-hide"),
    ("68.02", "Расчёты по&nbsp;НДС", "3 104 512,00", "Кт", SIGMA, "суммы пересчитаны", "m-hide"),
]


def ledger(ctx):
    rows = []
    for code, name, s, dk, d, label, cls in LEDGER_ROWS:
        flag = cls == "flag"
        ell = ('<svg class="mk ell" id="flagEll" viewBox="0 0 200 50" preserveAspectRatio="none" aria-hidden="true"><path pathLength="1" d="M104 5C150 3 195 10 195 25 195 41 142 47 98 46 48 45 6 40 6 24 6 10 54 3 116 7"/></svg>') if flag else ""
        attrs = ' data-flag' if flag else (' class="%s"' % cls if cls else "")
        rows.append('<tr%s><td class="code">%s</td><td>%s</td><td class="sum">%s<i class="dk">%s</i>%s</td><td class="tk">%s</td></tr>'
                    % (attrs, code, name, s, dk, ell, mk(d, label=label)))
    legend = "".join('<li>%s<span>%s</span></li>' % (mk(d), t) for d, t in
                     ((TICK, "сверено с первичными документами"), (SIGMA, "суммы пересчитаны"), (PERP, "сверено с банковской выпиской"), (RING, "требует внимания")))
    return (
        '<section class="sec-band method" id="method" data-tone="light" aria-labelledby="m-h">\n  <div class="wrap method-grid">\n'
        '    <div class="method-copy" data-rise>\n      <h2 class="h2" id="m-h">Как аудитор проверяет учёт</h2>\n'
        '      <p class="lead">Каждую строку отчётности аудитор сверяет с первичными документами, выписками банка и регистрами учёта. Проверенное отмечает пометкой, спорное обводит и комментирует на полях.</p>\n'
        '      <p>Так выглядят рабочие документы аудитора. По ним видно, что именно проверено и что стоит исправить до сдачи отчётности.</p>\n'
        '      <ul class="legend" data-dv>%s</ul>\n    </div>\n'
        '    <figure class="stage" id="stage">%s'
        '      <div class="sheet" role="group" aria-label="Пример: фрагмент оборотно-сальдовой ведомости с пометками аудитора">\n'
        '        <div class="sheet-hd"><div><p class="sheet-title">Оборотно-сальдовая ведомость</p><p class="sheet-meta">Компания-пример · 2025 год · фрагмент</p></div>'
        '<div class="sheet-ref"><span class="ref" title="Рабочий документ аудитора">РД Б-2</span><span class="status" id="sheetStatus">%s<span id="statusText">проверено</span></span></div></div>\n'
        '        <div class="sheet-body">\n          <div class="ledger-wrap" id="ledgerWrap"><div class="scan" id="scan" aria-hidden="true"></div>\n'
        '            <table class="ledger" id="ledger"><thead><tr><th scope="col">Счёт</th><th scope="col">Наименование</th><th scope="col" class="r">Сальдо на&nbsp;31.12, ₽</th><th scope="col"><span class="sr">Пометка аудитора</span></th></tr></thead><tbody>%s</tbody></table>\n'
        '            <div class="ledger-foot" id="ledgerFoot"><span>Итого сальдо Дт по&nbsp;фрагменту</span><span class="sum">119 791 486,45</span><span class="tk">%s</span></div>\n          </div>\n'
        '          <div class="margin" id="sheetMargin" aria-label="Заметки аудитора на полях">\n'
        '            <p class="note hand" id="note1"><svg class="mk note-arrow" id="note1Arrow" viewBox="0 0 60 24" aria-hidden="true"><path pathLength="1" d="M56 5C42 9 25 12 7 15M7 15l8-7M7 15l9 4"/></svg>нет счёта-фактуры: риск по&nbsp;НДС</p>\n'
        '            <p class="note hand" id="note2">исправлено до&nbsp;сдачи отчётности %s</p>\n          </div>\n        </div>\n'
        '        <div class="sheet-ft"><span>Пример · данные условные</span><button class="replay" id="replay" type="button">Повторить проверку</button></div>\n      </div>\n    </figure>\n  </div>\n</section>\n'
        % (legend, figure(ctx, "binders-color", "", cls="stage-bg", sizes="(max-width:1000px) 100vw, 700px"), mk(), "".join(rows), mk(SIGMA, label="итог пересчитан"), mk(extra=' id="note2Tick"')))


INDUSTRIES8 = INDUSTRIES + [
    ("Арендный бизнес", "ind-rent", "Бизнес-центр с арендными площадями", ["учет аренды у арендодателя по ФСБУ 25/2018", "доходы от аренды, НДС и налог на имущество по объектам"]),
    ("Сельское хозяйство", "ind-agro", "Поле и сельскохозяйственная техника", ["ЕСХН и условия его применения", "субсидии и целевое финансирование (ПБУ 13/2000)"]),
    ("Инвестиционные компании", "ind-invest", "Деловой центр, офисы инвестиционных компаний", ["финансовые вложения и их обесценение (ПБУ 19/02)", "консолидация группы и отчетность для инвесторов"]),
]


def industries(ctx, items):
    notes = {"Торговля": ("остатки сверены", "12%", "72%"), "Строительство": ("214-ФЗ", "10%", "16%"), "Производство": ("себестоимость", "12%", "16%"),
             "Лизинг": ("ФСБУ 25", "10%", "16%"), "IT": ("НМА", "12%", "76%"), "Арендный бизнес": ("ФСБУ 25", "12%", "16%"),
             "Сельское хозяйство": ("субсидии", "12%", "74%"), "Инвестиционные компании": ("ПБУ 19", "10%", "16%")}
    ells = ["M62 30C80 28 92 36 92 48 92 60 80 66 64 66 48 66 38 58 39 47 40 36 52 30 70 31", "M48 52C70 50 90 58 90 70 90 82 70 88 50 88 28 88 10 82 10 70 10 58 28 52 56 53",
            "M40 42C62 40 82 48 82 60 82 72 64 78 44 78 24 78 10 70 10 59 10 48 24 42 50 43", "M46 40C70 38 94 48 94 60 94 72 72 78 48 78 24 78 6 70 6 59 6 48 24 40 54 41",
            "M48 30C66 29 80 38 80 50 80 62 66 68 50 68 32 68 20 61 20 49 20 37 33 30 56 31"]
    cards = []
    for n, (name, key, alt, pts) in enumerate(items):
        note, left, top = notes.get(name, (name, "12%", "16%"))
        ph = figure(ctx, key, alt, cls="ind-ph", sizes="(max-width:640px) 76vw, (max-width:1100px) 46vw, 290px", extra="", tick=False)
        if not ph:
            ph = '<figure class="ind-ph ind-ph--empty" aria-hidden="true"></figure>'
        ph = ph.replace("</figure>", '<svg class="mk ann" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><path pathLength="1" d="%s"/></svg><p class="ann-note hand" style="left:%s;top:%s">%s ✓</p></figure>' % (ells[n % 5], left, top, esc(note)))
        li = "".join("<li>%s<span>%s</span></li>" % (mk(), esc(p)) for p in pts)
        cards.append('<article class="ind-card" data-ann>%s<h3>%s</h3><ul class="ticks">%s</ul></article>' % (ph, esc(name), li))
    return (
        '<section class="sec-band ind cv" id="industries" data-tone="dark" aria-labelledby="ind-h">\n  <div class="wrap">\n'
        '    <div class="sec-head sec-head--one" data-rise><h2 class="h2" id="ind-h">Кто наши основные клиенты</h2></div>\n'
        '    <div class="ind-scroll"><div class="ind-grid">%s</div></div>\n    <p class="ind-hint" aria-hidden="true">Листайте карточки вбок →</p>\n  </div>\n</section>\n' % "".join(cards))


COLLAGE_KEYS = ["ind-construction-2", "ind-trade", "ind-production", "ind-agro", "ind-leasing", "ind-it", "ind-rent"]
COLLAGE_ALT = {"ind-construction-2": "Строящиеся башни и краны", "ind-trade": "Стеллажи с коробками на складе", "ind-production": "Производственный цех",
               "ind-agro": "Поле и сельскохозяйственная техника", "ind-leasing": "Экскаватор на строительной площадке", "ind-it": "Коридор серверного зала", "ind-rent": "Бизнес-центр"}
ICONS = {
    "percent": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="7.5" cy="7.5" r="2.5"/><circle cx="16.5" cy="16.5" r="2.5"/><path d="M18 6 6 18"/></svg>',
    "grid": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.5"/></svg>',
    "medal": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="9" r="5.5"/><path d="M9 13.8 7.5 21l4.5-2.4L16.5 21 15 13.8M10 9l1.5 1.5L14.5 7.5"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 4.5 6v5.2c0 4.4 3 8.1 7.5 9.8 4.5-1.7 7.5-5.4 7.5-9.8V6Z"/><path d="M8.8 12.2l2.2 2.2 4.3-4.6"/></svg>',
    "lock": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5M12 14.5v2.5"/></svg>',
    "check": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
}


def collage(ctx, cls="collage", lazy=True):
    """Мозаика из фотографий отраслей (первая плитка высокая) с одной пометкой аудитора."""
    tiles = []
    for key in COLLAGE_KEYS:
        f = figure(ctx, key, COLLAGE_ALT.get(key, ""), cls="ph col-ph", sizes="(max-width:900px) 50vw, 260px", lazy=lazy, tick=(len(tiles) == 3))
        if f:
            tiles.append(f)
        if len(tiles) == 5:
            break
    if tiles:
        ann = ('<svg class="mk ann" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><path pathLength="1" d="M40 36C62 34 84 42 84 54 84 66 64 72 44 72 24 72 10 64 10 53 10 42 24 36 52 37"/></svg>'
               '<p class="ann-note hand" style="left:10%;top:66%">проверено ✓</p>')
        tiles[0] = tiles[0].replace("</figure>", ann + "</figure>")
    return '<div class="%s" data-ann role="img" aria-label="Отрасли наших клиентов: стройка, торговля, производство, лизинг, IT">%s</div>' % (cls, "".join(tiles))


# Двое специалистов спиной к спине против закатного солнца (картинку запекает src/duo.py). Только на широких экранах
# На узких экранах силуэты скрыты: <source> подставляет пустой gif, чтобы телефон не качал картинку зря
# Силуэты лежат внутри <figure class="hero-img">, чтобы на телефоне считаться в процентах от рамки фото.
# Где силуэтов нет (планшеты и телефон горизонтально), <source> подсовывает 1px-гифку, и картинка не качается.
HERO_DUO = ('<picture><source media="(min-width: 641px) and (max-width: 999px), (min-width: 641px) and (max-aspect-ratio: 5/4), (max-width: 640px) and (orientation: landscape)" srcset="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==">'
            '<img class="hero-duo" src="/assets/hero-duo.webp" width="829" height="931" alt="" aria-hidden="true" decoding="async" fetchpriority="low"></picture>')


def render_home(ctx, page):
    h = page.get("hero") or {}
    h1 = h.get("h1_html") or esc(page["h1"])
    uline = '<svg class="mk uline" id="uline" viewBox="0 0 300 20" preserveAspectRatio="none" aria-hidden="true"><path pathLength="1" d="M4 13C78 6 170 4 296 8M34 17c66-4 146-5 224-2"/></svg>'
    h1 = re.sub(r'<span class="accent">(.*?)</span>', lambda m: '<span class="u">%s%s</span>' % (m.group(1), uline), h1, count=1)
    tag = '<p class="hero-tag">%s</p>' % esc(h["tagline"]) if h.get("tagline") else ""
    hero_img = figure(ctx, h.get("photo") or "moscow-city-sunset", "Москва-Сити на закате, вид на набережную и проспект", cls="hero-img", sizes="100vw", lazy=False)
    hero_img = hero_img.replace("</figure>", HERO_DUO + "</figure>")
    hero = (
        '<section class="hero" id="top" data-tone="dark" aria-labelledby="hero-h">\n  %s\n  <div class="hero-shade" aria-hidden="true"></div>\n'
        '  <div class="wrap hero-in">\n    <p class="hero-kicker">%s</p>\n    <h1 id="hero-h">%s</h1>\n%s    <p class="hero-lead">%s</p>\n'
        '    <div class="hero-cta">%s%s</div>\n  </div>\n  <div class="wrap"><dl class="hero-strip">'
        '<div><dt>Услуги</dt><dd>аудит, МСФО, консалтинг, бухучет</dd></div><div><dt>Опыт</dt><dd>700+ проектов с&nbsp;2010 года</dd></div>'
        '<div><dt>Отрасли</dt><dd>производство, торговля, с/х, инвестиции, аренда, IT</dd></div><div><dt>Членство в&nbsp;СРО</dt><dd>СРО ААС<br>ОРНЗ <span class="nb">12006082980</span></dd></div></dl></div>\n</section>\n'
        % (hero_img, esc(h.get("kicker") or "Аудиторская компания • с 2010 года • Работаем по всей России"), h1, tag, h.get("sub") or page.get("lead", ""),
           btn(*(h.get("cta") or ("Узнать стоимость", "#zayavka"))), btn(*(h.get("cta2") or ("Обязательный аудит", "/audit/obyazatelnyj/")), "glass", arrow=False)))

    d = page.get("directory") or []
    rows = "".join('<a href="%s">%s<span>%s</span></a>' % (esc(href), mk(), esc(t)) for t, href in d)
    directory = ('<section class="sec-band" id="services" data-tone="light" aria-labelledby="svc-h"><div class="wrap"><div class="sec-head sec-head--one" data-rise><h2 class="h2" id="svc-h">%s</h2></div>'
                 '<div class="dir2" data-dv>%s</div></div></section>\n' % (esc(page.get("directory_h2") or "Наши услуги"), rows)) if d else ""

    steps = page.get("process") or []
    st_ = "".join('<li class="step"><span class="node">%d%s</span><h3>%s</h3><p>%s</p></li>' % (i, mk(), esc(a), esc(b)) for i, (a, b) in enumerate(steps, 1))
    process = ('<section class="sec-band cv" id="process" data-tone="light" aria-labelledby="proc-h"><div class="wrap"><div class="sec-head sec-head--one" data-rise><h2 class="h2" id="proc-h">%s</h2></div>'
               '<ol class="proc" id="proc"><li class="track" aria-hidden="true"><span class="fill" id="fill"></span></li>%s</ol>'
               '</div></section>\n'
               % (esc(page.get("process_h2") or "Как мы строим нашу работу"), st_)) if steps else ""

    extra, _ = doc_sections(ctx, page)
    body = hero + directory + industries(ctx, page.get("industries") or INDUSTRIES8) + process + doc_block(ctx, page, extra, [], with_toc=False) + zayavka(page)
    return base(ctx, page, body, tone="dark", pre=preload(ctx, h.get("photo") or "moscow-city-sunset", "100vw"))


def render_404(ctx):
    page = dict(kind="page", path="404.html", title="Страница не найдена — Инком-Аудит", description="Такой страницы нет. Перейдите на главную или в раздел услуг.", h1="Страница не найдена")
    body = ('<section class="phero phero--nophoto" data-tone="light"><div class="wrap phero-in"><div class="phero-text"><p class="kicker">Ошибка 404</p><h1>Страница не найдена</h1>'
            '<p class="lead">Возможно, адрес изменился. Начните с главной или выберите раздел.</p><div class="phero-cta">%s%s</div></div></div></section>\n'
            % (btn("На главную", "/"), btn("Аудиторские услуги", "/audit/", "ink", arrow=False)))
    html = base(ctx, page, body + zayavka(page))
    return html.replace('<link rel="canonical" href="%s/404.html">\n' % ctx["site_url"], "")


def render(page, ctx):
    ctx = dict(ctx, page=page)
    k = page["kind"]
    if k == "home":
        return render_home(ctx, page)
    if k == "article":
        return render_article(ctx, page)
    if k == "blog":
        return render_blog(ctx, page)
    if k == "contacts":
        return render_contacts(ctx, page)
    return render_doc(ctx, page)
