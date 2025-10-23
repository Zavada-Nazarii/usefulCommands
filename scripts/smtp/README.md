# SMTP утиліти

У каталозі є два окремих скрипти для перевірки поштових сервісів:

- `scan_smtp.py` – масовий сканер SMTP/POP3/IMAP з опціональним пошуком піддоменів.
- `smtp_check.py` – детальний аудит поштової інфраструктури домену через DNS та перевірку SMTP на 25 порту.

Нижче описані їх можливості, вимоги та приклади використання.

---

## 1. `scan_smtp.py` – масовий сканер сервісів

### Основна логіка
- Нормалізує домен / URL та (за наявності) збирає піддомени через `subfinder`.
- Для кожної цілі створює файл `smtp_email_scan_<target>_<timestamp>.txt`.
- Послідовно тестує порти:
  - SMTP: `25`, `465`, `587` (банер, open relay через `swaks`, AUTH LOGIN).
  - POP3: `110`, `995`.
  - IMAP: `143`, `993`.
- Результати додає у журнал, розділяючи секції рядком з `-` (зручно для grep/less).
- Перевірка open relay автоматично інтерпретує типові відповіді (5.1.1, 5.7.0, relay denied) і при потребі повторює тест зі STARTTLS.

### Зовнішні залежності
- `subfinder` (опційно, для пошуку піддоменів).
- `swaks` (для open relay перевірок на портах 25/465/587).

### Запуск
```bash
# Скан однієї цілі
python3 scan_smtp.py --domain example.com

# Скан списку доменів (по одному в рядок)
python3 scan_smtp.py --file targets.txt

# Додатковий вивід ходу роботи
python3 scan_smtp.py --domain example.com --debug

# Власні адреси для перевірки релею
python3 scan_smtp.py --domain example.com --relay-from user@yourdomain.tld --relay-to inbox@trusted.tld
```

### Швидкий аналіз результатів
```bash
grep -riE "Auth success|AUTH LOGIN accepted|Open relay|messages found" smtp_email_scan_*.txt
```
Команда покаже потенційні знахідки: успішні логіни, наявні листи, відкриті релеї.

Для архівації:
```bash
tar -czvf smtp_scan_results_<date>.tar.gz smtp_email_scan_*.txt
```

---

## 2. `smtp_check.py` – аудит доменної поштової інфраструктури

### Що перевіряє
- MX-записи, IP-адреси та PTR для кожного MX.
- SPF, DMARC, TLS-RPT, MTA-STS TXT записи.
- Публічні ключі DKIM (набір поширених селекторів або передані через `--selectors`).
- Банер SMTP, підтримка STARTTLS, основні дані сертифіката.
- Спроба відкритого релею (MAIL FROM/RCPT TO на порт 25).

> Усі SMTP-перевірки працюють лише по TCP-порту **25**, оскільки це порт для міжсерверної доставки. Порт 587 (submission) не тестується і за потреби може бути доданий окремо.

### Запуск
```bash
python3 smtp_check.py --domain example.com
python3 smtp_check.py --domain example.com --selectors selector1,selector2
python3 smtp_check.py --domain example.com --outdir reports/
```

Скрипт виводить звіт у консоль і зберігає його у файл `smtp_remote_check_<domain>_<timestamp>.log`.

---

## 3. Типові проблеми та поради
- Якщо секції з SMTP-перевірками показують `timed out`, найімовірніше, вихідні з’єднання на порт 25 блокуються провайдером або сервером.
- Відсутність SPF/DMARC/TLS-RPT/MTA-STS у звіті означає, що DNS-записи не налаштовані або домен виконує іншу роль (наприклад, це хост конкретного MX).
- Для `scan_smtp.py` на портах 465/587 відкритий релей практично не трапляється, але тест показує, чи сервер взагалі приймає SMTP-команди без автентифікації.
- Якщо сервер відхиляє типовий `test@external.com`, використовуйте прапор `--relay-to`, щоб вказати реальну адресу у дозволеному домені.

---

## 4. Мінімальні вимоги
- Python 3.x з модулями `smtplib`, `ssl`, `poplib`, `imaplib`, `dnspython` (необов’язково, але пришвидшує DNS-запити `smtp_check.py`).
- Зовнішні утиліти: `subfinder`, `swaks`, `dig`.

---

Готово! Обирайте потрібний скрипт залежно від задачі: масове тестування сервісів (`scan_smtp.py`) чи точковий аудит домену (`smtp_check.py`).
