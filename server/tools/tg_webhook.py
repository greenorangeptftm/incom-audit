#!/usr/bin/env python3
"""Webhook бота для кнопок под заявками.
  python3 server/tools/tg_webhook.py set https://incom-consult.ru/api/tg.php   — поставить (секрет создается и сохраняется в secrets.env)
  python3 server/tools/tg_webhook.py info                                       — проверить
  python3 server/tools/tg_webhook.py delete                                     — снять
  python3 server/tools/tg_webhook.py show-secret                                — показать секрет для config.local.php на сервере
Токен берется из TELEGRAM_BOT_TOKEN или ~/.config/incom-audit/secrets.env и на экран не выводится."""
import json, sys, secrets, pathlib, urllib.request, urllib.parse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import _secrets

SECRETS = pathlib.Path.home() / ".config" / "incom-audit" / "secrets.env"

def save(key, val):
    SECRETS.parent.mkdir(parents=True, exist_ok=True); SECRETS.parent.chmod(0o700)
    lines = [l for l in (SECRETS.read_text().splitlines() if SECRETS.is_file() else []) if not l.startswith(key + "=")]
    lines.append("%s=%s" % (key, val)); SECRETS.write_text("\n".join(lines) + "\n"); SECRETS.chmod(0o600)

def api(token, method, **params):
    data = urllib.parse.urlencode(params).encode() if params else None
    try:
        with urllib.request.urlopen("https://api.telegram.org/bot%s/%s" % (token, method), data=data, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8", "replace"))

cmd = sys.argv[1] if len(sys.argv) > 1 else "info"
token = _secrets.get("TELEGRAM_BOT_TOKEN") or sys.exit("Нет токена: sh server/tools/save-token.sh")
if cmd == "set":
    url = sys.argv[2] if len(sys.argv) > 2 else sys.exit("Укажите адрес: ... set https://домен/api/tg.php")
    secret = _secrets.get("TELEGRAM_WEBHOOK_SECRET") or secrets.token_urlsafe(32)
    save("TELEGRAM_WEBHOOK_SECRET", secret)
    r = api(token, "setWebhook", url=url, secret_token=secret, allowed_updates=json.dumps(["message", "callback_query"]), drop_pending_updates="true")
    print("setWebhook:", "ok" if r.get("ok") else r.get("description"))
    print("Секрет сохранен в", SECRETS, "— его же нужно вписать в telegram_webhook_secret на сервере (show-secret покажет)")
elif cmd == "delete":
    print("deleteWebhook:", api(token, "deleteWebhook").get("ok"))
elif cmd == "show-secret":
    print(_secrets.get("TELEGRAM_WEBHOOK_SECRET") or "секрет еще не создан: сначала set")
else:
    info = api(token, "getWebhookInfo").get("result", {})
    print(json.dumps({k: info.get(k) for k in ("url", "has_custom_certificate", "pending_update_count", "last_error_date", "last_error_message", "allowed_updates")}, ensure_ascii=False, indent=1))
