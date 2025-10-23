#!/usr/bin/env python3

import argparse
import subprocess
import socket
import smtplib
import ssl
import poplib
import imaplib
import re
from datetime import datetime
import shutil
import os

PORTS = [25, 465, 587, 110, 995, 143, 993]
SWAKS_OPEN_RELAY = [
    "swaks",
    "--to", "{rcpt}",
    "--from", "{sender}",
    "--server", "{ip}",
    "--port", "{port}",
    "--timeout", "8",
]
SWAKS_TLS_FLAG = ["--tls"]
SWAKS_TLS_ON_CONNECT_FLAG = ["--tls-on-connect"]

DEBUG = False

def debug_print(message: str):
    if DEBUG:
        print(f"[DEBUG] {message}")

def safe_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', name)

def normalize_domain(raw_domain: str) -> str:
    domain = raw_domain.strip().lower()
    domain = re.sub(r'^https?://', '', domain)
    domain = domain.split('/')[0]
    return domain

def log_result(output: str, file_path: str):
    with open(file_path, "a") as f:
        f.write(output + "\n" + "-" * 80 + "\n")

def run_subfinder(domain: str) -> list:
    debug_print(f"Running subfinder for: {domain}")
    subdomains = []
    if shutil.which("subfinder") is None:
        print("[ERROR] subfinder not found in PATH.")
        return subdomains
    try:
        result = subprocess.run(["subfinder", "-d", domain, "-silent"], capture_output=True, text=True, timeout=60)
        subdomains = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        debug_print(f"Found subdomains: {subdomains}")
    except Exception as e:
        print(f"[ERROR] Subfinder failed: {e}")
    return subdomains

def test_banner(ip: str, port: int, log_file: str):
    debug_print(f"Testing banner on {ip}:{port}")
    try:
        s = socket.create_connection((ip, port), timeout=5)
        banner = s.recv(1024).decode(errors="ignore")
        s.close()
        result = f"[BANNER] {ip}:{port} -> {banner.strip()}"
        log_result(result, log_file)
    except Exception as e:
        log_result(f"[BANNER] {ip}:{port} -> ERROR: {e}", log_file)

def _classify_swaks_output(output: str) -> str:
    text = output.lower()
    if "must issue a starttls command first" in text:
        return "STARTTLS потрібен для перевірки"
    if "relay access denied" in text or "relay not permitted" in text:
        return "Релей заборонено (relay access denied)"
    if "recipient address rejected" in text or "5.1.1" in text:
        return "Релей заблоковано (отримувач відхилений)"
    if "530 5.7.0" in text:
        return "Релей заблоковано (530 5.7.0)"
    if "250 2.0.0" in text or "250 2.1.5" in text:
        return "Можливий відкритий релей! Перевірте журнал нижче"
    return "Результат потребує ручної перевірки"

def run_swaks_open_relay(ip: str, port: int, log_file: str, sender: str, rcpt: str):
    debug_print(f"Testing open relay on {ip}:{port}")
    if not shutil.which("swaks"):
        log_result(f"[SWAKS OPEN RELAY] {ip}:{port} -> ERROR: swaks not found", log_file)
        return
    def _run_swaks(extra_flags=None):
        args = list(SWAKS_OPEN_RELAY)
        if extra_flags:
            args.extend(extra_flags)
        cmd = [arg.format(ip=ip, port=str(port), sender=sender, rcpt=rcpt) for arg in args]
        debug_print(f"Running command: {' '.join(cmd)}")
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20)

    try:
        extra_flags = []
        used_tls = False
        if port == 465:
            extra_flags = SWAKS_TLS_ON_CONNECT_FLAG
            used_tls = True
        result = _run_swaks(extra_flags)
        combined = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
        summary = _classify_swaks_output(combined)

        if ("must issue a starttls command first" in combined.lower()) and not used_tls:
            log_result(f"[SWAKS OPEN RELAY] {ip}:{port} -> Сервер вимагає STARTTLS, повторюємо з TLS.", log_file)
            result = _run_swaks(SWAKS_TLS_FLAG)
            combined = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
            summary = _classify_swaks_output(combined)
            used_tls = True

        log_lines = [
            f"[SWAKS OPEN RELAY] {ip}:{port}",
            f"  Відправник: {sender}",
            f"  Отримувач: {rcpt}",
            f"  Підсумок: {summary}",
            "",
            result.stdout.strip() if result.stdout else "(stdout порожній)",
        ]
        if result.stderr:
            log_lines.append("")
            log_lines.append("stderr:")
            log_lines.append(result.stderr.strip())
        log_result("\n".join(log_lines), log_file)
    except subprocess.TimeoutExpired:
        log_result(f"[SWAKS OPEN RELAY] {ip}:{port} -> TIMEOUT", log_file)
    except Exception as e:
        log_result(f"[SWAKS OPEN RELAY] {ip}:{port} -> ERROR: {e}", log_file)

def test_auth_smtp(ip: str, port: int, log_file: str):
    debug_print(f"Testing SMTP AUTH on {ip}:{port}")
    try:
        if port == 465:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(ip, port, timeout=10, context=context)
            server.ehlo()
        else:
            server = smtplib.SMTP(ip, port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
        server.login("test", "test")
        log_result(f"[AUTH SMTP] {ip}:{port} -> AUTH LOGIN accepted (unexpected!)", log_file)
        server.quit()
    except smtplib.SMTPAuthenticationError:
        log_result(f"[AUTH SMTP] {ip}:{port} -> AUTH LOGIN rejected (as expected)", log_file)
    except Exception as e:
        log_result(f"[AUTH SMTP] {ip}:{port} -> ERROR: {e}", log_file)

def test_pop3(ip: str, port: int, log_file: str):
    debug_print(f"Testing POP3 on {ip}:{port}")
    try:
        if port == 995:
            pop = poplib.POP3_SSL(ip, port, timeout=8)
        else:
            pop = poplib.POP3(ip, port, timeout=8)
        pop.user("test")
        pop.pass_("test")
        count, _ = pop.stat()
        log_result(f"[POP3] {ip}:{port} -> Auth success. {count} messages found.", log_file)
        pop.quit()
    except poplib.error_proto as e:
        log_result(f"[POP3] {ip}:{port} -> AUTH ERROR: {e}", log_file)
    except Exception as e:
        log_result(f"[POP3] {ip}:{port} -> ERROR: {e}", log_file)

def test_imap(ip: str, port: int, log_file: str):
    debug_print(f"Testing IMAP on {ip}:{port}")
    try:
        if port == 993:
            imap = imaplib.IMAP4_SSL(ip, port)
        else:
            imap = imaplib.IMAP4(ip, port)
            imap.starttls()
        imap.login("test", "test")
        imap.select()
        typ, data = imap.search(None, 'ALL')
        log_result(f"[IMAP] {ip}:{port} -> Auth success. {len(data[0].split())} messages found.", log_file)
        imap.logout()
    except imaplib.IMAP4.error as e:
        log_result(f"[IMAP] {ip}:{port} -> AUTH ERROR: {e}", log_file)
    except Exception as e:
        log_result(f"[IMAP] {ip}:{port} -> ERROR: {e}", log_file)

def run_all_tests(ip: str, log_file: str, relay_sender: str, relay_recipient: str):
    for port in PORTS:
        test_banner(ip, port, log_file)
        if port in [25, 465, 587]:
            run_swaks_open_relay(ip, port, log_file, relay_sender, relay_recipient)
            test_auth_smtp(ip, port, log_file)
        elif port in [110, 995]:
            test_pop3(ip, port, log_file)
        elif port in [143, 993]:
            test_imap(ip, port, log_file)

def parse_args():
    parser = argparse.ArgumentParser(description="SMTP/POP3/IMAP Vulnerability Scanner with Subdomain Enumeration and Debug Mode")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-d", "--domain", help="Base domain or full URL")
    group.add_argument("-f", "--file", help="File with list of domains or URLs")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--relay-from", default="test@victim.local", help="MAIL FROM адреса для open relay тесту (default: test@victim.local)")
    parser.add_argument("--relay-to", default="test@external.com", help="RCPT TO адреса для open relay тесту (default: test@external.com)")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    DEBUG = args.debug
    raw_domains = []

    if args.domain:
        raw_domains = [args.domain]
    elif args.file:
        with open(args.file, "r") as f:
            raw_domains = [line.strip() for line in f if line.strip()]

    for raw in raw_domains:
        domain = normalize_domain(raw)
        subdomains = run_subfinder(domain)
        all_targets = list(set(subdomains + [domain]))
        for target in all_targets:
            safe_name = safe_filename(target)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"smtp_email_scan_{safe_name}_{timestamp}.txt"
            log_result(f"STARTING SCAN FOR: {target}", log_file)
            run_all_tests(target, log_file, args.relay_from, args.relay_to)
            log_result(f"FINISHED SCAN FOR: {target}", log_file)
