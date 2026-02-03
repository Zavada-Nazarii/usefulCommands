# Інструкція: smtp_confirm.py

## Призначення
`smtp_confirm.py` перевіряє SMTP‑сервери на банер, STARTTLS, VRFY, відкритий релей і (за бажанням) відправляє тестовий лист. Скрипт використовує службові адреси `sender@example.com` та `recipient@example.com` за замовчуванням, але їх можна змінити.

## Встановлення
1. Переконайтесь, що в системі є Python 3.
2. Файл `smtp_confirm.py` лежить у кореневій директорії проєкту (`../smtp_confirm.py` відносно папки результатів). Ніяких додаткових залежностей не потрібно.

## Базовий запуск
```
python3 smtp_confirm.py 192.168.1.1
```
- На екран виводяться банер, відповіді на `EHLO`/`STARTTLS`, результат `VRFY`, статус `MAIL FROM`, `RCPT TO`.
- Якщо на `RCPT TO` приходить код 2xx, скрипт позначить “OPEN RELAY”.

## Читання цілей із файлу
```
python3 smtp_confirm.py -f smtp_confirm_targets.txt --send-data --subject "Test" --message "TEST"
```
Файл має містити по одній IP/назві в рядку.

## Зміна ключових параметрів
- Порт: `--port 587`
- Таймаут (сек): `--timeout 5`
- Відправник/одержувач: `--sender me@example.com --recipient you@example.com`
- Адреса для `VRFY`: `--vrfy admin`
- Пропустити STARTTLS: `--skip-starttls`
- Докладний протокол smtplib: `--debug`

## Відправка реального тестового листа
Додайте `--send-data`:
```
python3 smtp_confirm.py --send-data 192.168.1.1
```
- За замовчуванням тема: “SMTP confirm test”, тіло: “ТЕСТ”.
- Можна змінити: `--subject "Test" --message "Будь-який текст"`.
- У виводі з’явиться рядок `DATA: 250 ...`, а лист надійде одержувачу.

## Типові сценарії
1. **Пошук відкритого релею**: `python3 smtp_confirm.py --send-data --sender sender@example.com --recipient recipient@example.com <IP>`.
2. **Швидке повторне тестування**: `python3 smtp_confirm.py -f ../smtp_confirm_targets.txt --send-data --subject "Test" --message "TEST"`.
3. **Валідація TLS без відправки листа**: `python3 smtp_confirm.py --skip-starttls` (якщо TLS падає) або без прапора (TLS за замовчуванням).

## Інтерпретація виводу
- `starttls error`: TLS не вдалося; скрипт перепід’єднається в plaintext і продовжить.
- `VRFY ... 252`: сервер підтверджує акаунт, що може дозволяти збір поштових адрес.
- `RCPT TO ... (OPEN RELAY)`: хост приймає лист на зовнішній домен без авторизації.
- `DATA: 250 ... queued as`: лист реально поставлено в чергу.
- `relay error: please run connect() first`: зазвичай означає, що попередній етап обірвав з’єднання; повторіть спробу і перевірте STARTTLS.

