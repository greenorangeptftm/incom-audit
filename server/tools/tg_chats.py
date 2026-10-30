#!/usr/bin/env python3
"""Показывает чаты, в которых бот видел сообщения, и их id. Сначала напишите боту «/start» в личке или добавьте его в группу
и отправьте туда любое сообщение. Токен берется из TELEGRAM_BOT_TOKEN или ~/.config/incom-audit/secrets.env, на экран не выводится."""
import json, sys, urllib.request, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import _secrets

token = _secrets.get("TELEGRAM_BOT_TOKEN")
if not token:
    sys.exit("Нет токена: sh server/tools/save-token.sh")
with urllib.request.urlopen("https://api.telegram.org/bot%s/getMe" % token, timeout=15) as r:
    me = json.load(r)["result"]
print("Бот: @%s (%s)" % (me.get("username"), me.get("first_name")))
with urllib.request.urlopen("https://api.telegram.org/bot%s/getUpdates" % token, timeout=15) as r:
    upd = json.load(r)["result"]
chats = {}
for u in upd:
    for k in ("message", "edited_message", "channel_post", "my_chat_member"):
        c = (u.get(k) or {}).get("chat")
        if c:
            chats[c["id"]] = c
if not chats:
    print("Бот еще не видел сообщений. Напишите ему /start или добавьте в группу и отправьте сообщение, затем запустите снова")
for cid, c in chats.items():
    print("chat_id=%s  тип=%s  %s" % (cid, c.get("type"), c.get("title") or ("@" + c["username"] if c.get("username") else c.get("first_name", ""))))
