import sys
import os

# Ensure the services directory is discoverable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.smtp_service import generate_permutations, verify_email_smtp

def run_smtp_tests():
    print("==================================================")
    print("🔍 Testing SMTP Service Isolation & Permutations")
    print("==================================================\n")

    # --- TEST 1: Permutation Generator ---
    print("1️⃣ Testing Permutation Generation:")
    first_name = "Tim"
    last_name = "Cook"
    domain = "apple.com"
    
    perms = generate_permutations(first_name, last_name, domain)
    print(f"Target: {first_name} {last_name} ({domain})")
    print("Generated Candidates:")
    for idx, p in enumerate(perms, 1):
        print(f"   [{idx}] {p}")
    print()

    # --- TEST 2: Live SMTP Handshake & Permutation Verification ---
    print("2️⃣ Testing Live SMTP Handshake Verification:")
    test_leads = [
        {
            "first_name": "Satya",
            "last_name": "Nadella",
            "domain": "microsoft.com",
            "title": "CEO",
            "linkedin_url": "https://www.linkedin.com/in/satyanadella"
        },
        {
            "first_name": "John",
            "last_name": "Doe",
            "domain": "nonexistentfakedomain9999.com",  # Expected to fail gracefully
            "title": "Manager",
            "linkedin_url": "https://www.linkedin.com/in/johndoe"
        }
    ]

    for lead in test_leads:
        fn = lead["first_name"]
        ln = lead["last_name"]
        dom = lead["domain"]
        
        print(f"Testing Lead: {fn} {ln} @ {dom}...")
        
        # Execute SMTP verification
        email, status = verify_email_smtp(fn, ln, dom)
        
        # Append email result as handled in app.py
        lead["email"] = email if status == "Valid" else ""
        
        print(f" ├─ SMTP Result Status : {status}")
        print(f" ├─ Assigned Email     : '{lead['email']}'")
        print(f" └─ Profile Retained   : Yes (LinkedIn: {lead['linkedin_url']})\n")

    print("==================================================")
    print("✅ SMTP Service Isolation Test Finished!")
    print("==================================================")

if __name__ == "__main__":
    run_smtp_tests()