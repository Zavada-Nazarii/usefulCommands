#!/usr/bin/env python3

import argparse
import subprocess
import smtplib
import ssl
import socket
from datetime import datetime
import shutil

RESULTS_FILE = f"smtp_scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
PORTS = [25, 465, 587]

# Шаблони swaks
SWAKS_OPEN_RELAY = ["swaks", "--to", "test@external.com", "--from", "test@victim.local", "--server", "{ip}", "--port", "{port}", "--timeout", "8"]
SWAKS_AUTH_TEST = ["swaks", "--auth", "LOGIN", "--auth-user", "test", "--auth-password", "test", "--server", "{ip}", "--port", "{port}", "--timeout", "8"]

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

def run_swaks(command_template, ip: str, port: int, label: str):
    if not shutil.which("swaks"):
        log_result(f"[{label}] ERROR: swaks not found in PATH.")
        return
    try:
        cmd = [arg.format(ip=ip, port=str(port)) for arg in command_template]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        log_result(f"[{label}] {ip}:{port}\n{result.stdout}")
    except subprocess.TimeoutExpired:
        log_result(f"[{label}] {ip}:{port} -> TIMEOUT")
    except Exception as e:
        log_result(f"[{label}] {ip}:{port} -> ERROR: {e}")

def test_swaks_open_relay(ip: str, port: int):
    run_swaks(SWAKS_OPEN_RELAY, ip, port, "SWAKS OPEN RELAY")

def test_swaks_auth(ip: str, port: int):
    run_swaks(SWAKS_AUTH_TEST, ip, port, "SWAKS AUTH TEST")

def test_ssl(ip: str, port: int):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((ip, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=ip) as ssock:
                cert = ssock.getpeercert()
                result = f"[SSL] {ip}:{port} -> SSL/TLS CERT: {cert.get('subject')}"
                log_result(result)
    except Exception as e:
        log_result(f"[SSL] {ip}:{port} -> ERROR: {e}")

def run_all_tests(ip: str):
    for port in PORTS:
        test_banner(ip, port)
        test_swaks_open_relay(ip, port)
        test_swaks_auth(ip, port)
        if port in [465, 587]:
            test_ssl(ip, port)

def parse_args():
    parser = argparse.ArgumentParser(description="SMTP Security Scanner")
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
