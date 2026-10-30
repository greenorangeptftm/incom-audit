<?php
/* Скопировать в config.local.php и заполнить. Файл не попадает в git и не должен быть доступен по адресу
   (см. .htaccess рядом; лучше всего вынести папку server выше корня сайта и поправить require в send.php). */
return [
    'telegram_token'   => '123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',   // токен от @BotFather
    'telegram_chat_id' => '-1004342603934',                                 // группа «заявки» (дал заказчик 30.10.2026); проверить: /id боту в группе
    'telegram_webhook_secret' => 'длинная случайная строка',                 // создается tools/tg_webhook.py set ... и должна совпадать здесь
    'mail_to'          => 'help@incom-consult.ru',
    'mail_from'        => 'site@incom-consult.ru',                          // ящик на домене; с него уходят письма
    'smtp' => [                                                             // настройки почты Jino: проверить в панели хостинга
        'host'     => 'smtp.jino.ru',
        'port'     => 465,
        'secure'   => 'ssl',
        'user'     => 'site@incom-consult.ru',
        'password' => 'пароль от ящика',
    ],
    // 'allowed_origins' => ['https://incom-consult.ru'],   // нужно только если форма и обработчик на разных доменах
    // 'log_file' => '/home/users/.../private/leads.log',
];
