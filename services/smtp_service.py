import socket
import smtplib
import dns.resolver
import time
import random

def generate_permutations(first_name, last_name, domain):
    """
    Generates common corporate email permutations based on name and domain.
    """
    if not first_name or not last_name or not domain:
        return []
        
    fn = first_name.strip().lower().replace(" ", "")
    ln = last_name.strip().lower().replace(" ", "")
    dom = domain.strip().lower()
    
    # Common B2B email permutations (prioritizing most likely first)
    perms = [
        f"{fn}.{ln}@{dom}",      # firstname.lastname@domain.com
        f"{fn}@{dom}",           # firstname@domain.com
        f"{fn[0]}{ln}@{dom}",    # flastname@domain.com
        f"{fn}{ln[0]}@{dom}",    # firstnamel@domain.com
        f"{fn}_{ln}@{dom}"       # firstname_lastname@domain.com
    ]
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(perms))

def get_mx_record(domain):
    """
    Retrieves the primary MX (Mail Exchange) server for a given domain.
    """
    try:
        records = dns.resolver.resolve(domain, 'MX')
        sorted_records = sorted(records, key=lambda r: r.preference)
        mx_record = str(sorted_records[0].exchange)
        return mx_record
    except Exception:
        return None

def check_catch_all(domain, mx_host):
    """
    SAFEGUARD 1: Tests if the domain is a catch-all server by probing a random fake email.
    If it accepts a fake address with 250 OK, brute-forcing permutations is skipped.
    """
    fake_email = f"nonexistenttestuser99998888@{domain}"
    try:
        server = smtplib.SMTP(timeout=8)
        server.connect(mx_host)
        server.helo("mail.lead-verify.net")
        server.mail("verify@lead-verify.net")
        code, _ = server.rcpt(fake_email)
        server.quit()
        return code == 250
    except Exception:
        return False

def verify_single_email(email):
    """
    Performs a secure, heavily throttled SMTP handshake verification for a single email candidate.
    """
    try:
        domain = email.split('@')[1]
        mx_host = get_mx_record(domain)
        
        if not mx_host:
            return "Invalid", False

        server = smtplib.SMTP(timeout=10)
        server.connect(mx_host)
        
        # SAFEGUARD 3: Use a realistic sender identity domain for EHLO and MAIL FROM
        server.helo("mail.lead-verify.net")
        server.mail("verify@lead-verify.net")
        
        code, _ = server.rcpt(email)
        server.quit()
        
        # SMTP code 250 means valid/accepted
        if code == 250:
            return "Valid", True
            
        # SAFEGUARD 4: Detect soft fails / temporary blocks (e.g., 421 service unavailable / rate-limited)
        if 400 <= code < 500:
            return "SoftFail", False
            
        return "Invalid", False
        
    except (smtplib.SMTPConnectError, socket.timeout, socket.error):
        # Network drop or rate limit connection refusal
        return "SoftFail", False
    except Exception:
        return "Invalid", False

def verify_email_smtp(first_name, last_name, domain):
    """
    Handles email permutation generation and local SMTP mail server validation
    with built-in anti-bot throttling, catch-all detection, and soft-fail protection.
    """
    if not domain:
        return "", "Invalid"

    mx_host = get_mx_record(domain)
    if not mx_host:
        return "", "Invalid"

    # SAFEGUARD 1: Check if the target domain is a Catch-All server
    if check_catch_all(domain, mx_host):
        print(f"⚠️ [SMTP Notice] Domain '{domain}' is a Catch-All server. Skipping permutation brute-force to protect IP reputation.")
        fn = first_name.strip().lower().replace(" ", "")
        ln = last_name.strip().lower().replace(" ", "")
        default_email = f"{fn}.{ln}@{domain}"
        return default_email, "Valid"

    permutations = generate_permutations(first_name, last_name, domain)
    if not permutations:
        return "", "Invalid"

    for email_candidate in permutations:
        # SAFEGUARD 2: Increased Pacing (3.0 to 5.0 seconds random jitter between probes)
        sleep_duration = random.uniform(3.0, 5.0)
        time.sleep(sleep_duration)

        status, is_valid = verify_single_email(email_candidate)
        
        if is_valid:
            return email_candidate, "Valid"
            
        # SAFEGUARD 4: Abort further permutations immediately if server gives a SoftFail / rate limit
        if status == "SoftFail":
            print(f"⚠️ [SMTP SoftFail] Server for {domain} throttled or temporarily blocked connection. Aborting further checks for safety.")
            break
            
    # Fallback if none of the permutations returned a 250 OK response
    return "", "Invalid"