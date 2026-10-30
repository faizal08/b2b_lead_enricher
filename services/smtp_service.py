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
        # Sort by preference/priority to hit the primary mail server first
        sorted_records = sorted(records, key=lambda r: r.preference)
        mx_record = str(sorted_records[0].exchange)
        return mx_record
    except Exception:
        return None

def verify_single_email(email):
    """
    Performs a secure, throttled SMTP handshake verification for a single email candidate.
    """
    try:
        domain = email.split('@')[1]
        mx_host = get_mx_record(domain)
        
        if not mx_host:
            return False

        # Establish SMTP connection with timeout protection
        server = smtplib.SMTP(timeout=10)
        server.connect(mx_host)
        
        # Use a realistic local hostname for the EHLO greeting
        server.helo("mail.leadintelligence.internal")
        server.mail("verify@leadintelligence.internal")
        
        code, _ = server.rcpt(email)
        server.quit()
        
        # SMTP code 250 means the email address is accepted/valid
        if code == 250:
            return True
            
        return False
        
    except (smtplib.SMTPConnectError, socket.timeout, socket.error):
        # Network timeout or connection drop (often due to rate limits)
        return False
    except Exception:
        return False

def verify_email_smtp(first_name, last_name, domain):
    """
    Handles email permutation generation and local SMTP mail server validation
    with built-in anti-bot throttling and random delays.
    """
    permutations = generate_permutations(first_name, last_name, domain)
    
    if not permutations:
        return "", "Invalid"

    for email_candidate in permutations:
        # ANTI-BOT SAFEGUARD: Add a human-like randomized delay between checks 
        # to prevent triggering server rate-limiters and IP blacklists.
        sleep_duration = random.uniform(1.2, 2.5)
        time.sleep(sleep_duration)

        is_valid = verify_single_email(email_candidate)
        if is_valid:
            return email_candidate, "Valid"
            
    # Fallback if none of the permutations returned a 250 OK response
    return "", "Invalid"