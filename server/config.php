<?php
/* Инком-Аудит: настройки приема заявок. Реальные значения лежат в config.local.php рядом с этим файлом (в git его нет)
   или в переменных окружения. Пример: config.local.example.php */
declare(strict_types=1);

$defaults = [
    'telegram_token'   => getenv('TELEGRAM_BOT_TOKEN') ?: '',
    'telegram_chat_id' => getenv('TELEGRAM_CHAT_ID') ?: '',      // id чата или группы, куда писать (см. tools/tg_chats.py или команда /id боту)
    'telegram_webhook_secret' => getenv('TELEGRAM_WEBHOOK_SECRET') ?: '',   // тот же секрет, что передан в setWebhook (tools/tg_webhook.py)
    'timezone'         => 'Europe/Moscow',
    'mail_to'          => getenv('MAIL_TO') ?: '',               // куда слать письма, через запятую
    'mail_from'        => getenv('MAIL_FROM') ?: '',             // от кого, ящик на домене (например site@incom-consult.ru)
    'mail_from_name'   => 'Сайт Инком-Аудит',
    'smtp'             => [                                      // пусто → PHP mail() хостинга
        'host'     => getenv('SMTP_HOST') ?: '',
        'port'     => (int) (getenv('SMTP_PORT') ?: 465),
        'secure'   => getenv('SMTP_SECURE') ?: 'ssl',            // ssl (465) или tls (587)
        'user'     => getenv('SMTP_USER') ?: '',
        'password' => getenv('SMTP_PASSWORD') ?: '',
    ],
    'allowed_origins'  => [],                                    // пусто → только тот же домен; иначе список https://...
    'rate_limit'       => ['max' => 5, 'window' => 600],         // не больше 5 заявок с одного IP за 10 минут
    'min_elapsed_ms'   => 3000,                                  // форма заполнена быстрее 3 с → похоже на робота
    'dry_run'          => false,                                 // true → ничего не отправлять, только отвечать ok (для проверки)
    'log_file'         => '',                                    // путь к файлу журнала вне корня сайта, пусто → не писать
];

$local = __DIR__ . '/config.local.php';
$cfg = $defaults;
if (is_file($local)) {
    $over = require $local;
    if (is_array($over)) {
        $cfg = array_replace_recursive($defaults, $over);
    }
}
date_default_timezone_set((string) $cfg['timezone']);
return $cfg;
