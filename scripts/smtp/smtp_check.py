#!/usr/bin/env python3
"""
smtp_remote_check.py
Віддалена перевірка поштової інфраструктури домену:
 - MX-записи та IP-адреси
 - Аналіз SPF TXT (v=spf1)
 - Наявність та вміст записів DMARC
 - Доступність відкритого ключа DKIM для поширених чи вказаних селекторів
 - Отримання банера SMTP (під'єднання до порту 25)
 - Перевірка підтримки STARTTLS і основної інформації про сертифікат
 - Перевірка на відкритий SMTP-релей
 - Додаткові DNS-перевірки (PTR для MX IP, TLS-RPT, MTA-STS)
Результат: зручний для читання звіт у консолі та лог-файл з часовою міткою.
Скрипт виконує лише віддалені перевірки (DNS-запити, TCP-підключення). НЕ потребує доступу до логів поштового сервера.
"""
import argparse
import datetime
import socket
import subprocess
import sys
import re
import os
import ssl
import smtplib
from typing import List, Tuple, Dict, Optional

# Спроба імпортувати dnspython, інакше використовуємо утиліти dig/host
try:
    import dns.resolver
    import dns.exception
    DNSPY = True
except Exception:
    DNSPY = False

# --- Утиліти --------------------------------------------------------------
def now_ts():
    return datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def eprint(*a, **k):
    print(*a, file=sys.stderr, **k)

# DNS-допоміжні функції (спершу dnspython, інакше системні утиліти dig/host)
def query_txt(name: str) -> List[str]:
    """Повертає перелік TXT-рядків для вказаного імені."""
    if DNSPY:
        try:
            answers = dns.resolver.resolve(name, 'TXT', lifetime=10)
            return ["".join(r.strings).decode() if isinstance(r.strings[0], bytes) else "".join(r.strings) for r in answers]
        except Exception:
            return []
    else:
        # Запасний варіант: використовуємо 'dig +short TXT'
        try:
            out = subprocess.check_output(["dig", "+short", "TXT", name], text=True, stderr=subprocess.DEVNULL, timeout=15)
            lines = [l.strip().strip('"') for l in out.splitlines() if l.strip()]
            return lines
        except Exception:
            return []

def query_mx(domain: str) -> List[Tuple[int, str]]:
    """Повертає перелік MX-записів як кортежі (пріоритет, хост)."""
    if DNSPY:
        try:
            answers = dns.resolver.resolve(domain, 'MX', lifetime=10)
            return sorted([(r.preference, str(r.exchange).rstrip('.')) for r in answers], key=lambda x: x[0])
        except Exception:
            return []
    else:
        try:
            out = subprocess.check_output(["dig", "+short", "MX", domain], text=True, stderr=subprocess.DEVNULL, timeout=15)
            res = []
            for l in out.splitlines():
                l = l.strip()
                if not l: continue
                parts = l.split()
                if len(parts) >= 2:
                    pref = int(parts[0])
                    host = parts[1].rstrip('.')
                    res.append((pref, host))
            return sorted(res, key=lambda x: x[0])
        except Exception:
            return []

def resolve_host_to_ips(host: str) -> List[str]:
    """Повертає перелік A/AAAA-адрес для вказаного хоста."""
    ips = set()
    if DNSPY:
        for rtype in ('A', 'AAAA'):
            try:
                answers = dns.resolver.resolve(host, rtype, lifetime=8)
                for r in answers:
                    ips.add(str(r))
            except Exception:
                continue
    else:
        # Резервний шлях: socket.getaddrinfo
        try:
            addrs = socket.getaddrinfo(host, None)
            for a in addrs:
                ips.add(a[4][0])
        except Exception:
            pass
    return sorted(ips)

# Розбір SPF (проста токенізація)
SPF_TOK_RE = re.compile(r'(?P<term>(?:include:|ip4:|ip6:|a:|mx:|all|redirect=)[^\s]+|~all|\-all|\+all|\?all)')

def get_spf_record(domain: str) -> Optional[str]:
    txts = query_txt(domain)
    for t in txts:
        if t.lower().startswith("v=spf1"):
            return t
    return None

def parse_spf(spf: str) -> Dict[str, List[str]]:
    tokens = SPF_TOK_RE.findall(spf)
    res = {'ip4':[], 'ip6':[], 'include':[], 'a':[], 'mx':[], 'redirect':[], 'all':[]}
    for tok in tokens:
        if tok.startswith("ip4:"):
            res['ip4'].append(tok.split(":",1)[1])
        elif tok.startswith("ip6:"):
            res['ip6'].append(tok.split(":",1)[1])
        elif tok.startswith("include:"):
            res['include'].append(tok.split(":",1)[1])
        elif tok.startswith("a:"):
            res['a'].append(tok.split(":",1)[1])
        elif tok.startswith("mx:"):
            res['mx'].append(tok.split(":",1)[1])
        elif tok.startswith("redirect="):
            res['redirect'].append(tok.split("=",1)[1])
        elif tok.endswith("all"):
            res['all'].append(tok)
    return res

def expand_spf_includes(domain_or_include: str, visited=None) -> List[str]:
    """Повертає перелік ip4/ip6 з SPF та include/redirect (неповний, лише прямі записи)."""
    if visited is None:
        visited = set()
    to_process = [domain_or_include]
    ips = []
    while to_process:
        d = to_process.pop()
        if d in visited:
            continue
        visited.add(d)
        spf = get_spf_record(d)
        if not spf:
            continue
        parsed = parse_spf(spf)
        ips.extend(parsed.get('ip4',[]))
        ips.extend(parsed.get('ip6',[]))
        # Обробка include
        for inc in parsed.get('include',[]):
            to_process.append(inc)
        # Обробка redirect
        for rd in parsed.get('redirect',[]):
            to_process.append(rd)
    return sorted(set(ips))

def query_dmarc(domain: str) -> List[str]:
    return query_txt(f"_dmarc.{domain}")

def query_dkim_pubkey(domain: str, selector: str) -> List[str]:
    name = f"{selector}._domainkey.{domain}"
    return query_txt(name)

def query_tls_rpt(domain: str) -> List[str]:
    """Повертає TXT-записи TLS-RPT (_smtp._tls.<домен>)."""
    return query_txt(f"_smtp._tls.{domain}")

def query_mta_sts(domain: str) -> List[str]:
    """Повертає TXT-записи MTA-STS (_mta-sts.<домен>)."""
    return query_txt(f"_mta-sts.{domain}")

def reverse_dns_lookup(ip: str) -> List[str]:
    """Повертає PTR-імена для IP-адреси."""
    try:
        host, aliases, _ = socket.gethostbyaddr(ip)
        names = {host}
        names.update(aliases)
        return sorted(names)
    except Exception:
        return []

def check_starttls_support(ip: str, helo_name: str, timeout: int = 8) -> Dict[str, object]:
    """Перевіряє наявність STARTTLS та витягує базову інформацію про сертифікат."""
    result: Dict[str, object] = {
        "advertised": None,
        "handshake": None,
        "tls_version": None,
        "cert_subject": None,
        "cert_expiry": None,
        "error": None,
        "connect_reply": None,
        "ehlo_reply": None,
    }
    try:
        with smtplib.SMTP(timeout=timeout) as smtp:
            connect_code, connect_msg = smtp.connect(ip, 25)
            result["connect_reply"] = f"{connect_code} {connect_msg.decode().strip() if isinstance(connect_msg, bytes) else str(connect_msg).strip()}"
            ehlo_code, ehlo_msg = smtp.ehlo(helo_name)
            result["ehlo_reply"] = f"{ehlo_code} {ehlo_msg.decode().strip() if isinstance(ehlo_msg, bytes) else str(ehlo_msg).strip()}"
            if smtp.has_extn("starttls"):
                result["advertised"] = "yes"
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                smtp.starttls(context=context)
                result["handshake"] = "ok"
                tls_sock = smtp.sock
                if tls_sock and hasattr(tls_sock, "version"):
                    try:
                        result["tls_version"] = tls_sock.version()
                    except Exception:
                        pass
                try:
                    cert = tls_sock.getpeercert()
                except Exception:
                    cert = None
                if cert:
                    subject = cert.get("subject", ())
                    common_name = None
                    for item in subject:
                        for key, value in item:
                            if key.lower() == "commonname":
                                common_name = value
                    if common_name:
                        result["cert_subject"] = common_name
                    result["cert_expiry"] = cert.get("notAfter")
            else:
                result["advertised"] = "no"
    except smtplib.SMTPResponseException as exc:
        result["error"] = f"{exc.smtp_code} {exc.smtp_error.decode().strip() if isinstance(exc.smtp_error, bytes) else str(exc.smtp_error).strip()}"
    except Exception as exc:
        result["error"] = str(exc)
    return result

def check_open_relay(host: str, ip: str, domain: str, timeout: int = 10) -> Dict[str, object]:
    """Виконує спробу релею: MAIL FROM/RCPT TO на зовнішній домен без DATA."""
    result: Dict[str, object] = {
        "is_open": None,
        "reason": None,
        "transcript": [],
        "error": None,
    }
    helo_name = f"relay-check.{domain}".strip(".")
    sender = "relay-test@external-test.invalid"
    recipient = "relayed@external-target.invalid"

    def _fmt_reply(code: int, msg) -> str:
        if msg is None:
            return str(code)
        if isinstance(msg, bytes):
            msg = msg.decode(errors="ignore")
        return f"{code} {msg.strip()}"

    try:
        with smtplib.SMTP(timeout=timeout) as smtp:
            code, msg = smtp.connect(ip, 25)
            result["transcript"].append(f"CONNECT {host} ({ip}) -> {_fmt_reply(code, msg)}")
            code, msg = smtp.ehlo(helo_name)
            result["transcript"].append(f"EHLO {helo_name} -> {_fmt_reply(code, msg)}")
            code, msg = smtp.mail(sender)
            result["transcript"].append(f"MAIL FROM:<{sender}> -> {_fmt_reply(code, msg)}")
            try:
                code, msg = smtp.rcpt(recipient)
                reply = _fmt_reply(code, msg)
                result["transcript"].append(f"RCPT TO:<{recipient}> -> {reply}")
                if code in (250, 251, 252):
                    result["is_open"] = "yes"
                    result["reason"] = f"RCPT прийнято з кодом {code}"
                else:
                    result["is_open"] = "no"
                    result["reason"] = f"RCPT відповів кодом {code}"
            except smtplib.SMTPRecipientsRefused as refused:
                result["is_open"] = "no"
                if refused.recipients:
                    addr, (rcode, rmsg) = next(iter(refused.recipients.items()))
                    reply = _fmt_reply(rcode, rmsg)
                    result["transcript"].append(f"RCPT TO:<{addr}> -> {reply}")
                    result["reason"] = f"RCPT відхилено з кодом {rcode}"
                else:
                    result["reason"] = "RCPT відхилено без детального коду"
            except smtplib.SMTPResponseException as exc:
                result["is_open"] = "no"
                reply = _fmt_reply(exc.smtp_code, exc.smtp_error)
                result["transcript"].append(f"RCPT виняток -> {reply}")
                result["reason"] = f"RCPT завершився помилкою {exc.smtp_code}"
            finally:
                try:
                    smtp.rset()
                except Exception:
                    pass
    except Exception as exc:
        result["error"] = str(exc)
        result["is_open"] = "unknown"
    if result["reason"] is None and result["error"]:
        result["reason"] = "Перевірка не виконана через помилку"
    return result

def smtp_banner_grab(ip: str, timeout=6) -> Tuple[bool, str]:
    """Під'єднується до ip:25, читає банер. Повертає (успіх, банер/помилка)."""
    try:
        sock = socket.create_connection((ip, 25), timeout=timeout)
        sock.settimeout(4)
        banner = sock.recv(1024).decode(errors='replace').strip()
        sock.close()
        return True, banner
    except Exception as e:
        return False, str(e)

# --- Генерація звіту -------------------------------------------------
COMMON_DKIM_SELECTORS = ["default", "mail", "s1", "selector1", "smtp", "dkim"]

def build_report(domain: str, selectors: List[str]) -> str:
    out_lines = []
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    out_lines.append(f"SMTP remote check report for: {domain}")
    out_lines.append(f"Timestamp (UTC): {ts}")
    out_lines.append("="*70)

    # MX-записи
    out_lines.append("\n[MX records]")
    mxs = query_mx(domain)
    host_ips: Dict[str, List[str]] = {}
    ip_details: Dict[str, Dict[str, object]] = {}
    if not mxs:
        out_lines.append("  No MX records found.")
    else:
        for pr, host in mxs:
            out_lines.append(f"  {pr:3d}  {host}")
            ips = resolve_host_to_ips(host)
            host_ips[host] = ips
            if ips:
                for ip in ips:
                    info = ip_details.setdefault(ip, {"hosts": set(), "ptrs": None})
                    info["hosts"].add(host)
                    if info["ptrs"] is None:
                        info["ptrs"] = reverse_dns_lookup(ip)
                    out_lines.append(f"       -> {ip}")
                    ptrs = info.get("ptrs") or []
                    if ptrs:
                        out_lines.append(f"          PTR: {', '.join(ptrs)}")
                    else:
                        out_lines.append("          PTR: (no PTR found)")
            else:
                out_lines.append("       -> (no A/AAAA found)")

    # SPF-записи
    out_lines.append("\n[SPF]")
    spf = get_spf_record(domain)
    if not spf:
        out_lines.append("  No SPF (v=spf1) TXT record found for domain.")
    else:
        out_lines.append(f"  SPF record: {spf}")
        parsed = parse_spf(spf)
        out_lines.append("  Parsed tokens:")
        for k in ('ip4','ip6','include','a','mx','redirect','all'):
            if parsed.get(k):
                out_lines.append(f"    {k}: {', '.join(parsed[k])}")
        # Розширюємо include/redirect, щоб зібрати додаткові ip4/ip6 (неповний список)
        out_lines.append("  Expanded ip4/ip6 from SPF and includes (may not include 'a'/'mx' resolved IPs):")
        expanded = expand_spf_includes(domain)
        if expanded:
            for ip in expanded:
                out_lines.append(f"    {ip}")
        else:
            out_lines.append("    (none found via includes)")

    # Перевіряємо, чи перетинаються IP MX із ip4/ip6 зі SPF (базова евристика)
    out_lines.append("\n[SPF vs MX heuristic]")
    if mxs and spf:
        mx_ips = []
        for _, host in mxs:
            mx_ips.extend(host_ips.get(host, []))
        spf_ip_list = expand_spf_includes(domain)  # ip4/ip6 з include/redirect
        # Додаємо безпосередні ip4/ip6 із розібраного SPF
        parsed = parse_spf(spf)
        spf_ip_list = sorted(set(spf_ip_list + parsed.get('ip4',[]) + parsed.get('ip6',[])))
        out_lines.append(f"  MX IPs: {', '.join(mx_ips) if mx_ips else '(none resolved)'}")
        out_lines.append(f"  SPF-declared IPs: {', '.join(spf_ip_list) if spf_ip_list else '(none found)'}")
        common = set(mx_ips).intersection(set(spf_ip_list))
        if common:
            out_lines.append(f"  Intersection: {', '.join(sorted(common))}  (some MX IPs appear in SPF)")
        else:
            out_lines.append("  Intersection: none (MX IPs not explicitly present in discovered SPF ip4/ip6 entries)")
    else:
        out_lines.append("  Skipped (no MX or no SPF)")

    # DMARC
    out_lines.append("\n[DMARC]")
    dmarc = query_dmarc(domain)
    if not dmarc:
        out_lines.append("  No DMARC record found at _dmarc."+domain)
    else:
        for line in dmarc:
            out_lines.append(f"  DMARC TXT: {line}")

    # TLS-RPT (_smtp._tls)
    out_lines.append("\n[TLS-RPT]")
    tls_rpt = query_tls_rpt(domain)
    if not tls_rpt:
        out_lines.append(f"  No TLS-RPT record found at _smtp._tls.{domain}")
    else:
        for line in tls_rpt:
            out_lines.append(f"  _smtp._tls TXT: {line}")

    # MTA-STS (_mta-sts)
    out_lines.append("\n[MTA-STS]")
    mta_sts = query_mta_sts(domain)
    if not mta_sts:
        out_lines.append(f"  No MTA-STS record found at _mta-sts.{domain}")
    else:
        for line in mta_sts:
            out_lines.append(f"  _mta-sts TXT: {line}")

    # DKIM-селектори
    out_lines.append("\n[DKIM public keys]")
    selectors_checked = selectors if selectors else COMMON_DKIM_SELECTORS
    for sel in selectors_checked:
        txts = query_dkim_pubkey(domain, sel)
        if txts:
            out_lines.append(f"  Selector '{sel}': FOUND (first line shown):")
            out_lines.append(f"    {txts[0]}")
        else:
            out_lines.append(f"  Selector '{sel}': not found")

    # Отримання банера SMTP для кожного MX IP
    out_lines.append("\n[SMTP banner grab (connect to MX IPs port 25)]")
    if mxs and ip_details:
        for ip, info in sorted(ip_details.items()):
            hosts = ", ".join(sorted(info.get("hosts", [])))
            out_lines.append(f"  Connecting to {hosts} ({ip}) ...")
            ok, banner = smtp_banner_grab(ip)
            info["banner"] = (ok, banner)
            if ok:
                out_lines.append(f"    Banner: {banner}")
            else:
                out_lines.append(f"    Error: {banner}")
    else:
        out_lines.append("  No MX records to connect to.")

    # Перевірка підтримки STARTTLS
    out_lines.append("\n[STARTTLS support]")
    if mxs and ip_details:
        for ip, info in sorted(ip_details.items()):
            hosts = sorted(info.get("hosts", []))
            display_host = hosts[0] if hosts else ip
            out_lines.append(f"  {display_host} ({ip})")
            result = check_starttls_support(ip, domain)
            info["starttls"] = result
            error = result.get("error")
            if result.get("connect_reply"):
                out_lines.append(f"    Connect: {result['connect_reply']}")
            if result.get("ehlo_reply"):
                out_lines.append(f"    EHLO: {result['ehlo_reply']}")
            if error:
                out_lines.append(f"    Error: {error}")
                continue
            advertised = result.get("advertised")
            if advertised == "yes":
                out_lines.append("    STARTTLS: advertised")
                if result.get("handshake") == "ok":
                    if result.get("tls_version"):
                        out_lines.append(f"    TLS version: {result['tls_version']}")
                    if result.get("cert_subject"):
                        out_lines.append(f"    Cert CN: {result['cert_subject']}")
                    if result.get("cert_expiry"):
                        out_lines.append(f"    Cert notAfter: {result['cert_expiry']}")
                else:
                    out_lines.append("    STARTTLS handshake failed")
            elif advertised == "no":
                out_lines.append("    STARTTLS: not offered")
            else:
                out_lines.append("    STARTTLS: unknown")
    else:
        out_lines.append("  No MX records to check.")

    # Перевірка на відкритий релей
    out_lines.append("\n[Open relay test]")
    if mxs and ip_details:
        for ip, info in sorted(ip_details.items()):
            hosts = sorted(info.get("hosts", []))
            display_host = hosts[0] if hosts else ip
            result = check_open_relay(display_host, ip, domain)
            info["relay"] = result
            out_lines.append(f"  {display_host} ({ip})")
            if result.get("error"):
                out_lines.append(f"    Error: {result['error']}")
                continue
            is_open = result.get("is_open") or "unknown"
            out_lines.append(f"    Open relay: {is_open}")
            if result.get("reason"):
                out_lines.append(f"    Reason: {result['reason']}")
            transcript = result.get("transcript") or []
            for line in transcript:
                out_lines.append(f"      {line}")
    else:
        out_lines.append("  No MX records to test.")

    out_lines.append("\n" + "="*70)
    out_lines.append("Note: this script performs remote checks only (DNS lookups and connecting to MX on port 25).")
    out_lines.append("It does NOT access mail server logs or any internal files. Interpret results as preliminary; "
                     "for full assurance, follow server-side log analysis and rotate keys/certificates if compromise suspected.")
    return "\n".join(out_lines)

def write_report_to_file(report: str, domain: str, outdir: str = ".") -> str:
    fname = f"smtp_remote_check_{domain}_{now_ts()}.log"
    path = os.path.join(outdir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    return path

# --- Інтерфейс командного рядка (CLI) --------------------------------------
def main():
    p = argparse.ArgumentParser(description="Remote SMTP checks for a domain (DNS, MX, SPF, DMARC, DKIM, STARTTLS, relay, banner).")
    p.add_argument("--domain", "-d", required=True, help="Domain to check (e.g. example.com)")
    p.add_argument("--selectors", "-s", default="", help="Comma-separated DKIM selectors to check (default: common set)")
    p.add_argument("--outdir", "-o", default=".", help="Directory to save the report file")
    args = p.parse_args()

    domain = args.domain.strip().lower()
    selectors = [x.strip() for x in args.selectors.split(",") if x.strip()] if args.selectors else []
    if not selectors:
        selectors = COMMON_DKIM_SELECTORS

    try:
        report = build_report(domain, selectors)
        print(report)
        path = write_report_to_file(report, domain, args.outdir)
        print(f"\nReport saved to: {path}")
    except Exception as exc:
        eprint("Error during checks:", exc)
        sys.exit(2)

if __name__ == "__main__":
    main()
