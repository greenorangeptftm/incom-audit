# Инком-Аудит — сайт (концепция «Сверка»)

Статический сайт аудиторской компании «Инком-Аудит». Собирается генератором из `src/` в `docs/`
(GitHub Pages публикует папку `docs`).

```bash
python3 -I src/build.py --theme sverka --out docs --site-url https://greenorangeptftm.github.io/incom-audit --noindex
```

- `src/pages/*.py` — тексты страниц (контракт в `src/CONTRACT.md`)
- `src/templates_sverka.py`, `src/assets-sverka/` — дизайн
- `src/WORDSTAT.md` — частотность запросов, под которые сделана структура

Пока это тестовая публикация: страницы закрыты от индексации (`--noindex`, `robots.txt`).
Для боевого домена: собрать с `--index` и своим `--site-url`.
