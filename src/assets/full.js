/* Инком-Аудит — полный сайт («Печать»). Один общий скрипт: шапка, печать на главной, бланки, формы, якоря. Все блоки необязательны. */
(() => {
  'use strict';
  const root = document.documentElement;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const listen = (mq, fn) => (mq.addEventListener ? mq.addEventListener('change', fn) : mq.addListener(fn));
  const restart = (el, value) => { if (!el) return; el.style.animation = 'none'; void el.getBoundingClientRect(); el.style.animation = value; };

  /* ——— Стеклянная шапка ——— */
  const lg = $('#lg');
  const bar = lg && $('.lg__bar', lg);
  const navLinks = lg ? $$('.lg__links a', lg) : [];
  const lens = lg && $('.lg__lens', lg);
  const toneSections = $$('[data-tone]').filter(s => s !== lg);
  const current = navLinks.find(a => a.getAttribute('aria-current') === 'page') || null;
  let hovering = false;
  const setHH = () => { if (bar) root.style.setProperty('--hh', Math.round(bar.getBoundingClientRect().bottom + 18) + 'px'); };
  function placeLens(a) {
    if (!lens) return;
    if (!a) { lens.style.opacity = '0'; return; }
    if (!lens.dataset.r) { lens.style.transition = 'none'; lens.dataset.r = '1'; setTimeout(() => { lens.style.transition = ''; }, 80); }
    lens.style.width = a.offsetWidth + 'px';
    lens.style.setProperty('--x', a.offsetLeft + 'px');
    lens.style.opacity = '1';
  }
  navLinks.forEach(a => {
    a.addEventListener('pointerenter', () => { hovering = true; placeLens(a); });
    a.addEventListener('focus', () => placeLens(a));
    a.addEventListener('blur', () => placeLens(current));
  });
  const linksNav = lg && $('.lg__links', lg);
  if (linksNav) linksNav.addEventListener('pointerleave', () => { hovering = false; placeLens(current); });
  function updHeader() {
    if (!bar) return;
    const r = bar.getBoundingClientRect();
    const y = r.top + r.height / 2;
    for (const s of toneSections) {
      const sr = s.getBoundingClientRect();
      if (sr.top <= y && sr.bottom > y) { if (lg.dataset.tone !== s.dataset.tone) lg.dataset.tone = s.dataset.tone; break; }
    }
    lg.classList.toggle('is-scrolled', window.scrollY > 40);
  }
  const burger = lg && $('.lg__burger', lg);
  const sheet = $('#lg-sheet');
  function setOpen(open) {
    if (!burger || !sheet) return;
    lg.classList.toggle('is-open', open);
    burger.setAttribute('aria-expanded', String(open));
    burger.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
    sheet.hidden = !open;
  }
  if (burger && sheet) {
    burger.addEventListener('click', () => setOpen(!lg.classList.contains('is-open')));
    sheet.addEventListener('click', e => { if (e.target.closest('a')) setOpen(false); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && lg.classList.contains('is-open')) { setOpen(false); burger.focus(); } });
    document.addEventListener('click', e => { if (lg.classList.contains('is-open') && !e.target.closest('.lg__bar') && !e.target.closest('#lg-sheet')) setOpen(false); });
    listen(window.matchMedia('(min-width: 1200px)'), e => { if (e.matches) setOpen(false); });
  }

  /* ——— Переключатель вариантов: прячется, пока листаете вниз ——— */
  const vswitch = $('#vswitch');
  let swY = window.scrollY;
  function updSwitch() {
    if (!vswitch) return;
    const y = window.scrollY;
    const nearEnd = y + window.innerHeight > root.scrollHeight - 160;
    if (y < 120 || nearEnd || y < swY - 6) vswitch.classList.remove('is-away');
    else if (y > swY + 6) vswitch.classList.add('is-away');
    swY = y;
  }

  /* ——— Печать в первом экране (только главная) ——— */
  const hero = $('#top');
  const layer = $('#stamps');
  if (hero && layer) {
    const NS = 'http://www.w3.org/2000/svg';
    const placed = [];
    const replaySeal = () => {
      if (reduce) return;
      restart($('.seal'), 'slam .62s both');
      restart($('.seal-fx'), 'fx .6s ease-out .3s both');
      restart($('.seal-shadow'), 'lift .66s ease-out both');
    };
    const stampAt = (x, y) => {
      const svg = document.createElementNS(NS, 'svg');
      svg.setAttribute('viewBox', '0 0 120 120');
      svg.setAttribute('class', 'mstamp');
      const use = document.createElementNS(NS, 'use');
      use.setAttribute('href', '#seal-mini');
      use.setAttribute('filter', 'url(#ink-s)');
      svg.appendChild(use);
      svg.style.left = x + 'px';
      svg.style.top = y + 'px';
      svg.style.setProperty('--r', (Math.random() * 44 - 22).toFixed(1) + 'deg');
      layer.appendChild(svg);
      placed.push(svg);
      if (placed.length > 6) {
        const old = placed.shift();
        if (reduce) { old.remove(); return; }
        old.classList.add('is-out');
        setTimeout(() => old.remove(), 600);
      }
    };
    hero.addEventListener('click', e => {
      if (e.target.closest('.seal-wrap')) { replaySeal(); return; }
      if (e.target.closest('a, button, input, select, textarea, label, h1, p, ul, figure')) return;
      const sel = window.getSelection ? window.getSelection() : null;
      if (sel && String(sel).length) return;
      const r = hero.getBoundingClientRect();
      stampAt(e.clientX - r.left, e.clientY - r.top);
    });
  }

  /* ——— Появление при прокрутке ——— */
  const io = ('IntersectionObserver' in window) ? new IntersectionObserver(entries => {
    entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
  }, { threshold: 0.25 }) : null;
  if (io && !reduce) {
    $$('[data-reveal]').forEach(el => {
      if (el.getBoundingClientRect().top > window.innerHeight * 0.92) { el.classList.add('pre'); io.observe(el); }
    });
  }

  /* ——— Порядок работы: линия заполняется по мере прокрутки ——— */
  const proc = $('.proc');
  const steps = $$('.proc__step');
  const vertMQ = window.matchMedia('(max-width: 1000px)');
  function updProc() {
    if (!proc) return;
    const r = proc.getBoundingClientRect();
    const vh = window.innerHeight;
    const vert = vertMQ.matches;
    let p;
    if (reduce) p = 1;
    else if (vert) p = clamp((vh * 0.62 - r.top) / r.height, 0, 1);
    else p = clamp((vh * 0.88 - r.top) / (vh * 0.5), 0, 1);
    proc.style.setProperty('--p', p.toFixed(3));
    steps.forEach(st => {
      const sr = st.getBoundingClientRect();
      const f = vert ? (sr.top - r.top) / r.height : (sr.left - r.left) / r.width;
      st.classList.toggle('is-done', p > 0 && p >= f - 0.001);
    });
  }

  /* ——— Оглавление страницы: подсветка текущего раздела ——— */
  const tocLinks = $$('.toc a');
  const tocTargets = tocLinks.map(a => document.getElementById(a.getAttribute('href').slice(1)));
  function updToc() {
    if (!tocLinks.length) return;
    const probe = (parseFloat(getComputedStyle(root).getPropertyValue('--hh')) || 96) + 40;
    let cur = -1;
    tocTargets.forEach((t, i) => { if (t && t.getBoundingClientRect().top <= probe) cur = i; });
    tocLinks.forEach((a, i) => a.classList.toggle('is-on', i === cur));
  }

  let dirty = true;
  window.addEventListener('scroll', () => { dirty = true; }, { passive: true });
  window.addEventListener('resize', () => { dirty = true; setHH(); });
  function frame() {
    if (dirty) { dirty = false; updHeader(); updSwitch(); updProc(); updToc(); }
    window.requestAnimationFrame(frame);
  }
  setHH();
  updHeader();
  updProc();
  updToc();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { setHH(); dirty = true; });
  window.addEventListener('load', () => { dirty = true; });
  window.requestAnimationFrame(frame);

  /* ——— Бланк проверки обязательного аудита ——— */
  const blank = $('#blank');
  if (blank) {
    const incEl = $('#b-inc'), astEl = $('#b-ast'), aoEl = $('#b-ao'), devEl = $('#b-dev'), secEl = $('#b-sec');
    const ex = $('#blankEx'), err = $('#blankErr'), res = $('#blankResult');
    const stamp = $('#rstamp'), stampMain = $('#rstampMain'), reasons = $('#blankReasons'), verdict = $('#blankVerdict');
    const parse = v => {
      const s = String(v).replace(/[\s ]/g, '').replace(',', '.');
      if (!s) return null;
      const n = Number(s);
      return Number.isFinite(n) && n >= 0 ? n : NaN;
    };
    const fmt = n => n.toLocaleString('ru-RU', { maximumFractionDigits: 1 });
    function evaluate() {
      const inc = parse(incEl.value), ast = parse(astEl.value);
      const ao = aoEl.checked, dev = devEl.checked, sec = secEl.checked;
      if (Number.isNaN(inc) || Number.isNaN(ast)) return { err: 'Введите суммы цифрами, в миллионах рублей. Например: 650.' };
      if (inc === null && ast === null && !ao && !dev && !sec) return { err: 'Укажите доходы и активы, хотя бы примерно.' };
      const list = [];
      if (inc !== null) list.push([inc > 800, inc > 800 ? 'Доходы ' + fmt(inc) + ' млн ₽ больше 800 млн ₽' : 'Доходы ' + fmt(inc) + ' млн ₽ не больше 800 млн ₽']);
      else list.push([null, 'Доходы не указаны']);
      if (ast !== null) list.push([ast > 400, ast > 400 ? 'Активы ' + fmt(ast) + ' млн ₽ больше 400 млн ₽' : 'Активы ' + fmt(ast) + ' млн ₽ не больше 400 млн ₽']);
      else list.push([null, 'Активы не указаны']);
      if (ao) list.push([null, 'Акционерное общество: скорее всего, аудит обязателен']);
      if (dev) list.push([true, 'Застройщик по 214-ФЗ проходит аудит ежегодно']);
      if (sec) list.push([true, 'Ценные бумаги на торгах или консолидированная отчётность']);
      if (list.some(r => r[0] === true)) return { state: 'must', rows: list, verdict: 'Аудит обязателен: для этого достаточно одного критерия.' };
      if (ao) return { state: 'check', rows: list, verdict: 'Для акционерных обществ аудит, скорее всего, обязателен. Уточним по вашей ситуации.' };
      if (inc === null || ast === null) return { state: 'check', rows: list, verdict: 'Не хватает одного показателя. Уточним на консультации.' };
      return { state: 'no', rows: list, verdict: 'По этим данным аудит не обязателен. Инициативный или экспресс-аудит поможет проверить учёт перед сделкой, проверкой или для банка.' };
    }
    function render(r) {
      reasons.textContent = '';
      r.rows.forEach(([ok, text]) => {
        const li = document.createElement('li');
        li.className = ok === true ? 'yes' : ok === false ? 'no' : 'na';
        li.textContent = text;
        reasons.appendChild(li);
      });
      verdict.textContent = r.verdict;
      stamp.classList.remove('is-must', 'is-no', 'is-check');
      stamp.classList.add('is-' + r.state);
      stampMain.textContent = r.state === 'must' ? 'Обязателен' : r.state === 'no' ? 'Не обязателен' : 'Уточним';
      res.classList.remove('is-stale');
      if (!reduce) restart(stamp, 'rslam .5s both');
    }
    blank.addEventListener('submit', e => {
      e.preventDefault();
      const r = evaluate();
      if (r.err) { err.textContent = r.err; return; }
      err.textContent = '';
      ex.hidden = true;
      render(r);
    });
    blank.addEventListener('input', () => { ex.hidden = true; res.classList.add('is-stale'); err.textContent = ''; });
  }

  /* ——— Оценка объёма работ (калькулятор): без выдуманных цифр, только факторы ——— */
  const calc = $('#calcForm');
  if (calc) {
    const num = v => { const s = String(v).replace(/[\s ]/g, '').replace(',', '.'); const n = Number(s); return s && Number.isFinite(n) && n >= 0 ? n : null; };
    const out = $('#calcFactors'), price = $('#calcPrice');
    const add = (list, ok, text) => list.push([ok, text]);
    calc.addEventListener('submit', e => {
      e.preventDefault();
      const rev = num($('#c-rev').value), ast = num($('#c-ast').value);
      const ent = Number($('#c-ent').value), type = $('#c-type').value, ind = $('#c-ind').value, term = $('#c-term').value;
      const f = [];
      if (rev === null && ast === null) add(f, null, 'Укажите выручку и активы хотя бы примерно, тогда оценка будет точнее');
      if (rev !== null) add(f, rev > 800, rev > 800 ? 'Выручка выше 800 млн ₽: больше операций и документов для выборки' : 'Выручка до 800 млн ₽: обычный объём выборки');
      if (ast !== null) add(f, ast > 400, ast > 400 ? 'Активы выше 400 млн ₽: больше участков учёта для проверки' : 'Активы до 400 млн ₽: обычный объём проверки');
      if (ent > 1) add(f, true, 'Несколько юридических лиц: отдельное заключение по каждому');
      if (type === 'dev') add(f, true, 'Застройщик по 214-ФЗ: проверяем раздельный учёт по объектам и эскроу-счета');
      if (type === 'ifrs') add(f, true, 'Отчётность по МСФО: объём зависит от трансформации и консолидации');
      if (type === 'tax') add(f, true, 'Налоговый аудит: сплошная проверка первички по выбранным налогам');
      if (type === 'dd') add(f, true, 'Due diligence: проверка под сделку, объём зависит от периода и участков');
      if (type === 'express') add(f, false, 'Экспресс-аудит: ограниченный объём, ниже базовой ставки обязательного аудита не бывает');
      if (ind === 'build') add(f, true, 'Строительство: незавершённое производство и договоры подряда проверяем отдельно');
      if (ind === 'lease') add(f, true, 'Лизинг: учёт аренды по ФСБУ 25/2018 по каждому договору');
      if (ind === 'prod') add(f, true, 'Производство: себестоимость и запасы по ФСБУ 5/2019');
      if (term === 'fast') add(f, true, 'Сжатые сроки: увеличиваем команду на проекте');
      if (!f.length) add(f, false, 'Объём стандартный: базовая ставка');
      out.textContent = '';
      f.forEach(([ok, text]) => { const li = document.createElement('li'); li.className = ok === true ? 'yes' : ok === false ? 'no' : 'na'; li.textContent = text; out.appendChild(li); });
      const up = f.filter(x => x[0] === true).length;
      price.textContent = up ? 'от 40 000 ₽ + ' + up + (up === 1 ? ' фактор' : up < 5 ? ' фактора' : ' факторов') + ' сверху' : 'от 40 000 ₽';
      if (!reduce) restart(price, 'rslamflat .4s both');
    });
  }

  /* ——— Копирование телефона и почты ——— */
  $$('[data-copy]').forEach(btn => {
    const label = btn.textContent;
    let timer = 0;
    const done = msg => { btn.textContent = msg; clearTimeout(timer); timer = setTimeout(() => { btn.textContent = label; }, 1800); };
    const fallback = () => {
      const target = document.getElementById(btn.dataset.target);
      if (target && window.getSelection) {
        const sel = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(target);
        sel.removeAllRanges();
        sel.addRange(range);
      }
      done('Выделено, скопируйте');
    };
    btn.addEventListener('click', () => {
      try {
        const p = navigator.clipboard && navigator.clipboard.writeText(btn.dataset.copy);
        if (p && p.then) p.then(() => done('Скопировано'), fallback); else fallback();
      } catch (_) { fallback(); }
    });
  });

  /* ——— Заявка: демо-режим ——— */
  const lead = $('#leadForm');
  if (lead) {
    const nameEl = $('#f-name'), phoneEl = $('#f-phone'), msg = $('#leadMsg');
    lead.addEventListener('submit', e => {
      e.preventDefault();
      const badName = !nameEl.value.trim();
      const badPhone = phoneEl.value.replace(/\D/g, '').length < 10;
      nameEl.setAttribute('aria-invalid', String(badName));
      phoneEl.setAttribute('aria-invalid', String(badPhone));
      msg.hidden = false;
      if (badName || badPhone) {
        msg.textContent = 'Укажите имя и телефон. В номере должно быть не меньше 10 цифр.';
        (badName ? nameEl : phoneEl).focus();
        return;
      }
      msg.textContent = 'Это демо-макет — в рабочей версии заявка уйдёт менеджеру.';
    });
  }

  /* ——— Якоря: заголовок встаёт под парящей шапкой ——— */
  function offset() { const r = bar ? bar.getBoundingClientRect() : { bottom: 84 }; return r.bottom + 24; }
  function go(id, push) {
    const t = document.getElementById(id);
    if (!t) return false;
    const h = (t.tagName === 'SECTION' || t.tagName === 'FOOTER' || t.tagName === 'DIV') ? (t.querySelector('h1,h2') || t) : t;
    const y = h.getBoundingClientRect().top + window.pageYOffset - offset();
    window.scrollTo({ top: Math.max(0, y), behavior: reduce ? 'auto' : 'smooth' });
    if (push) { try { history.pushState(null, '', '#' + id); } catch (_) { /* ignore */ } }
    return true;
  }
  document.addEventListener('click', e => {
    const a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a || e.defaultPrevented) return;
    const id = a.getAttribute('href').slice(1);
    if (!id || !document.getElementById(id)) return;
    e.preventDefault();
    go(id, true);
  });
  if (location.hash.length > 1) setTimeout(() => go(location.hash.slice(1), false), 80);
})();
