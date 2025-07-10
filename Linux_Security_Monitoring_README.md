# Linux Security Monitoring & Forensics Guide

Цей файл містить зібрані техніки, команди та приклади для моніторингу дій у системі Linux, зокрема:

- Перевірка запусків команд (`wget`, `chmod`, `.sh`)
- Аудит авторизацій користувачів
- Логування мережевих підключень
- Виявлення змін у файловій системі

---

## 🔍 1. Пошук запусків команд (`wget`, `chmod`, .sh)

### Через `auditd`:
```bash
sudo ausearch -x wget
sudo ausearch -x chmod
sudo ausearch -f .sh
```

### Через `journalctl`:
```bash
journalctl _UID=$(id -u username) --since "today" | grep wget
journalctl _PID=501878
```

---

## 📂 2. Виведення активних мережевих підключень

```bash
sudo lsof -nPi
sudo ss -tuna
sudo netstat -plant
```

---

## 👁 3. Моніторинг підозрілих директорій (наприклад, '$user_name$')

### Перевірити вміст:
```bash
ls -la '/home/$user_name$'
find '/home/$user_name$' -type f -exec file {} \;
```

### Перевірити хто створив:
```bash
ausearch -f /home/\$user_name\$
```

---

## ⌚ 4. Перевірка, коли створено користувача

### Через дату створення домашнього каталогу:
```bash
stat /home/username
```

### Через `auth.log`:
```bash
grep useradd /var/log/auth.log*
```

### Чи є користувач у `sudoers`:
```bash
sudo -l -U username
```

### Через `auditd`:
```bash
ausearch -m ADD_USER --start today
```
---

## 👤 5. Перевірка прав користувача

```bash
id username
sudo -l -U username
groups username
grep username /etc/passwd
```

---

## 🔐 6. Вхід до системи та активні сесії

```bash
last username
who
w -h
loginctl list-sessions
journalctl _UID=$(id -u username) --grep="session opened"
```

---

## 🌐 7. Логування мережевого трафіку

### Через UFW / iptables:
```bash
sudo less /var/log/ufw.log
sudo journalctl -k | grep 'IN='
```

### Через `auditd`:
```bash
auditctl -a always,exit -F arch=b64 -S connect -k net_connect
ausearch -k net_connect
```

### Інструменти:
- `tcpdump -i any -nn`
- `nethogs`
- `iftop`

---

## 📁 8. Зміни у файловій системі за сьогодні

```bash
sudo find / -type f -newermt "$(date +%Y-%m-%d)" 2>/dev/null
```

### Варіанти:
```bash
sudo find / -type f -newermt "$(date +%Y-%m-%d)" 2>/dev/null # Змінені файли за сьогодні по всій файловій системі
sudo find / -type f -cnewermt "$(date +%Y-%m-%d)"  # Зміна прав, власника
sudo find / -type f -newermt "$(date +%Y-%m-%d)" \( -iname "*.sh" -o -iname "*.py" \)
sudo find / -type f -newermt "$(date +%Y-%m-%d)" -exec ls -lh --time-style=long-iso {} \; 2>/dev/null
sudo find / -type f -newermt "$(date +%Y-%m-%d)" \( -iname "*.sh" -o -iname "*.py" -o -iname "*.conf" -o -iname "*.service" \) 2>/dev/null

```
---
