<?php
/* Инком-Аудит: webhook Telegram-бота. Telegram присылает сюда нажатия кнопок под заявками (и сообщения боту).
   Нажали «Обработано» → заявка редактируется: статус, кто и когда, кнопка меняется на «Вернуть в работу».
   Доступ только с секретом из setWebhook (config: telegram_webhook_secret). Поставить webhook: tools/tg_webhook.py */
declare(strict_types=1);

ini_set('display_errors', '0');   // ошибки только в журнал сервера, не в ответ
$cfg = require __DIR__ . '/config.php';
require __DIR__ . '/lib.php';

header('Content-Type: text/plain; charset=utf-8');
$secret = $_SERVER['HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN'] ?? '';
if ($cfg['telegram_webhook_secret'] === '' || !hash_equals((string) $cfg['telegram_webhook_secret'], (string) $secret)) {
    http_response_code(403);
    exit('forbidden');
}
$token = (string) $cfg['telegram_token'];
$u = json_decode(file_get_contents('php://input') ?: '', true);
if (!is_array($u)) {
    exit('ok');
}

if (isset($u['callback_query'])) {
    $cq = $u['callback_query'];
    $msg = $cq['message'] ?? null;
    $data = (string) ($cq['data'] ?? '');
    if (!$msg || !in_array($data, ['done', 'undo'], true)) {
        tg_api($token, 'answerCallbackQuery', ['callback_query_id' => $cq['id']]);
        exit('ok');
    }
    $chatId = (string) ($msg['chat']['id'] ?? '');
    if ($cfg['telegram_chat_id'] !== '' && $chatId !== (string) $cfg['telegram_chat_id']) {
        tg_api($token, 'answerCallbackQuery', ['callback_query_id' => $cq['id'], 'text' => 'Этот чат не подключен к заявкам']);
        exit('ok');
    }
    $parts = lead_parse((string) ($msg['text'] ?? ''));
    $state = $data === 'done' ? 'done' : 'work';
    $who = tg_person($cq['from'] ?? []);
    $when = date('d.m.Y H:i');
    $res = tg_api($token, 'editMessageText', [
        'chat_id' => $chatId,
        'message_id' => $msg['message_id'],
        'text' => lead_text($state, $who, $when, $parts['id'], $parts['body']),
        'parse_mode' => 'HTML',
        'disable_web_page_preview' => 'true',
        'reply_markup' => lead_keyboard($state),
    ]);
    tg_api($token, 'answerCallbackQuery', [
        'callback_query_id' => $cq['id'],
        'text' => $res === null ? 'Не удалось обновить, попробуйте еще раз' : ($state === 'done' ? 'Отмечено: обработано' : 'Возвращено в работу'),
    ]);
    exit('ok');
}

if (isset($u['message']['text'])) {
    $m = $u['message'];
    $text = trim((string) $m['text']);
    if (preg_match('~^/(start|id)(@\w+)?$~', $text)) {
        $chat = $m['chat'];
        $label = $chat['title'] ?? trim(($chat['first_name'] ?? '') . ' ' . ($chat['last_name'] ?? ''));
        tg_api($token, 'sendMessage', [
            'chat_id' => $chat['id'],
            'text' => "Чат: " . $label . "\nchat_id: " . $chat['id'] . "\nЭтот id нужно указать в настройках приема заявок (telegram_chat_id)",
        ]);
    }
}
exit('ok');
