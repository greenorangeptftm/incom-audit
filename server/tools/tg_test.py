#!/usr/bin/env python3
"""Отправляет тестовое сообщение в чат: python3 server/tools/tg_test.py <chat_id>. Токен из TELEGRAM_BOT_TOKEN или secrets.env."""
import json, sys, urllib.request, urllib.parse, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import _secrets

if len(sys.argv) < 2:
    sys.exit("Укажите chat_id: python3 server/tools/tg_test.py -1001234567890")
token = _secrets.get("TELEGRAM_BOT_TOKEN") or sys.exit("Нет токена: sh server/tools/save-token.sh")
data = urllib.parse.urlencode({"chat_id": sys.argv[1], "text": "Проверка: сюда будут приходить заявки с сайта Инком-Аудит"}).encode()
try:
    with urllib.request.urlopen("https://api.telegram.org/bot%s/sendMessage" % token, data=data, timeout=15) as r:
        print("Отправлено" if json.load(r).get("ok") else "Telegram ответил без ok")
except urllib.error.HTTPError as e:
    print("Ошибка Telegram:", e.code, json.loads(e.read().decode("utf-8", "replace")).get("description"))
