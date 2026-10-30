<?php
/* Инком-Аудит: прием заявок с формы сайта. Принимает JSON (или обычный POST), проверяет поля, отправляет заявку
   в Telegram и на почту. Ответ — JSON {"ok":true,"telegram":true,"mail":true}. Заявка считается принятой,
   если дошел хотя бы один канал. Токены и пароли — только в config.local.php на сервере. */
declare(strict_types=1);

ini_set('display_errors', '0');   // ошибки только в журнал сервера, не в ответ
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

$cfg = require __DIR__ . '/config.php';
require __DIR__ . '/lib.php';

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '' && in_array($origin, $cfg['allowed_origins'], true)) {
    header('Access-Control-Allow-Origin: ' . $origin);
    header('Vary: Origin');
    header('Access-Control-Allow-Methods: POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    header('Access-Control-Max-Age: 86400');
}
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') {
    http_response_code(204);
    exit;
}
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    reply(405, ['ok' => false, 'error' => 'method']);
}

$raw = file_get_contents('php://input') ?: '';
$data = json_decode($raw, true);
if (!is_array($data)) {
    $data = $_POST;
}
$str = static function (string $key, int $max) use ($data): string {
    $v = $data[$key] ?? '';
    $v = is_scalar($v) ? trim((string) $v) : '';
    $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $v) ?? '';
    return mb_substr($v, 0, $max);
};

/* роботы: скрытое поле заполнено или форма отправлена слишком быстро → молча отвечаем ok, ничего не шлем */
$elapsed = (int) ($data['elapsed'] ?? 0);
if ($str('website', 200) !== '' || ($elapsed > 0 && $elapsed < $cfg['min_elapsed_ms'])) {
    reply(200, ['ok' => true]);
}

/* не больше N заявок с одного адреса за окно времени */
$ip = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? '0';
$ip = trim(explode(',', (string) $ip)[0]);
if (!rate_ok($ip, (int) $cfg['rate_limit']['max'], (int) $cfg['rate_limit']['window'])) {
    reply(429, ['ok' => false, 'error' => 'rate']);
}

$name    = $str('name', 120);
$phone   = $str('phone', 40);
$email   = $str('email', 120);
$company = $str('company', 200);
$message = $str('message', 2000);
$task    = $str('task', 80);
$consent = $str('consent', 10);
$page    = $str('page', 300);
$source  = $str('source', 20);

$errors = [];
if ($name === '')                                      $errors[] = 'name';
if (strlen(preg_replace('/\D/', '', $phone) ?? '') < 10) $errors[] = 'phone';
if (!filter_var($email, FILTER_VALIDATE_EMAIL))        $errors[] = 'email';
if ($company === '')                                   $errors[] = 'company';
if ($message === '')                                   $errors[] = 'message';
if ($consent !== 'yes')                                $errors[] = 'consent';
if ($errors) {
    reply(422, ['ok' => false, 'error' => 'fields', 'fields' => $errors]);
}

$when = date('d.m.Y H:i');
$leadId = strtoupper(base_convert((string) (time() - 1700000000), 10, 36)) . strtoupper(substr(bin2hex(random_bytes(1)), 0, 2));   // короткий номер заявки, он же в теме письма
$body = implode("\n", [
    'Имя: ' . $name,
    'Телефон: ' . $phone,
    'E-mail: ' . $email,
    'Компания: ' . $company,
    'Услуга: ' . ($task !== '' ? $task : 'не указана'),
    'Сообщение: ' . $message,
]);
/* техническая отметка: только в письмо и журнал, в Telegram не показывается */
$meta = 'Страница: ' . ($page !== '' ? $page : 'не передана') . ($source !== '' ? ' (' . $source . ')' : '') . ' · ' . $when
    . ' · согласие на обработку персональных данных получено';
$text = 'Новая заявка с сайта №' . $leadId . "\n" . $body . "\n\n" . $meta;

$okTg = false;
$okMail = false;
if ($cfg['dry_run']) {
    log_line($cfg['log_file'], 'DRY ' . $ip . ' ' . str_replace("\n", ' | ', $text));
    reply(200, ['ok' => true, 'telegram' => true, 'mail' => true, 'dry_run' => true]);
}
if ($cfg['telegram_token'] !== '' && $cfg['telegram_chat_id'] !== '') {
    $okTg = tg_api($cfg['telegram_token'], 'sendMessage', [
        'chat_id' => (string) $cfg['telegram_chat_id'],
        'text' => lead_text('new', '', '', $leadId, $body),
        'parse_mode' => 'HTML',
        'disable_web_page_preview' => 'true',
        'reply_markup' => lead_keyboard('new'),
    ]) !== null;
}
if ($cfg['mail_to'] !== '') {
    $subject = 'Заявка с сайта №' . $leadId . ': ' . ($task !== '' ? $task : $name);
    $okMail = mail_send($cfg, $subject, $text, $email, $name);
}
log_line($cfg['log_file'], sprintf('%s tg=%d mail=%d %s', $ip, $okTg ? 1 : 0, $okMail ? 1 : 0, str_replace("\n", ' | ', $text)));

if ($okTg || $okMail) {
    reply(200, ['ok' => true, 'telegram' => $okTg, 'mail' => $okMail, 'id' => $leadId]);
}
reply(502, ['ok' => false, 'error' => 'delivery']);

/* ---------- функции ---------- */

function reply(int $code, array $payload): void
{
    http_response_code($code);
    echo json_encode($payload, JSON_UNESCAPED_UNICODE);
    exit;
}

function rate_ok(string $ip, int $max, int $window): bool
{
    if ($max <= 0) {
        return true;
    }
    $file = sys_get_temp_dir() . '/incom-lead-' . hash('sha256', $ip);
    $now = time();
    $hits = [];
    if (is_file($file)) {
        $hits = array_filter(array_map('intval', explode("\n", (string) file_get_contents($file))), static fn($t) => $t > $now - $window);
    }
    if (count($hits) >= $max) {
        return false;
    }
    $hits[] = $now;
    @file_put_contents($file, implode("\n", $hits), LOCK_EX);
    return true;
}

function mail_send(array $cfg, string $subject, string $text, string $replyTo, string $replyName): bool
{
    $to = array_values(array_filter(array_map('trim', explode(',', (string) $cfg['mail_to']))));
    if (!$to) {
        return false;
    }
    $from = $cfg['mail_from'] !== '' ? $cfg['mail_from'] : $to[0];
    $fromName = mb_encode_mimeheader((string) $cfg['mail_from_name'], 'UTF-8', 'B');
    $replyName = mb_encode_mimeheader($replyName, 'UTF-8', 'B');
    $headers = [
        'From: ' . $fromName . ' <' . $from . '>',
        'Reply-To: ' . $replyName . ' <' . $replyTo . '>',
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Transfer-Encoding: base64',
        'X-Mailer: incom-audit-site',
    ];
    $encSubject = mb_encode_mimeheader($subject, 'UTF-8', 'B');
    $body = chunk_split(base64_encode($text));
    $smtp = $cfg['smtp'];
    if (($smtp['host'] ?? '') !== '') {
        return smtp_send($smtp, $from, $to, $encSubject, $headers, $body);
    }
    return mail(implode(', ', $to), $encSubject, $body, implode("\r\n", $headers), '-f' . $from);
}

/* Минимальный SMTP-клиент: SSL (465) или STARTTLS (587), AUTH LOGIN. Без внешних библиотек. */
function smtp_send(array $s, string $from, array $to, string $subject, array $headers, string $body): bool
{
    $secure = strtolower((string) ($s['secure'] ?? 'ssl'));
    $host = (string) $s['host'];
    $port = (int) ($s['port'] ?: ($secure === 'ssl' ? 465 : 587));
    $remote = ($secure === 'ssl' ? 'ssl://' : 'tcp://') . $host . ':' . $port;
    $fp = @stream_socket_client($remote, $errno, $errstr, 10, STREAM_CLIENT_CONNECT);
    if (!$fp) {
        error_log('incom send.php: smtp connect failed: ' . $errstr);
        return false;
    }
    stream_set_timeout($fp, 10);
    $read = static function () use ($fp): string {
        $out = '';
        while (($line = fgets($fp, 1024)) !== false) {
            $out .= $line;
            if (strlen($line) < 4 || $line[3] !== '-') {
                break;
            }
        }
        return $out;
    };
    $say = static function (string $cmd, string $expect) use ($fp, $read): bool {
        fwrite($fp, $cmd . "\r\n");
        $r = $read();
        if (strpos($r, $expect) !== 0) {
            error_log('incom send.php: smtp ' . substr($cmd, 0, 12) . ' -> ' . trim($r));
            return false;
        }
        return true;
    };
    $ok = strpos($read(), '220') === 0;
    $me = $_SERVER['SERVER_NAME'] ?? 'localhost';
    $ok = $ok && $say('EHLO ' . $me, '250');
    if ($ok && $secure === 'tls') {
        $ok = $say('STARTTLS', '220')
            && stream_socket_enable_crypto($fp, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)
            && $say('EHLO ' . $me, '250');
    }
    if ($ok && ($s['user'] ?? '') !== '') {
        $ok = $say('AUTH LOGIN', '334')
            && $say(base64_encode((string) $s['user']), '334')
            && $say(base64_encode((string) $s['password']), '235');
    }
    $ok = $ok && $say('MAIL FROM:<' . $from . '>', '250');
    foreach ($to as $rcpt) {
        $ok = $ok && $say('RCPT TO:<' . $rcpt . '>', '250');
    }
    if ($ok && $say('DATA', '354')) {
        $msg = 'To: ' . implode(', ', $to) . "\r\n" . 'Subject: ' . $subject . "\r\n" . 'Date: ' . date(DATE_RFC2822) . "\r\n"
            . implode("\r\n", $headers) . "\r\n\r\n" . str_replace("\n.", "\n..", $body) . "\r\n.";
        $ok = $say($msg, '250');
    }
    fwrite($fp, "QUIT\r\n");
    fclose($fp);
    return $ok;
}

function log_line(string $file, string $line): void
{
    if ($file === '') {
        return;
    }
    @file_put_contents($file, date('c') . ' ' . $line . "\n", FILE_APPEND | LOCK_EX);
}
