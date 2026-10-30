"""Чтение секретов для локальных проверок: переменные окружения или ~/.config/incom-audit/secrets.env. Значения не печатаем."""
import os, pathlib

def get(key):
    v = os.environ.get(key)
    if v:
        return v
    f = pathlib.Path.home() / ".config" / "incom-audit" / "secrets.env"
    if f.is_file():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip()
    return ""
