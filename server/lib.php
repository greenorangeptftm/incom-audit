<?php
/* Инком-Аудит: общее для send.php и tg.php — вызовы Telegram Bot API и вид заявки в чате. */
declare(strict_types=1);

function tg_api(string $token, string $method, array $params): ?array
{
    $ch = curl_init('https://api.telegram.org/bot' . $token . '/' . $method);
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => http_build_query($params),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 10,
        CURLOPT_CONNECTTIMEOUT => 5,
    ]);
    $res = curl_exec($ch);
    $code = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    $j = $res === false ? null : json_decode((string) $res, true);
    if (!is_array($j) || empty($j['ok'])) {
        error_log('incom tg ' . $method . ' -> http ' . $code . ' ' . (is_array($j) ? ($j['description'] ?? '') : 'no response'));
        return null;
    }
    return is_array($j['result'] ?? null) ? $j['result'] : [];
}

function h(string $s): string
{
    return htmlspecialchars($s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

const LEAD_LABELS = ['Имя', 'Телефон', 'E-mail', 'Компания', 'Услуга', 'Сообщение'];

/* Заголовок сообщения по состоянию: new / work / done. $who и $when — кто и когда нажал кнопку. */
function lead_header(string $state, string $who, string $when, string $id): string
{
    $tail = $id !== '' ? '   <code>№' . h($id) . '</code>' : '';
    if ($state === 'done') {
        return '✅ <b>Обработано</b> — ' . h($who) . ', ' . h($when) . $tail;
    }
    if ($state === 'work') {
        return '🔄 <b>В работе</b> — ' . h($who) . ', ' . h($when) . $tail;
    }
    return '🆕 <b>Новая заявка с сайта</b>' . $tail;
}

/* Тело: строки «Поле: значение» в HTML с жирными подписями. $body — обычный текст. */
function lead_body_html(string $body): string
{
    $re = '/^(' . implode('|', array_map('preg_quote', LEAD_LABELS)) . '): /u';
    $out = [];
    foreach (explode("\n", $body) as $line) {
        $out[] = preg_replace_callback($re, static fn($m) => '<b>' . h($m[1]) . ':</b> ', h($line)) ?? h($line);
    }
    return implode("\n", $out);
}

function lead_text(string $state, string $who, string $when, string $id, string $body): string
{
    return lead_header($state, $who, $when, $id) . "\n\n" . lead_body_html($body);
}

function lead_keyboard(string $state): string
{
    $row = $state === 'done'
        ? [['text' => '↩️ Вернуть в работу', 'callback_data' => 'undo']]
        : [['text' => '✅ Обработано', 'callback_data' => 'done']];
    return (string) json_encode(['inline_keyboard' => [$row]], JSON_UNESCAPED_UNICODE);
}

/* Разбор текста сообщения из Telegram (без разметки): заголовок и тело заявки. */
function lead_parse(string $plain): array
{
    $lines = explode("\n", str_replace("\r", '', $plain));
    $header = array_shift($lines) ?? '';
    $id = preg_match('/№(\S+)/u', $header, $m) ? $m[1] : '';
    while ($lines && trim($lines[0]) === '') {
        array_shift($lines);
    }
    while ($lines && trim(end($lines)) === '') {
        array_pop($lines);
    }
    return ['id' => $id, 'body' => implode("\n", $lines)];
}

function tg_person(array $from): string
{
    $name = trim(($from['first_name'] ?? '') . ' ' . ($from['last_name'] ?? ''));
    $user = isset($from['username']) ? '@' . $from['username'] : '';
    if ($name === '') {
        return $user !== '' ? $user : 'сотрудник';
    }
    return $user !== '' ? $name . ' (' . $user . ')' : $name;
}
