#!/usr/bin/env python3
import argparse
import smtplib
import ssl
from typing import List, Dict, Any

DEFAULT_SENDER = "sender@example.com"
DEFAULT_RECIPIENT = "recipient@example.com"

def build_parser():
    parser = argparse.ArgumentParser(
        description="Швидка перевірка SMTP на банер, STARTTLS, VRFY та відкритий релей"
    )
    parser.add_argument("targets", nargs="*", help="IP або хости для перевірки")
    parser.add_argument(
        "-f",
        "--target-file",
        help="Файл зі списком цілей (по одному значенню на рядок)",
    )
    parser.add_argument("--port", type=int, default=25, help="SMTP порт (стандарт 25)")
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="TCP таймаут у секундах",
    )
    parser.add_argument("--sender", default=DEFAULT_SENDER, help="MAIL FROM адреса")
    parser.add_argument("--recipient", default=DEFAULT_RECIPIENT, help="RCPT TO адреса")
    parser.add_argument("--vrfy", default="postmaster", help="Аргумент для команди VRFY")
    parser.add_argument(
        "--skip-starttls",
        action="store_true",
        help="Не виконувати STARTTLS (залишитися у plaintext)",
    )
    parser.add_argument(
        "--send-data",
        action="store_true",
        help="Надіслати простий лист після успішного RCPT (тільки для контрольованих адрес)",
    )
    parser.add_argument("--subject", default="SMTP confirm test", help="Тема листа для DATA")
    parser.add_argument("--message", default="ТЕСТ", help="Текст листа для DATA")
    parser.add_argument("--debug", action="store_true", help="Увімкнути smtplib debug вивід")
    return parser

def load_targets(path: str) -> List[str]:
    items: List[str] = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            items.append(line)
    return items

def format_resp(code, message) -> str:
    parts = []
    if code is not None:
        parts.append(str(code))
    if message:
        if isinstance(message, bytes):
            try:
                message = message.decode("utf-8", "ignore")
            except Exception:
                message = repr(message)
        parts.append(message.strip())
    return " ".join(parts) if parts else ""

def check_host(host: str, args) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "host": host,
        "banner": "",
        "ehlo": "",
        "ehlo_tls": "",
        "starttls": "",
        "vrfy": "",
        "relay_mail": "",
        "relay_rcpt": "",
        "relay_error": "",
        "open_relay": False,
        "data_resp": "",
        "error": "",
        "sender": args.sender,
        "recipient": args.recipient,
        "vrfy_target": args.vrfy,
    }
    client = None
    def connect_client():
        local_client = smtplib.SMTP(timeout=args.timeout)
        local_client.set_debuglevel(1 if args.debug else 0)
        code, banner = local_client.connect(host, args.port)
        # Конвертуємо відповіді на банер / EHLO
        result["banner"] = format_resp(code, banner)
        code, msg = local_client.ehlo()
        result["ehlo"] = format_resp(code, msg)
        # Зберігаємо host для TLS, якщо smtplib знадобиться
        try:
            local_client._host = host
        except Exception:
            pass
        return local_client
    try:
        client = connect_client()
        if not args.skip_starttls:
            try:
                ssl_context = ssl.create_default_context()
                # Під час сканування можемо працювати з IP/невірними CN, тому вимикаємо перевірку
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                code, msg = client.starttls(context=ssl_context)
                result["starttls"] = format_resp(code, msg)
                code, msg = client.ehlo()
                result["ehlo_tls"] = format_resp(code, msg)
            except Exception as exc:
                result["starttls"] = f"error: {exc}"
                # Перепідключаємось у plaintext, щоб VRFY/relay все одно відпрацювали
                try:
                    client.close()
                except Exception:
                    pass
                client = connect_client()
        try:
            code, msg = client.docmd("VRFY", args.vrfy)
            result["vrfy"] = format_resp(code, msg)
        except Exception as exc:
            result["vrfy"] = f"error: {exc}"
        try:
            code, msg = client.mail(args.sender)
            result["relay_mail"] = format_resp(code, msg)
            code, msg = client.rcpt(args.recipient)
            result["relay_rcpt"] = format_resp(code, msg)
            if code is not None and 200 <= code < 300:
                result["open_relay"] = True
                if args.send_data:
                    payload = (
                        f"Subject: {args.subject}\r\n"
                        f"To: {args.recipient}\r\n"
                        f"From: {args.sender}\r\n"
                        "\r\n"
                        f"{args.message}\r\n"
                    )
                    try:
                        code, msg = client.data(payload)
                        result["data_resp"] = format_resp(code, msg)
                    except Exception as exc:
                        result["data_resp"] = f"error: {exc}"
        except Exception as exc:
            result["relay_error"] = f"{exc}"
        finally:
            try:
                client.rset()
            except Exception:
                pass
    except Exception as exc:
        result["error"] = str(exc)
    finally:
        if client is not None:
            try:
                client.quit()
            except Exception:
                try:
                    client.close()
                except Exception:
                    pass
    return result

def print_result(data: Dict[str, Any]) -> None:
    host = data.get("host", "")
    print(f"=== {host} ===")
    error_val = data.get("error")
    if error_val:
        print(f"connection error: {error_val}")
        print()
        return
    banner = data.get("banner")
    if banner:
        print(f"banner: {banner}")
    ehlo = data.get("ehlo")
    if ehlo:
        print(f"EHLO: {ehlo}")
    starttls = data.get("starttls")
    if starttls:
        print(f"STARTTLS: {starttls}")
    ehlo_tls = data.get("ehlo_tls")
    if ehlo_tls:
        print(f"EHLO (post TLS): {ehlo_tls}")
    vrfy_resp = data.get("vrfy")
    if vrfy_resp:
        vrfy_target = data.get("vrfy_target")
        print(f"VRFY {vrfy_target}: {vrfy_resp}")
    relay_mail = data.get("relay_mail")
    if relay_mail:
        sender = data.get("sender")
        print(f"MAIL FROM <{sender}>: {relay_mail}")
    relay_rcpt = data.get("relay_rcpt")
    if relay_rcpt:
        recipient = data.get("recipient")
        state = "OPEN RELAY" if data.get("open_relay") else "relay blocked"
        print(f"RCPT TO <{recipient}>: {relay_rcpt} ({state})")
    relay_error = data.get("relay_error")
    if relay_error:
        print(f"relay error: {relay_error}")
    data_resp = data.get("data_resp")
    if data_resp:
        print(f"DATA: {data_resp}")
    print()

def main():
    parser = build_parser()
    args = parser.parse_args()
    targets: List[str] = []
    targets.extend(args.targets)
    if args.target_file:
        targets.extend(load_targets(args.target_file))
    targets = [t.strip() for t in targets if t.strip()]
    if not targets:
        parser.error("Не вказано жодної цілі для перевірки")
    for host in targets:
        data = check_host(host, args)
        print_result(data)

if __name__ == "__main__":
    main()
