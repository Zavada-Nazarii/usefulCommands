# 📬 SMTP/POP3/IMAP Mass Scan Utility – README

Цей README пояснює, як працювати з результатами сканування після запуску `smtp_scan_debug.py`, особливо коли є **багато лог-файлів**.

---

## 📁 Структура результатів

Після сканування будуть створені файли у форматі:

```
smtp_email_scan_<домен або IP>_<timestamp>.txt
```

Кожен з них містить результат тестування SMTP/POP3/IMAP на:
- банери
- open relay
- AUTH LOGIN
- спроби доступу до вхідних листів

---

## 🔍 Як швидко перевірити, чи щось знайшли

### ✅ 1. **Grep – основна команда для пошуку успішного доступу чи вразливості:**

```bash
grep -riE "Auth success|AUTH LOGIN accepted|Open relay|messages found" smtp_email_scan_*.txt
```

Ця команда виведе:
- успішні входи в поштову скриньку
- знайдені листи
- вразливості типу open relay

---

### ✅ 2. **Архівація всіх логів:**

```bash
tar -czvf smtp_scan_results.tar.gz smtp_email_scan_*.txt
```

---



