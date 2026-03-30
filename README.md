# AI Oil Articles Agent

Скрипт-агент, который ежедневно ищет новые статьи по применению ИИ в нефтепереработке и отправляет ссылки на почту.

## Что делает
- Выполняет поиск по Google News RSS.
- Фильтрует свежие публикации (по умолчанию за последние 24 часа).
- Отправляет HTML-письмо на `rataganov78@gmail.com`.

## Установка
```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Внешние Python-зависимости не требуются.

## Настройка SMTP (боевой режим, Gmail)
```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_STARTTLS="1"
export SMTP_USER="your_gmail@gmail.com"
export SMTP_PASSWORD="your_app_password"

export SENDER_EMAIL="your_gmail@gmail.com"
export RECIPIENT_EMAIL="rataganov78@gmail.com"

# Опционально
export WITHIN_HOURS="24"
export NEWS_QUERY='("искусственный интеллект" OR AI) ("нефтепереработка" OR "oil refining" OR НПЗ) (статья OR research OR paper OR кейс)'
```

## Ручной запуск
```bash
export RESULT_PDF_PATH="/workspace/first-project/agent_search_results.pdf"
python3 ai_oil_articles_agent.py
```

По умолчанию после запуска создаётся PDF-отчёт `agent_search_results.pdf`.
Можно задать путь через `RESULT_PDF_PATH`.

## Локальная проверка SMTP без реальной отправки
1) Поднимите локальный SMTP-сервер:
```bash
python3 -m smtpd -c DebuggingServer -n 127.0.0.1:1025
```

2) В отдельном терминале запустите агент на тестовом RSS (без внешней сети):
```bash
export SMTP_HOST="127.0.0.1"
export SMTP_PORT="1025"
export SMTP_STARTTLS="0"
unset SMTP_USER
unset SMTP_PASSWORD
export SENDER_EMAIL="agent@localhost"
export RECIPIENT_EMAIL="rataganov78@gmail.com"
export NEWS_FEED_URL="file:///workspace/first-project/sample_feed.xml"
export RESULT_PDF_PATH="/workspace/first-project/agent_search_results.pdf"
python3 ai_oil_articles_agent.py
```

## Ежедневный запуск в 14:15
Откройте crontab:
```bash
crontab -e
```

Добавьте строку (каждый день в 14:15 по времени сервера):
```cron
15 14 * * * cd /workspace/first-project && /usr/bin/env bash -lc 'source .venv/bin/activate && python3 ai_oil_articles_agent.py >> agent.log 2>&1'
```

Если нужно строгое локальное время (например, Europe/Moscow), задайте `CRON_TZ`:
```cron
CRON_TZ=Europe/Moscow
15 14 * * * cd /workspace/first-project && /usr/bin/env bash -lc 'source .venv/bin/activate && python3 ai_oil_articles_agent.py >> agent.log 2>&1'
```
