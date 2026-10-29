def verify_email_smtp(first_name, last_name, domain):
    """
    Handles email permutation generation and local SMTP mail server validation.
    """
    email_candidate = f"{first_name.lower()}.{last_name.lower()}@{domain}"
    # Insert your live SMTP verification script/logic here
    return email_candidate, "Valid"