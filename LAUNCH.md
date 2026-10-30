# Выкладка на домен: инструкция

Сайт статический, собирается `src/build.py` (Python 3, нужен Pillow для WebP), публикуется как папка `docs/`.
Обработчик заявок — папка `server/` (PHP 8, без зависимостей). Предрелизный аудит пройден 30.10.2026
(валидный HTML, ссылки и картинки без ошибок, консоль чистая, Lighthouse 84–97).

## Что известно о хостинге
- Домен **incom-consult.ru**: DNS и хостинг Jino (ns*.jino.ru, Apache, PHP 8.3), там же старый сайт на WordPress.
- Почта домена тоже на Jino (MX `mail.incom-consult.ru`, SPF `redirect=_spf.jino.ru`). Ящик для заявок: **help@incom-consult.ru**.
- Старый сайт: все 68 адресов из его `sitemap_index.xml` учтены — в `docs/.htaccess` стоят 301 на новые страницы,
  плюс на каждый старый адрес есть HTML-заглушка с мгновенной переадресацией (на случай, если `.htaccess` не сработает).

## 1. Сборка под боевой домен
```
python3 src/build.py --theme sverka --out docs --site-url https://incom-consult.ru --index --form-endpoint /api/send.php
```
- `--index` снимает `noindex` со страниц и пишет открытый `robots.txt`.
- `--form-endpoint /api/send.php` включает отправку формы (без флага форма в тестовом режиме и просит позвонить).
- Все canonical, og:url, sitemap, JSON-LD и `.htaccess` берут адрес из `--site-url`.
- `/info/` и `/policy/` закрыты от поиска по просьбе клиента и в sitemap не входят.
- Проверка собранного: `python3 src/tools/site_audit.py docs https://incom-consult.ru --external` (должно остаться только
  про длину title/description, это осознанно).

## 2. Размещение на Jino (вместо WordPress)
1. Сделать резервную копию старого сайта и его базы.
2. Очистить корень сайта и загрузить туда содержимое `docs/` (включая `.htaccess`, `.nojekyll` не нужен, но не мешает).
3. Создать в корне папку `api/` и загрузить в нее содержимое `server/` (без `tools/`): `send.php`, `tg.php`, `lib.php`,
   `config.php`, `.htaccess`. Рядом создать `config.local.php` по образцу `config.local.example.php` (его самого на сервер
   не класть). Лучше: вынести `config.local.php` выше корня сайта и поправить путь `require` в `config.php`.
4. HTTPS: включить сертификат Let's Encrypt в панели Jino. `.htaccess` сам переводит на https и адрес без www;
   если получится цикл переадресации (прокси хостинга), заменить в нем условие `%{HTTPS} !=on`
   на `%{HTTP:X-Forwarded-Proto} !https`.
5. Проверить: главная, любая внутренняя, несуществующий адрес (своя 404 со стилями), старый адрес
   `https://incom-consult.ru/contacts/` → 301 на `/kontakty/`, `robots.txt`, `sitemap.xml`.

Альтернатива (GitHub Pages с привязкой домена): файл `CNAME` в `src/assets-sverka/_root/`, A-записи
185.199.108.153/.109.153/.110.153/.111.153 и CNAME `www` → `greenorangeptftm.github.io`, «Enforce HTTPS» в настройках
репозитория. Тогда обработчик формы нужно разместить на Jino отдельно и указать полный адрес в `--form-endpoint`,
а в `config.local.php` добавить `allowed_origins`.

## 3. Форма заявки: почта + Telegram
Обработчик `server/send.php` принимает JSON с сайта, проверяет поля (ловушка для роботов, лимит 5 заявок с IP за 10 минут),
отправляет заявку **в Telegram** (с кнопкой «Обработано») **и на почту**. Заявка принята, если дошел хотя бы один канал.
Каждой заявке присваивается короткий номер, он есть и в Telegram, и в теме письма.

`config.local.php` (значения на сервере, в git их нет):
- `telegram_token` — токен бота от @BotFather.
- `telegram_chat_id` = `-1004342603934` (группа для заявок, передана 30.10.2026). Бот должен быть добавлен в эту группу.
  Если чат поменяется: отправить боту в группе `/id` (после установки webhook) или `python3 server/tools/tg_chats.py` (до нее).
- `telegram_webhook_secret` — секрет для кнопок (см. ниже).
- `mail_to` = `help@incom-consult.ru`; `mail_from` — ящик на домене (можно тот же `help@`, можно завести `site@`).
  Без `smtp` письмо уходит через `mail()` хостинга, этого на Jino достаточно; при проблемах с доставкой заполнить `smtp`
  (сервер исходящей почты Jino — смотреть в панели, обычно `smtp.jino.ru`, порт 465, SSL, логин = адрес ящика).
- `log_file` — путь к журналу вне корня сайта (по желанию).
- Для проверки без реальной отправки: `'dry_run' => true`.

**Кнопки в Telegram.** Под каждой заявкой кнопка «✅ Обработано». Нажатие присылает Telegram на `api/tg.php`:
сообщение редактируется (в заголовке статус, имя и ник сотрудника, время), кнопка меняется на «↩️ Вернуть в работу».
Для этого нужен webhook с секретом:
```
sh server/tools/save-token.sh TELEGRAM_BOT_TOKEN            # токен сохраняется в ~/.config/incom-audit/secrets.env (600); в чаты и git не вставлять
python3 server/tools/tg_webhook.py set https://incom-consult.ru/api/tg.php
python3 server/tools/tg_webhook.py show-secret               # это значение → telegram_webhook_secret в config.local.php
python3 server/tools/tg_webhook.py info                      # проверка: url стоит, last_error пустой
```
Порядок: сначала выложить `api/`, потом ставить webhook. Проверка руками: отправить заявку с сайта, увидеть сообщение
в чате и письмо на help@, нажать кнопку, убедиться, что сообщение переписалось с именем нажавшего.

Проверка обработчика с сервера (ответ должен быть `{"ok":true,...}`):
```
curl -s -H 'Content-Type: application/json' -d '{"name":"Тест","phone":"+79160000000","email":"t@example.com","company":"ООО","message":"проверка","task":"Другое","consent":"yes","elapsed":9000}' https://incom-consult.ru/api/send.php
```

## 4. Поисковики и аналитика
- Яндекс.Вебмастер и Google Search Console: подтвердить сайт, отправить `https://incom-consult.ru/sitemap.xml`.
  Место для `<meta name="yandex-verification">` помечено комментарием в `<head>` (функция `base()` в `src/templates_sverka.py`).
- Яндекс.Метрика: код счетчика вставить перед `</head>` там же. Если ставится счетчик, политика обработки данных
  должна упоминать cookies и Метрику (текст согласовать с клиентом).

## 5. Тексты (решает клиент, технически не блокирует)
- Раскрытие информации за последний год (страница `/info/`), юридическая проверка `/policy/`.
- Заголовки длиннее 60 и описания длиннее 160 знаков оставлены сознательно: ключевые слова в начале, режется только хвост.
