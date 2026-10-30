#!/bin/sh
# Безопасно сохраняет секрет в ~/.config/incom-audit/secrets.env (права 600, вне репозитория).
# Использование: sh server/tools/save-token.sh [ИМЯ_ПЕРЕМЕННОЙ]   (по умолчанию TELEGRAM_BOT_TOKEN)
KEY="${1:-TELEGRAM_BOT_TOKEN}"
DIR="$HOME/.config/incom-audit"; FILE="$DIR/secrets.env"
mkdir -p "$DIR" && chmod 700 "$DIR"
printf 'Вставьте значение %s и нажмите Enter (ввод скрыт): ' "$KEY"
stty -echo 2>/dev/null; IFS= read -r VAL; stty echo 2>/dev/null; echo
if [ -z "$VAL" ]; then echo "Пусто, ничего не сохранено"; exit 1; fi
touch "$FILE" && chmod 600 "$FILE"
grep -v "^$KEY=" "$FILE" > "$FILE.tmp" 2>/dev/null; printf '%s=%s\n' "$KEY" "$VAL" >> "$FILE.tmp"
mv "$FILE.tmp" "$FILE" && chmod 600 "$FILE"
unset VAL
echo "Сохранено: $KEY в $FILE (длина значения скрыта)"
