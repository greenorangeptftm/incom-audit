/* Инком-Аудит — тема «Сверка». Один общий скрипт: шапка, пометки аудитора, ведомость, бланки, формы, якоря.
   Все блоки необязательны: скрипт ищет элементы и молчит, если их нет. Без библиотек, без canvas. */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  root.classList.add('js');
  var q = function (s, c) { return (c || d).querySelector(s); };
  var qa = function (s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); };
  var RM = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hasIO = 'IntersectionObserver' in window;
  var RW = parseFloat(getComputedStyle(d.body).paddingTop) || 0;   // «разбег» для iOS Safari 26, см. sverka.css (.rw)
  var sleep = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  var arm = function (el) { if (el) { el.classList.remove('is-on'); el.classList.add('is-armed'); } };
  var draw = function (el) { if (!el) return; if (!el.classList.contains('is-armed')) { el.classList.add('is-armed'); void el.getBoundingClientRect(); } el.classList.add('is-on'); };
  var drawSoon = function (el) { if (!el) return; arm(el); requestAnimationFrame(function () { requestAnimationFrame(function () { draw(el); }); }); };
  var inView = function (el) { var r = el.getBoundingClientRect(); return r.top < innerHeight && r.bottom > 0; };
  var clamp = function (v, a, b) { return Math.min(b, Math.max(a, v)); };
  var listen = function (mq, fn) { if (mq.addEventListener) mq.addEventListener('change', fn); else mq.addListener(fn); };

  /* ——— силуэты на первом экране: проявляются, когда картинка загрузилась ——— */
  var duo = q('.hero-duo');
  if (duo) {
    var duoIn = function () { requestAnimationFrame(function () { duo.classList.add('is-in'); }); };
    if (RM) duo.classList.add('is-in');
    else if (duo.complete && duo.naturalWidth) setTimeout(duoIn, 200);
    else { duo.addEventListener('load', function () { setTimeout(duoIn, 120); }); duo.addEventListener('error', function () { duo.remove(); }); }
  }

  /* ——— стеклянная шапка ——— */
  var lg = q('#lg'), bar = lg && q('.lg__bar', lg), links = lg && q('.lg__links', lg), lens = lg && q('.lg__lens', lg);
  var navLinks = links ? qa('a', links) : [];
  var current = navLinks.filter(function (a) { return a.getAttribute('aria-current') === 'page'; })[0] || null;
  function setHH() { if (bar) root.style.setProperty('--hh', Math.round(bar.getBoundingClientRect().bottom + 18) + 'px'); }
  function placeLens(a) {
    if (!lens) return;
    if (!a) { lens.style.opacity = '0'; return; }
    if (!lens.dataset.r) { lens.style.transition = 'none'; lens.dataset.r = '1'; setTimeout(function () { lens.style.transition = ''; }, 80); }
    lens.style.width = a.offsetWidth + 'px'; lens.style.setProperty('--x', a.offsetLeft + 'px'); lens.style.opacity = '1';
  }
  navLinks.forEach(function (a) {
    a.addEventListener('pointerenter', function () { placeLens(a); });
    a.addEventListener('focus', function () { placeLens(a); });
    a.addEventListener('blur', function () { placeLens(current); });
  });
  if (links) links.addEventListener('pointerleave', function () { placeLens(current); });
  var toneSecs = qa('[data-tone]').filter(function (s) { return s !== lg; });
  function updHeader() {
    if (!bar) return;
    var pr = bar.getBoundingClientRect(), y = pr.top + pr.height / 2;
    for (var i = 0; i < toneSecs.length; i++) {
      var r = toneSecs[i].getBoundingClientRect();
      if (r.top <= y && r.bottom > y) { if (lg.dataset.tone !== toneSecs[i].dataset.tone) lg.dataset.tone = toneSecs[i].dataset.tone; break; }
    }
    lg.classList.toggle('is-scrolled', window.scrollY > 40 + RW);
  }
  var burger = lg && q('.lg__burger', lg), sheetNav = q('#lg-sheet');
  function setMenu(o) {
    if (!burger || !sheetNav) return;
    lg.classList.toggle('is-open', o); burger.setAttribute('aria-expanded', String(o));
    burger.setAttribute('aria-label', o ? 'Закрыть меню' : 'Открыть меню'); sheetNav.hidden = !o;
  }
  if (burger && sheetNav) {
    burger.addEventListener('click', function () { setMenu(!lg.classList.contains('is-open')); });
    sheetNav.addEventListener('click', function (e) { if (e.target.closest('a')) setMenu(false); });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && lg.classList.contains('is-open')) { setMenu(false); burger.focus(); } });
    d.addEventListener('click', function (e) { if (lg.classList.contains('is-open') && !lg.contains(e.target)) setMenu(false); });
    listen(window.matchMedia('(min-width: 1081px)'), function (e) { if (e.matches) setMenu(false); });
  }

  /* ——— подчеркивание в заголовке первого экрана ——— */
  var uline = q('#uline');
  if (uline && !RM) { arm(uline); setTimeout(function () { draw(uline); }, (d.fonts && d.fonts.status !== 'loaded') ? 900 : 500); }

  /* ——— пометки рисуются, когда группа попадает в кадр; заголовки всплывают ——— */
  if (!RM && hasIO) {
    var dvIO = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (!e.isIntersecting) return; dvIO.unobserve(e.target); qa('.mk', e.target).forEach(function (m, k) { setTimeout(function () { draw(m); }, 120 + k * 140); }); });
    }, { threshold: 0.3 });
    qa('[data-dv]').forEach(function (g) { if (inView(g)) return; qa('.mk', g).forEach(arm); dvIO.observe(g); });
    var rIO = new IntersectionObserver(function (es) { es.forEach(function (e) { if (!e.isIntersecting) return; rIO.unobserve(e.target); e.target.classList.add('rise-in'); }); }, { rootMargin: '0px 0px 6% 0px' });
    qa('[data-rise]').forEach(function (el) { if (!inView(el)) rIO.observe(el); });
  }

  /* ——— ведомость: проверка строка за строкой (только главная) ——— */
  var stage = q('#stage');
  if (stage) {
    var wrap = q('#ledgerWrap'), table = q('#ledger'), scan = q('#scan');
    var rows = qa('tbody tr', table), foot = q('#ledgerFoot'), flag = q('tr[data-flag]', table);
    var ell = q('#flagEll'), n1 = q('#note1'), n2 = q('#note2'), n1a = q('#note1Arrow'), n2t = q('#note2Tick');
    var footMk = q('.mk', foot), stat = q('#sheetStatus'), statT = q('#statusText'), statMk = q('.mk', stat);
    var rowMarks = rows.map(function (r) { return q('.tk .mk', r); });
    var seqEls = rowMarks.concat([ell, n1, n2, n1a, n2t, footMk, statMk]);
    var sideMQ = window.matchMedia('(min-width: 640px)');
    var visibleRows = function () { return rows.filter(function (r) { return r.offsetParent !== null; }); };
    var yOf = function (el) { var y = 0, n = el; while (n && n !== wrap) { y += n.offsetTop; n = n.offsetParent; } return y; };
    function placeNotes() {
      if (!sideMQ.matches) { n1.style.top = ''; n2.style.top = ''; return; }
      var mid = yOf(flag) + flag.offsetHeight / 2, t1 = Math.max(4, mid - 15);
      n1.style.top = t1 + 'px'; n2.style.top = (t1 + n1.offsetHeight + 18) + 'px';
    }
    var scanTo = function (el) { scan.style.height = el.offsetHeight + 'px'; scan.style.transform = 'translateY(' + yOf(el) + 'px)'; };
    var runId = 0;
    async function play() {
      var id = ++runId, live = function () { return id === runId; };
      var vr = visibleRows();
      seqEls.forEach(arm); stat.classList.add('is-pending'); statT.textContent = 'в работе'; scan.classList.remove('is-on');
      await sleep(380); if (!live()) return;
      scanTo(vr[0]); void scan.getBoundingClientRect(); scan.classList.add('is-on');
      for (var i = 0; i < vr.length; i++) {
        var r = vr[i]; scanTo(r);
        await sleep(290); if (!live()) return;
        if (r === flag) {
          draw(ell); await sleep(560); if (!live()) return;
          draw(n1a); await sleep(220); if (!live()) return;
          draw(n1); await sleep(1400); if (!live()) return;
        } else { draw(rowMarks[rows.indexOf(r)]); await sleep(160); if (!live()) return; }
      }
      scanTo(foot); await sleep(320); if (!live()) return;
      draw(footMk); await sleep(480); if (!live()) return;
      scan.classList.remove('is-on');
      draw(n2); await sleep(950); if (!live()) return;
      draw(n2t); draw(rowMarks[rows.indexOf(flag)]); await sleep(420); if (!live()) return;
      stat.classList.remove('is-pending'); statT.textContent = 'проверено'; draw(statMk);
    }
    placeNotes();
    window.addEventListener('resize', placeNotes);
    if (d.fonts && d.fonts.ready) d.fonts.ready.then(placeNotes);
    listen(sideMQ, placeNotes);
    var replayBtn = q('#replay');
    if (!RM) {
      if (hasIO && !inView(stage)) {
        seqEls.forEach(arm); stat.classList.add('is-pending'); statT.textContent = 'в работе';
        var sIO = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { sIO.disconnect(); play(); } }); }, { threshold: 0.35 });
        sIO.observe(stage);
      } else { play(); }
      if (replayBtn) replayBtn.addEventListener('click', play);
    } else if (replayBtn) { replayBtn.hidden = true; }
  }

  /* ——— отрасли: пометки на фотографиях ——— */
  var annCards = qa('[data-ann]');
  if (annCards.length && !RM && hasIO) {
    var annotate = function (card) {
      draw(q('.ann', card)); setTimeout(function () { draw(q('.ann-note', card)); }, 520);
      qa('.ticks .mk', card).forEach(function (m, k) { setTimeout(function () { draw(m); }, 900 + k * 180); });
    };
    var aIO = new IntersectionObserver(function (es) { es.forEach(function (en) { if (!en.isIntersecting) return; aIO.unobserve(en.target); annotate(en.target); }); }, { threshold: 0.45 });
    annCards.forEach(function (c) { if (inView(c) && c.getBoundingClientRect().bottom < innerHeight) return; arm(q('.ann', c)); arm(q('.ann-note', c)); qa('.ticks .mk', c).forEach(arm); aIO.observe(c); });
  }

  /* ——— рабочий документ: критерии обязательного аудита (оценка меняется по мере ввода) ——— */
  var cf = q('#checkForm');
  if (cf) {
    var fInc = q('#inc'), fAst = q('#ast'), fAo = q('#ao'), fDev = q('#dev'), fSec = q('#secu');
    var vEl = q('#verdict'), vWhy = q('#verdictWhy'), vCta = q('#checkCtaT'), vActs = q('#checkActs');
    var num = function (v) { v = String(v || '').replace(/[\s ]/g, '').replace(',', '.'); if (!v) return null; var n = parseFloat(v); return isFinite(n) ? n : null; };
    var setSt = function (key, state) {
      var st = q('#st-' + key); if (!st) return;
      var prev = st.getAttribute('data-state'); st.setAttribute('data-state', state);
      var mk = q('.mk', st);
      if (state === 'yes') { if (prev !== 'yes') drawSoon(mk); } else { arm(mk); }
    };
    var evalCheck = function () {
      var i = num(fInc.value), a = num(fAst.value), R = [];
      setSt('inc', i === null ? 'empty' : (i > 800 ? 'yes' : 'no')); if (i !== null && i > 800) R.push('доходы за 2025 год больше 800 млн ₽');
      setSt('ast', a === null ? 'empty' : (a > 400 ? 'yes' : 'no')); if (a !== null && a > 400) R.push('активы на 31.12.2025 больше 400 млн ₽');
      setSt('ao', fAo.checked ? 'yes' : 'no'); if (fAo.checked) R.push('компания — акционерное общество (как правило, аудит обязателен, уточним на консультации)');
      setSt('dev', fDev.checked ? 'yes' : 'no'); if (fDev.checked) R.push('компания — застройщик по 214-ФЗ');
      setSt('sec', fSec.checked ? 'yes' : 'no'); if (fSec.checked) R.push('ценные бумаги на торгах или консолидированная отчетность');
      var mode = R.length ? 'yes' : (i === null || a === null) ? 'empty' : 'no';
      vEl.setAttribute('data-v', mode); if (vActs) vActs.setAttribute('data-v', mode); vCta.textContent = 'Отправить заявку';
      if (mode === 'yes') { vEl.textContent = 'Скорее всего, обязательный аудит нужен'; vWhy.textContent = 'Основание: ' + R.join('; '); }
      else if (mode === 'empty') { vEl.textContent = 'Впишите доходы и активы'; vWhy.textContent = 'Для оценки нужны оба показателя за 2025 год, в миллионах рублей'; }
      else { vEl.textContent = 'Компания не подлежит обязательному аудиту'; vWhy.textContent = 'Инициативный и налоговый аудит поможет собственнику избежать возможных рисков'; }
    };
    cf.addEventListener('input', evalCheck); cf.addEventListener('change', evalCheck);
    cf.addEventListener('submit', function (e) { e.preventDefault(); });
    evalCheck();
  }

  /* ——— калькулятор: только факторы, без выдуманных цифр ——— */
  var calc = q('#calcForm');
  if (calc) {
    var cnum = function (v) { var s = String(v).replace(/[\s ]/g, '').replace(',', '.'); var n = Number(s); return s && isFinite(n) && n >= 0 ? n : null; };
    var out = q('#calcFactors'), price = q('#calcPrice');
    calc.addEventListener('submit', function (e) {
      e.preventDefault();
      var rev = cnum(q('#c-rev').value), ast = cnum(q('#c-ast').value);
      var ent = Number(q('#c-ent').value), type = q('#c-type').value, ind = q('#c-ind').value, term = q('#c-term').value;
      var f = [], add = function (ok, text) { f.push([ok, text]); };
      if (rev === null && ast === null) add(null, 'Укажите выручку и активы хотя бы примерно, тогда оценка будет точнее');
      if (rev !== null) add(rev > 800, rev > 800 ? 'Выручка выше 800 млн ₽: больше операций и документов для выборки' : 'Выручка до 800 млн ₽: обычный объем выборки');
      if (ast !== null) add(ast > 400, ast > 400 ? 'Активы выше 400 млн ₽: больше участков учета для проверки' : 'Активы до 400 млн ₽: обычный объем проверки');
      if (ent > 1) add(true, 'Несколько юридических лиц: отдельное заключение по каждому');
      if (type === 'dev') add(true, 'Застройщик по 214-ФЗ: проверяем раздельный учет по объектам и эскроу-счета');
      if (type === 'ifrs') add(true, 'Отчетность по МСФО: объем зависит от трансформации и консолидации');
      if (type === 'tax') add(true, 'Налоговый аудит: сплошная проверка первички по выбранным налогам');
      if (type === 'express') add(false, 'Экспресс-аудит: ограниченный объем, цена ниже полного аудита');
      if (ind === 'build') add(true, 'Строительство: незавершенное производство и договоры подряда проверяем отдельно');
      if (ind === 'lease') add(true, 'Лизинг: учет аренды по ФСБУ 25/2018 по каждому договору');
      if (ind === 'prod') add(true, 'Производство: себестоимость и запасы по ФСБУ 5/2019');
      if (term === 'fast') add(true, 'Сжатые сроки: увеличиваем команду на проекте');
      if (!f.length) add(false, 'Объем стандартный');
      out.textContent = '';
      f.forEach(function (x) { var li = d.createElement('li'); li.className = x[0] === true ? 'yes' : x[0] === false ? 'no' : 'na'; li.textContent = x[1]; out.appendChild(li); });
      var up = f.filter(function (x) { return x[0] === true; }).length;
      price.textContent = up ? 'выше стандартного: ' + up + (up === 1 ? ' фактор' : up < 5 ? ' фактора' : ' факторов') : 'стандартный';
    });
  }

  /* ——— порядок работы на главной: линия заполняется при прокрутке ——— */
  var proc = q('#proc'), fill = q('#fill'), steps = proc ? qa('.step', proc) : [], vertMQ = window.matchMedia('(max-width: 1000px)');
  function progress() {
    if (!proc) return;
    var r = proc.getBoundingClientRect(), vh = innerHeight, p;
    if (RM) p = 1;
    else if (vertMQ.matches) p = (vh * .62 - r.top) / Math.max(1, r.height);
    else p = (vh * .85 - r.top) / Math.max(1, r.height + vh * .35);
    p = clamp(p, 0, 1);
    fill.style.transform = vertMQ.matches ? 'scaleY(' + p.toFixed(4) + ')' : 'scaleX(' + p.toFixed(4) + ')';
    var L = steps.length;
    steps.forEach(function (s, k) {
      var done = vertMQ.matches ? (q('.node', s).getBoundingClientRect().top + 22 <= vh * .62) : (p >= k / (L - 1) - .001);
      if (done && !s.classList.contains('is-done')) { s.classList.add('is-done'); if (!RM) drawSoon(q('.node .mk', s)); }
      else if (!done && s.classList.contains('is-done')) s.classList.remove('is-done');
    });
  }

  /* ——— этапы в документе: вертикальная линия ——— */
  var docSteps = qa('[data-steps]');
  function stepsFill() {
    docSteps.forEach(function (ol) {
      var r = ol.getBoundingClientRect(), vh = innerHeight;
      var p = RM ? 1 : clamp((vh * .66 - r.top) / Math.max(1, r.height), 0, 1);
      ol.style.setProperty('--p', p.toFixed(3));
      qa('li', ol).forEach(function (li) { li.classList.toggle('is-done', RM || li.getBoundingClientRect().top + 20 <= vh * .66); });
    });
  }

  /* ——— оглавление: подсветка текущего раздела ——— */
  var tocLinks = qa('.toc a');
  var tocTargets = tocLinks.map(function (a) { return d.getElementById(a.getAttribute('href').slice(1)); });
  function updToc() {
    if (!tocLinks.length) return;
    var probe = (parseFloat(getComputedStyle(root).getPropertyValue('--hh')) || 96) + 40, cur = -1;
    tocTargets.forEach(function (t, i) { if (t && t.getBoundingClientRect().top <= probe) cur = i; });
    tocLinks.forEach(function (a, i) { a.classList.toggle('is-on', i === cur); });
  }

  /* ——— нижняя панель на телефонах: прячется у формы, подвала и пока на экране кнопки первого экрана
     (иначе «Позвонить / Заявка» дублируют кнопки hero). Состояние храним по каждому элементу, а не счётчиком ——— */
  var mbar = q('#mbar');
  if (mbar && hasIO) {
    var mWatch = qa('#zayavka, .ftr, .hero-cta, .phero-cta');
    var mIO = new IntersectionObserver(function (es) {
      es.forEach(function (e) { e.target._mbOn = e.isIntersecting; });
      mbar.classList.toggle('is-hidden', Array.prototype.some.call(mWatch, function (el) { return el._mbOn; }));
    }, { threshold: 0.05 });
    Array.prototype.forEach.call(mWatch, function (el) { mIO.observe(el); });
  }

  /* ——— один цикл прокрутки на все наблюдатели ——— */
  var ticking = false;
  function onScroll() { if (ticking) return; ticking = true; requestAnimationFrame(function () { ticking = false; updHeader(); progress(); stepsFill(); updToc(); }); }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', function () { setHH(); onScroll(); });
  setHH(); updHeader(); progress(); stepsFill(); updToc();
  if (d.fonts && d.fonts.ready) d.fonts.ready.then(function () { setHH(); onScroll(); });
  window.addEventListener('load', onScroll);

  /* ——— копирование телефона, почты и адреса: подпись и иконка меняются без скачка ширины ——— */
  var live = d.createElement('span'); live.className = 'sr'; live.setAttribute('aria-live', 'polite'); d.body.appendChild(live);
  qa('[data-copy]').forEach(function (btn) {
    var timer = 0;
    var done = function (ok) {
      btn.classList.add('is-done'); live.textContent = ok ? 'Скопировано' : 'Текст выделен, нажмите Ctrl+C';
      clearTimeout(timer); timer = setTimeout(function () { btn.classList.remove('is-done'); live.textContent = ''; }, 2200);
    };
    var fallback = function () {
      var t = d.getElementById(btn.dataset.target);
      if (t && window.getSelection) { var s = window.getSelection(), rg = d.createRange(); rg.selectNodeContents(t); s.removeAllRanges(); s.addRange(rg); }
      done(false);
    };
    btn.addEventListener('click', function () {
      try { var p = navigator.clipboard && navigator.clipboard.writeText(btn.dataset.copy); if (p && p.then) p.then(function () { done(true); }, fallback); else fallback(); }
      catch (err) { fallback(); }
    });
  });

  /* ——— вопросы и ответы, оглавление на телефоне: раскрываются и сворачиваются плавно ——— */
  qa('.faq details, details.toc-m').forEach(function (det) {
    var sum = q('summary', det), body = sum && sum.nextElementSibling;
    if (!sum || !body || RM || !det.animate) return;
    var anim = null, stopBody = function () { body.getAnimations().forEach(function (a) { a.cancel(); }); };
    sum.addEventListener('click', function (e) {
      e.preventDefault();
      var h0 = det.offsetHeight;   /* текущая высота, даже если анимация ещё идёт */
      if (anim) anim.cancel();
      stopBody();
      det.style.overflow = 'hidden';
      if (det.open && !det.classList.contains('is-closing')) {
        det.classList.add('is-closing');
        anim = det.animate([{ height: h0 + 'px' }, { height: sum.offsetHeight + 'px' }], { duration: 280, easing: 'cubic-bezier(.4,0,.2,1)' });
        body.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 160, easing: 'ease-out', fill: 'forwards' });
        anim.onfinish = function () { det.open = false; det.classList.remove('is-closing'); det.style.overflow = ''; anim = null; stopBody(); };
      } else {
        det.classList.remove('is-closing'); det.open = true;
        anim = det.animate([{ height: h0 + 'px' }, { height: det.scrollHeight + 'px' }], { duration: 340, easing: 'cubic-bezier(.2,.8,.2,1)' });
        body.animate([{ opacity: 0, transform: 'translateY(-6px)' }, { opacity: 1, transform: 'none' }], { duration: 300, delay: 70, easing: 'ease-out', fill: 'backwards' });
        anim.onfinish = function () { det.style.overflow = ''; anim = null; };
      }
    });
  });

  /* ——— заявка: обязательные поля, счетчик символов; бланк внизу страницы и в окне ——— */
  qa('form[data-lead]').forEach(function (lead) {
    var msg = q('.form-msg', lead), msgT = q('.form-msg__t', lead), msgEl = lead.elements.message, cnt = q('[data-count]', lead);
    var req = [['name', function (v) { return !!v.trim(); }], ['phone', function (v) { return v.replace(/\D/g, '').length >= 10; }],
               ['email', function (v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim()); }], ['company', function (v) { return !!v.trim(); }],
               ['message', function (v) { return !!v.trim(); }]];
    if (msgEl && cnt) {
      var lim = Number(msgEl.getAttribute('maxlength')) || 500;
      var upd = function () { if (msgEl.value.length > lim) msgEl.value = msgEl.value.slice(0, lim); cnt.textContent = msgEl.value.length + ' / ' + lim; };
      msgEl.addEventListener('input', upd); upd();
    }
    if (lead.elements.consent) lead.elements.consent.addEventListener('change', function () { if (this.checked) this.removeAttribute('aria-invalid'); });
    lead.addEventListener('submit', function (e) {
      e.preventDefault();
      var first = null;
      req.forEach(function (r) { var el = lead.elements[r[0]]; if (!el) return; var ok = r[1](el.value); el.setAttribute('aria-invalid', String(!ok)); if (!ok && !first) first = el; });
      var cb = lead.elements.consent, cbOk = !cb || cb.checked;
      if (cb) cb.setAttribute('aria-invalid', String(!cbOk));
      msg.hidden = false;
      if (first) { msg.classList.add('is-warn'); msgT.textContent = 'Заполните поля со звездочкой: имя, телефон, e-mail, компания и сообщение'; first.focus(); return; }
      if (!cbOk) { msg.classList.add('is-warn'); msgT.textContent = 'Чтобы отправить заявку, подтвердите согласие на обработку персональных данных'; cb.focus(); return; }
      msg.classList.remove('is-warn'); msgT.textContent = 'Тестовая версия сайта: заявка пока не отправляется. Позвоните нам по телефону выше';
      if (!RM) drawSoon(q('.mk', msg));
    });
  });

  /* ——— всплывающее окно заявки: «Узнать стоимость» и «Оставить заявку» открывают его вместо прокрутки к форме ——— */
  var modal = q('#modal'), openModal = null;
  if (modal && typeof modal.showModal === 'function') {
    var panel = q('.modal__panel', modal), lastFocus = null, closing = false, deskMQ = window.matchMedia('(min-width: 901px)');
    openModal = function (trigger) {
      if (modal.open) return;
      lastFocus = trigger || d.activeElement;
      root.style.setProperty('--sbw', Math.max(0, window.innerWidth - root.clientWidth) + 'px');
      root.classList.add('has-modal');
      modal.showModal();
      panel.scrollTop = 0;
      if (RM) { modal.classList.add('is-in'); } else { requestAnimationFrame(function () { requestAnimationFrame(function () { modal.classList.add('is-in'); }); }); }
      if (deskMQ.matches) setTimeout(function () { var f = q('input', modal); if (f && modal.open) f.focus({ preventScroll: true }); }, RM ? 0 : 420);
    };
    var closeModal = function () {
      if (!modal.open || closing) return;
      closing = true; modal.classList.remove('is-in');
      var done = function () {
        if (!closing) return; closing = false; modal.close(); root.classList.remove('has-modal'); root.style.removeProperty('--sbw');
        if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
      };
      if (RM) { done(); return; }
      var t = setTimeout(done, 450);
      panel.addEventListener('transitionend', function h(e) { if (e.target !== panel) return; panel.removeEventListener('transitionend', h); clearTimeout(t); done(); });
    };
    modal.addEventListener('cancel', function (e) { e.preventDefault(); closeModal(); });
    modal.addEventListener('click', function (e) { if (e.target === modal) closeModal(); });
    q('.modal__x', modal).addEventListener('click', closeModal);
  }

  /* ——— якоря: заголовок встает под парящей шапкой ——— */
  function offset() { var r = bar ? bar.getBoundingClientRect() : { bottom: 84 }; return r.bottom + 24; }
  var goTimer = 0;
  function targetY(id) {
    var t = d.getElementById(id); if (!t) return null;
    var h = (t.tagName === 'SECTION' || t.tagName === 'FOOTER' || t.tagName === 'DIV') ? (t.querySelector('h1,h2') || t) : t;
    return Math.max(0, h.getBoundingClientRect().top + window.pageYOffset - offset());
  }
  function go(id, push) {
    var y = targetY(id); if (y === null) return false;
    window.scrollTo({ top: y, behavior: RM ? 'auto' : 'smooth' });
    /* плавная прокрутка иногда промахивается из-за сдвига макета — доводим так же плавно, когда она закончится */
    clearTimeout(goTimer);
    goTimer = setTimeout(function () { var y2 = targetY(id); if (y2 !== null && Math.abs(window.pageYOffset - y2) > 24) window.scrollTo({ top: y2, behavior: RM ? 'auto' : 'smooth' }); }, RM ? 60 : 1000);
    if (push) { try { history.pushState(null, '', '#' + id); } catch (err) { /* ignore */ } }
    return true;
  }
  d.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"], a[href$="/#zayavka"]');
    if (!a || e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey) return;
    var id = a.getAttribute('href').split('#')[1];
    if (id === 'zayavka' && openModal) { e.preventDefault(); openModal(a); return; }
    if (!id || !d.getElementById(id) || a.getAttribute('href').charAt(0) !== '#') return;
    e.preventDefault(); go(id, true);
  });
  if (location.hash.length > 1) setTimeout(function () { go(location.hash.slice(1), false); }, 80);

  /* ——— iOS Safari 26: в самой верхней точке (scrollY = 0) область статус-бара заливается сплошным цветом фона страницы,
     а на прокрученной странице сквозь стекло видно саму страницу. На главной для телефонов body получает верхний
     отступ RW (sverka.css), и страница при открытии сразу стоит на нем: картинка та же, что без отступа, но Safari считает
     страницу прокрученной и показывает фото под часами с первого кадра. Если страницу оттянули в самый верх,
     мягко возвращаем ее на отступ ——— */
  if (RW > 0 && location.hash.length < 2) {
    var rwT, toRunway = function (smooth) {
      if (d.documentElement.scrollHeight > window.innerHeight + RW && window.scrollY < RW) window.scrollTo({ top: RW, left: 0, behavior: (smooth && !RM) ? 'smooth' : 'instant' });
    };
    toRunway(false);
    window.addEventListener('load', function () { toRunway(false); });
    window.addEventListener('pageshow', function () { toRunway(false); });
    window.addEventListener('scroll', function () { clearTimeout(rwT); rwT = setTimeout(function () { if (window.scrollY < RW / 2) toRunway(true); }, 400); }, { passive: true });
  }
})();
