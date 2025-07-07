#!/usr/bin/env python3

import argparse
import subprocess
import socket
import smtplib
import ssl
from datetime import datetime
import shutil

RESULTS_FILE = f"smtp_scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
PORTS = [25, 465, 587]

SWAKS_OPEN_RELAY = ["swaks", "--to", "test@external.com", "--from", "test@victim.local", "--server", "{ip}", "--port", "{port}", "--timeout", "8"]

def log_result(output: str):
    with open(RESULTS_FILE, "a") as f:
        f.write(output + "\n" + "-" * 80 + "\n")

def test_banner(ip: str, port: int):
    try:
        s = socket.create_connection((ip, port), timeout=5)
        banner = s.recv(1024).decode(errors="ignore")
        s.close()
        result = f"[BANNER] {ip}:{port} -> {banner.strip()}"
        print(result)
        log_result(result)
    except Exception as e:
        log_result(f"[BANNER] {ip}:{port} -> ERROR: {e}")

def run_swaks_open_relay(ip: str, port: int):
    if not shutil.which("swaks"):
        log_result(f"[SWAKS OPEN RELAY] {ip}:{port} -> ERROR: swaks not found")
        return
    try:
        cmd = [arg.format(ip=ip, port=str(port)) for arg in SWAKS_OPEN_RELAY]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        log_result(f"[SWAKS OPEN RELAY] {ip}:{port}\n{result.stdout}")
    except subprocess.TimeoutExpired:
        log_result(f"[SWAKS OPEN RELAY] {ip}:{port} -> TIMEOUT")
    except Exception as e:
        log_result(f"[SWAKS OPEN RELAY] {ip}:{port} -> ERROR: {e}")

def test_auth_smtplib(ip: str, port: int):
    log_result(f"[AUTH TEST] Starting AUTH LOGIN test for {ip}:{port}")
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

        # Dummy auth attempt
        server.login("test", "test")
        log_result(f"[AUTH TEST] {ip}:{port} -> AUTH LOGIN accepted (unexpected!)")
        server.quit()
    except smtplib.SMTPAuthenticationError:
        log_result(f"[AUTH TEST] {ip}:{port} -> AUTH LOGIN rejected (as expected)")
    except Exception as e:
        log_result(f"[AUTH TEST] {ip}:{port} -> ERROR: {e}")

def test_ssl(ip: str, port: int):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((ip, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=ip) as ssock:
                cert = ssock.getpeercert()
                result = f"[SSL] {ip}:{port} -> SSL/TLS CERT SUBJECT: {cert.get('subject')}"
                log_result(result)
    except Exception as e:
        log_result(f"[SSL] {ip}:{port} -> ERROR: {e}")

def run_all_tests(ip: str):
    for port in PORTS:
        test_banner(ip, port)
        run_swaks_open_relay(ip, port)
        test_auth_smtplib(ip, port)
        if port in [465, 587]:
            test_ssl(ip, port)

def parse_args():
    parser = argparse.ArgumentParser(description="SMTP Security Scanner with AUTH and TLS")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--url", help="Target IP or hostname")
    group.add_argument("-f", "--file", help="File with list of IPs/domains")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    targets = []

    if args.url:
        targets.append(args.url.strip())
    elif args.file:
        with open(args.file, "r") as f:
            targets = [line.strip() for line in f if line.strip()]

    for target in targets:
        log_result(f"STARTING SCAN FOR: {target}")
        run_all_tests(target)
        log_result(f"FINISHED SCAN FOR: {target}\n")
